"""LLMClient provider 路由单测。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.analyzers.llm_client import LLMClient, resolve_completion_model_and_auth


def test_resolve_deepseek_uses_deepseek_key_and_prefixes_model() -> None:
    resolved = resolve_completion_model_and_auth(
        provider="deepseek",
        model="deepseek-chat",
        openai_api_key="sk-openai",
        deepseek_api_key="sk-deepseek",
    )
    assert resolved["model"] == "deepseek/deepseek-chat"
    assert resolved["api_key"] == "sk-deepseek"
    assert "api_base" not in resolved


def test_resolve_openai_uses_openai_key_and_base_url() -> None:
    resolved = resolve_completion_model_and_auth(
        provider="openai",
        model="gpt-4o-mini",
        openai_api_key="sk-openai",
        openai_base_url="https://proxy.example/v1",
    )
    assert resolved["model"] == "gpt-4o-mini"
    assert resolved["api_key"] == "sk-openai"
    assert resolved["api_base"] == "https://proxy.example/v1"


def test_resolve_ollama_strips_v1_suffix_from_base_url() -> None:
    resolved = resolve_completion_model_and_auth(
        provider="ollama",
        model="llama3",
        openai_base_url="http://localhost:11434/v1",
    )
    assert resolved["model"] == "ollama/llama3"
    assert resolved["api_base"] == "http://localhost:11434"


def test_chat_json_passes_provider_specific_kwargs() -> None:
    fake_resp = MagicMock()
    fake_resp.choices = [MagicMock(message=MagicMock(content='{"summary":"ok","score":8,"tags":["LLM"],"category":"product"}'))]
    fake_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=20)

    with patch("app.analyzers.llm_client.litellm.completion", return_value=fake_resp) as mock_completion:
        client = LLMClient(model="deepseek-chat", provider="deepseek")
        with patch("app.analyzers.llm_client.settings") as mock_settings:
            mock_settings.llm_model = "deepseek-chat"
            mock_settings.llm_provider = "deepseek"
            mock_settings.llm_timeout_seconds = 60
            mock_settings.openai_api_key = "sk-openai"
            mock_settings.openai_base_url = ""
            mock_settings.anthropic_api_key = ""
            mock_settings.deepseek_api_key = "sk-deepseek"
            result = client.chat_json(system="sys", user="usr")

    mock_completion.assert_called_once()
    kwargs = mock_completion.call_args.kwargs
    assert kwargs["model"] == "deepseek/deepseek-chat"
    assert kwargs["api_key"] == "sk-deepseek"
    assert "api_base" not in kwargs
    assert result.model == "deepseek/deepseek-chat"
