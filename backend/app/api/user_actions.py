"""用户行为记录端点。"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import UserActionIn, UserActionOut
from app.db import get_db
from app.db.models import Article, UserAction

router = APIRouter(prefix="/user-actions", tags=["user-actions"])

ALLOWED_ACTIONS = {"bookmark", "later", "dismiss", "open", "note", "hide"}


@router.get("", response_model=list[UserActionOut])
def list_user_actions(
    article_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> list[UserAction]:
    stmt = select(UserAction).order_by(UserAction.created_at.desc()).limit(limit)
    if article_id is not None:
        stmt = stmt.where(UserAction.article_id == article_id)
    if action is not None:
        stmt = stmt.where(UserAction.action == action.strip().lower())
    return list(db.execute(stmt).scalars())


@router.post("", response_model=UserActionOut)
def create_user_action(payload: UserActionIn, db: Session = Depends(get_db)) -> UserAction:
    action = payload.action.strip().lower()
    if action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail=f"不支持的 action: {payload.action}")

    article = db.get(Article, payload.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article 不存在")

    record = UserAction(
        article_id=payload.article_id,
        action=action,
        note=payload.note,
        channel=payload.channel or "dashboard",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
