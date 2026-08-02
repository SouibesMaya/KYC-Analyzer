def test_upload_rejects_disallowed_extension(client):
    response = client.post(
        "/api/documents/upload",
        files={"file": ("malware.exe", b"MZ\x90\x00fake-binary", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "traceback" not in response.text.lower()


def test_upload_rejects_disallowed_extension_txt(client):
    response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400


def test_unknown_route_returns_404(client):
    response = client.get("/api/this-route-does-not-exist")
    assert response.status_code == 404


def test_404_response_has_no_raw_traceback(client):
    response = client.get("/api/documents/analyses/unknown-id")
    assert response.status_code == 404
    assert "traceback" not in response.text.lower()
    assert "Traceback (most recent call last)" not in response.text


def test_validation_error_has_no_raw_traceback(client):
    response = client.post("/api/cases/", json={"user_id": "only-one-field"})
    assert response.status_code == 422
    assert "traceback" not in response.text.lower()
