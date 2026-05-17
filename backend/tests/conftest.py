from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app

_PARA = (
    "Retrieval-augmented generation combines a dense retrieval step with a "
    "generative language model to produce grounded, cited answers. "
    "The retriever selects the most relevant passages from a large corpus, "
    "and the generator conditions its output on those passages. "
    "Hybrid retrieval systems that combine dense vector search with sparse "
    "keyword methods such as BM25 consistently outperform either approach alone. "
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    doc = pymupdf.open()

    for heading, body in [
        ("Introduction", _PARA * 5),
        ("Methods", _PARA * 5),
    ]:
        page = doc.new_page()
        page.insert_textbox(
            pymupdf.Rect(72, 72, 540, 720),
            f"{heading}\n\n{body}",
            fontsize=11,
        )

    path = tmp_path / "sample.pdf"
    doc.save(str(path))
    doc.close()
    return path
