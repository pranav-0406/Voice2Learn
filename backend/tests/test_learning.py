from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import Database
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "voice2learn-test.sqlite3"
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(database_path))
    get_settings.cache_clear()

    with TestClient(app) as test_client:
        yield test_client, database_path

    get_settings.cache_clear()


def test_create_learner_generates_and_persists_uuid(client) -> None:
    test_client, database_path = client

    response = test_client.post("/api/learners", json={"nickname": "Asha", "grade_band": "8-9"})

    assert response.status_code == 201
    learner = response.json()
    assert UUID(learner["id"]).version == 4
    assert learner["nickname"] == "Asha"
    assert learner["grade_band"] == "8-9"
    assert Database(database_path).get_learner(learner["id"]) == learner


@pytest.mark.parametrize("nickname", ["", "   ", "x" * 41])
def test_create_learner_rejects_invalid_nicknames(client, nickname: str) -> None:
    test_client, _ = client

    response = test_client.post("/api/learners", json={"nickname": nickname})

    assert response.status_code == 422


def test_subject_listing_returns_seeded_subjects(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/subjects")

    assert response.status_code == 200
    assert response.json() == {
        "subjects": [
            {"id": "english", "name": "English", "language": "English"},
            {"id": "mathematics", "name": "Mathematics", "language": "English"},
            {"id": "science", "name": "Science", "language": "English"},
            {"id": "social_science", "name": "Social Science", "language": "English"},
        ]
    }


def test_get_seeded_lesson(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/lessons/science-matter-basics")

    assert response.status_code == 200
    lesson = response.json()
    assert lesson["subject"] == "Science"
    assert lesson["topic"] == "States of Matter"
    assert "key_points" in lesson["content"]


def test_unknown_lesson_returns_404(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/lessons/not-a-lesson")

    assert response.status_code == 404
    assert response.json() == {"detail": "Lesson not found"}


def test_existing_health_endpoint_remains_available(client) -> None:
    test_client, _ = client

    assert test_client.get("/api/health").status_code == 200
