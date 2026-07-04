"""HTMLCollector：本地 HTML 解析单测（不联网）。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.collectors.html import HTMLSourceConfig, extract_articles_from_html

FIXTURE = Path(__file__).parent / "fixtures" / "html_list_sample.html"


def test_extract_articles_basic() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    cfg = HTMLSourceConfig(
        entry_url="https://blog.example.com/news/",
        list_selector="ul.posts li.post",
        link_selector="a.title",
        title_selector="a.title",
        summary_selector="p.excerpt",
        time_selector="time[datetime]",
        max_items=10,
    )
    items = extract_articles_from_html(html, cfg)
    assert len(items) == 2

    first = items[0]
    assert first.title == "First Post"
    assert first.url == "https://blog.example.com/articles/one"
    assert first.summary == "Summary one"
    assert first.published_at == datetime(2026, 1, 2, 12, 0, tzinfo=UTC)

    second = items[1]
    assert second.title == "Second Post"
    assert second.url == "https://other.example/full"
    assert second.summary is None


def test_html_source_config_requires_fields() -> None:
    with pytest.raises(ValueError, match="缺少必填字段"):
        HTMLSourceConfig.from_dict({"entry_url": "https://x.com"})
