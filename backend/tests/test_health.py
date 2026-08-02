def test_root_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint_returns_200(client):
    response = client.get("/health/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
