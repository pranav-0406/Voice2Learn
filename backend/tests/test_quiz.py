from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import Database
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "voice2learn-quiz-test.sqlite3"
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(database_path))
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client, database_path
    get_settings.cache_clear()


def create_learner(client: TestClient) -> str:
    response = client.post("/api/learners", json={"nickname": "Asha"})
    assert response.status_code == 201
    return response.json()["id"]


def answer(client: TestClient, learner_id: str, question_id: str, value: str):
    return client.post(
        "/api/quiz/answer",
        json={"learner_id": learner_id, "question_id": question_id, "answer": value},
    )


def test_question_delivery_hides_answer_key(client) -> None:
    test_client, _ = client
    learner_id = create_learner(test_client)

    response = test_client.get(f"/api/quiz/next?learner_id={learner_id}&subject=science")

    assert response.status_code == 200
    question = response.json()["question"]
    assert question["difficulty"] == "medium"
    assert "accepted_answers" not in question
    assert "rating" not in question


def test_correct_answer_updates_points_and_persisted_progress(client) -> None:
    test_client, database_path = client
    learner_id = create_learner(test_client)

    response = answer(test_client, learner_id, "matter-gas-space", "Its particles spread out")

    assert response.status_code == 200
    assert response.json()["correct"] is True
    assert response.json()["points_awarded"] == 15
    progress = test_client.get(f"/api/progress/{learner_id}").json()
    assert progress["points"] == 15
    assert progress["ability"] > 1000
    assert progress["topics"] == [
        {"topic": "States of Matter", "attempts": 1, "correct_answers": 1, "mastery_percent": 100.0}
    ]
    assert Database(database_path).get_progress(learner_id)["points"] == 15


def test_incorrect_answer_updates_ability_without_points(client) -> None:
    test_client, _ = client
    learner_id = create_learner(test_client)

    response = answer(test_client, learner_id, "matter-water-states", "Freezing")

    assert response.status_code == 200
    assert response.json()["correct"] is False
    assert response.json()["points_awarded"] == 0
    assert response.json()["ability"] < 1000
    assert test_client.get(f"/api/progress/{learner_id}").json()["incorrect_streak"] == 1


def test_two_correct_answers_raise_target_difficulty(client) -> None:
    test_client, _ = client
    learner_id = create_learner(test_client)

    assert answer(test_client, learner_id, "matter-gas-space", "particles spread out").json()["correct"] is True
    response = answer(test_client, learner_id, "matter-water-states", "heating")

    assert response.json()["target_difficulty"] == "hard"
    next_question = test_client.get(f"/api/quiz/next?learner_id={learner_id}&subject=science").json()["question"]
    assert next_question["difficulty"] == "hard"


def test_two_incorrect_answers_lower_target_difficulty(client) -> None:
    test_client, _ = client
    learner_id = create_learner(test_client)

    assert answer(test_client, learner_id, "matter-gas-space", "heating").json()["correct"] is False
    response = answer(test_client, learner_id, "matter-water-states", "freezing")

    assert response.json()["target_difficulty"] == "easy"
    next_question = test_client.get(f"/api/quiz/next?learner_id={learner_id}&subject=science").json()["question"]
    assert next_question["difficulty"] == "easy"


def test_duplicate_submission_does_not_double_award_points(client) -> None:
    test_client, _ = client
    learner_id = create_learner(test_client)

    first = answer(test_client, learner_id, "matter-solid-shape", "solid")
    duplicate = answer(test_client, learner_id, "matter-solid-shape", "solid")

    assert first.json()["points_awarded"] == 15
    assert duplicate.json()["duplicate_submission"] is True
    assert duplicate.json()["points_awarded"] == 0
    assert test_client.get(f"/api/progress/{learner_id}").json()["points"] == 15


def test_invalid_learner_and_question_ids_return_appropriate_errors(client) -> None:
    test_client, _ = client
    learner_id = create_learner(test_client)

    missing_learner = test_client.get(f"/api/quiz/next?learner_id={uuid4()}&subject=science")
    missing_question = answer(test_client, learner_id, "not-a-question", "solid")
    malformed_learner = test_client.post(
        "/api/quiz/answer",
        json={"learner_id": "invalid", "question_id": "matter-solid-shape", "answer": "solid"},
    )

    assert missing_learner.status_code == 404
    assert missing_question.status_code == 404
    assert malformed_learner.status_code == 422


def test_empty_question_pool_returns_a_graceful_response(client) -> None:
    test_client, database_path = client
    learner_id = create_learner(test_client)
    with Database(database_path).connection() as connection:
        connection.execute("DELETE FROM questions")

    response = test_client.get(f"/api/quiz/next?learner_id={learner_id}&subject=science")

    assert response.status_code == 200
    assert response.json() == {
        "question": None,
        "message": "No unanswered questions remain for this subject",
    }
