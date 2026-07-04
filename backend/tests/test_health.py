"""健康检查端点测试。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "app" in data
    assert "version" in data


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "env" in data
    assert "db" in data


def test_config_interests_parsing() -> None:
    from app.config import Settings

    s = Settings(user_interests="LLM=1.0, Agent=0.5 ,bad, Multi=0.3")
    interests = s.interests_map
    assert interests["LLM"] == 1.0
    assert interests["Agent"] == 0.5
    assert interests["Multi"] == 0.3
    assert "bad" not in interests
