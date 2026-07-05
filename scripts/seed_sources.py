"""预置 AI 资讯信息源。

用法（Docker，与开发进度文档一致）::

    docker compose exec -w /app backend python -m scripts.seed_sources

本地（项目根目录，需已配置 DATABASE_URL）::

    python -m scripts.seed_sources
    python -m scripts.seed_sources --update   # 已存在时同步名称/描述
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.db.models import Source


@dataclass(frozen=True, slots=True)
class SeedSource:
    name: str
    url: str
    type: str = "rss"
    description: str | None = None
    enabled: bool = True


# 开发指导 §1.1 推荐源；URL 以 2026 年仍可订阅的 feed 为准。
DEFAULT_SOURCES: tuple[SeedSource, ...] = (
    SeedSource(
        name="OpenAI News",
        url="https://openai.com/news/rss.xml",
        description="OpenAI 官方新闻与产品发布",
    ),
    SeedSource(
        name="Anthropic News",
        url="https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml",
        description="Anthropic 新闻（社区维护 RSS，官方暂无 feed）",
    ),
    SeedSource(
        name="Hugging Face Blog",
        url="https://huggingface.co/blog/feed.xml",
        description="Hugging Face 官方博客：模型、工具与生态",
    ),
    SeedSource(
        name="Google AI Blog",
        url="https://blog.google/technology/ai/rss/",
        description="Google AI 与 Gemini 相关发布",
    ),
    SeedSource(
        name="MIT Technology Review — AI",
        url="https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        description="MIT TR 人工智能专题深度报道",
    ),
    SeedSource(
        name="arXiv cs.AI",
        url="https://rss.arxiv.org/rss/cs.AI",
        description="arXiv 人工智能方向每日新论文",
    ),
    SeedSource(
        name="机器之心",
        url="https://www.jiqizhixin.com/articles",
        type="jiqizhixin",
        description="中文 AI 产业与技术资讯（GraphQL，官方 RSS 已下线）",
    ),
    SeedSource(
        name="量子位",
        url="https://www.qbitai.com/feed",
        description="中文 AI 行业快讯与深度",
    ),
)


def seed_sources(session: Session, *, update_existing: bool = False) -> tuple[int, int, int]:
    """写入预置信息源，按 url 去重。

    Returns:
        (inserted, updated, skipped) 条数。
    """
    inserted = 0
    updated = 0
    skipped = 0

    for item in DEFAULT_SOURCES:
        existing = session.scalar(select(Source).where(Source.url == item.url))
        if existing is None:
            session.add(
                Source(
                    name=item.name,
                    url=item.url,
                    type=item.type,
                    description=item.description,
                    enabled=item.enabled,
                )
            )
            inserted += 1
            continue

        if update_existing:
            existing.name = item.name
            existing.type = item.type
            existing.description = item.description
            existing.enabled = item.enabled
            updated += 1
        else:
            skipped += 1

    session.commit()
    return inserted, updated, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="预置 AI 资讯 RSS 信息源")
    parser.add_argument(
        "--update",
        action="store_true",
        help="对已存在的源（按 URL 匹配）更新名称、类型与描述",
    )
    args = parser.parse_args(argv)

    with SessionLocal() as session:
        inserted, updated, skipped = seed_sources(session, update_existing=args.update)

    total = len(DEFAULT_SOURCES)
    print(f"完成：新增 {inserted} 条，更新 {updated} 条，跳过 {skipped} 条（预置共 {total} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
