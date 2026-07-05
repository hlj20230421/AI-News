"""日报/即时推送服务。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.config import settings
from app.db import SessionLocal
from app.db.models import Analysis, Article, PushLog
from app.notifiers import DigestItem, FeishuNotifier, build_daily_digest_card
from app.utils.quiet_hours import in_quiet_hours


@dataclass
class DigestResult:
    pushed: bool
    item_count: int
    batch_key: str
    skipped_reason: str | None = None


def _upsert_push_log(
    session,
    *,
    channel: str,
    event: str,
    batch_key: str,
    article_id: int | None,
    payload: dict,
    status: str,
    error: str | None,
) -> None:
    """按 (channel, batch_key) 写入或更新推送日志，避免 force 重推时触发唯一约束。"""
    existing = session.execute(
        select(PushLog).where(PushLog.channel == channel, PushLog.batch_key == batch_key)
    ).scalar_one_or_none()
    now = datetime.now(tz=UTC)
    if existing is not None:
        existing.event = event
        existing.article_id = article_id
        existing.payload = payload
        existing.status = status
        existing.error = error
        existing.pushed_at = now
        return

    session.add(
        PushLog(
            channel=channel,
            event=event,
            batch_key=batch_key,
            article_id=article_id,
            payload=payload,
            status=status,
            error=error,
            pushed_at=now,
        )
    )


def send_daily_digest(*, min_score: float | None = None, top_n: int | None = None, force: bool = False) -> DigestResult:
    min_score = settings.daily_push_min_score if min_score is None else min_score
    top_n = settings.daily_push_top_n if top_n is None else top_n
    batch_key = f"daily:{datetime.now(tz=UTC).strftime('%Y-%m-%d')}"

    with SessionLocal() as session:
        if not force:
            existing = session.execute(
                select(PushLog).where(PushLog.channel == "feishu", PushLog.batch_key == batch_key, PushLog.status == "success")
            ).scalar_one_or_none()
            if existing:
                prev_count = int((existing.payload or {}).get("item_count") or 0)
                if prev_count > 0:
                    return DigestResult(False, 0, batch_key, "already_pushed")

        since = datetime.now(tz=UTC) - timedelta(hours=24)
        analyses = list(
            session.execute(
                select(Analysis)
                .options(joinedload(Analysis.article).joinedload(Article.source))
                .where(Analysis.score >= min_score, Analysis.analyzed_at >= since)
                .order_by(Analysis.score.desc(), Analysis.analyzed_at.desc())
                .limit(top_n)
            ).scalars()
        )
        items = [
            DigestItem(
                title=a.article.title,
                url=a.article.url,
                summary=a.summary,
                score=a.score,
                tags=list(a.tags or []),
                source_name=a.article.source.name if a.article.source else "",
                article_id=a.article_id,
                published_at=a.article.published_at,
            )
            for a in analyses
        ]
        if not items and not force:
            return DigestResult(False, 0, batch_key, "no_candidates")

        payload = build_daily_digest_card(items=items, title=f"AI 日报 · TOP {len(items)}")
        ok = FeishuNotifier().send(payload)
        _upsert_push_log(
            session,
            channel="feishu",
            event="daily",
            batch_key=batch_key,
            article_id=None,
            payload={"item_count": len(items)},
            status="success" if ok else "failed",
            error=None if ok else "see logs",
        )
        session.commit()
        return DigestResult(ok, len(items), batch_key, None if ok else "send_failed")


def send_instant_digest(*, force: bool = False) -> DigestResult:
    if not force and in_quiet_hours():
        return DigestResult(False, 0, "instant:quiet", "quiet_hours")

    with SessionLocal() as session:
        since = datetime.now(tz=UTC) - timedelta(hours=6)
        candidates = list(
            session.execute(
                select(Analysis)
                .options(joinedload(Analysis.article).joinedload(Article.source))
                .where(Analysis.score >= settings.instant_push_min_score, Analysis.analyzed_at >= since)
                .order_by(Analysis.score.desc(), Analysis.analyzed_at.desc())
                .limit(20)
            ).scalars()
        )
        if not candidates:
            return DigestResult(False, 0, "instant:scan", "no_candidates")

        pushed_ids: list[int] = []
        for analysis in candidates:
            batch_key = f"article:{analysis.article_id}"
            if not force:
                existing = session.execute(
                    select(PushLog).where(
                        PushLog.channel == "feishu",
                        PushLog.event == "instant",
                        PushLog.batch_key == batch_key,
                        PushLog.status == "success",
                    )
                ).scalar_one_or_none()
                if existing:
                    continue

            payload = build_daily_digest_card(
                items=[
                    DigestItem(
                        title=analysis.article.title,
                        url=analysis.article.url,
                        summary=analysis.summary,
                        score=analysis.score,
                        tags=list(analysis.tags or []),
                        source_name=analysis.article.source.name if analysis.article.source else "",
                        article_id=analysis.article_id,
                    )
                ],
                title="🔥 AI 快讯 · 突发",
                instant=True,
            )
            ok = FeishuNotifier().send(payload)
            _upsert_push_log(
                session,
                channel="feishu",
                event="instant",
                batch_key=batch_key,
                article_id=analysis.article_id,
                payload={"score": analysis.score},
                status="success" if ok else "failed",
                error=None if ok else "see logs",
            )
            if ok:
                pushed_ids.append(analysis.article_id)
            session.commit()
            if ok:
                return DigestResult(True, 1, batch_key, None)

        return DigestResult(False, 0, "instant:scan", "all_already_pushed" if candidates else "no_candidates")
