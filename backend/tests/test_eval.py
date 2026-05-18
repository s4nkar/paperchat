import json
from unittest.mock import AsyncMock, patch

import pytest

from app.eval.metrics import _precision, _recall, _reciprocal_rank, run_eval

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
_EXPECTED = [{"filename": "policy.pdf", "page": 2}]


# --- unit tests ---

def test_recall_hit_in_top_k():
    assert _recall([_MATCH, _OTHER], _EXPECTED, k=5) is True

def test_recall_miss_outside_top_k():
    assert _recall([_OTHER, _MATCH], _EXPECTED, k=1) is False

def test_recall_empty():
    assert _recall([], _EXPECTED, k=5) is False

def test_reciprocal_rank_first():
    assert _reciprocal_rank([_MATCH, _OTHER], _EXPECTED, k=3) == pytest.approx(1.0)

def test_reciprocal_rank_second():
    assert _reciprocal_rank([_OTHER, _MATCH], _EXPECTED, k=3) == pytest.approx(0.5)

def test_reciprocal_rank_not_found():
    assert _reciprocal_rank([_OTHER], _EXPECTED, k=3) == pytest.approx(0.0)

def test_precision_all_relevant():
    assert _precision([_MATCH, _MATCH], _EXPECTED, k=2) == pytest.approx(1.0)

def test_precision_half_relevant():
    assert _precision([_MATCH, _OTHER], _EXPECTED, k=2) == pytest.approx(0.5)

def test_precision_none_relevant():
    assert _precision([_OTHER, _OTHER], _EXPECTED, k=2) == pytest.approx(0.0)


# --- run_eval integration tests ---

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
