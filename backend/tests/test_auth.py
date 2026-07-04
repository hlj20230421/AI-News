"""JWT 认证单测。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import get_db
from app.main import app


@pytest.fixture()
def authed_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("ADMIN_PASSWORD", "test-pass")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    get_settings.cache_clear()

    import app.api.auth as auth_module
    import app.config as config_module
    import app.middleware.auth as middleware_module

    fresh = get_settings()
    monkeypatch.setattr(config_module, "settings", fresh, raising=False)
    monkeypatch.setattr(auth_module, "settings", fresh, raising=False)
    monkeypatch.setattr(middleware_module, "settings", fresh, raising=False)

    yield TestClient(app)
    get_settings.cache_clear()


def test_login_success(authed_client: TestClient) -> None:
    resp = authed_client.post("/auth/login", json={"password": "test-pass"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password(authed_client: TestClient) -> None:
    resp = authed_client.post("/auth/login", json={"password": "wrong"})
    assert resp.status_code == 401


def test_protected_route_requires_token(authed_client: TestClient) -> None:
    resp = authed_client.get("/stats")
    assert resp.status_code == 401

    login = authed_client.post("/auth/login", json={"password": "test-pass"})
    token = login.json()["access_token"]

    class FakeSession:
        def scalar(self, _stmt: object) -> int:
            return 0

    def override_db():
        yield FakeSession()

    app.dependency_overrides[get_db] = override_db
    try:
        resp2 = authed_client.get("/stats", headers={"Authorization": f"Bearer {token}"})
        assert resp2.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_health_is_public(authed_client: TestClient) -> None:
    resp = authed_client.get("/health")
    assert resp.status_code == 200
