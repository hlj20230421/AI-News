"""手动触发端点：抓取、分析、推送。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas import (
    CollectResponse,
    PushDailyResponse,
    StatsOut,
)
from app.db import get_db
from app.db.models import Analysis, Article, PushLog, Source
from app.services.analyze_service import analyze_article_by_id
from app.services.collect_service import collect_source
from app.services.digest_service import send_daily_digest

router = APIRouter(tags=["actions"])


@router.post("/collect/{source_id}", response_model=CollectResponse)
def trigger_collect(source_id: int) -> CollectResponse:
    try:
        result = collect_source(source_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CollectResponse(
        source_id=result.source_id,
        source_name=result.source_name,
        fetched=result.fetched,
        inserted=result.inserted,
        skipped=result.skipped,
        error=result.error,
    )


@router.post("/articles/{article_id}/analyze")
def trigger_analyze(article_id: int) -> dict:
    analysis_id = analyze_article_by_id(article_id)
    if analysis_id is None:
        raise HTTPException(status_code=400, detail="分析失败或文章不存在")
    return {"article_id": article_id, "analysis_id": analysis_id}


@router.post("/push/daily", response_model=PushDailyResponse)
def trigger_daily_digest(force: bool = False) -> PushDailyResponse:
    result = send_daily_digest(force=force)
    return PushDailyResponse(
        pushed=result.pushed,
        item_count=result.item_count,
        batch_key=result.batch_key,
        skipped_reason=result.skipped_reason,
    )


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)) -> StatsOut:
    today_start = datetime.now(tz=timezone.utc) - timedelta(hours=24)

    sources_total = db.scalar(select(func.count(Source.id))) or 0
    sources_enabled = (
        db.scalar(select(func.count(Source.id)).where(Source.enabled.is_(True))) or 0
    )
    articles_total = db.scalar(select(func.count(Article.id))) or 0
    articles_today = (
        db.scalar(
            select(func.count(Article.id)).where(Article.collected_at >= today_start)
        )
        or 0
    )
    analyses_total = db.scalar(select(func.count(Analysis.id))) or 0
    cost_total = db.scalar(select(func.coalesce(func.sum(Analysis.cost_usd), 0.0))) or 0.0
    pushes_today = (
        db.scalar(
            select(func.count(PushLog.id)).where(PushLog.pushed_at >= today_start)
        )
        or 0
    )

    return StatsOut(
        sources_total=sources_total,
        sources_enabled=sources_enabled,
        articles_total=articles_total,
        articles_today=articles_today,
        analyses_total=analyses_total,
        cost_usd_total=float(cost_total),
        pushes_today=pushes_today,
    )
