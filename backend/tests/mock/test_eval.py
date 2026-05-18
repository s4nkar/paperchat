"""
Mocked integration tests for run_eval().

The metric formulas (recall, MRR, precision) are tested without mocks in
tests/test_metrics.py. These tests verify that run_eval() correctly aggregates
scores across questions — without hitting live retrieval or reranking APIs.
"""
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.eval.metrics import run_eval

_MATCH = {
    "text": "The cost is £100 for new candidates.",
    "metadata": {"filename": "policy.pdf", "page": 2, "section": ""},
    "score": 0.9,
}
_OTHER = {
    "text": "Some unrelated content.",
    "metadata": {"filename": "other.pdf", "page": 1, "section": ""},
    "score": 0.5,
}


def _make_questions_file(tmp_path):
    questions = [
        {
            "id": "q1",
            "question": "What is the cost?",
            "expected_sources": [{"filename": "policy.pdf", "page": 2}],
        }
    ]
    f = tmp_path / "questions.json"
    f.write_text(json.dumps(questions), encoding="utf-8")
    return f


@pytest.mark.asyncio
async def test_run_eval_perfect_scores(tmp_path, monkeypatch):
    monkeypatch.setattr("app.eval.metrics._QUESTIONS_PATH", _make_questions_file(tmp_path))

    with (
        patch("app.eval.metrics.retrieve", new_callable=AsyncMock, return_value=[_MATCH]),
        patch("app.eval.metrics.rerank", new_callable=AsyncMock, return_value=[_MATCH]),
    ):
        result = await run_eval(retrieval_k=5, rerank_k=3)

    assert result["recall_at_k"] == pytest.approx(1.0)
    assert result["mrr"] == pytest.approx(1.0)
    assert result["precision_at_k"] == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_run_eval_zero_scores(tmp_path, monkeypatch):
    monkeypatch.setattr("app.eval.metrics._QUESTIONS_PATH", _make_questions_file(tmp_path))

    with (
        patch("app.eval.metrics.retrieve", new_callable=AsyncMock, return_value=[_OTHER]),
        patch("app.eval.metrics.rerank", new_callable=AsyncMock, return_value=[_OTHER]),
    ):
        result = await run_eval(retrieval_k=5, rerank_k=3)

    assert result["recall_at_k"] == pytest.approx(0.0)
    assert result["mrr"] == pytest.approx(0.0)
    assert result["precision_at_k"] == pytest.approx(0.0)
