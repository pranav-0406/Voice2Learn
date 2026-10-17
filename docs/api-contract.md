# Voice2Learn API Contract (v0.1)

Base URL: http://localhost:8000/api
Format: JSON, UTF-8. Prototype is local-only.

## Privacy
- Use a generated learner UUID and nickname.
- Store grade_band as "6-7" or "8-9".
- Do not store voice recordings.
- Process uploaded audio in memory and delete it after transcription.

## Intent types
- command
- quiz_answer
- question
- unknown

## Endpoints

| Method | Path | Owner | Purpose |
|---|---|---|---|
| GET | /health | Pranav | Backend readiness |
| POST | /learners | Santhosh | Create learner |
| POST | /voice/transcribe | Pranav | Audio to text |
| POST | /voice/interpret | Pranav | Interpret spoken text |
| POST | /qa/ask | Shared | Grounded educational answer |
| GET | /subjects | Santhosh | List subjects |
| GET | /lessons/{lesson_id} | Santhosh | Get lesson |
| GET | /quiz/next | Santhosh | Get adaptive question |
| POST | /quiz/answer | Santhosh | Evaluate answer |
| GET | /progress/{learner_id} | Santhosh | Get progress |

## Adaptive learning rules
- Initial ability: 1000.
- Elo K-factor: 32.
- Two correct answers in a row raise the target difficulty band.
- Two incorrect answers in a row lower the target difficulty band.
- Correct answer: 10 points, plus 5 points for a first-attempt answer.

## Mocking
Frontend development must support mock responses for every endpoint.
Backend endpoints must be testable independently.

## Implemented prototype payloads

The endpoint table intentionally left payload details open. For the first local
prototype, the following small JSON shapes are stable:

- `POST /learners` accepts `{"nickname": "Asha", "grade_band": "6-7"}`.
  `grade_band` is optional and defaults to `"6-7"`; it may also be `"8-9"`.
  It returns `{"id": "<uuid>", "nickname": "Asha", "grade_band": "6-7"}`.
- `GET /subjects` returns `{"subjects": [{"id": "science", "name": "Science", "language": "English"}]}`.
- `GET /lessons/science-matter-basics` returns the lesson `id`, `subject`,
  `topic`, `title`, and a structured `content` object containing a summary,
  key points, vocabulary, an activity, and quiz-ready facts. An unknown lesson
  returns HTTP 404 with `{"detail": "Lesson not found"}`.
- `GET /quiz/next?learner_id=<uuid>&subject=science` returns
  `{"question": {...}, "message": "Question ready"}`. The question includes
  `id`, `lesson_id`, `topic`, `difficulty`, `prompt`, and `choices`; it never
  includes ratings or accepted answers. A valid learner with no unanswered
  questions receives HTTP 200 with `"question": null`.
- `POST /quiz/answer` accepts
  `{"learner_id": "<uuid>", "question_id": "...", "answer": "..."}` and
  returns correctness, awarded points, updated ability, target difficulty,
  duplicate-submission status, and feedback. The first recorded correct answer
  for a question earns 15 points (10 points plus the 5-point first-attempt bonus).
  A repeated submission returns the original correctness but awards zero points.
- `GET /progress/<learner_id>` returns persisted ability, points, correct and
  incorrect streaks, target difficulty, plus per-topic and per-lesson attempt,
  correct-answer, and mastery-percentage aggregates.
- `POST /voice/transcribe` accepts one multipart field named `audio`, using
  `audio/wav`, `audio/x-wav`, or `audio/webm`, up to the configured size limit.
  It returns `{"text": "...", "metadata": {"language": "en", "duration_seconds": 1.2,
  "model": "small", "device": "cpu"}}`. Audio is temporary and is never
  retained. When local STT is unavailable, it returns HTTP 503; unreadable or
  non-transcribable audio returns HTTP 422 without exposing internal details.
- `POST /voice/interpret` accepts `{"text": "next question", "context":
  {"active_quiz": false}}` and returns `intent`, `confidence`, and optional
  `command` or `answer`. It is a deterministic rule-based interpreter: only a
  clear command is a `command`, and a non-question utterance becomes a
  `quiz_answer` only when `active_quiz` is true.
