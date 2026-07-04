"""add user_actions table

Revision ID: 0002_user_actions
Revises: 0002_pgvector_embedding
Create Date: 2026-04-29 12:00:00
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_user_actions"
down_revision: Union[str, None] = "0002_pgvector_embedding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="dashboard"),
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
    )
    op.create_index("ix_user_actions_article_id", "user_actions", ["article_id"])
    op.create_index("ix_user_actions_action", "user_actions", ["action"])
    op.create_index("ix_user_actions_created_at", "user_actions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_user_actions_created_at", table_name="user_actions")
    op.drop_index("ix_user_actions_action", table_name="user_actions")
    op.drop_index("ix_user_actions_article_id", table_name="user_actions")
    op.drop_table("user_actions")
