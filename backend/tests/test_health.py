from unittest.mock import AsyncMock, patch


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_eval_endpoint_responds(client):
    fake_result = {"recall_at_k": 1.0, "mrr": 1.0, "precision_at_k": 1.0, "retrieval_k": 5, "rerank_k": 3, "results": []}

    with patch("app.routes.eval.run_eval", new_callable=AsyncMock, return_value=fake_result):
        response = client.get("/api/eval")

    assert response.status_code == 200
    data = response.json()
    assert "recall_at_k" in data
    assert "mrr" in data
    assert "precision_at_k" in data
    assert "results" in data
