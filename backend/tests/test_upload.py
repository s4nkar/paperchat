from pathlib import Path
from unittest.mock import AsyncMock, patch

import pymupdf
import pytest
from fastapi.testclient import TestClient


def _mock_ingest(chunk_count: int = 5):
    return patch("app.routes.upload.ingest_pdf", new_callable=AsyncMock, return_value=chunk_count)


def test_upload_pdf(client: TestClient, sample_pdf: Path, tmp_path: Path, monkeypatch):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    with _mock_ingest(), open(sample_pdf, "rb") as f:
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
    assert data[0]["chunk_count"] == 5
    assert (tmp_path / "sample.pdf").exists()


def test_upload_rejects_non_pdf(client: TestClient, tmp_path: Path, monkeypatch):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    response = client.post(
        "/api/upload",
        files=[("files", ("notes.txt", b"hello", "text/plain"))],
    )
    assert response.status_code == 422


def test_upload_warns_image_only_pdf(client: TestClient, tmp_path: Path, monkeypatch):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    doc = pymupdf.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    with _mock_ingest(0):
        response = client.post(
            "/api/upload",
            files=[("files", ("scan.pdf", pdf_bytes, "application/pdf"))],
        )

    assert response.status_code == 200
    data = response.json()
    assert data[0]["warning"] is not None
    assert "scanned" in data[0]["warning"].lower()


def test_upload_rejects_path_traversal_filename(
    client: TestClient, sample_pdf: Path, tmp_path: Path, monkeypatch
):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    with _mock_ingest(), open(sample_pdf, "rb") as f:
        response = client.post(
            "/api/upload",
            files=[("files", ("../../evil.pdf", f, "application/pdf"))],
        )

    assert response.status_code == 200
    # File must be written inside UPLOAD_DIR, not two levels up
    assert (tmp_path / "evil.pdf").exists()
    assert not (tmp_path.parent.parent / "evil.pdf").exists()


def test_upload_rejects_fake_pdf(client: TestClient, tmp_path: Path, monkeypatch):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    response = client.post(
        "/api/upload",
        files=[("files", ("malware.pdf", b"MZ\x90\x00not a pdf", "application/pdf"))],
    )
    assert response.status_code == 422


def test_upload_validates_all_before_writing(
    client: TestClient, sample_pdf: Path, tmp_path: Path, monkeypatch
):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    with open(sample_pdf, "rb") as f:
        response = client.post(
            "/api/upload",
            files=[
                ("files", ("good.pdf", f, "application/pdf")),
                ("files", ("bad.txt", b"hello", "text/plain")),
            ],
        )

    assert response.status_code == 422
    # good.pdf must NOT have been written since validation failed
    assert not (tmp_path / "good.pdf").exists()


def test_upload_multiple_pdfs(
    client: TestClient, sample_pdf: Path, tmp_path: Path, monkeypatch
):
    import app.routes.upload as upload_module

    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path)

    with _mock_ingest(), open(sample_pdf, "rb") as f1, open(sample_pdf, "rb") as f2:
        response = client.post(
            "/api/upload",
            files=[
                ("files", ("a.pdf", f1, "application/pdf")),
                ("files", ("b.pdf", f2, "application/pdf")),
            ],
        )

    assert response.status_code == 200
    assert len(response.json()) == 2
