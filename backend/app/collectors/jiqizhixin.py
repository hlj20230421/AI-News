"""JiqizhixinCollector：机器之心 GraphQL 采集器。

官方 RSS（/rss）已下线并重定向，改走文章库页获取 CSRF 后调用 GraphQL timelines。
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta, timezone
from urllib.parse import urljoin

import httpx

from app.collectors.base import BaseCollector, RawArticle
from app.utils.logging import logger

DEFAULT_ENTRY_URL = "https://www.jiqizhixin.com/articles"
DEFAULT_TIMEOUT = 20.0
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; AI-News-Bot/0.1; +https://example.com)"
)
_GRAPHQL_URL = "https://www.jiqizhixin.com/graphql"
_TIMELINES_QUERY = """
query Timelines($count: Int, $cursor: String) {
  timelines(first: $count, after: $cursor) {
    edges {
      node {
        id
        content {
          ... on Article {
            title
            path
            publishedAt
            description
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""
# 机器之心站内时间为北京时间（UTC+8）
_CN_TZ = timezone(timedelta(hours=8))


def _parse_published_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.strptime(value.strip(), "%Y/%m/%d %H:%M").replace(tzinfo=_CN_TZ)
        return dt.astimezone(UTC)
    except ValueError:
        return None


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'csrf-token" content="([^"]+)"', html)
    if not match:
        raise RuntimeError("机器之心页面缺少 CSRF token")
    return match.group(1)


class JiqizhixinCollector(BaseCollector):
    name = "jiqizhixin"

    def __init__(
        self,
        source_url: str = DEFAULT_ENTRY_URL,
        *,
        max_items: int = 30,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.entry_url = source_url or DEFAULT_ENTRY_URL
        self.max_items = max_items
        self.timeout = timeout

    def fetch(self) -> list[RawArticle]:
        logger.info("JiqizhixinCollector start: {}", self.entry_url)
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers=headers,
        ) as client:
            page = client.get(self.entry_url)
            page.raise_for_status()
            csrf = _extract_csrf_token(page.text)
            gql_headers = {
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": self.entry_url,
                "Origin": "https://www.jiqizhixin.com",
            }

            results: list[RawArticle] = []
            cursor: str | None = None
            while len(results) < self.max_items:
                batch_size = min(30, self.max_items - len(results))
                resp = client.post(
                    _GRAPHQL_URL,
                    json={
                        "query": _TIMELINES_QUERY,
                        "variables": {"count": batch_size, "cursor": cursor},
                    },
                    headers=gql_headers,
                )
                resp.raise_for_status()
                payload = resp.json()
                if payload.get("errors"):
                    raise RuntimeError(f"机器之心 GraphQL 错误: {payload['errors']}")

                timelines = (payload.get("data") or {}).get("timelines") or {}
                edges = timelines.get("edges") or []
                if not edges:
                    break

                for edge in edges:
                    node = edge.get("node") or {}
                    article = node.get("content") or {}
                    path = (article.get("path") or "").strip()
                    title = (article.get("title") or "").strip()
                    if not path or not title:
                        continue
                    results.append(
                        RawArticle(
                            url=urljoin("https://www.jiqizhixin.com", path),
                            title=title,
                            published_at=_parse_published_at(article.get("publishedAt")),
                            summary=(article.get("description") or None) or None,
                            content=(article.get("description") or None) or None,
                            lang="zh",
                            extra={"timeline_id": node.get("id")},
                        )
                    )
                    if len(results) >= self.max_items:
                        break

                page_info = timelines.get("pageInfo") or {}
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
                if not cursor:
                    break

        logger.info("JiqizhixinCollector done: {} items", len(results))
        return results


__all__ = ["JiqizhixinCollector"]
