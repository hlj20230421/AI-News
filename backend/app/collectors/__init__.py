"""采集器模块。

Step 1：仅 RSSCollector。
"""

from app.collectors.arxiv import ArxivCollector
from app.collectors.base import BaseCollector, RawArticle
from app.collectors.hackernews import HackerNewsCollector
from app.collectors.html import HTMLCollector
from app.collectors.jiqizhixin import JiqizhixinCollector
from app.collectors.rss import RSSCollector

COLLECTOR_TYPES: dict[str, type[BaseCollector]] = {
    "rss": RSSCollector,
    "hackernews": HackerNewsCollector,
    "arxiv": ArxivCollector,
    "html": HTMLCollector,
    "jiqizhixin": JiqizhixinCollector,
}

__all__ = [
    "BaseCollector",
    "RawArticle",
    "RSSCollector",
    "HackerNewsCollector",
    "ArxivCollector",
    "HTMLCollector",
    "JiqizhixinCollector",
    "COLLECTOR_TYPES",
]
