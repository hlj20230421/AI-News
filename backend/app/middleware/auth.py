"""全局 JWT 认证中间件。"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.auth import decode_access_token
from app.config import settings

PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth/login",
    "/callbacks/feishu/card",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.auth_required or request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path.rstrip("/") or "/"
        if path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return JSONResponse(status_code=401, content={"detail": "需要登录"})
        token = auth_header.split(" ", 1)[1].strip()
        try:
            decode_access_token(token)
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "无效或过期的令牌"})
        return await call_next(request)
