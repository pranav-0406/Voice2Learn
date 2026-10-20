import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "voice2learn-curriculum-test.sqlite3"
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(database_path))
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client, database_path
    get_settings.cache_clear()


def test_list_curriculum_subjects(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/subjects")

    assert response.status_code == 200
    data = response.json()
    assert "subjects" in data
    subjects = data["subjects"]
    assert len(subjects) == 4

    subject_ids = [s["id"] for s in subjects]
    assert subject_ids == ["english", "mathematics", "science", "social_science"]

    # Verify each subject metadata
    eng = subjects[0]
    assert eng["code"] == "ENG"
    assert eng["chapter_count"] == 3
    assert 1 in eng["terms_available"]

    math = subjects[1]
    assert math["code"] == "MATH"
    assert math["chapter_count"] == 6

    sci = subjects[2]
    assert sci["code"] == "SCI"
    assert sci["chapter_count"] == 7

    soc = subjects[3]
    assert soc["code"] == "SOC"
    assert soc["chapter_count"] == 8


def test_get_curriculum_subject_by_id(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/subjects/science")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "science"
    assert data["name"] == "Science"
    assert data["code"] == "SCI"
    assert data["chapter_count"] == 7


def test_get_unknown_curriculum_subject_returns_404(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/subjects/astronomy")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_term_chapters_english(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/subjects/english/terms/1")

    assert response.status_code == 200
    data = response.json()
    assert data["subject_id"] == "english"
    assert data["term"] == 1
    chapters = data["chapters"]
    assert len(chapters) == 3
    assert chapters[0]["id"] == "eng-term1-ch01"
    assert "Sea Turtles" in chapters[0]["title"]
    assert chapters[0]["lesson_id"] == "english-sea-turtles"


def test_get_term_chapters_mathematics(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/subjects/mathematics/terms/1")

    assert response.status_code == 200
    data = response.json()
    assert data["subject_id"] == "mathematics"
    assert len(data["chapters"]) == 6
    assert data["chapters"][0]["title"] == "Chapter 1: Numbers"


def test_get_term_chapters_science(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/subjects/science/terms/1")

    assert response.status_code == 200
    data = response.json()
    assert data["subject_id"] == "science"
    assert len(data["chapters"]) == 7


def test_get_term_chapters_social_science(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/subjects/social_science/terms/1")

    assert response.status_code == 200
    data = response.json()
    assert data["subject_id"] == "social_science"
    assert len(data["chapters"]) == 8


def test_get_term_chapters_invalid_term_returns_422(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/subjects/science/terms/5")

    assert response.status_code == 422


def test_get_chapter_detail_with_concepts(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/chapters/sci-term1-ch01")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "sci-term1-ch01"
    assert data["subject_id"] == "science"
    assert data["chapter_number"] == 1
    assert "Measurements" in data["title"]
    assert len(data["concepts"]) >= 1
    concept = data["concepts"][0]
    assert "SI Units" in concept["title"]
    assert len(concept["key_points"]) > 0


def test_get_unknown_chapter_returns_404(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/chapters/nonexistent-ch99")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_concept_detail(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/concepts/math-ch01-c02")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "math-ch01-c02"
    assert "BIDMAS" in data["title"]
    assert any("Brackets" in pt for pt in data["key_points"])


def test_get_unknown_concept_returns_404(client) -> None:
    test_client, _ = client

    response = test_client.get("/api/curriculum/concepts/unknown-concept")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
