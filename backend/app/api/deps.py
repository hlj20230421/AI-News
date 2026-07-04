"""API 依赖：认证等。"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.auth import decode_access_token
from app.config import settings

_bearer = HTTPBearer(auto_error=False)


def require_auth(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    if not settings.auth_required:
        return "anonymous"
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_access_token(credentials.credentials)
    return payload.sub
