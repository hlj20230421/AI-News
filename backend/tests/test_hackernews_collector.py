"""HackerNewsCollector 单测（mock HTTP）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.collectors.hackernews import HackerNewsCollector


SAMPLE_RESPONSE = {
    "hits": [
        {
            "objectID": "123",
            "title": "OpenAI releases new model",
            "url": "https://example.com/post",
            "author": "alice",
            "created_at": "2026-05-20T08:00:00Z",
            "points": 100,
            "num_comments": 20,
        }
    ]
}


@patch("app.collectors.hackernews.httpx.Client")
def test_hackernews_fetch_parses_hits(mock_client_cls: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_resp
    mock_client_cls.return_value = mock_client

    collector = HackerNewsCollector("https://hn.algolia.com/?query=AI")
    items = collector.fetch()

    assert len(items) == 1
    assert items[0].title == "OpenAI releases new model"
    assert items[0].url == "https://example.com/post"
    assert items[0].extra["hn_id"] == "123"
