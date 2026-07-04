from __future__ import annotations

from app.services.collect_service import _cosine_similarity


def test_cosine_similarity_identical() -> None:
    assert _cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 1.0


def test_cosine_similarity_orthogonal() -> None:
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
