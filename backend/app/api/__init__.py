"""REST API 路由汇总。"""

from fastapi import APIRouter

from app.api import actions, articles, auth, callbacks, health, push_logs, sources, user_actions

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(callbacks.router)
api_router.include_router(sources.router)
api_router.include_router(articles.router)
api_router.include_router(user_actions.router)
api_router.include_router(push_logs.router)
api_router.include_router(actions.router)

__all__ = ["api_router"]
