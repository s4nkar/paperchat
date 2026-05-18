def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_stubs_return_501(client):
    assert client.get("/api/eval").status_code == 501
