"""采集器抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawArticle:
    """采集器产出的原始文章结构。"""

    url: str
    title: str
    author: str | None = None
    published_at: datetime | None = None
    summary: str | None = None
    content: str | None = None
    raw_html: str | None = None
    lang: str | None = None
    extra: dict = field(default_factory=dict)


class BaseCollector(ABC):
    """所有采集器的基类。Step 1 将添加具体实现。"""

    name: str = "base"

    @abstractmethod
    def fetch(self) -> list[RawArticle]:
        """抓取并返回原始文章列表。"""
        raise NotImplementedError
