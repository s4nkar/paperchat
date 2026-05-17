def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_stubs_return_501(client):
    assert client.post("/api/upload").status_code == 501
    assert client.post("/api/chat").status_code == 501
    assert client.get("/api/documents").status_code == 501
    assert client.get("/api/eval").status_code == 501
