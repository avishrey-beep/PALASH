from backend.app.models.user import User, Role
from backend.app.core.security import get_password_hash

def test_user_registration(client, db):
    # Ensure TEACHER role exists
    if not db.query(Role).filter_by(name="TEACHER").first():
        db.add(Role(name="TEACHER", description="Teacher"))
        db.commit()

    payload = {
        "username": "new_teacher_ranchi",
        "email": "teacher.ranchi@schools.jharkhand.gov.in",
        "password": "Password123!",
        "full_name": "Ravi Kumar",
        "school_id": "GPS_RANCHI_05",
        "roles": ["TEACHER"]
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_teacher_ranchi"
    assert "TEACHER" in data["roles"]

def test_user_login_and_profile(client, db):
    # Create test user
    role = db.query(Role).filter_by(name="TEACHER").first()
    if not role:
        role = Role(name="TEACHER", description="Teacher")
        db.add(role)
        db.commit()

    test_user = User(
        username="login_test_user",
        email="login_test@example.com",
        hashed_password=get_password_hash("SecretPass123!"),
        full_name="Login Tester",
        school_id="GPS_01",
        is_active=True,
        roles=[role]
    )
    db.add(test_user)
    db.commit()

    # Successful login
    login_res = client.post("/api/v1/auth/login", json={
        "username": "login_test_user",
        "password": "SecretPass123!"
    })
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Access protected profile
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    profile_res = client.get("/api/v1/auth/me", headers=headers)
    assert profile_res.status_code == 200
    assert profile_res.json()["username"] == "login_test_user"

    # Profile carries the default preferred_language.
    assert profile_res.json()["preferred_language"] == "sat"

    # PATCH /me updates editable fields against real supported languages.
    patch_res = client.patch(
        "/api/v1/auth/me",
        json={"full_name": "Login Tester Ji", "preferred_language": "unr"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["full_name"] == "Login Tester Ji"
    assert patched["preferred_language"] == "unr"

    # An unsupported language code is rejected, never silently stored.
    bad_res = client.patch(
        "/api/v1/auth/me",
        json={"preferred_language": "zz"},
        headers=headers,
    )
    assert bad_res.status_code == 400

    # Token refresh
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "username": "login_test_user",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401

def test_compatibility_routes(client, db):
    # Test /api/auth/login and /api/users/me compatibility aliases
    login_res = client.post("/api/auth/login", json={
        "username": "login_test_user",
        "password": "SecretPass123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    users_me_res = client.get("/api/users/me", headers=headers)
    assert users_me_res.status_code == 200
    assert users_me_res.json()["username"] == "login_test_user"

    v1_users_me_res = client.get("/api/v1/users/me", headers=headers)
    assert v1_users_me_res.status_code == 200
    assert v1_users_me_res.json()["username"] == "login_test_user"
