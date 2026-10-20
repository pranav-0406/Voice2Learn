"""Tests for CurriculumResolver, active position tracking, and API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.curriculum.resolver import CurriculumResolver
from app.db.database import Database
from app.main import app
from app.voice.interpreter import interpret_text, _paraphrase_command


@pytest.fixture
def client_and_db(tmp_path, monkeypatch):
    database_path = tmp_path / "voice2learn-resolver-test.sqlite3"
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(database_path))
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        db = Database(database_path)
        yield test_client, db
    get_settings.cache_clear()


# =====================================================================
# 1. Direct CurriculumResolver Unit Tests
# =====================================================================

def test_resolver_science_unit_2(client_and_db) -> None:
    _, db = client_and_db
    resolver = CurriculumResolver(db)

    # The exact phrase from the user prompt: "Go to Science Unit 2 and start where I left off"
    res = resolver.resolve("Go to Science Unit 2 and start where I left off")
    assert res.found is True
    assert res.subject_id == "science"
    assert res.chapter_number == 2
    assert "Force and Motion" in res.chapter_title
    assert res.concept_id == "sci-ch02-c01"
    assert res.chapter_id == "sci-term1-ch02"
    assert res.target_url == "/concept/sci-ch02-c01"


def test_resolver_science_unit_1_and_3(client_and_db) -> None:
    _, db = client_and_db
    resolver = CurriculumResolver(db)

    # Unit 1
    res1 = resolver.resolve("Science Unit 1")
    assert res1.found is True
    assert res1.chapter_number == 1
    assert "Measurements" in res1.chapter_title
    assert res1.concept_id == "sci-ch01-c01"

    # Unit 3
    res3 = resolver.resolve("let's do science unit three")
    assert res3.found is True
    assert res3.chapter_number == 3
    assert "Matter Around Us" in res3.chapter_title
    assert res3.concept_id == "sci-ch03-c01"


def test_resolver_math_english_social(client_and_db) -> None:
    _, db = client_and_db
    resolver = CurriculumResolver(db)

    # Math Unit 1
    res_math = resolver.resolve("Mathematics chapter 1")
    assert res_math.found is True
    assert res_math.subject_id == "mathematics"
    assert res_math.chapter_number == 1
    assert "Numbers" in res_math.chapter_title

    # English Unit 1
    res_eng = resolver.resolve("English unit 1")
    assert res_eng.found is True
    assert res_eng.subject_id == "english"
    assert res_eng.chapter_number == 1
    assert "Sea Turtles" in res_eng.chapter_title

    # Social Science Unit 1
    res_soc = resolver.resolve("Social Science chapter 1")
    assert res_soc.found is True
    assert res_soc.subject_id == "social_science"
    assert res_soc.chapter_number == 1
    assert "What is History?" in res_soc.chapter_title


def test_resolver_nonexistent_unit_returns_honest_error(client_and_db) -> None:
    _, db = client_and_db
    resolver = CurriculumResolver(db)

    # Science only has 7 units in Class 6 Term 1
    res = resolver.resolve("Science Unit 99")
    assert res.found is False
    assert res.error is not None
    assert "Science has 7 units" in res.error
    # Crucially: it must NOT silently default to Science Chapter 3!
    assert res.chapter_id is None
    assert res.concept_id is None


def test_resolver_unknown_subject(client_and_db) -> None:
    _, db = client_and_db
    resolver = CurriculumResolver(db)

    res = resolver.resolve("French Unit 2")
    assert res.found is False
    assert res.error is not None
    assert "Could not identify" in res.error


def test_resolver_title_query(client_and_db) -> None:
    _, db = client_and_db
    resolver = CurriculumResolver(db)

    # Match by chapter title
    res = resolver.resolve("Matter Around Us")
    assert res.found is True
    assert res.subject_id == "science"
    assert res.chapter_number == 3
    assert "Matter Around Us" in res.chapter_title


# =====================================================================
# 2. Database Active Learner Position Tracking
# =====================================================================

def test_learner_active_position_crud(client_and_db) -> None:
    _, db = client_and_db

    # Initially empty
    pos = db.get_active_position("learner-test-1")
    assert pos is None

    # Save active position for Science Chapter 2
    db.save_active_position(
        learner_id="learner-test-1",
        subject_id="science",
        chapter_id="sci-term1-ch02",
        concept_id="sci-ch02-c01",
    )

    pos = db.get_active_position("learner-test-1")
    assert pos is not None
    assert pos["learner_id"] == "learner-test-1"
    assert pos["subject_id"] == "science"
    assert pos["chapter_id"] == "sci-term1-ch02"
    assert pos["concept_id"] == "sci-ch02-c01"
    assert "Force and Motion" in pos["chapter_title"]
    assert pos["chapter_number"] == 2

    # Save position for Mathematics Chapter 1
    db.save_active_position(
        learner_id="learner-test-1",
        subject_id="mathematics",
        chapter_id="math-term1-ch01",
        concept_id="math-ch01-c01",
    )

    # Fetching without subject returns the most recently updated (Mathematics)
    latest = db.get_active_position("learner-test-1")
    assert latest["subject_id"] == "mathematics"
    assert "Numbers" in latest["chapter_title"]

    # Fetching specifically for science returns Science position
    sci_pos = db.get_active_position("learner-test-1", subject_id="science")
    assert sci_pos is not None
    assert sci_pos["subject_id"] == "science"
    assert "Force and Motion" in sci_pos["chapter_title"]


# =====================================================================
# 3. API Endpoints
# =====================================================================

def test_api_curriculum_resolve_endpoint(client_and_db) -> None:
    client, _ = client_and_db

    response = client.post("/api/curriculum/resolve", json={"query": "Science Unit 2"})
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert data["subject_id"] == "science"
    assert data["chapter_number"] == 2
    assert "Force and Motion" in data["chapter_title"]
    assert data["concept_id"] == "sci-ch02-c01"
    assert data["target_url"] == "/concept/sci-ch02-c01"


def test_api_curriculum_resolve_nonexistent(client_and_db) -> None:
    client, _ = client_and_db

    response = client.post("/api/curriculum/resolve", json={"query": "Science Unit 50"})
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is False
    assert data["error"] is not None


def test_api_progress_position_endpoints(client_and_db) -> None:
    client, _ = client_and_db

    # Initially empty
    get_res = client.get("/api/progress/learner-42/position")
    assert get_res.status_code == 200
    assert get_res.json() is None

    # Save position
    post_res = client.post(
        "/api/progress/position",
        json={
            "learner_id": "learner-42",
            "subject_id": "science",
            "chapter_id": "sci-term1-ch02",
            "concept_id": "sci-ch02-c01",
        },
    )
    assert post_res.status_code == 200
    assert post_res.json()["chapter_id"] == "sci-term1-ch02"

    # Retrieve position
    get_res2 = client.get("/api/progress/learner-42/position")
    assert get_res2.status_code == 200
    pos_data = get_res2.json()
    assert pos_data is not None
    assert "Force and Motion" in pos_data["chapter_title"]
    assert pos_data["chapter_number"] == 2
    assert pos_data["concept_id"] == "sci-ch02-c01"


# =====================================================================
# 4. Interpreter Regression Test
# =====================================================================

def test_interpreter_does_not_strip_unit_to_generic_open_lesson() -> None:
    # Generic "open lesson" without unit -> maps to OPEN_LESSON
    res1 = interpret_text("open lesson", active_quiz=False)
    assert res1.command == "OPEN_LESSON"

    # Specific "science unit 2" must NOT be reduced to parameterless OPEN_LESSON!
    res2 = interpret_text("let's study science unit 2", active_quiz=False)
    assert res2.command != "OPEN_LESSON"

    # Direct paraphrase check
    cmd_para = _paraphrase_command("science unit 2")
    assert cmd_para is None
