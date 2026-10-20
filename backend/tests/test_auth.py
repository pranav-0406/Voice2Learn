"""Unit and integration tests for student authentication, PIN verification, and session tokens."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_pin,
    verify_pin,
)
from app.db.database import Database
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "voice2learn-auth-test.sqlite3"
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(database_path))
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client, database_path
    get_settings.cache_clear()


def test_hash_and_verify_pin():
    pin = "1234"
    pin_hash = hash_pin(pin)
    assert pin_hash.startswith("pbkdf2:sha256:100000$")
    assert verify_pin("1234", pin_hash) is True
    assert verify_pin("9999", pin_hash) is False
    assert verify_pin("", pin_hash) is False
    assert verify_pin("1234", "invalid_format") is False


def test_create_and_decode_token():
    payload = {"sub": "student-123", "nickname": "Kavitha", "class_level": 6}
    token = create_access_token(payload, expires_delta_seconds=3600)
    assert isinstance(token, str)
    assert token.count(".") == 2

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "student-123"
    assert decoded["nickname"] == "Kavitha"
    assert decoded["class_level"] == 6
    assert "exp" in decoded


def test_token_expiration():
    payload = {"sub": "student-expired"}
    # Token expired 10 seconds ago
    token = create_access_token(payload, expires_delta_seconds=-10)
    decoded = decode_access_token(token)
    assert decoded is None


def test_register_student_success(client):
    test_client, db_path = client

    response = test_client.post(
        "/api/auth/register",
        json={"nickname": "Santhosh", "pin": "5678", "grade_band": "6-7"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    student = data["student"]
    assert student["nickname"] == "Santhosh"
    assert student["board"] == "TN_STATE_BOARD"
    assert student["class_level"] == 6

    # Verify student is also present in learners table for backwards compatibility
    db = Database(db_path)
    learner = db.get_learner(student["id"])
    assert learner is not None
    assert learner["nickname"] == "Santhosh"


def test_register_student_duplicate_nickname(client):
    test_client, _ = client

    # First registration
    test_client.post(
        "/api/auth/register",
        json={"nickname": "Aarav", "pin": "1234"},
    )

    # Duplicate registration (case-insensitive)
    response = test_client.post(
        "/api/auth/register",
        json={"nickname": "aarav", "pin": "9999"},
    )

    assert response.status_code == 409
    assert "already taken" in response.json()["detail"].lower()


def test_register_student_invalid_pin(client):
    test_client, _ = client

    # PIN too short
    response = test_client.post(
        "/api/auth/register",
        json={"nickname": "Priya", "pin": "12"},
    )
    assert response.status_code == 422

    # PIN non-numeric
    response = test_client.post(
        "/api/auth/register",
        json={"nickname": "Priya", "pin": "abcd"},
    )
    assert response.status_code == 422


def test_login_student_success(client):
    test_client, _ = client

    # Register first
    test_client.post(
        "/api/auth/register",
        json={"nickname": "Meena", "pin": "4321"},
    )

    # Login
    response = test_client.post(
        "/api/auth/login",
        json={"nickname": "Meena", "pin": "4321"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["student"]["nickname"] == "Meena"


def test_login_student_wrong_pin(client):
    test_client, _ = client

    test_client.post(
        "/api/auth/register",
        json={"nickname": "Vikram", "pin": "1111"},
    )

    response = test_client.post(
        "/api/auth/login",
        json={"nickname": "Vikram", "pin": "2222"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_student(client):
    test_client, _ = client

    response = test_client.post(
        "/api/auth/login",
        json={"nickname": "NonExistent", "pin": "1234"},
    )

    assert response.status_code == 401


def test_get_current_student_profile(client):
    test_client, _ = client

    # Register
    reg_res = test_client.post(
        "/api/auth/register",
        json={"nickname": "Ananya", "pin": "9876"},
    )
    token = reg_res.json()["access_token"]

    # Access protected /auth/me
    response = test_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "Ananya"


def test_get_current_student_unauthorized(client):
    test_client, _ = client

    # No token
    res1 = test_client.get("/api/auth/me")
    assert res1.status_code == 401

    # Bad token
    res2 = test_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer totally-fake-token"},
    )
    assert res2.status_code == 401
