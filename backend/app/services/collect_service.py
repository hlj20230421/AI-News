"""采集服务：按源类型调度采集器、去重、入库。"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select

from app.collectors import COLLECTOR_TYPES
from app.db import SessionLocal
from app.db.models import Article, Source
from app.services.dedup_service import find_similar_article_id
from app.utils.logging import logger

@dataclass
class CollectResult:
    source_id: int
    source_name: str
    fetched: int = 0
    inserted: int = 0
    skipped: int = 0
    semantic_skipped: int = 0
    article_ids: list[int] | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.article_ids is None:
            self.article_ids = []


def _content_hash(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha1(text.strip().encode("utf-8", errors="ignore")).hexdigest()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_collector(source: Source):
    collector_cls = COLLECTOR_TYPES.get(source.type)
    if collector_cls is None:
        raise ValueError(f"暂不支持 type={source.type}")
    return collector_cls(source.url)


def collect_source(source_id: int) -> CollectResult:
    with SessionLocal() as session:
        source = session.get(Source, source_id)
        if not source:
            raise ValueError(f"Source id={source_id} 不存在")
        if not source.enabled:
            return CollectResult(source_id=source.id, source_name=source.name)

        try:
            raw_items = _get_collector(source).fetch()
        except Exception as exc:  # noqa: BLE001
            source.last_status = "error"
            source.last_error = str(exc)[:500]
            source.last_fetched_at = datetime.now(tz=UTC)
            session.commit()
            return CollectResult(source_id=source.id, source_name=source.name, error=str(exc))

        result = CollectResult(source_id=source.id, source_name=source.name, fetched=len(raw_items))
        existing_urls = set(session.execute(select(Article.url)).scalars())
        for item in raw_items:
            if item.url in existing_urls:
                result.skipped += 1
                continue

            similar_id, similarity = find_similar_article_id(
                session,
                title=item.title,
                summary=item.summary,
                content=item.content,
            )
            if similar_id is not None:
                result.semantic_skipped += 1
                result.skipped += 1
                logger.info(
                    "跳过语义重复 url={} similar_article_id={} similarity={}",
                    item.url,
                    similar_id,
                    similarity,
                )
                continue

            article = Article(
                source_id=source.id,
                url=item.url,
                title=item.title[:1024],
                author=(item.author or None) and item.author[:255],
                published_at=item.published_at,
                summary=item.summary,
                content=item.content,
                raw_html=None,
                lang=item.lang,
                content_hash=_content_hash(item.content or item.summary),
                extra={**(item.extra or {}), "collector": source.type},
                collected_at=datetime.now(tz=UTC),
            )
            session.add(article)
            session.flush()
            result.inserted += 1
            result.article_ids.append(article.id)
            existing_urls.add(item.url)

        source.last_fetched_at = datetime.now(tz=UTC)
        source.last_status = "ok"
        source.last_error = None
        session.commit()

        if result.article_ids:
            from app.scheduler.tasks import analyze_article

            for article_id in result.article_ids:
                analyze_article.delay(article_id)

        return result


def collect_all_sources() -> list[CollectResult]:
    with SessionLocal() as session:
        ids = list(session.execute(select(Source.id).where(Source.enabled.is_(True))).scalars())
    return [collect_source(i) for i in ids]
