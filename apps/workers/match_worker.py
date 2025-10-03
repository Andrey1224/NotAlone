"""Match worker for processing match queue."""

import asyncio
from datetime import datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.workers.notifier import notifier
from core.db import AsyncSessionLocal
from core.redis import get_redis
from models.match import Match
from models.recent_contact import RecentContact
from models.topic import Topic, UserTopic


class MatchWorker:
    """Worker for processing match queue from Redis."""

    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        """Start the match worker."""
        self.running = True
        redis_client = await get_redis()

        stream_name = "match.find"
        group_name = "matchers"
        consumer_name = "worker-1"

        print(f"Match worker started, consuming from {stream_name}...")

        # Create consumer group if not exists
        try:
            await redis_client.xgroup_create(name=stream_name, groupname=group_name, id="0", mkstream=True)
            print(f"Created consumer group: {group_name}")
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                print(f"Error creating group: {e}")

        while self.running:
            try:
                # Read from Redis stream with blocking
                messages = await redis_client.xreadgroup(
                    groupname=group_name,
                    consumername=consumer_name,
                    streams={stream_name: ">"},
                    count=1,
                    block=5000,  # 5 seconds timeout
                )

                if messages:
                    for stream_key, stream_messages in messages:
                        for message_id, message_data in stream_messages:
                            print(f"Processing message {message_id}: {message_data}")

                            try:
                                # Extract data
                                user_id = int(message_data["user_id"])
                                topics = message_data["topics"].split(",")
                                timezone = message_data["timezone"]

                                # Process match request
                                match = await self.process_match_request(user_id, topics, timezone)

                                if match:
                                    print(f"[WORKER] Created match: {match.id}")
                                    # Send notification to both users via bot
                                    print(f"[WORKER] Sending notifications for match {match.id}...")
                                    async with AsyncSessionLocal() as db:
                                        print(f"[WORKER] Notifying user_a={match.user_a}...")
                                        result_a = await notifier.send_match_proposal(
                                            db, match.id, match.user_a, match.user_b
                                        )
                                        print(f"[WORKER] User A notification result: {result_a}")

                                        print(f"[WORKER] Notifying user_b={match.user_b}...")
                                        result_b = await notifier.send_match_proposal(
                                            db, match.id, match.user_b, match.user_a
                                        )
                                        print(f"[WORKER] User B notification result: {result_b}")

                                    print(f"[WORKER] ✅ Match {match.id} notifications completed")
                                else:
                                    print(f"[WORKER] No match found for user {user_id}")

                                # Acknowledge message
                                await redis_client.xack(stream_name, group_name, message_id)  # type: ignore[no-untyped-call]

                            except Exception as e:
                                print(f"Error processing message {message_id}: {e}")
                                # Move to dead letter queue
                                await redis_client.xadd("match.dead", message_data)
                                await redis_client.xack(stream_name, group_name, message_id)  # type: ignore[no-untyped-call]

            except Exception as e:
                print(f"Error in match worker loop: {e}")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop the match worker."""
        self.running = False

    async def process_match_request(self, user_id: int, topics: list[str], timezone: str) -> Match | None:
        """
        Process match request for a user.

        Args:
            user_id: User ID looking for match
            topics: List of topic slugs
            timezone: User timezone

        Returns:
            Match object if found, None otherwise
        """
        async with AsyncSessionLocal() as db:
            # Find candidates with overlapping topics
            candidates = await self._find_candidates(db, user_id, topics, timezone)

            if not candidates:
                return None

            # Score candidates
            best_candidate = await self._score_candidates(db, user_id, candidates, topics)

            if not best_candidate:
                return None

            # Create match with 5 minute expiry
            # Use ordered pair (u_lo, u_hi) to prevent duplicate matches
            u_lo, u_hi = sorted([user_id, best_candidate])
            expires_at = datetime.utcnow() + timedelta(minutes=5)

            match = Match(
                user_a=user_id,
                user_b=best_candidate,
                u_lo=u_lo,
                u_hi=u_hi,
                status="proposed",
                expires_at=expires_at,
            )

            try:
                db.add(match)
                await db.commit()
                await db.refresh(match)
                return match
            except Exception as e:
                # Handle duplicate match race condition (unique index violation)
                await db.rollback()
                print(f"Match creation failed (likely duplicate): {e}")
                # Try to find existing match
                from sqlalchemy import and_, select

                result = await db.execute(
                    select(Match).where(and_(Match.u_lo == u_lo, Match.u_hi == u_hi, Match.status == "proposed"))
                )
                existing_match = result.scalar_one_or_none()
                if existing_match:
                    print(f"Found existing match: {existing_match.id}")
                    return existing_match
                # If no existing match found, re-raise
                raise

    async def _find_candidates(self, db: AsyncSession, user_id: int, topics: list[str], timezone: str) -> list[int]:
        """Find potential match candidates."""
        # Get topic IDs from slugs
        topic_result = await db.execute(select(Topic.id).where(Topic.slug.in_(topics)))
        topic_ids = [row[0] for row in topic_result.all()]

        if len(topic_ids) < 2:
            return []

        # Find users with ≥2 overlapping topics
        # Exclude: self, recent contacts
        query = (
            select(UserTopic.user_id, func.count(UserTopic.topic_id).label("shared_count"))
            .where(
                and_(
                    UserTopic.topic_id.in_(topic_ids),
                    UserTopic.user_id != user_id,
                    # Exclude recent contacts
                    ~UserTopic.user_id.in_(
                        select(RecentContact.other_id).where(
                            and_(RecentContact.user_id == user_id, RecentContact.until > datetime.utcnow())
                        )
                    ),
                )
            )
            .group_by(UserTopic.user_id)
            .having(func.count(UserTopic.topic_id) >= 2)
            .limit(10)
        )

        result = await db.execute(query)
        candidates = [row[0] for row in result.all()]

        # TODO: Filter by timezone compatibility (±3 hours)
        return candidates

    async def _score_candidates(
        self, db: AsyncSession, user_id: int, candidates: list[int], topics: list[str]
    ) -> int | None:
        """
        Score and rank candidates.

        Scoring formula: 0.6 * tag_overlap + 0.2 * time_overlap + 0.2 * helpfulness_score
        """
        if not candidates:
            return None

        # Get topic IDs from slugs
        topic_result = await db.execute(select(Topic.id).where(Topic.slug.in_(topics)))
        user_topic_ids = {row[0] for row in topic_result.all()}

        best_candidate = None
        best_score = -1.0

        for candidate_id in candidates:
            # Get candidate's topics
            candidate_topics_result = await db.execute(
                select(UserTopic.topic_id).where(UserTopic.user_id == candidate_id)
            )
            candidate_topic_ids = {row[0] for row in candidate_topics_result.all()}

            # Calculate shared topics
            shared_topics = user_topic_ids & candidate_topic_ids
            shared_count = len(shared_topics)

            # Tag overlap score: min(shared / 5, 1.0) to normalize
            tag_score = min(shared_count / 5.0, 1.0)

            # Time overlap: placeholder (TODO: implement timezone check)
            time_score = 0.5  # Assume 50% overlap for now

            # Helpfulness score: placeholder (TODO: implement based on ratings)
            helpfulness_score = 0.5  # Neutral score

            # Calculate total score
            total_score = 0.6 * tag_score + 0.2 * time_score + 0.2 * helpfulness_score

            if total_score > best_score:
                best_score = total_score
                best_candidate = candidate_id

        return best_candidate


async def main() -> None:
    """Run match worker."""
    worker = MatchWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
