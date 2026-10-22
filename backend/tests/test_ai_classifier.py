import json
import time

import pytest
from fastapi.testclient import TestClient

from app.api.routes import voice as voice_route
from app.core.config import get_settings
from app.main import app
from app.voice.interpreter import Interpretation
from app.voice.understanding import (
    classify_intent,
    resolve_with_classifier,
)


class FakeProvider:
    configured = True

    def __init__(self, output=None, error=None, delay=0):
        self.output = output
        self.error = error
        self.delay = delay
        self.calls = []

    def answer(self, prompt: str) -> str:
        self.calls.append(prompt)
        if self.delay:
            time.sleep(self.delay)
        if self.error:
            raise self.error
        return self.output


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(tmp_path / "classifier.sqlite3"))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("VOICE2LEARN_OLLAMA_MODEL", raising=False)
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def classifier(label, confidence=0.95, command=None):
    return json.dumps({"label": label, "confidence": confidence, "command": command})


def post(client, text, active_quiz=False, screen="/quiz"):
    return client.post(
        "/api/voice/interpret",
        json={"text": text, "context": {"active_quiz": active_quiz, "screen": screen}},
    )


def test_flag_disabled_preserves_quiz_command_and_question_paths(client, monkeypatch):
    provider = FakeProvider(classifier("unrelated_speech"))
    monkeypatch.setattr(voice_route, "get_default_llm_provider", lambda settings: provider)
    monkeypatch.setattr(
        voice_route,
        "resolve_with_classifier",
        lambda *args, **kwargs: pytest.fail("classifier must be disabled"),
    )
    monkeypatch.delenv("VOICE2LEARN_AI_CLASSIFIER", raising=False)
    get_settings.cache_clear()

    answer = post(client, "seven", active_quiz=True)
    command = post(client, "next question", active_quiz=True)
    question = post(client, "What is matter?", active_quiz=True)

    assert answer.json()["intent"] == "quiz_answer"
    assert answer.json()["answer"] == "seven"
    assert command.json()["command"] == "NEXT_QUESTION"
    assert question.json()["intent"] == "question"


@pytest.mark.parametrize("text", ["b", "seven", "photosynthesis", "water changes into vapor"])
def test_enabled_classifier_accepts_short_and_free_text_quiz_answers(client, monkeypatch, text):
    provider = FakeProvider(classifier("quiz_answer"))
    monkeypatch.setenv("VOICE2LEARN_AI_CLASSIFIER", "yes")
    get_settings.cache_clear()
    monkeypatch.setattr(voice_route, "get_default_llm_provider", lambda settings: provider)

    response = post(client, text, active_quiz=True)

    assert response.json()["intent"] == "quiz_answer"
    assert response.json()["answer"] == text
    assert len(provider.calls) == 1


def test_enabled_classifier_accepts_matching_and_paraphrased_commands(client, monkeypatch):
    provider = FakeProvider(classifier("command", command="NEXT_QUESTION"))
    monkeypatch.setenv("VOICE2LEARN_AI_CLASSIFIER", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(voice_route, "get_default_llm_provider", lambda settings: provider)

    response = post(client, "move on", active_quiz=True)

    assert response.json()["command"] == "NEXT_QUESTION"
    assert response.json()["category"] == "application"


@pytest.mark.parametrize("text", ["maybe", "not sure", "I do not know", "Not sure."])
def test_excluded_quiz_phrases_are_not_accepted_when_classifier_enabled(client, monkeypatch, text):
    provider = FakeProvider(classifier("quiz_answer"))
    monkeypatch.setenv("VOICE2LEARN_AI_CLASSIFIER", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(voice_route, "get_default_llm_provider", lambda settings: provider)

    response = post(client, text, active_quiz=True)
    data = response.json()

    assert data["intent"] != "quiz_answer"
    assert data["answer"] is None


@pytest.mark.parametrize("text", ["b", "7"])
def test_single_character_answers_are_accepted_when_classifier_enabled(client, monkeypatch, text):
    provider = FakeProvider(classifier("quiz_answer"))
    monkeypatch.setenv("VOICE2LEARN_AI_CLASSIFIER", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(voice_route, "get_default_llm_provider", lambda settings: provider)

    response = post(client, text, active_quiz=True)

    assert response.json()["intent"] == "quiz_answer"
    assert response.json()["answer"] == text


@pytest.mark.parametrize("text", ["b", "7"])
def test_single_character_answers_keep_flag_off_behavior(client, monkeypatch, text):
    monkeypatch.delenv("VOICE2LEARN_AI_CLASSIFIER", raising=False)
    get_settings.cache_clear()

    response = post(client, text, active_quiz=True)
    data = response.json()

    assert data["intent"] == "unknown"
    assert data["answer"] is None


def test_different_confident_command_requires_clarification(client, monkeypatch):
    provider = FakeProvider(classifier("command", command="HINT"))
    monkeypatch.setenv("VOICE2LEARN_AI_CLASSIFIER", "1")
    get_settings.cache_clear()
    monkeypatch.setattr(voice_route, "get_default_llm_provider", lambda settings: provider)

    response = post(client, "next question", active_quiz=True)
    data = response.json()

    assert data["intent"] == "unknown"
    assert data["command"] is None
    assert data["category"] == "clarification"
    assert data["clarification"]


def test_invalid_ai_command_is_rejected_for_quiz_answer():
    provider = FakeProvider('{"label":"command","confidence":0.99,"command":"RUN_CODE"}')
    result = resolve_with_classifier(
        "b",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="quiz_answer", confidence=0.8, answer="b"),
        provider,
        5,
    )
    assert result.interpretation.intent == "unknown"
    assert result.interpretation.answer is None
    assert result.category == "clarification"


def test_command_invalid_on_current_screen_is_not_executed():
    provider = FakeProvider(classifier("command", command="SELECT_OPTION_A"))
    result = resolve_with_classifier(
        "select option a",
        {"active_quiz": False, "screen": "/lesson/science"},
        Interpretation(intent="command", confidence=1.0, command="SELECT_OPTION_A"),
        provider,
        5,
    )
    assert result.interpretation.intent == "unknown"
    assert result.interpretation.command is None
    assert result.category == "clarification"


def test_tv_like_speech_becomes_noise():
    provider = FakeProvider(classifier("unrelated_speech"))
    result = resolve_with_classifier(
        "Welcome back to tonight's show",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="quiz_answer", confidence=0.8, answer="Welcome back to tonight's show"),
        provider,
        5,
    )
    assert result.interpretation.intent == "noise"
    assert result.category == "noise"
    assert result.interpretation.answer is None


def test_classifier_quiz_answer_without_active_quiz_is_rejected():
    provider = FakeProvider(classifier("quiz_answer"))
    result = resolve_with_classifier(
        "seven",
        {"active_quiz": False, "screen": "/dashboard"},
        Interpretation(intent="quiz_answer", confidence=0.8, answer="seven"),
        provider,
        5,
    )
    assert result.interpretation.intent == "unknown"
    assert result.category == "clarification"


def test_educational_question_is_handed_to_existing_understanding(monkeypatch):
    provider = FakeProvider(classifier("educational_question"))
    called = []

    def fake_understand(text, context, fallback, provider, assistant=None):
        called.append((text, context, fallback, provider, assistant))
        from app.voice.understanding import Understanding
        return Understanding(fallback, "learning", response="Grounded answer")

    monkeypatch.setattr("app.voice.understanding.understand", fake_understand)
    result = resolve_with_classifier(
        "what is photosynthesis?",
        {"active_quiz": True, "screen": "/quiz", "question": "What is it?"},
        Interpretation(intent="quiz_answer", confidence=0.8, answer="what is photosynthesis?"),
        provider,
        5,
    )
    assert result.category == "learning"
    assert result.response == "Grounded answer"
    assert called and called[0][2].intent == "question"


def test_empty_transcript_does_not_call_classifier():
    provider = FakeProvider(classifier("quiz_answer"))
    assert classify_intent("   ", {"active_quiz": True}, provider, 5) is None
    assert provider.calls == []


def test_whitespace_transcript_does_not_call_classifier(client, monkeypatch):
    provider = FakeProvider(classifier("quiz_answer"))
    monkeypatch.setenv("VOICE2LEARN_AI_CLASSIFIER", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(voice_route, "get_default_llm_provider", lambda settings: provider)

    response = post(client, "   ", active_quiz=True)

    assert response.status_code == 200
    assert provider.calls == []


@pytest.mark.parametrize(
    "output",
    [
        "not json",
        "[]",
        '{"label":"bad","confidence":0.9,"command":null}',
        '{"label":"quiz_answer","confidence":2,"command":null}',
        '{"label":"quiz_answer","confidence":"high","command":null}',
    ],
)
def test_malformed_classifier_output_rejects_quiz_answer(output):
    provider = FakeProvider(output)
    result = resolve_with_classifier(
        "b",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="quiz_answer", confidence=0.8, answer="b"),
        provider,
        5,
    )
    assert result.interpretation.intent == "unknown"
    assert result.interpretation.answer is None
    assert result.category == "clarification"


def test_low_confidence_rejects_quiz_answer():
    provider = FakeProvider(classifier("quiz_answer", confidence=0.69))
    result = resolve_with_classifier(
        "b",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="quiz_answer", confidence=0.8, answer="b"),
        provider,
        5,
    )
    assert result.category == "clarification"
    assert result.interpretation.answer is None


@pytest.mark.parametrize("provider", [
    FakeProvider(classifier("quiz_answer"), error=RuntimeError("boom")),
    FakeProvider(classifier("quiz_answer"), delay=0.1),
])
def test_classifier_failures_reject_answers_or_keep_commands(provider):
    quiz_result = resolve_with_classifier(
        "b",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="quiz_answer", confidence=0.8, answer="b"),
        provider,
        0 if provider.delay else 5,
    )
    assert quiz_result.category == "clarification"
    assert quiz_result.interpretation.answer is None
    assert len(provider.calls) == 1

    command_provider = FakeProvider(None, error=RuntimeError("boom"))
    command_result = resolve_with_classifier(
        "next question",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="command", confidence=1.0, command="NEXT_QUESTION"),
        command_provider,
        5,
    )
    assert command_result.interpretation.command == "NEXT_QUESTION"
    assert len(command_provider.calls) == 1


def test_malformed_json_calls_classifier_once_and_rejects_answer():
    provider = FakeProvider("not json")
    result = resolve_with_classifier(
        "b",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="quiz_answer", confidence=0.8, answer="b"),
        provider,
        5,
    )
    assert len(provider.calls) == 1
    assert result.interpretation.answer is None
    assert result.interpretation.command is None


def test_timeout_calls_classifier_once_and_keeps_deterministic_command():
    provider = FakeProvider(classifier("command", command="NEXT_QUESTION"), delay=0.1)
    result = resolve_with_classifier(
        "next question",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="command", confidence=1.0, command="NEXT_QUESTION"),
        provider,
        0,
    )
    assert len(provider.calls) == 1
    assert result.interpretation.command == "NEXT_QUESTION"


def test_no_provider_rejects_quiz_answers_and_keeps_commands():
    quiz_result = resolve_with_classifier(
        "b",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="quiz_answer", confidence=0.8, answer="b"),
        None,
        5,
    )
    command_result = resolve_with_classifier(
        "next question",
        {"active_quiz": True, "screen": "/quiz"},
        Interpretation(intent="command", confidence=1.0, command="NEXT_QUESTION"),
        None,
        5,
    )
    assert quiz_result.category == "clarification"
    assert command_result.interpretation.command == "NEXT_QUESTION"
