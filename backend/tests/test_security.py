import io

def test_rbac_teacher_forbidden_from_curriculum_upload(client, teacher_auth_headers):
    file_payload = ("test.txt", io.BytesIO(b"TITLE: Test"), "text/plain")
    res = client.post(
        "/api/v1/curriculum/upload",
        files={"file": file_payload},
        data={"title": "Test"},
        headers=teacher_auth_headers
    )
    # Teacher does not have CURRICULUM_MANAGER or ADMIN role
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]

def test_unauthenticated_request_rejected(client):
    res = client.post(
        "/api/v1/curriculum/upload",
        files={"file": ("test.txt", io.BytesIO(b"Test"), "text/plain")},
        data={"title": "Test"}
    )
    assert res.status_code == 401

def test_tampered_jwt_token_rejected(client):
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.tampered_signature"
    headers = {"Authorization": f"Bearer {tampered_token}"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
