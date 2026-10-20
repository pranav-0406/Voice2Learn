"""Tests for M04 concept-lesson endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "voice2learn-concept-lesson-test.sqlite3"
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(database_path))
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_concept_lesson_success(client: TestClient) -> None:
    """GET /api/curriculum/concepts/{id}/lesson returns ConceptLessonResponse."""
    # First, discover a valid concept ID via the chapter detail endpoint
    chapters_resp = client.get("/api/curriculum/subjects/science/terms/1")
    assert chapters_resp.status_code == 200
    chapters = chapters_resp.json()["chapters"]
    assert len(chapters) > 0

    # Pick first chapter that has at least one concept
    chapter_with_concepts = next(
        (ch for ch in chapters if ch["concept_count"] > 0), None
    )
    assert chapter_with_concepts is not None, "Science term 1 must have at least one concept"

    chapter_resp = client.get(f"/api/curriculum/chapters/{chapter_with_concepts['id']}")
    assert chapter_resp.status_code == 200
    chapter_data = chapter_resp.json()
    concepts = chapter_data["concepts"]
    assert len(concepts) > 0

    concept_id = concepts[0]["id"]

    # Now test the M04 endpoint
    resp = client.get(f"/api/curriculum/concepts/{concept_id}/lesson")
    assert resp.status_code == 200
    data = resp.json()

    # Required top-level fields
    assert data["id"] == concept_id
    assert "title" in data
    assert "summary" in data
    assert isinstance(data["key_points"], list)
    assert "chapter_id" in data
    assert "chapter_title" in data
    assert "subject_id" in data
    assert "subject_name" in data
    assert "subject_icon" in data
    assert "subject_accent" in data
    assert "term" in data
    assert "chapter_number" in data
    assert isinstance(data["index"], int)
    assert isinstance(data["total"], int)
    assert data["total"] >= 1
    assert 0 <= data["index"] < data["total"]
    assert isinstance(data["all_concepts"], list)
    assert len(data["all_concepts"]) == data["total"]


def test_concept_lesson_first_has_no_prev(client: TestClient) -> None:
    """The first concept in a chapter should have prev_concept = null."""
    chapters_resp = client.get("/api/curriculum/subjects/science/terms/1")
    chapters = chapters_resp.json()["chapters"]
    chapter_with_concepts = next(
        (ch for ch in chapters if ch["concept_count"] > 0), None
    )
    assert chapter_with_concepts is not None

    chapter_resp = client.get(f"/api/curriculum/chapters/{chapter_with_concepts['id']}")
    first_concept_id = chapter_resp.json()["concepts"][0]["id"]

    resp = client.get(f"/api/curriculum/concepts/{first_concept_id}/lesson")
    assert resp.status_code == 200
    data = resp.json()
    assert data["prev_concept"] is None
    assert data["index"] == 0


def test_concept_lesson_last_has_no_next(client: TestClient) -> None:
    """The last concept in a chapter should have next_concept = null."""
    chapters_resp = client.get("/api/curriculum/subjects/science/terms/1")
    chapters = chapters_resp.json()["chapters"]
    chapter_with_concepts = next(
        (ch for ch in chapters if ch["concept_count"] > 1), None
    )
    if chapter_with_concepts is None:
        pytest.skip("Need a chapter with more than 1 concept for this test")

    chapter_resp = client.get(f"/api/curriculum/chapters/{chapter_with_concepts['id']}")
    last_concept_id = chapter_resp.json()["concepts"][-1]["id"]

    resp = client.get(f"/api/curriculum/concepts/{last_concept_id}/lesson")
    assert resp.status_code == 200
    data = resp.json()
    assert data["next_concept"] is None


def test_concept_lesson_navigation_chain(client: TestClient) -> None:
    """Verify prev→current→next navigation links are consistent."""
    chapters_resp = client.get("/api/curriculum/subjects/mathematics/terms/1")
    chapters = chapters_resp.json()["chapters"]
    chapter_with_multi = next(
        (ch for ch in chapters if ch["concept_count"] > 1), None
    )
    if chapter_with_multi is None:
        pytest.skip("Need a chapter with 2+ concepts")

    chapter_resp = client.get(f"/api/curriculum/chapters/{chapter_with_multi['id']}")
    concepts = chapter_resp.json()["concepts"]

    first_resp = client.get(f"/api/curriculum/concepts/{concepts[0]['id']}/lesson")
    first_data = first_resp.json()

    assert first_data["next_concept"] is not None
    next_id = first_data["next_concept"]["id"]

    second_resp = client.get(f"/api/curriculum/concepts/{next_id}/lesson")
    second_data = second_resp.json()

    assert second_data["prev_concept"] is not None
    assert second_data["prev_concept"]["id"] == concepts[0]["id"]


def test_concept_lesson_not_found(client: TestClient) -> None:
    """404 returned for non-existent concept ID."""
    resp = client.get("/api/curriculum/concepts/does-not-exist/lesson")
    assert resp.status_code == 404


def test_concept_lesson_all_subjects(client: TestClient) -> None:
    """concept/lesson endpoint returns data for all 4 subjects."""
    subjects_resp = client.get("/api/curriculum/subjects")
    subjects = subjects_resp.json()["subjects"]

    for subject in subjects:
        chapters_resp = client.get(f"/api/curriculum/subjects/{subject['id']}/terms/1")
        chapters = chapters_resp.json()["chapters"]
        chapter_with_concepts = next(
            (ch for ch in chapters if ch["concept_count"] > 0), None
        )
        if chapter_with_concepts is None:
            continue  # Skip subjects with no seeded concepts

        chapter_resp = client.get(f"/api/curriculum/chapters/{chapter_with_concepts['id']}")
        first_concept_id = chapter_resp.json()["concepts"][0]["id"]

        resp = client.get(f"/api/curriculum/concepts/{first_concept_id}/lesson")
        assert resp.status_code == 200, (
            f"Expected 200 for {subject['name']} concept {first_concept_id}"
        )
        data = resp.json()
        assert data["subject_id"] == subject["id"]
        assert data["subject_name"] == subject["name"]
