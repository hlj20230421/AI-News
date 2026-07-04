"""推送历史查询。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.schemas import PushLogOut
from app.db import get_db
from app.db.models import PushLog

router = APIRouter(prefix="/push-logs", tags=["push-logs"], dependencies=[Depends(require_auth)])


@router.get("", response_model=list[PushLogOut])
def list_push_logs(
    channel: str | None = Query(default=None),
    event: str | None = Query(default=None),
    status: str | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[PushLog]:
    stmt = select(PushLog).order_by(PushLog.pushed_at.desc())
    if channel:
        stmt = stmt.where(PushLog.channel == channel)
    if event:
        stmt = stmt.where(PushLog.event == event)
    if status:
        stmt = stmt.where(PushLog.status == status)
    if start_at is not None:
        stmt = stmt.where(PushLog.pushed_at >= start_at)
    if end_at is not None:
        stmt = stmt.where(PushLog.pushed_at <= end_at)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.execute(stmt).scalars())
