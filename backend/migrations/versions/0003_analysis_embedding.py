"""add pgvector extension and analysis.embedding

Revision ID: 0003_analysis_embedding
Revises: 0002_user_actions
Create Date: 2026-05-21 10:00:00
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0003_analysis_embedding"
down_revision: Union[str, None] = "0002_user_actions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS embedding vector(1536)")


def downgrade() -> None:
    op.execute("ALTER TABLE analyses DROP COLUMN IF EXISTS embedding")
