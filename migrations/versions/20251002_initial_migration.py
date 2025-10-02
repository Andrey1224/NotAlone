"""Initial migration: users, topics, matches, chats, tips, ai

Revision ID: 20251002
Revises:
Create Date: 2025-10-02 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20251002'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create topics table
    op.create_table('topics',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('slug', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=128), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topics_slug'), 'topics', ['slug'], unique=True)

    # Create users table
    op.create_table('users',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('tg_id', sa.BigInteger(), nullable=False),
    sa.Column('nickname', sa.String(length=64), nullable=False),
    sa.Column('tz', sa.String(length=32), nullable=False),
    sa.Column('bio_short', sa.String(length=160), nullable=True),
    sa.Column('safety_ack', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_tg_id'), 'users', ['tg_id'], unique=True)

    # Create user_topics table
    op.create_table('user_topics',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'topic_id')
    )
    op.create_index('idx_user_topics_topic_id', 'user_topics', ['topic_id'], unique=False)

    # Create matches table
    op.create_table('matches',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_a', sa.BigInteger(), nullable=False),
    sa.Column('user_b', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('declined_by', sa.BigInteger(), nullable=True),
    sa.Column('declined_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_a'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_b'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_matches_user_a'), 'matches', ['user_a'], unique=False)
    op.create_index(op.f('ix_matches_user_b'), 'matches', ['user_b'], unique=False)

    # Create chat_sessions table
    op.create_table('chat_sessions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('match_id', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('ended_at', sa.DateTime(), nullable=True),
    sa.Column('rating_a', sa.Integer(), nullable=True),
    sa.Column('rating_b', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    # Create tips table
    op.create_table('tips',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('match_id', sa.Integer(), nullable=False),
    sa.Column('from_user', sa.BigInteger(), nullable=False),
    sa.Column('to_user', sa.BigInteger(), nullable=False),
    sa.Column('amount_minor', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('provider', sa.String(length=32), nullable=False),
    sa.Column('provider_fee_minor', sa.Integer(), nullable=False),
    sa.Column('our_commission_minor', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('paid_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['from_user'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['to_user'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    # Create ai_hints table
    op.create_table('ai_hints',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('chat_session_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('hint_type', sa.String(length=32), nullable=False),
    sa.Column('text', sa.String(length=512), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('accepted', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['chat_session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    # Create safety_flags table
    op.create_table('safety_flags',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('chat_session_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('label', sa.String(length=64), nullable=False),
    sa.Column('severity', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['chat_session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('safety_flags')
    op.drop_table('ai_hints')
    op.drop_table('tips')
    op.drop_table('chat_sessions')
    op.drop_index(op.f('ix_matches_user_b'), table_name='matches')
    op.drop_index(op.f('ix_matches_user_a'), table_name='matches')
    op.drop_table('matches')
    op.drop_index('idx_user_topics_topic_id', table_name='user_topics')
    op.drop_table('user_topics')
    op.drop_index(op.f('ix_users_tg_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_topics_slug'), table_name='topics')
    op.drop_table('topics')
