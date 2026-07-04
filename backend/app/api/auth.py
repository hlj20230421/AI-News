"""JWT 单用户认证。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    password: str = Field(min_length=1)


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    exp: int


def create_access_token() -> tuple[str, int]:
    expires = timedelta(hours=settings.jwt_expire_hours)
    expire_at = datetime.now(tz=UTC) + expires
    payload = {"sub": "admin", "exp": int(expire_at.timestamp())}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, int(expires.total_seconds())


def decode_access_token(token: str) -> TokenPayload:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenPayload(sub=data["sub"], exp=data["exp"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效或过期的令牌") from exc


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn) -> LoginOut:
    if not settings.admin_password:
        raise HTTPException(status_code=503, detail="未配置 ADMIN_PASSWORD，认证已禁用")
    if payload.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="口令错误")
    token, expires_in = create_access_token()
    return LoginOut(access_token=token, expires_in=expires_in)
