"""Analyzer 字段规范化单测：mock LLMClient.chat_json。"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.analyzers.analyzer import Analyzer, AnalyzerInput
from app.analyzers.llm_client import LLMCallResult


def _fake_result(data: dict) -> LLMCallResult:
    return LLMCallResult(
        data=data,
        model="fake-model",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.001,
        raw_response=str(data),
    )


def test_analyzer_normalizes_fields() -> None:
    fake_llm = MagicMock()
    fake_llm.chat_json.return_value = _fake_result(
        {
            "summary": "中文摘要" * 3,
            "tags": ["LLM", "Agent", 123, "", "RAG"],
            "category": "RESEARCH",
            "score": "9.5",
            "score_reason": "重要的研究突破",
        }
    )
    analyzer = Analyzer(llm_client=fake_llm)

    normalized, _ = analyzer.analyze_input(
        AnalyzerInput(
            title="Some Title",
            source_name="OpenAI Blog",
            published_at=None,
            content="Some content body",
        )
    )

    assert normalized["category"] == "research"
    assert normalized["score"] == 9.5
    assert "LLM" in normalized["tags"]
    assert 123 not in normalized["tags"]
    assert "" not in normalized["tags"]


def test_analyzer_clamps_invalid_score() -> None:
    fake_llm = MagicMock()
    fake_llm.chat_json.return_value = _fake_result(
        {"summary": "x", "score": "not-a-number", "tags": [], "category": "weird"}
    )
    analyzer = Analyzer(llm_client=fake_llm)

    normalized, _ = analyzer.analyze_input(
        AnalyzerInput(title="t", source_name="s", published_at=None, content="c")
    )

    assert normalized["score"] == 5.0
    assert normalized["category"] == "other"


def test_analyzer_handles_empty_summary() -> None:
    fake_llm = MagicMock()
    fake_llm.chat_json.return_value = _fake_result(
        {"summary": "", "score": 7, "tags": ["LLM"], "category": "product"}
    )
    analyzer = Analyzer(llm_client=fake_llm)

    normalized, _ = analyzer.analyze_input(
        AnalyzerInput(title="t", source_name="s", published_at=None, content="c")
    )

    assert normalized["summary"]
    assert "未返回有效摘要" in normalized["summary"]
