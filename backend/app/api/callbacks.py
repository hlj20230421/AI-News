"""飞书卡片回调。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import FeishuCardCallbackIn, UserActionOut
from app.config import settings
from app.db import get_db
from app.db.models import Article, UserAction

router = APIRouter(prefix="/callbacks/feishu", tags=["callbacks"])

ALLOWED_ACTIONS = {"bookmark", "later", "dismiss", "open", "note", "hide"}


def _parse_action_value(value: Any) -> tuple[int, str]:
    if isinstance(value, dict):
        article_id = value.get("article_id") or value.get("articleId")
        action = value.get("action") or value.get("type")
        if article_id is not None and action:
            return int(article_id), str(action).strip().lower()
    if isinstance(value, str):
        parts = value.split(":", 1)
        if len(parts) == 2 and parts[0].isdigit():
            return int(parts[0]), parts[1].strip().lower()
    raise ValueError("无法解析 action value")


@router.post("/card")
def feishu_card_callback(payload: FeishuCardCallbackIn, db: Session = Depends(get_db)) -> dict:
    if payload.challenge:
        return {"challenge": payload.challenge}

    if settings.feishu_secret and payload.token and payload.token != settings.feishu_secret:
        raise HTTPException(status_code=403, detail="token 校验失败")

    action_block = payload.action or {}
    value = action_block.get("value")
    if value is None:
        return {"ok": True}

    try:
        article_id, action = _parse_action_value(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail=f"不支持的 action: {action}")

    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article 不存在")

    record = UserAction(
        article_id=article_id,
        action=action,
        note=None,
        channel="feishu",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return UserActionOut.model_validate(record).model_dump()
