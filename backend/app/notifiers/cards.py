"""飞书交互卡片生成。

仅生成 dict（payload），HTTP 发送由 FeishuNotifier 负责。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


def score_emoji(score: float) -> str:
    if score >= 9:
        return "🔥"
    if score >= 7.5:
        return "⭐"
    if score >= 6:
        return "✨"
    return "📰"


def _truncate(text: str, n: int) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


@dataclass
class DigestItem:
    """日报中的一条文章。"""

    title: str
    url: str
    summary: str
    score: float
    tags: list[str]
    source_name: str
    article_id: int | None = None
    published_at: datetime | None = None


def _format_tags(tags: list[str]) -> str:
    if not tags:
        return ""
    return " ".join(f"`{t}`" for t in tags[:5])


def build_daily_digest_card(
    *,
    items: list[DigestItem],
    title: str = "AI 日报 · TOP",
    instant: bool = False,
) -> dict[str, Any]:
    """构造日报飞书交互卡片。"""
    elements: list[dict[str, Any]] = []

    if not items:
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**今天没有达到推送阈值的文章。**",
                },
            }
        )
    else:
        for idx, item in enumerate(items, start=1):
            tag_line = _format_tags(item.tags)
            prefix = "🔥 " if instant and item.score >= 9 else ""
            md_lines = [
                f"**{idx}. {prefix}{score_emoji(item.score)} [{_truncate(item.title, 80)}]({item.url})**",
                f"评分：`{item.score:.1f}` · 来源：{item.source_name}",
            ]
            if tag_line:
                md_lines.append(f"标签：{tag_line}")
            md_lines.append("")
            md_lines.append(_truncate(item.summary, 280))

            elements.append(
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "\n".join(md_lines),
                    },
                }
            )
            elements.append(
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "阅读原文"},
                            "type": "primary",
                            "url": item.url,
                        }
                    ],
                }
            )
            if idx != len(items):
                elements.append({"tag": "hr"})

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": "blue",
        },
        "elements": elements,
    }

    return {"msg_type": "interactive", "card": card}


def build_text_message(text: str) -> dict[str, Any]:
    """简单文本消息（用于自测）。"""
    return {"msg_type": "text", "content": {"text": text}}


__all__ = [
    "DigestItem",
    "build_daily_digest_card",
    "build_text_message",
    "score_emoji",
]
