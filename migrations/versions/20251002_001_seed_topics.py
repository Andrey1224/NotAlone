"""Seed initial topics

Revision ID: 20251002_001
Revises: 20251002
Create Date: 2025-10-02 10:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = '20251002_001'
down_revision: Union[str, None] = '20251002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create topics table reference
    topics_table = table('topics',
        column('slug', sa.String),
        column('title', sa.String)
    )

    # Insert seed topics
    op.bulk_insert(topics_table, [
        {'slug': 'divorce', 'title': '💔 Развод'},
        {'slug': 'burnout', 'title': '🔥 Выгорание'},
        {'slug': 'relocation', 'title': '🏠 Переезд'},
        {'slug': 'job_change', 'title': '💼 Смена работы'},
        {'slug': 'loss', 'title': '😢 Утрата'},
        {'slug': 'growth', 'title': '🌱 Личностный рост'},
        {'slug': 'anxiety', 'title': '😰 Тревога'},
        {'slug': 'loneliness', 'title': '🫂 Одиночество'},
        {'slug': 'parenting', 'title': '👶 Родительство'},
        {'slug': 'health', 'title': '🏥 Здоровье'},
        {'slug': 'relationships', 'title': '💑 Отношения'},
        {'slug': 'career', 'title': '📈 Карьера'},
    ])


def downgrade() -> None:
    # Delete seed topics
    op.execute("DELETE FROM topics WHERE slug IN ('divorce', 'burnout', 'relocation', 'job_change', 'loss', 'growth', 'anxiety', 'loneliness', 'parenting', 'health', 'relationships', 'career')")
