"""Celery 任务定义。

Step 1：
- ping：链路连通性
- collect_all：定时采集所有启用的 RSS 源
- analyze_article：分析单篇文章
- send_daily_digest：推送日报
"""

from __future__ import annotations

from app.scheduler.celery_app import celery_app
from app.utils.logging import logger


@celery_app.task(name="app.scheduler.tasks.ping")
def ping() -> str:
    logger.info("ping task executed")
    return "pong"


@celery_app.task(name="app.scheduler.tasks.collect_all")
def collect_all() -> dict[str, int]:
    """定时采集任务：抓取所有启用源并触发新文章的分析。"""
    from app.services.collect_service import collect_all_sources

    results = collect_all_sources()
    total_inserted = sum(r.inserted for r in results)
    new_ids: list[int] = []
    for r in results:
        new_ids.extend(r.article_ids)

    for aid in new_ids:
        analyze_article.delay(aid)

    logger.info(
        "collect_all 完成：sources={} inserted={} dispatched={}",
        len(results),
        total_inserted,
        len(new_ids),
    )
    return {
        "sources": len(results),
        "inserted": total_inserted,
        "dispatched": len(new_ids),
    }


@celery_app.task(name="app.scheduler.tasks.analyze_article")
def analyze_article(article_id: int) -> int | None:
    """异步分析单篇文章。"""
    from app.services.analyze_service import analyze_article_by_id

    return analyze_article_by_id(article_id)


@celery_app.task(name="app.scheduler.tasks.analyze_pending")
def analyze_pending(limit: int = 10) -> dict:
    from app.services.analyze_service import analyze_pending_articles

    ids = analyze_pending_articles(limit=limit)
    return {"analyzed": len(ids), "analysis_ids": ids}


@celery_app.task(name="app.scheduler.tasks.send_daily_digest")
def send_daily_digest(force: bool = False) -> dict:
    """日报推送。"""
    from app.services.digest_service import send_daily_digest as _send

    result = _send(force=force)
    return {
        "pushed": result.pushed,
        "item_count": result.item_count,
        "batch_key": result.batch_key,
        "skipped_reason": result.skipped_reason,
    }


@celery_app.task(name="app.scheduler.tasks.send_instant_digest")
def send_instant_digest(force: bool = False) -> dict:
    """即时推送扫描。"""
    from app.services.digest_service import send_instant_digest as _send

    result = _send(force=force)
    return {
        "pushed": result.pushed,
        "item_count": result.item_count,
        "batch_key": result.batch_key,
        "skipped_reason": result.skipped_reason,
    }
