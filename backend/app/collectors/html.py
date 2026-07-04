"""HTMLCollector：按 YAML 配置用 CSS 选择器抓取列表页条目。

`Source.type == "html"` 时，`Source.url` 应指向容器内可读的 YAML 文件路径，
例如 `/app/scripts/html_sources/lobsters.yaml`（需挂载 `scripts` 目录）。

YAML 字段：
- entry_url: 列表页 URL（必填）
- list_selector: 每条目根节点的 CSS 选择器（必填）
- link_selector: 条目内文章链接的 CSS 选择器，相对 list 节点（必填）
- title_selector: 可选；缺省则用链接文本
- summary_selector: 可选
- time_selector: 可选；优先取元素的 `datetime` 属性
- max_items: 默认 30
- timeout / user_agent: 可选
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

import httpx
import yaml
from bs4 import BeautifulSoup
from bs4.element import Tag

from app.collectors.base import BaseCollector, RawArticle
from app.utils.logging import logger

DEFAULT_TIMEOUT = 15.0
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; AI-News-Bot/0.1; +https://example.com)"


@dataclass
class HTMLSourceConfig:
    entry_url: str
    list_selector: str
    link_selector: str
    title_selector: str | None = None
    summary_selector: str | None = None
    time_selector: str | None = None
    max_items: int = 30
    timeout: float = DEFAULT_TIMEOUT
    user_agent: str = DEFAULT_USER_AGENT

    @classmethod
    def from_dict(cls, data: dict) -> HTMLSourceConfig:
        if not isinstance(data, dict):
            raise ValueError("YAML 根节点必须是 mapping")
        required = ("entry_url", "list_selector", "link_selector")
        missing = [k for k in required if not (data.get(k) or "").strip()]
        if missing:
            raise ValueError(f"YAML 缺少必填字段: {', '.join(missing)}")

        max_items = int(data.get("max_items") or 30)
        if max_items < 1:
            max_items = 1
        if max_items > 100:
            max_items = 100

        timeout = float(data.get("timeout") or DEFAULT_TIMEOUT)

        return cls(
            entry_url=str(data["entry_url"]).strip(),
            list_selector=str(data["list_selector"]).strip(),
            link_selector=str(data["link_selector"]).strip(),
            title_selector=(str(data["title_selector"]).strip() if data.get("title_selector") else None),
            summary_selector=(
                str(data["summary_selector"]).strip() if data.get("summary_selector") else None
            ),
            time_selector=(str(data["time_selector"]).strip() if data.get("time_selector") else None),
            max_items=max_items,
            timeout=timeout,
            user_agent=str(data.get("user_agent") or DEFAULT_USER_AGENT).strip(),
        )


def _parse_time_element(el: Tag | None) -> datetime | None:
    if el is None:
        return None
    raw = el.get("datetime") or el.get("title")
    if not raw:
        text = el.get_text(strip=True)
        raw = text if text else None
    if not raw:
        return None
    raw = str(raw).strip()
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw.replace(" ", "T", 1))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except ValueError:
        return None


def extract_articles_from_html(html: str, cfg: HTMLSourceConfig) -> list[RawArticle]:
    """从已下载的 HTML 解析条目（便于单测）。"""
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(cfg.list_selector)
    results: list[RawArticle] = []
    seen_urls: set[str] = set()

    for root in items[: cfg.max_items]:
        link_el = root.select_one(cfg.link_selector)
        if link_el is None:
            continue
        href = (link_el.get("href") or "").strip()
        if not href:
            continue
        url = urljoin(cfg.entry_url, href)
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = ""
        if cfg.title_selector:
            t_el = root.select_one(cfg.title_selector)
            title = t_el.get_text(strip=True) if t_el else ""
        if not title:
            title = link_el.get_text(strip=True)
        if not title:
            continue

        summary: str | None = None
        if cfg.summary_selector:
            s_el = root.select_one(cfg.summary_selector)
            if s_el:
                summary = s_el.get_text(" ", strip=True) or None

        published_at: datetime | None = None
        if cfg.time_selector:
            time_el = root.select_one(cfg.time_selector)
            published_at = _parse_time_element(time_el)

        results.append(
            RawArticle(
                url=url,
                title=title[:1024],
                author=None,
                published_at=published_at,
                summary=summary,
                content=summary or title,
                lang=None,
                extra={"collector": "html"},
            )
        )

    return results


class HTMLCollector(BaseCollector):
    name = "html"

    def __init__(self, config_path: str) -> None:
        self.config_path = Path(config_path)

    def _load_config(self) -> HTMLSourceConfig:
        if not self.config_path.is_file():
            raise FileNotFoundError(f"HTML 采集配置不存在: {self.config_path}")
        raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        return HTMLSourceConfig.from_dict(raw or {})

    def fetch(self) -> list[RawArticle]:
        cfg = self._load_config()
        logger.info("HTMLCollector start: {} ({})", cfg.entry_url, self.config_path)

        headers = {"User-Agent": cfg.user_agent}
        with httpx.Client(timeout=cfg.timeout, follow_redirects=True, headers=headers) as client:
            resp = client.get(cfg.entry_url)
            resp.raise_for_status()
            html = resp.text

        results = extract_articles_from_html(html, cfg)
        for item in results:
            item.extra = {**(item.extra or {}), "config_path": str(self.config_path)}

        logger.info("HTMLCollector done: {} items", len(results))
        return results


__all__ = ["HTMLCollector", "HTMLSourceConfig", "extract_articles_from_html"]
