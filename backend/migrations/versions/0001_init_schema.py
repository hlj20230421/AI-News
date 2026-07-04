"""init schema (Step 1): sources / articles / analyses / push_logs

Revision ID: 0001_init_schema
Revises:
Create Date: 2026-04-27 00:00:00
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_init_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=32), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("url", name="uq_sources_url"),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=1024), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("lang", sa.String(length=16), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("url", name="uq_articles_url"),
    )
    op.create_index("ix_articles_content_hash", "articles", ["content_hash"])
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index(
        "ix_articles_source_id_published_at",
        "articles",
        ["source_id", "published_at"],
    )

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("score_reason", sa.Text(), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["article_id"], ["articles.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("article_id", name="uq_analyses_article_id"),
    )
    op.create_index("ix_analyses_score", "analyses", ["score"])
    op.create_index("ix_analyses_analyzed_at", "analyses", ["analyzed_at"])

    op.create_table(
        "push_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("event", sa.String(length=32), nullable=False),
        sa.Column("batch_key", sa.String(length=128), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "status", sa.String(length=16), nullable=False, server_default="success"
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("pushed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["article_id"], ["articles.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint(
            "channel", "batch_key", name="uq_push_logs_channel_batch"
        ),
    )
    op.create_index("ix_push_logs_event", "push_logs", ["event"])
    op.create_index("ix_push_logs_pushed_at", "push_logs", ["pushed_at"])


def downgrade() -> None:
    op.drop_index("ix_push_logs_pushed_at", table_name="push_logs")
    op.drop_index("ix_push_logs_event", table_name="push_logs")
    op.drop_table("push_logs")

    op.drop_index("ix_analyses_analyzed_at", table_name="analyses")
    op.drop_index("ix_analyses_score", table_name="analyses")
    op.drop_table("analyses")

    op.drop_index("ix_articles_source_id_published_at", table_name="articles")
    op.drop_index("ix_articles_published_at", table_name="articles")
    op.drop_index("ix_articles_content_hash", table_name="articles")
    op.drop_table("articles")

    op.drop_table("sources")
