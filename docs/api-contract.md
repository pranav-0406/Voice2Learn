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
