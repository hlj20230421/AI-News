"""飞书 Notifier 与卡片单测。"""

from __future__ import annotations

import base64
import hashlib
import hmac

from app.notifiers.cards import DigestItem, build_daily_digest_card, score_emoji
from app.notifiers.feishu import gen_feishu_sign


def test_feishu_sign_matches_official_algorithm() -> None:
    ts = 1700000000
    secret = "abc123"

    expected_key = f"{ts}\n{secret}".encode("utf-8")
    expected = base64.b64encode(
        hmac.new(expected_key, b"", hashlib.sha256).digest()
    ).decode("utf-8")

    assert gen_feishu_sign(ts, secret) == expected


def test_score_emoji_levels() -> None:
    assert score_emoji(9.5) == "🔥"
    assert score_emoji(8.0) == "⭐"
    assert score_emoji(6.5) == "✨"
    assert score_emoji(3.0) == "📰"


def test_build_daily_digest_card_with_items() -> None:
    items = [
        DigestItem(
            title="Title A",
            url="https://example.com/a",
            summary="Summary A",
            score=9.0,
            tags=["LLM", "Agent"],
            source_name="OpenAI Blog",
        ),
        DigestItem(
            title="Title B",
            url="https://example.com/b",
            summary="Summary B",
            score=7.5,
            tags=["RAG"],
            source_name="Anthropic",
        ),
    ]
    payload = build_daily_digest_card(items=items, title="测试日报")
    assert payload["msg_type"] == "interactive"
    assert payload["card"]["header"]["title"]["content"] == "测试日报"
    elements = payload["card"]["elements"]
    assert any("Title A" in str(el) for el in elements)
    assert any("阅读原文" in str(el) for el in elements)


def test_build_daily_digest_card_empty() -> None:
    payload = build_daily_digest_card(items=[])
    elements = payload["card"]["elements"]
    assert any("没有达到推送阈值" in str(el) for el in elements)
