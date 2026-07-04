"""业务编排层（Step 1）：

- collect_service：信息源 → 文章持久化（去重）
- analyze_service：文章 → LLM 分析持久化
- digest_service：聚合 TOP N → 飞书日报
"""

from app.services.collect_service import collect_source, collect_all_sources
from app.services.analyze_service import analyze_article_by_id, analyze_pending_articles
from app.services.digest_service import send_daily_digest

__all__ = [
    "collect_source",
    "collect_all_sources",
    "analyze_article_by_id",
    "analyze_pending_articles",
    "send_daily_digest",
]
