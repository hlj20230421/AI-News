"""ArxivCollector：基于 arXiv API（Atom）。"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlencode

import feedparser
import httpx

from app.collectors.base import BaseCollector, RawArticle
from app.utils.logging import logger

DEFAULT_TIMEOUT = 20.0
DEFAULT_BASE_URL = "http://export.arxiv.org/api/query"
DEFAULT_CATEGORIES = ("cs.AI", "cs.CL", "cs.LG")


def _build_query(categories: tuple[str, ...]) -> str:
    return " OR ".join(f"cat:{c}" for c in categories)


class ArxivCollector(BaseCollector):
    name = "arxiv"

    def __init__(
        self,
        source_url: str = DEFAULT_BASE_URL,
        *,
        categories: tuple[str, ...] = DEFAULT_CATEGORIES,
        max_items: int = 30,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = source_url or DEFAULT_BASE_URL
        self.categories = categories
        self.max_items = max_items
        self.timeout = timeout

    def _request_url(self) -> str:
        params = {
            "search_query": _build_query(self.categories),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "start": 0,
            "max_results": self.max_items,
        }
        return f"{self.base_url}?{urlencode(params)}"

    def fetch(self) -> list[RawArticle]:
        request_url = self._request_url()
        logger.info("ArxivCollector start: {}", request_url)
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            resp = client.get(request_url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

        if getattr(feed, "bozo", False) and not feed.entries:
            err = getattr(feed, "bozo_exception", "unknown")
            raise RuntimeError(f"Arxiv parse failed: {err}")

        results: list[RawArticle] = []
        for entry in feed.entries[: self.max_items]:
            link = (entry.get("link") or "").strip()
            title = (entry.get("title") or "").strip()
            if not link or not title:
                continue
            summary = (entry.get("summary") or "").strip() or None
            author = ", ".join(a.get("name", "") for a in entry.get("authors", []) if a.get("name")) or None
            published = entry.get("published_parsed")
            published_at = datetime(*published[:6], tzinfo=UTC) if published else None
            tags = [t.get("term") for t in entry.get("tags", []) if t.get("term")]
            results.append(
                RawArticle(
                    url=link,
                    title=title.replace("\n", " ").strip(),
                    author=author,
                    published_at=published_at,
                    summary=summary,
                    content=summary,
                    lang="en",
                    extra={"categories": tags, "entry_id": entry.get("id")},
                )
            )
        logger.info("ArxivCollector done: {} items", len(results))
        return results


__all__ = ["ArxivCollector"]
