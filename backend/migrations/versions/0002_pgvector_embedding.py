"""step2 pgvector: analyses.embedding + article content tsvector index

Revision ID: 0002_pgvector_embedding
Revises: 0001_init_schema
Create Date: 2026-04-28 23:00:00
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_pgvector_embedding"
down_revision: Union[str, None] = "0001_init_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("analyses", sa.Column("embedding", sa.ARRAY(sa.Float()), nullable=True))
    op.execute("ALTER TABLE analyses ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_articles_content_tsv
        ON articles
        USING gin (to_tsvector('simple', coalesce(content, '')))
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_articles_content_tsv")
    op.drop_column("analyses", "embedding")
