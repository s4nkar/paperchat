from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Page one of a test document.")
    doc.new_page()
    doc[-1].insert_text((72, 72), "Page two of a test document.")
    path = tmp_path / "sample.pdf"
    doc.save(str(path))
    doc.close()
    return path
