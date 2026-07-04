"""FastAPI 应用入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import api_router
from app.config import settings
from app.middleware.auth import AuthMiddleware
from app.utils.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger.info(
        "Starting {} v{} in {} mode",
        settings.app_name,
        __version__,
        settings.app_env,
    )
    yield
    logger.info("Shutting down {}", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI-News",
        description="AI 资讯智能聚合与推送系统",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "dev" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuthMiddleware)

    app.include_router(api_router)
    return app


app = create_app()
