"""Step 1 数据模型 v1。

四张表：Source / Article / Analysis / PushLog
依赖：app.db.base.Base + TimestampMixin
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Source(Base, TimestampMixin):
    """信息源（RSS / 后续扩展 arxiv / github 等）。"""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="rss")
    url: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    last_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    articles: Mapped[list["Article"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Source id={self.id} name={self.name!r} type={self.type}>"


class Article(Base, TimestampMixin):
    """采集到的原始文章。"""

    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_source_id_published_at", "source_id", "published_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )

    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    lang: Mapped[str | None] = mapped_column(String(16), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    source: Mapped[Source] = relationship(back_populates="articles")
    analysis: Mapped["Analysis | None"] = relationship(
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Article id={self.id} title={self.title[:40]!r}>"


class Analysis(Base, TimestampMixin):
    """LLM 分析结果（一对一 Article）。"""

    __tablename__ = "analyses"
    __table_args__ = (
        Index("ix_analyses_score", "score"),
        Index("ix_analyses_analyzed_at", "analyzed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    article: Mapped[Article] = relationship(back_populates="analysis")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Analysis id={self.id} score={self.score} category={self.category}>"


class PushLog(Base, TimestampMixin):
    """推送记录。

    `batch_key` 用于幂等：
    - 单文章即时推送：`article:{article_id}`
    - 日报：`daily:YYYY-MM-DD`
    - 周报：`weekly:YYYY-WW`
    """

    __tablename__ = "push_logs"
    __table_args__ = (
        UniqueConstraint("channel", "batch_key", name="uq_push_logs_channel_batch"),
        Index("ix_push_logs_event", "event"),
        Index("ix_push_logs_pushed_at", "pushed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    event: Mapped[str] = mapped_column(String(32), nullable=False)
    batch_key: Mapped[str] = mapped_column(String(128), nullable=False)
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("articles.id", ondelete="SET NULL"), nullable=True
    )

    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    pushed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class UserAction(Base, TimestampMixin):
    """用户行为（收藏 / 稍后读 / 不感兴趣 / 笔记等）。"""

    __tablename__ = "user_actions"
    __table_args__ = (
        Index("ix_user_actions_article_id", "article_id"),
        Index("ix_user_actions_action", "action"),
        Index("ix_user_actions_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="dashboard")


__all__ = ["Source", "Article", "Analysis", "PushLog", "UserAction"]
