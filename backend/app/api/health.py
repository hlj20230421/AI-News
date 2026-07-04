"""健康检查与基础信息端点。"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app import __version__
from app.config import settings
from app.db import engine
from app.utils.logging import logger

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    env: str
    db: str
    redis: str = "unknown"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """简单健康检查：顺便探活 DB。"""
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {exc.__class__.__name__}"
        logger.warning("DB health check failed: {}", exc)

    return HealthResponse(
        status="ok",
        version=__version__,
        env=settings.app_env,
        db=db_status,
    )


@router.get("/")
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "version": __version__,
        "docs": "/docs",
    }
