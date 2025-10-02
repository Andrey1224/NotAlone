"""Match worker for processing match queue."""

import asyncio
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import AsyncSessionLocal
from core.redis import get_redis
from models.user import User
from models.topic import UserTopic
from models.match import Match


class MatchWorker:
    """Worker for processing match queue from Redis."""

    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        """Start the match worker."""
        self.running = True
        redis_client = await get_redis()

        print("Match worker started...")

        while self.running:
            try:
                # Read from Redis stream
                # TODO: Implement Redis Streams consumer
                # messages = await redis_client.xreadgroup(...)

                # For now, just sleep
                await asyncio.sleep(5)

            except Exception as e:
                print(f"Error in match worker: {e}")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop the match worker."""
        self.running = False

    async def process_match_request(self, user_id: int, topics: list[str], timezone: str) -> Optional[Match]:
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

            # Create match
            match = Match(user_a=user_id, user_b=best_candidate, status="proposed")
            db.add(match)
            await db.commit()

            return match

    async def _find_candidates(
        self, db: AsyncSession, user_id: int, topics: list[str], timezone: str
    ) -> list[int]:
        """Find potential match candidates."""
        # TODO: Implement candidate finding logic
        # 1. Find users with ≥2 overlapping topics
        # 2. Filter by timezone compatibility
        # 3. Exclude recent matches
        # 4. Exclude users not in queue

        return []

    async def _score_candidates(
        self, db: AsyncSession, user_id: int, candidates: list[int], topics: list[str]
    ) -> Optional[int]:
        """
        Score and rank candidates.

        Scoring formula: 0.6 * tag_overlap + 0.2 * time_overlap + 0.2 * helpfulness_score
        """
        # TODO: Implement scoring logic
        return candidates[0] if candidates else None


async def main() -> None:
    """Run match worker."""
    worker = MatchWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
