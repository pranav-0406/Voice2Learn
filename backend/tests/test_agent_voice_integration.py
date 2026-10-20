"""Regression tests for natural-language voice agent integration and safety (Phase 2 fix)."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.agent.runtime import AgentRuntime, is_valid_route
from app.agent.schemas import (
    ActionType,
    AgentAction,
    AgentContext,
    AgentRunRequest,
)
from app.core.config import Settings, get_settings
from app.curriculum.resolver import CurriculumResolver
from app.db.database import Database
from app.main import app
from app.qa.groq import GroqLLMProvider
from app.voice.interpreter import interpret_text


@pytest.fixture
def agent_test_client(tmp_path, monkeypatch):
    database_path = tmp_path / "voice2learn-integration.sqlite3"
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(database_path))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        db = Database(database_path)
        resolver = CurriculumResolver(db)
        runtime = AgentRuntime(database=db, resolver=resolver)
        yield test_client, db, resolver, runtime
    get_settings.cache_clear()


# =====================================================================
# 1. Model Configuration & Settings
# =====================================================================

def test_groq_llm_model_defaults_to_accessible_model() -> None:
    settings = Settings()
    assert settings.groq_llm_model == "openai/gpt-oss-20b"
    assert settings.groq_agent_model == "openai/gpt-oss-120b"


def test_groq_llm_provider_initialization() -> None:
    settings = Settings(groq_api_key="mock_key", groq_llm_model="openai/gpt-oss-20b")
    provider = GroqLLMProvider(settings)
    assert provider.configured is True
    assert provider._model == "openai/gpt-oss-20b"


# =====================================================================
# 2. Fast-Path Deterministic Rules
# =====================================================================

@pytest.mark.parametrize(
    "phrase",
    [
        "show me progress",
        "show me the progress",
        "show my progress",
        "see my progress",
        "i want to see my progress",
        "let's see my progress",
        "show progress",
        "view progress",
    ],
)
def test_fast_path_show_progress_variations(phrase: str) -> None:
    result = interpret_text(phrase, active_quiz=False)
    assert result.intent == "command"
    assert result.command == "SHOW_PROGRESS"


@pytest.mark.parametrize(
    "phrase",
    [
        "continue learning",
        "let's continue learning",
        "keep learning",
        "resume lesson",
        "continue lesson",
    ],
)
def test_fast_path_continue_learning_variations(phrase: str) -> None:
    result = interpret_text(phrase, active_quiz=False)
    assert result.intent == "command"
    assert result.command == "OPEN_LESSON"


@pytest.mark.parametrize(
    "phrase",
    [
        "let's learn Science Unit 1",
        "open Science Unit 1",
        "let's study Science Unit 2",
        "take me to Math Unit 3",
    ],
)
def test_unit_phrases_not_captured_by_generic_command(phrase: str) -> None:
    result = interpret_text(phrase, active_quiz=False)
    # Unit requests bypass generic parameterless commands so the agent can resolve them
    assert result.command is None


# =====================================================================
# 3. Agent Unit Resolution & Endpoint Execution
# =====================================================================

def test_agent_resolves_science_unit_1(agent_test_client) -> None:
    client, _, _, _ = agent_test_client
    resp = client.post(
        "/api/agent/run",
        json={
            "prompt": "Let’s learn Science Unit 1",
            "context": {"learner_id": "demo-learner", "current_url": "/dashboard"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["target_url"] == "/concept/sci-ch01-c01"
    assert "Measurements" in data["final_message"] or "opened" in data["final_message"].lower()


def test_agent_resolves_science_unit_2(agent_test_client) -> None:
    client, _, _, _ = agent_test_client
    resp = client.post(
        "/api/agent/run",
        json={
            "prompt": "open Science Unit 2",
            "context": {"learner_id": "demo-learner", "current_url": "/dashboard"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["target_url"] == "/concept/sci-ch02-c01"
    assert "Force" in data["final_message"] or "opened" in data["final_message"].lower()


def test_agent_resolves_math_unit_3(agent_test_client) -> None:
    client, _, _, _ = agent_test_client
    resp = client.post(
        "/api/agent/run",
        json={
            "prompt": "Let's study Math Unit 3",
            "context": {"learner_id": "demo-learner", "current_url": "/dashboard"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["target_url"] == "/concept/math-ch03-c01"


def test_agent_rejects_invalid_unit_with_clarification(agent_test_client) -> None:
    client, _, _, _ = agent_test_client
    resp = client.post(
        "/api/agent/run",
        json={
            "prompt": "Let's learn Science Unit 99",
            "context": {"learner_id": "demo-learner", "current_url": "/dashboard"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "needs_clarification"
    assert data["target_url"] is None
    assert "Unit 99 does not exist" in data["final_message"]


# =====================================================================
# 4. Context Preservation & Active Position
# =====================================================================

def test_agent_resumes_saved_active_position(agent_test_client) -> None:
    client, db, _, _ = agent_test_client
    # Save student active position at Unit 2 Concept 1
    db.save_active_position("student-42", "science", "sci-term1-ch02", "sci-ch02-c01")

    resp = client.post(
        "/api/agent/run",
        json={
            "prompt": "Let's continue learning",
            "context": {"learner_id": "student-42", "current_url": "/dashboard"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["target_url"] == "/concept/sci-ch02-c01"
    assert "continue" in data["final_message"].lower() or "welcome back" in data["final_message"].lower()


def test_agent_falls_back_to_initial_concept_when_no_active_position(agent_test_client) -> None:
    client, _, _, _ = agent_test_client
    resp = client.post(
        "/api/agent/run",
        json={
            "prompt": "Let's continue learning",
            "context": {"learner_id": "new-student", "current_url": "/dashboard"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["target_url"] == "/concept/sci-ch01-c01"


# =====================================================================
# 5. Route Validation & Safety
# =====================================================================

def test_is_valid_route() -> None:
    # Allowed static routes
    assert is_valid_route("/dashboard") is True
    assert is_valid_route("/quiz") is True
    assert is_valid_route("/progress") is True
    assert is_valid_route("/login") is True
    assert is_valid_route("/register") is True

    # Allowed concept routes
    assert is_valid_route("/concept/sci-ch01-c01") is True
    assert is_valid_route("/concept/math-ch03-c02") is True

    # Invalid / Disallowed routes
    assert is_valid_route(None) is False
    assert is_valid_route("") is False
    assert is_valid_route("/malicious/exploit") is False
    assert is_valid_route("/admin/delete_all") is False
    assert is_valid_route("https://external-site.com") is False
    assert is_valid_route("/concept/../../etc/passwd") is False


def test_agent_rejects_hallucinated_route_and_marks_failed(agent_test_client) -> None:
    _, db, resolver, runtime = agent_test_client

    # Mock tool call returning a hallucinated/invalid URL
    fake_tool = MagicMock()
    fake_tool.function.name = "navigate"
    fake_tool.function.arguments = '{"url": "/unauthorized/internal-page", "reason": "Hallucinated page"}'

    fake_msg = MagicMock()
    fake_msg.tool_calls = [fake_tool]
    fake_msg.content = None

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value.choices = [MagicMock(message=fake_msg)]

    with patch.object(runtime, "_get_groq_client", return_value=fake_client):
        req = AgentRunRequest(
            prompt="open unauthorized internal page",
            context=AgentContext(learner_id="test", current_url="/dashboard"),
        )
        res = runtime.run(req)

        assert res.status == "failed"
        assert res.target_url is None
        assert "not an allowed lesson route" in res.final_message
