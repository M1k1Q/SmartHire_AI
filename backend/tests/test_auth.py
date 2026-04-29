"""
tests/test_auth.py
Unit tests for authentication endpoints.
"""
import pytest
import json
from app import create_app
from app.config import DevelopmentConfig


class TestConfig(DevelopmentConfig):
    TESTING = True
    MONGO_URI = "mongodb://localhost:27017/test_recruitment_db"
    MONGO_DBNAME = "test_recruitment_db"
    JWT_SECRET_KEY = "test-jwt-secret"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app
    # Teardown: drop test database
    with app.app_context():
        from app.extensions import mongo
        mongo.db.client.drop_database("test_recruitment_db")


@pytest.fixture
def client(app):
    return app.test_client()


class TestRegister:
    def test_register_hr_success(self, client):
        """HR user can register successfully."""
        response = client.post("/api/auth/register", json={
            "name": "Alice HR",
            "email": "alice@hr.com",
            "password": "password123",
            "role": "hr",
        })
        assert response.status_code == 201
        data = response.get_json()
        assert "token" in data
        assert data["user"]["role"] == "hr"
        assert data["user"]["email"] == "alice@hr.com"

    def test_register_candidate_success(self, client):
        """Candidate user can register successfully."""
        response = client.post("/api/auth/register", json={
            "name": "Bob Candidate",
            "email": "bob@candidate.com",
            "password": "pass1234",
            "role": "candidate",
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["user"]["role"] == "candidate"

    def test_register_missing_fields(self, client):
        """Registration fails when required fields are missing."""
        response = client.post("/api/auth/register", json={
            "email": "test@test.com",
        })
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_register_invalid_email(self, client):
        """Registration fails with invalid email format."""
        response = client.post("/api/auth/register", json={
            "name": "Test",
            "email": "not-an-email",
            "password": "abc123",
            "role": "candidate",
        })
        assert response.status_code == 400

    def test_register_invalid_role(self, client):
        """Registration fails with invalid role."""
        response = client.post("/api/auth/register", json={
            "name": "Test",
            "email": "test@test.com",
            "password": "abc123",
            "role": "superadmin",
        })
        assert response.status_code == 400

    def test_register_duplicate_email(self, client):
        """Duplicate email registration returns 409."""
        payload = {"name": "X", "email": "dup@test.com", "password": "abc123", "role": "candidate"}
        client.post("/api/auth/register", json=payload)
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 409

    def test_register_short_password(self, client):
        """Password shorter than 6 chars is rejected."""
        response = client.post("/api/auth/register", json={
            "name": "Test", "email": "t@t.com", "password": "ab", "role": "hr"
        })
        assert response.status_code == 400


class TestLogin:
    @pytest.fixture(autouse=True)
    def register_user(self, client):
        """Register a user before each login test."""
        client.post("/api/auth/register", json={
            "name": "Login User",
            "email": "login@test.com",
            "password": "mypassword",
            "role": "hr",
        })

    def test_login_success(self, client):
        """Registered user can log in."""
        response = client.post("/api/auth/login", json={
            "email": "login@test.com",
            "password": "mypassword",
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data

    def test_login_wrong_password(self, client):
        """Login fails with wrong password."""
        response = client.post("/api/auth/login", json={
            "email": "login@test.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_email(self, client):
        """Login fails with unknown email."""
        response = client.post("/api/auth/login", json={
            "email": "nobody@unknown.com",
            "password": "abc123",
        })
        assert response.status_code == 401


class TestMe:
    def test_me_with_valid_token(self, client):
        """Authenticated user can retrieve their profile."""
        reg = client.post("/api/auth/register", json={
            "name": "Me User", "email": "me@test.com", "password": "abc123", "role": "candidate"
        }).get_json()
        token = reg["token"]

        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["email"] == "me@test.com"

    def test_me_without_token(self, client):
        """Unauthenticated request returns 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
