"""应用配置：从环境变量 / .env 加载。"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- 应用 ----------
    app_env: Literal["dev", "prod"] = "dev"
    app_name: str = "ai-news"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    timezone: str = "Asia/Shanghai"

    # ---------- 数据库 ----------
    database_url: str = Field(
        default="postgresql+psycopg://ainews:ainews_pass_change_me@postgres:5432/ainews"
    )

    # ---------- Redis / Celery ----------
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # ---------- LLM ----------
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    openai_base_url: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    llm_monthly_budget_usd: float = 30.0
    llm_timeout_seconds: int = 60

    # ---------- Embedding ----------
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    embedding_similarity_threshold: float = 0.92
    embedding_dedup_days: int = 7

    # ---------- Dashboard 认证 ----------
    admin_password: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    auth_enabled: bool = True

    # ---------- 飞书 ----------
    feishu_webhook: str = ""
    feishu_secret: str = ""

    # ---------- 推送策略 ----------
    daily_digest_cron: str = "30 8 * * *"
    weekly_digest_cron: str = "0 9 * * 1"
    collect_cron: str = "*/30 * * * *"
    instant_push_cron: str = "*/5 * * * *"
    instant_push_min_score: float = 9.0
    daily_push_min_score: float = 7.0
    daily_push_top_n: int = 10
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:30"

    # ---------- 用户偏好 ----------
    user_interests: str = "LLM=1.0,Agent=0.9,RAG=0.8"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def auth_required(self) -> bool:
        return self.auth_enabled and bool(self.admin_password.strip())

    @property
    def interests_map(self) -> dict[str, float]:
        """解析 USER_INTERESTS 为 dict。"""
        result: dict[str, float] = {}
        for pair in self.user_interests.split(","):
            pair = pair.strip()
            if not pair or "=" not in pair:
                continue
            key, value = pair.split("=", 1)
            try:
                result[key.strip()] = float(value.strip())
            except ValueError:
                continue
        return result


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例获取配置。"""
    return Settings()


settings = get_settings()
