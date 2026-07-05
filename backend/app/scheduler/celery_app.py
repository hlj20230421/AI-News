"""Celery 应用入口。

beat_schedule 从 settings 的 cron 字符串解析（minute hour day-of-month month day-of-week）。
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings


def _crontab_from_str(expr: str) -> crontab:
    """把 5 段 crontab 字符串转换为 Celery crontab 对象。"""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(
            f"cron 表达式必须 5 段（minute hour dom month dow），实际：{expr!r}"
        )
    minute, hour, dom, month, dow = parts
    return crontab(
        minute=minute,
        hour=hour,
        day_of_month=dom,
        month_of_year=month,
        day_of_week=dow,
    )


celery_app = Celery(
    "ai_news",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.scheduler.tasks"],
)

celery_app.conf.update(
    timezone=settings.timezone,
    enable_utc=False,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    result_expires=60 * 60 * 24 * 7,
)

celery_app.conf.beat_schedule = {
    "collect-all": {
        "task": "app.scheduler.tasks.collect_all",
        "schedule": _crontab_from_str(settings.collect_cron),
    },
    "send-daily-digest": {
        "task": "app.scheduler.tasks.send_daily_digest",
        "schedule": _crontab_from_str(settings.daily_digest_cron),
    },
    "send-instant-digest": {
        "task": "app.scheduler.tasks.send_instant_digest",
        "schedule": _crontab_from_str(settings.instant_push_cron),
    },
    "analyze-pending": {
        "task": "app.scheduler.tasks.analyze_pending",
        "schedule": crontab(minute="*/10"),
        "kwargs": {"limit": 20},
    },
}
