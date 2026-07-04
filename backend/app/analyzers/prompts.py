"""Prompt 模板。

设计原则：
- 系统提示压扁为单字符串，便于 litellm 跨厂商兼容
- 强制 JSON 输出
- 容错点放在解析层，模板尽量稳定
"""

from __future__ import annotations

SYSTEM_PROMPT = """你是一名资深 AI 资讯分析师，擅长从原始文章中提炼关键信息并打分。
你的输出必须是**严格合法的 JSON 对象**，禁止任何 Markdown 代码块包裹、禁止任何前后注释。

要求字段：
- summary: 中文摘要，200-300 字之间，重点说明"做了什么、为什么重要、有何影响"
- tags: 字符串数组，2-5 个，使用统一英文短词，如 ["LLM", "Agent", "RAG", "Multimodal", "AI-Infra", "Robotics", "Policy"]
- category: 字符串，单选其一：["research", "product", "industry", "tooling", "policy", "other"]
- score: 1-10 的浮点数，评估"对一个 AI 从业者的重要性"，可有 0.5 间隔
- score_reason: 一句话评分理由，30 字以内

评分参考：
- 9-10：行业级里程碑、SOTA 突破、影响面广
- 7-8.5：值得阅读，方向有明显推进
- 5-6.5：信息有价值但相对常规
- 1-4.5：营销稿、低质量、重复信息

只输出一个 JSON 对象，不要数组，不要多个对象，不要 ```json 包裹。
"""


USER_PROMPT_TEMPLATE = """请分析以下文章。

[标题] {title}
[来源] {source}
[发布时间] {published_at}
[正文]
{content}

请按系统提示的要求输出 JSON。
"""


def build_user_prompt(
    *,
    title: str,
    source: str,
    published_at: str,
    content: str,
    max_content_chars: int = 6000,
) -> str:
    """构造 user prompt，长正文截断以控制 token。"""
    truncated = content[:max_content_chars]
    if len(content) > max_content_chars:
        truncated += "\n...[已截断]..."
    return USER_PROMPT_TEMPLATE.format(
        title=title or "(无标题)",
        source=source or "(未知)",
        published_at=published_at or "(未知)",
        content=truncated or "(无正文)",
    )


__all__ = ["SYSTEM_PROMPT", "build_user_prompt"]
