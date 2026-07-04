"""LLM JSON 容错解析单测。"""

from __future__ import annotations

import pytest

from app.analyzers.llm_client import LLMResponseFormatError, _parse_json_loose


def test_parse_pure_json() -> None:
    out = _parse_json_loose('{"summary": "hi", "score": 8}')
    assert out["summary"] == "hi"
    assert out["score"] == 8


def test_parse_with_code_fence() -> None:
    raw = '```json\n{"summary": "x", "score": 7.5}\n```'
    out = _parse_json_loose(raw)
    assert out["score"] == 7.5


def test_parse_with_trailing_text() -> None:
    raw = '前缀解释\n{"summary": "y", "score": 6}\n这里是尾巴'
    out = _parse_json_loose(raw)
    assert out["summary"] == "y"


def test_parse_empty_raises() -> None:
    with pytest.raises(LLMResponseFormatError):
        _parse_json_loose("")


def test_parse_invalid_raises() -> None:
    with pytest.raises(LLMResponseFormatError):
        _parse_json_loose("not json at all, totally garbage")
