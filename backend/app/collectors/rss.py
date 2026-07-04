"""RSSCollector：基于 feedparser + trafilatura。

工作流：
1. https 源用 httpx 拉取 XML 再 feedparser.parse（避免 urllib 在部分环境下 SSL EOF）
2. 对每条尝试用 trafilatura 抓正文（HTTP 失败时降级到 RSS summary）
3. 返回 RawArticle 列表（不直接入库，由 service 层做去重 + 持久化）
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import feedparser
import httpx
import trafilatura

from app.collectors.base import BaseCollector, RawArticle
from app.utils.logging import logger

DEFAULT_TIMEOUT = 15.0
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; AI-News-Bot/0.1; +https://example.com)"
)


def _struct_time_to_dt(value: time.struct_time | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime(*value[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _parse_published(entry: dict) -> datetime | None:
    return _struct_time_to_dt(
        entry.get("published_parsed") or entry.get("updated_parsed")
    )


def _fetch_html(url: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """优先通过 httpx 拿 HTML（带超时 + UA），失败返回 None。"""
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as exc:  # noqa: BLE001
        logger.debug("RSS fetch_html failed for {}: {}", url, exc)
        return None


def _fetch_feed_body(url: str, timeout: float) -> bytes:
    """拉取 RSS/Atom XML。httpx 的 TLS 栈在部分环境下比 urllib（feedparser 默认 URL 抓取）更稳。"""
    last_exc: Exception | None = None
    for attempt in range(_FEED_FETCH_RETRIES):
        if attempt > 0:
            time.sleep(_FEED_FETCH_BACKOFF_SEC[attempt])
        try:
            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": DEFAULT_USER_AGENT},
            ) as client:
                resp = client.get(url)
                resp.raise_for_status()
                return resp.content
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "RSS feed HTTP attempt {}/{} failed for {}: {}",
                attempt + 1,
                _FEED_FETCH_RETRIES,
                url,
                exc,
            )
    raise RuntimeError(f"RSS feed fetch failed for {url}: {last_exc}") from last_exc


def _parse_feed(source_url: str, timeout: float):
    """解析 feed：远程 http(s) 走 httpx；file:// 等保持 feedparser 直接解析。"""
    if source_url.startswith(("http://", "https://")):
        body = _fetch_feed_body(source_url, timeout)
        return feedparser.parse(body)
    return feedparser.parse(source_url)


def _extract_main_text(html: str | None) -> str | None:
    if not html:
        return None
    try:
        return trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("trafilatura extract failed: {}", exc)
        return None


class RSSCollector(BaseCollector):
    """RSS 采集器。"""

    name = "rss"

    def __init__(
        self,
        source_url: str,
        *,
        max_items: int = 30,
        fetch_full_content: bool = True,
        request_timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.source_url = source_url
        self.max_items = max_items
        self.fetch_full_content = fetch_full_content
        self.request_timeout = request_timeout

    def fetch(self) -> list[RawArticle]:
        logger.info("RSSCollector start: {}", self.source_url)
        feed = _parse_feed(self.source_url, self.request_timeout)

        if getattr(feed, "bozo", False) and not feed.entries:
            err = getattr(feed, "bozo_exception", "unknown")
            raise RuntimeError(f"RSS parse failed for {self.source_url}: {err}")

        results: list[RawArticle] = []
        for entry in feed.entries[: self.max_items]:
            url = (entry.get("link") or "").strip()
            title = (entry.get("title") or "").strip()
            if not url or not title:
                continue

            published_at = _parse_published(entry)
            summary = (
                entry.get("summary")
                or entry.get("description")
                or None
            )
            author = entry.get("author") or None

            content: str | None = None
            raw_html: str | None = None
            if self.fetch_full_content:
                raw_html = _fetch_html(url, timeout=self.request_timeout)
                content = _extract_main_text(raw_html)

            content = content or summary

            results.append(
                RawArticle(
                    url=url,
                    title=title,
                    author=author,
                    published_at=published_at,
                    summary=summary,
                    content=content,
                    raw_html=None,  # 不入库，节省空间
                    lang=feed.feed.get("language"),
                    extra={
                        "feed_title": feed.feed.get("title"),
                        "entry_id": entry.get("id"),
                    },
                )
            )

        logger.info(
            "RSSCollector done: {} items from {}", len(results), self.source_url
        )
        return results


__all__ = ["RSSCollector"]
