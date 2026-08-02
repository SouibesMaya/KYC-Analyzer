def test_documents_router_exists(client):
    response = client.get("/api/documents/test")
    assert response.status_code == 200
    assert "message" in response.json()


def test_upload_without_file_returns_controlled_error(client):
    # Aucun champ "file" envoyé : FastAPI doit renvoyer une erreur de
    # validation contrôlée (422), pas une exception non gérée (500).
    response = client.post("/api/documents/upload")
    assert response.status_code == 422


def test_list_analyses_returns_json(client):
    response = client.get("/api/documents/analyses")
    assert response.status_code == 200
    body = response.json()
    assert "total" in body
    assert "items" in body
    assert isinstance(body["items"], list)


def test_get_unknown_analysis_returns_404(client):
    response = client.get("/api/documents/analyses/does-not-exist")
    assert response.status_code == 404
