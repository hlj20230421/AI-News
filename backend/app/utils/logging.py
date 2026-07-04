"""日志配置：基于 loguru 统一输出。"""

from __future__ import annotations

import sys

from loguru import logger

from app.config import settings


def setup_logging() -> None:
    """初始化全局日志。幂等，可多次调用。"""
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=settings.app_env == "dev",
    )


__all__ = ["logger", "setup_logging"]
