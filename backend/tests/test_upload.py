from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_upload_pdf(client: TestClient, sample_pdf: Path, tmp_path: Path, monkeypatch):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    with open(sample_pdf, "rb") as f:
        response = client.post(
            "/api/upload",
            files=[("files", ("sample.pdf", f, "application/pdf"))],
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["filename"] == "sample.pdf"
    assert data[0]["pages"] == 2
    assert data[0]["size"] > 0
    assert (tmp_path / "sample.pdf").exists()


def test_upload_rejects_non_pdf(client: TestClient, tmp_path: Path, monkeypatch):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    response = client.post(
        "/api/upload",
        files=[("files", ("notes.txt", b"hello", "text/plain"))],
    )
    assert response.status_code == 422


def test_upload_multiple_pdfs(
    client: TestClient, sample_pdf: Path, tmp_path: Path, monkeypatch
):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    with open(sample_pdf, "rb") as f1, open(sample_pdf, "rb") as f2:
        response = client.post(
            "/api/upload",
            files=[
                ("files", ("a.pdf", f1, "application/pdf")),
                ("files", ("b.pdf", f2, "application/pdf")),
            ],
        )

    assert response.status_code == 200
    assert len(response.json()) == 2
