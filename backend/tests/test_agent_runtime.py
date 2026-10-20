"""Tests for the Voice2Learn AI Browser Agent Runtime and Action Engine (Phase 2)."""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.agent.runtime import AgentRuntime
from app.agent.schemas import (
    ActionType,
    AgentAction,
    AgentContext,
    AgentRunRequest,
)
from app.agent.tools import AGENT_TOOLS, parse_tool_call
from app.core.config import Settings, get_settings
from app.curriculum.resolver import CurriculumResolver
from app.db.database import Database
from app.main import app


@pytest.fixture
def agent_setup(tmp_path, monkeypatch):
    database_path = tmp_path / "voice2learn-agent-test.sqlite3"
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(database_path))
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        db = Database(database_path)
        resolver = CurriculumResolver(db)
        runtime = AgentRuntime(database=db, resolver=resolver)
        yield test_client, db, resolver, runtime
    get_settings.cache_clear()


# =====================================================================
# 1. Tool Definitions and Parser Tests
# =====================================================================

def test_agent_tools_schema() -> None:
    assert len(AGENT_TOOLS) == 7
    tool_names = [t["function"]["name"] for t in AGENT_TOOLS]
    assert "resolve_curriculum" in tool_names
    assert "navigate" in tool_names
    assert "click_element" in tool_names
    assert "scroll_page" in tool_names
    assert "read_aloud" in tool_names
    assert "complete_task" in tool_names
    assert "ask_clarification" in tool_names


def test_parse_tool_call() -> None:
    # Navigate
    action_nav = parse_tool_call("navigate", '{"url": "/concept/sci-ch02-c01", "reason": "Opening unit 2"}')
    assert action_nav.action_type == ActionType.NAVIGATE
    assert action_nav.target_url == "/concept/sci-ch02-c01"
    assert "Opening unit 2" in action_nav.thought

    # Click
    action_click = parse_tool_call("click_element", '{"selector": "#btn-continue", "reason": "Continue learning"}')
    assert action_click.action_type == ActionType.CLICK
    assert action_click.selector == "#btn-continue"

    # Scroll
    action_scroll = parse_tool_call("scroll_page", '{"direction": "down", "reason": "View next section"}')
    assert action_scroll.action_type == ActionType.SCROLL
    assert action_scroll.scroll_direction == "down"

    # Complete
    action_done = parse_tool_call("complete_task", '{"message": "Lesson loaded!", "success": true}')
    assert action_done.action_type == ActionType.COMPLETE_TASK
    assert action_done.message == "Lesson loaded!"
    assert action_done.success is True

    # Clarification
    action_clarify = parse_tool_call("ask_clarification", '{"question": "Did you mean Unit 2 or Unit 3?"}')
    assert action_clarify.action_type == ActionType.ASK_CLARIFICATION
    assert action_clarify.message == "Did you mean Unit 2 or Unit 3?"


# =====================================================================
# 2. Curriculum Resolution via Runtime
# =====================================================================

def test_agent_runtime_curriculum_resolution(agent_setup) -> None:
    _, _, _, runtime = agent_setup

    # Science Unit 2 resolution
    res = runtime.execute_curriculum_resolution({"subject": "science", "unit_number": 2})
    assert res["found"] is True
    assert res["subject_id"] == "science"
    assert res["chapter_number"] == 2
    assert "Force and Motion" in res["chapter_title"]
    assert res["target_url"] == "/concept/sci-ch02-c01"

    # Invalid unit resolution
    res_invalid = runtime.execute_curriculum_resolution({"subject": "science", "unit_number": 99})
    assert res_invalid["found"] is False
    assert "Science has 7 units" in res_invalid["error"]


# =====================================================================
# 3. Deterministic Fallback Execution
# =====================================================================

def test_agent_runtime_fallback_science_unit_2(agent_setup) -> None:
    _, _, _, runtime = agent_setup

    req = AgentRunRequest(
        prompt="Go to Science Unit 2 and start where I left off",
        context=AgentContext(current_url="/dashboard", page_title="Dashboard"),
    )

    resp = runtime._fallback_rule_execution("test_run_1", req)
    assert resp.status == "completed"
    assert resp.target_url == "/concept/sci-ch02-c01"
    assert len(resp.steps) >= 2
    assert resp.steps[0].action.action_type == ActionType.NAVIGATE
    assert resp.steps[1].action.action_type == ActionType.COMPLETE_TASK


def test_agent_runtime_fallback_nonexistent_unit(agent_setup) -> None:
    _, _, _, runtime = agent_setup

    req = AgentRunRequest(
        prompt="Open Science Unit 99",
        context=AgentContext(current_url="/dashboard", page_title="Dashboard"),
    )

    resp = runtime._fallback_rule_execution("test_run_2", req)
    assert resp.status == "needs_clarification"
    assert "Science has 7 units" in resp.final_message


def test_agent_runtime_fallback_quiz(agent_setup) -> None:
    _, _, _, runtime = agent_setup

    req = AgentRunRequest(
        prompt="Take me to the adaptive quiz",
        context=AgentContext(current_url="/dashboard"),
    )

    resp = runtime._fallback_rule_execution("test_run_3", req)
    assert resp.status == "completed"
    assert resp.target_url == "/quiz"


# =====================================================================
# 4. Multi-Step Groq LLM Tool Calling Simulation
# =====================================================================

def test_agent_runtime_with_mock_groq(agent_setup) -> None:
    _, _, _, runtime = agent_setup

    # Mock response 1: LLM decides to call resolve_curriculum
    mock_tool_call_1 = MagicMock()
    mock_tool_call_1.id = "call_resolv_1"
    mock_tool_call_1.function.name = "resolve_curriculum"
    mock_tool_call_1.function.arguments = '{"subject": "science", "unit_number": 2}'

    mock_msg_1 = MagicMock()
    mock_msg_1.tool_calls = [mock_tool_call_1]
    mock_msg_1.content = None

    mock_choice_1 = MagicMock()
    mock_choice_1.message = mock_msg_1

    mock_resp_1 = MagicMock()
    mock_resp_1.choices = [mock_choice_1]

    # Mock response 2: LLM receives resolution and calls complete_task
    mock_tool_call_2 = MagicMock()
    mock_tool_call_2.id = "call_complete_2"
    mock_tool_call_2.function.name = "complete_task"
    mock_tool_call_2.function.arguments = '{"message": "I opened Science Unit 2: Force and Motion for you!", "success": true}'

    mock_msg_2 = MagicMock()
    mock_msg_2.tool_calls = [mock_tool_call_2]
    mock_msg_2.content = None

    mock_choice_2 = MagicMock()
    mock_choice_2.message = mock_msg_2

    mock_resp_2 = MagicMock()
    mock_resp_2.choices = [mock_choice_2]

    mock_groq = MagicMock()
    mock_groq.chat.completions.create.side_effect = [mock_resp_1, mock_resp_2]

    with patch.object(runtime, "_get_groq_client", return_value=mock_groq):
        req = AgentRunRequest(
            prompt="Go to Science Unit 2 and start where I left off",
            context=AgentContext(learner_id="test-learner", current_url="/dashboard"),
        )
        resp = runtime.run(req)

        assert resp.status == "completed"
        assert resp.target_url == "/concept/sci-ch02-c01"
        assert resp.total_steps == 2
        assert "Force and Motion" in resp.final_message


# =====================================================================
# 5. FastAPI Endpoint Test
# =====================================================================

def test_api_agent_run_endpoint(agent_setup) -> None:
    client, _, _, _ = agent_setup

    response = client.post(
        "/api/agent/run",
        json={
            "prompt": "Go to Science Unit 2 and start where I left off",
            "context": {
                "learner_id": "test-learner",
                "current_url": "/dashboard",
                "page_title": "Dashboard",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"completed", "needs_clarification"}
    assert data["target_url"] == "/concept/sci-ch02-c01"
    assert data["total_steps"] >= 1
    assert "run_id" in data
