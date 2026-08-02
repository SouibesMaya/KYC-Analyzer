def test_create_case_with_valid_payload(client):
    response = client.post(
        "/api/cases/",
        json={"user_id": "USR-TEST-1", "requested_doc_type": "identity_card"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "USR-TEST-1"
    assert body["requested_doc_type"] == "identity_card"
    assert body["status"] == "pending"
    assert "case_id" in body


def test_create_case_missing_fields_is_rejected(client):
    # user_id manquant : erreur de validation Pydantic (422), pas un crash.
    response = client.post(
        "/api/cases/",
        json={"requested_doc_type": "identity_card"},
    )
    assert response.status_code == 422


def test_create_case_invalid_doc_type_is_rejected(client):
    response = client.post(
        "/api/cases/",
        json={"user_id": "USR-TEST-2", "requested_doc_type": "passeport_martien"},
    )
    assert response.status_code == 400


def test_list_cases_returns_json(client):
    response = client.get("/api/cases/")
    assert response.status_code == 200
    body = response.json()
    assert "total" in body
    assert "items" in body
    assert isinstance(body["items"], list)


def test_get_unknown_case_returns_404(client):
    response = client.get("/api/cases/does-not-exist")
    assert response.status_code == 404


def test_submit_document_on_unknown_case_returns_404(client):
    response = client.post(
        "/api/cases/does-not-exist/submit-document",
        files={"file": ("test.png", b"not a real image", "image/png")},
    )
    assert response.status_code == 404
