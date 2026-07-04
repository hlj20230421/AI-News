"""HackerNewsCollector：Algolia HN Search API。"""

from __future__ import annotations

import time
from datetime import UTC, datetime
import httpx

from app.collectors.base import BaseCollector, RawArticle

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
DEFAULT_QUERY = "AI OR LLM OR OpenAI OR Claude OR Gemini"
_LAST_REQUEST_AT = 0.0
_MIN_INTERVAL_SEC = 3.0


def _rate_limit() -> None:
    global _LAST_REQUEST_AT  # noqa: PLW0603
    elapsed = time.monotonic() - _LAST_REQUEST_AT
    if elapsed < _MIN_INTERVAL_SEC:
        time.sleep(_MIN_INTERVAL_SEC - elapsed)
    _LAST_REQUEST_AT = time.monotonic()


def _parse_created_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class HackerNewsCollector(BaseCollector):
    name = "hackernews"

    def __init__(self, source_url: str, *, max_items: int = 30) -> None:
        self.source_url = source_url
        self.max_items = max_items

    def _query_from_url(self) -> str:
        if "query=" in self.source_url:
            return self.source_url.split("query=", 1)[1].split("&", 1)[0]
        return DEFAULT_QUERY

    def fetch(self) -> list[RawArticle]:
        _rate_limit()
        params = {
            "query": self._query_from_url(),
            "tags": "story",
            "hitsPerPage": min(self.max_items, 50),
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(HN_SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        results: list[RawArticle] = []
        for hit in data.get("hits", [])[: self.max_items]:
            object_id = hit.get("objectID")
            title = (hit.get("title") or "").strip()
            if not object_id or not title:
                continue
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            results.append(
                RawArticle(
                    url=url,
                    title=title,
                    author=hit.get("author"),
                    published_at=_parse_created_at(hit.get("created_at")),
                    summary=hit.get("story_text") or hit.get("comment_text"),
                    content=hit.get("story_text"),
                    lang="en",
                    extra={"hn_id": object_id, "points": hit.get("points"), "num_comments": hit.get("num_comments")},
                )
            )
        return results


__all__ = ["HackerNewsCollector"]
