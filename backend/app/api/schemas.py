"""API 端点用到的 pydantic 模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    # rss/arxiv/hn 为 URL；html 可为容器内 YAML 路径（如 /app/scripts/html_sources/foo.yaml）
    url: str = Field(min_length=1, max_length=1024)
    type: str = Field(default="rss", max_length=32)
    description: str | None = None
    enabled: bool = True


class SourceUpdate(BaseModel):
    name: str | None = None
    url: str | None = Field(default=None, min_length=1, max_length=1024)
    type: str | None = Field(default=None, max_length=32)
    description: str | None = None
    enabled: bool | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    url: str
    description: str | None = None
    enabled: bool
    last_fetched_at: datetime | None = None
    last_status: str | None = None
    last_error: str | None = None


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: str
    tags: list[str] | None = None
    category: str | None = None
    score: float
    score_reason: str | None = None
    model: str | None = None
    analyzed_at: datetime


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    url: str
    title: str
    author: str | None = None
    published_at: datetime | None = None
    summary: str | None = None
    lang: str | None = None
    collected_at: datetime
    analysis: AnalysisOut | None = None


class CollectResponse(BaseModel):
    source_id: int
    source_name: str
    fetched: int
    inserted: int
    skipped: int
    error: str | None = None


class StatsOut(BaseModel):
    sources_total: int
    sources_enabled: int
    articles_total: int
    articles_today: int
    analyses_total: int
    cost_usd_total: float
    pushes_today: int


class PushDailyResponse(BaseModel):
    pushed: bool
    item_count: int
    batch_key: str
    skipped_reason: str | None = None


class PushLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    event: str
    batch_key: str
    article_id: int | None = None
    status: str
    error: str | None = None
    pushed_at: datetime


class UserActionIn(BaseModel):
    article_id: int = Field(ge=1)
    action: str = Field(min_length=1, max_length=32)
    note: str | None = None
    channel: str = Field(default="dashboard", max_length=32)


class UserActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    action: str
    note: str | None = None
    channel: str
    created_at: datetime


class FeishuCardCallbackIn(BaseModel):
    challenge: str | None = None
    token: str | None = None
    type: str | None = None
    action: dict | None = None
