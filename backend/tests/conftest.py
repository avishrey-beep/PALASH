import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User, Role
from data.seed.init_db import seed_database

TEST_DB_URL = "sqlite:///./test_app.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Seed full schema and standard baseline data
    seed_database(engine_override=test_engine)
    
    db = TestingSessionLocal()
    try:
        admin_role = db.query(Role).filter_by(name="ADMIN").first()
        teacher_role = db.query(Role).filter_by(name="TEACHER").first()
        reviewer_role = db.query(Role).filter_by(name="LANGUAGE_REVIEWER").first()

        if not db.query(User).filter_by(id="test_admin_01").first():
            db.add(User(
                id="test_admin_01",
                username="test_admin",
                email="admin@test.gov.in",
                hashed_password=get_password_hash("AdminPass123!"),
                is_active=True,
                roles=[admin_role]
            ))
        if not db.query(User).filter_by(id="test_teacher_01").first():
            db.add(User(
                id="test_teacher_01",
                username="test_teacher",
                email="teacher@test.gov.in",
                school_id="GPS_DUMKA_01",
                hashed_password=get_password_hash("TeacherPass123!"),
                is_active=True,
                roles=[teacher_role]
            ))
        if not db.query(User).filter_by(id="test_reviewer_01").first():
            db.add(User(
                id="test_reviewer_01",
                username="test_reviewer",
                email="reviewer@test.gov.in",
                hashed_password=get_password_hash("ReviewerPass123!"),
                is_active=True,
                roles=[reviewer_role]
            ))
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_app.db"):
        try:
            os.remove("./test_app.db")
        except Exception:
            pass

@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def teacher_auth_headers():
    token = create_access_token(subject="test_teacher_01", roles=["TEACHER"])
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_auth_headers():
    token = create_access_token(subject="test_admin_01", roles=["ADMIN"])
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def reviewer_auth_headers():
    token = create_access_token(subject="test_reviewer_01", roles=["LANGUAGE_REVIEWER"])
    return {"Authorization": f"Bearer {token}"}
