"""Unit and integration tests for Module M09: Curriculum-Grounded RAG Learning Assistant.

Verifies:
1. Retrieval and multi-factor ranking across SQLite curriculum concepts.
2. Subject-specific filtering and query-inferred subject detection.
3. Active lesson / screen context boosts.
4. Ranking on ambiguous and overlapping queries.
5. Strict rejection of unsupported / out-of-scope questions (anti-hallucination).
6. Grounded answer generation with mock LLM providers.
7. Direct-summary fallback when LLM is unavailable (offline mode).
8. Provider failures (timeouts, network errors) degrade gracefully to direct summaries.
9. Anaphoric follow-up resolution and vague query clarifications.
10. Preservation of command separation: questions NEVER trigger or return commands.
11. REST API endpoint /api/curriculum/ask response structure and source attribution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pytest
from starlette.testclient import TestClient

from app.core.config import get_settings
from app.db.database import Database
from app.main import app
from app.qa.assistant import (
    CLARIFICATION_PROMPT,
    OUT_OF_SCOPE_MESSAGE,
    CurriculumAssistant,
    is_anaphoric_follow_up,
    resolve_follow_up_query,
)
from app.qa.groq import LanguageModelUnavailableError
from app.qa.retriever import CurriculumRetriever, tokenize_query
from app.voice.understanding import LanguageModelProvider, NullLLMProvider


@pytest.fixture
def test_db(tmp_path: Path) -> Database:
    """Initialize a test database with curriculum tables seeded."""
    db_path = tmp_path / "rag_test.sqlite3"
    db = Database(db_path)
    db.initialize()
    return db


@pytest.fixture
def retriever(test_db: Database) -> CurriculumRetriever:
    return CurriculumRetriever(test_db)


@pytest.fixture
def assistant(retriever: CurriculumRetriever) -> CurriculumAssistant:
    return CurriculumAssistant(retriever)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(tmp_path / "rag_api.sqlite3"))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("VOICE2LEARN_OLLAMA_MODEL", raising=False)
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


# ─── 1. Tokenization & Helper Tests ──────────────────────────────────────────

def test_tokenize_query_removes_stop_words() -> None:
    tokens = tokenize_query("What is the state of matter?")
    assert "state" in tokens
    assert "matter" in tokens
    assert "what" not in tokens
    assert "is" not in tokens
    assert "the" not in tokens
    assert "of" not in tokens


def test_tokenize_query_handles_all_stop_words_fallback() -> None:
    tokens = tokenize_query("what is it")
    assert tokens == ["what", "is", "it"]


# ─── 2. Curriculum Retrieval & Relevance Ranking ──────────────────────────────

def test_retriever_finds_matter_concept(retriever: CurriculumRetriever) -> None:
    docs = retriever.retrieve("What is matter?")
    assert len(docs) > 0
    top = docs[0]
    assert top.is_supported
    assert "matter" in top.summary.lower() or "matter" in (top.concept_title or "").lower()
    assert top.subject_id == "science"


def test_retriever_finds_sea_turtles(retriever: CurriculumRetriever) -> None:
    docs = retriever.retrieve("Tell me about sea turtles")
    assert len(docs) > 0
    top = docs[0]
    assert top.is_supported
    assert "turtle" in (top.concept_title or "").lower() or "turtle" in top.summary.lower()
    assert top.subject_id == "english"


def test_retriever_finds_measurements(retriever: CurriculumRetriever) -> None:
    docs = retriever.retrieve("What is an SI unit of length?")
    assert len(docs) > 0
    top = docs[0]
    assert top.is_supported
    assert top.subject_id == "science"
    assert "measurement" in top.chapter_title.lower() or "measurements" in (top.concept_title or "").lower()


# ─── 3. Subject Filters & Inferred Filters ─────────────────────────────────────

def test_retriever_explicit_subject_filter(retriever: CurriculumRetriever) -> None:
    docs = retriever.retrieve("units", subject_id="science")
    for doc in docs:
        assert doc.subject_id == "science"


def test_retriever_infers_subject_from_query(retriever: CurriculumRetriever) -> None:
    docs = retriever.retrieve("What do we learn in science about matter?")
    assert len(docs) > 0
    assert docs[0].subject_id == "science"


def test_retriever_infers_mathematics_from_query(retriever: CurriculumRetriever) -> None:
    docs = retriever.retrieve("What are fractions in math?")
    assert len(docs) > 0
    assert docs[0].subject_id == "mathematics"


# ─── 4. Active Screen Context Boosts ──────────────────────────────────────────

def test_retriever_context_boosts_matching_concept(retriever: CurriculumRetriever) -> None:
    context = {"screen": "/concept/sci-ch01-c01", "concept_id": "sci-ch01-c01"}
    docs = retriever.retrieve("measurements", context=context)
    assert len(docs) > 0
    # The active concept gets a relevance boost
    assert docs[0].concept_id == "sci-ch01-c01"


# ─── 5. Anti-Hallucination & Out-of-Scope Rejection ───────────────────────────

def test_retriever_rejects_completely_unsupported_topic(retriever: CurriculumRetriever) -> None:
    docs = retriever.retrieve("Who won the 2026 World Cup in football?")
    if docs:
        assert not docs[0].is_supported


def test_assistant_returns_out_of_scope_for_unrelated_topic(assistant: CurriculumAssistant) -> None:
    result = assistant.answer_question("What is cryptocurrency and Bitcoin?")
    assert not result.supported
    assert result.source is None
    assert "outside our Class 6 curriculum" in result.answer


def test_assistant_rejects_random_single_keyword_hit(assistant: CurriculumAssistant) -> None:
    """A single incidental keyword match without topical coverage must be rejected."""
    result = assistant.answer_question("Where can I buy a quantum computer in Tokyo?")
    assert not result.supported
    assert "outside our Class 6 curriculum" in result.answer


# ─── 6. Direct Summary Fallback (Offline Mode) ────────────────────────────────

def test_assistant_direct_summary_fallback_when_no_llm(assistant: CurriculumAssistant) -> None:
    """When no LLM provider is configured, the assistant provides verified curriculum facts directly."""
    null_provider = NullLLMProvider()
    result = assistant.answer_question(
        "What are the three states of matter?",
        context={"screen": "/lesson/science-matter-basics"},
        provider=null_provider,
    )
    assert result.supported
    assert result.source is not None
    assert result.source.subject_id == "science"
    assert "matter" in result.answer.lower() or "solid" in result.answer.lower()


def test_assistant_extracts_relevant_key_point(assistant: CurriculumAssistant) -> None:
    null_provider = NullLLMProvider()
    result = assistant.answer_question(
        "Which sea turtle is the largest?",
        provider=null_provider,
    )
    assert result.supported
    assert result.source is not None
    assert "Leatherback" in result.answer or "turtle" in result.answer.lower()


# ─── 7. Grounded Answer Synthesis with Mock LLM ───────────────────────────────

class MockLLMProvider:
    configured = True

    def __init__(self, response_text: str, supported: bool = True):
        self.response_text = response_text
        self.supported = supported
        self.last_prompt: str | None = None

    def answer(self, prompt: str) -> str:
        self.last_prompt = prompt
        return json.dumps({
            "supported": self.supported,
            "response": self.response_text,
            "clarification": None if self.supported else "Topic not supported",
        })


def test_assistant_synthesizes_grounded_answer(assistant: CurriculumAssistant) -> None:
    mock = MockLLMProvider("Matter is anything that has mass and takes up space.")
    result = assistant.answer_question(
        "What is matter?",
        context={"screen": "/lesson/science-matter-basics"},
        provider=mock,  # type: ignore
    )
    assert result.supported
    assert result.answer == "Matter is anything that has mass and takes up space."
    assert result.source is not None
    assert result.source.subject_id == "science"
    assert "Retrieved Evidence:" in (mock.last_prompt or "")


# ─── 8. Graceful Provider Failure Fallback ────────────────────────────────────

class FailingLLMProvider:
    configured = True

    def answer(self, prompt: str) -> str:
        raise LanguageModelUnavailableError("Groq service rate limit exceeded")


def test_assistant_falls_back_to_direct_summary_on_llm_failure(assistant: CurriculumAssistant) -> None:
    failing = FailingLLMProvider()
    result = assistant.answer_question(
        "What is matter?",
        provider=failing,  # type: ignore
    )
    # Must not crash! Must fall back gracefully to direct curriculum summary
    assert result.supported
    assert result.source is not None
    assert "matter" in result.answer.lower() or "mass" in result.answer.lower()


# ─── 9. Anaphoric Follow-Up & Context Resolution ──────────────────────────────

def test_detects_anaphoric_follow_up() -> None:
    assert is_anaphoric_follow_up("What is its state?")
    assert is_anaphoric_follow_up("Why does it do that?")
    assert is_anaphoric_follow_up("Explain this please")
    assert not is_anaphoric_follow_up("What are the characteristics of living organisms?")


def test_resolves_follow_up_with_active_context() -> None:
    context = {"lesson_topic": "States of Matter"}
    resolved = resolve_follow_up_query("What is its shape?", context)
    assert "States of Matter" in resolved


def test_vague_question_without_context_asks_clarification(assistant: CurriculumAssistant) -> None:
    result = assistant.answer_question("what is it")
    assert not result.supported
    assert result.clarification == CLARIFICATION_PROMPT


# ─── 10. Command Separation Integrity ─────────────────────────────────────────

def test_questions_never_produce_commands(assistant: CurriculumAssistant) -> None:
    mock = MockLLMProvider("Matter has mass and volume.")
    result = assistant.answer_question("What is matter?", provider=mock)  # type: ignore
    # Assert assistant answer has no command attribute or execution hook
    assert not hasattr(result, "command") or getattr(result, "command") is None


# ─── 11. REST API /api/curriculum/ask Endpoint ────────────────────────────────

def test_curriculum_ask_endpoint_valid_question(client: TestClient) -> None:
    response = client.post(
        "/api/curriculum/ask",
        json={"question": "What is matter?", "context": {"screen": "/lesson/science-matter-basics"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is matter?"
    assert data["supported"] is True
    assert "matter" in data["answer"].lower() or "mass" in data["answer"].lower()
    assert data["source"] is not None
    assert data["source"]["subject_id"] == "science"
    assert data["source"]["chapter_title"] is not None


def test_curriculum_ask_endpoint_out_of_scope(client: TestClient) -> None:
    response = client.post(
        "/api/curriculum/ask",
        json={"question": "How do I trade cryptocurrencies on the stock market?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["supported"] is False
    assert "outside our Class 6 curriculum" in data["answer"]
    assert data["source"] is None


def test_curriculum_ask_endpoint_subject_filter(client: TestClient) -> None:
    response = client.post(
        "/api/curriculum/ask",
        json={"question": "Tell me about sea turtles", "subject_id": "english"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["supported"] is True
    assert data["source"]["subject_id"] == "english"
