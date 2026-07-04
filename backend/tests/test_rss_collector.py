"""RSSCollector 解析单测：用本地 fixture 文件，不联网。"""

from __future__ import annotations

from pathlib import Path

from app.collectors.rss import RSSCollector

FIXTURE = Path(__file__).parent / "fixtures" / "sample_rss.xml"


def test_rss_parse_basic() -> None:
    collector = RSSCollector(FIXTURE.as_uri(), fetch_full_content=False)
    items = collector.fetch()

    assert len(items) == 2
    titles = [item.title for item in items]
    assert "OpenAI releases new model" in titles
    assert "New Agent framework benchmarks" in titles

    first = next(i for i in items if i.title == "OpenAI releases new model")
    assert first.url == "https://example.com/post/1"
    assert first.author == "alice@example.com"
    assert first.published_at is not None
    assert first.summary  # 不为空


def test_rss_parse_skip_empty_link() -> None:
    collector = RSSCollector(FIXTURE.as_uri(), fetch_full_content=False)
    items = collector.fetch()
    urls = [item.url for item in items]
    assert all(u for u in urls)
