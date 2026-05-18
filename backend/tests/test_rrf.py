from app.rag.retriever import _rrf

_CHUNK_A = {"text": "council tax proof of address", "metadata": {"filename": "a.pdf", "page": 1, "section": ""}, "score": 0.9}
_CHUNK_B = {"text": "utility bill proof of address", "metadata": {"filename": "a.pdf", "page": 1, "section": ""}, "score": 0.7}
_CHUNK_C = {"text": "passport identity document",   "metadata": {"filename": "b.pdf", "page": 2, "section": ""}, "score": 0.5}


def test_rrf_chunk_in_both_lists_ranks_first():
    result = _rrf([[_CHUNK_A, _CHUNK_B], [_CHUNK_A, _CHUNK_C]])
    assert result[0]["text"] == _CHUNK_A["text"]


def test_rrf_deduplicates_same_text():
    result = _rrf([[_CHUNK_A], [_CHUNK_A]])
    assert len(result) == 1


def test_rrf_includes_chunks_from_single_list():
    result = _rrf([[_CHUNK_A, _CHUNK_B], [_CHUNK_C]])
    texts = [r["text"] for r in result]
    assert _CHUNK_B["text"] in texts
    assert _CHUNK_C["text"] in texts


def test_rrf_empty_lists():
    assert _rrf([[], []]) == []


def test_rrf_one_empty_list():
    result = _rrf([[_CHUNK_A, _CHUNK_B], []])
    assert len(result) == 2
