# Voice2Learn — Verified API Reference Manual

**Base URL:** `http://localhost:8000/api`  
**Protocol:** HTTP/1.1 REST  
**Data Format:** JSON (UTF-8) / Multipart Form Data (Audio)  
**Authentication Scheme:** Optional Anonymous / Bearer Token (`Authorization: Bearer <JWT>`)  
**Verified Against:** OpenAPI Specification (`http://localhost:8000/openapi.json`) and route handlers in `backend/app/api/routes/`

---

## 1. Architectural Foundation & HTTP Concepts

### 1.1 HTTP Verbs
* **`GET`:** Safe, idempotent retrieval requests that do not modify database state. Used for reading health status, curriculum trees, lessons, questions, and learner progress.
* **`POST`:** Non-idempotent state-mutating requests with a JSON or multipart payload in the request body. Used for learner registration, answer evaluation, audio transcription, and voice interpretation.

### 1.2 Pydantic Validation & Route Handlers
FastAPI routes use Pydantic v2 schemas (`backend/app/api/schemas.py`). If a client submits malformed JSON, missing fields, or incorrect types (e.g. an unrecognised grade band), FastAPI intercepts the request before route handler execution and automatically returns **HTTP 422 Unprocessable Entity** with descriptive field-level error messages.

### 1.3 Client Communication
The React frontend uses a centralised request utility in `frontend/src/api.ts:request<T>()`. It automatically retrieves the active JWT token from browser `localStorage` (`voice2learn_auth_token`), injects the `Authorization: Bearer <token>` header, serialises JSON bodies, and parses JSON responses.

---

## 2. Complete Verified Endpoint Inventory

### 2.1 System & Health

#### `GET /api/health`
* **Purpose:** System readiness, provider status check, and runtime health.
* **Request:** None.
* **Response (200 OK):**
```json
{
  "status": "ok",
  "message": "Voice2Learn backend is running",
  "stt_backend": "not_configured",
  "llm_backend": "not_configured",
  "retrieval_ready": false
}
```
* **Database Operations:** None.
* **Calling Frontend:** Used during service verification and diagnostics.

---

### 2.2 Student Authentication (M03)

#### `POST /api/auth/register`
* **Purpose:** Register a new student profile with nickname and numeric 4-digit PIN.
* **Calling Frontend:** `frontend/src/components/auth/AuthModal.tsx` (`registerStudent`)
* **Request Body:**
```json
{
  "nickname": "Asha",
  "pin": "1234",
  "board": "TN_STATE_BOARD",
  "class_level": 6,
  "grade_band": "6-7"
}
```
* **Validation Rules:** `nickname` (min 2, max 30 chars), `pin` (exactly 4 digits `^\d{4}$`), `grade_band` must be `"6-7"` or `"8-9"`.
* **Database Operations:** `INSERT INTO students`, `INSERT OR IGNORE INTO learners`.
* **Error Responses:** `409 Conflict` (nickname taken), `422 Unprocessable Entity` (invalid PIN format).
* **Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "student": {
    "id": "c1f7a28b-9e4a-4d2b-a01b-8e390c5031b2",
    "nickname": "Asha",
    "board": "TN_STATE_BOARD",
    "class_level": 6,
    "grade_band": "6-7",
    "created_at": "2026-10-20T17:35:00.000Z"
  }
}
```

#### `POST /api/auth/login`
* **Purpose:** Authenticate student using nickname and 4-digit PIN.
* **Calling Frontend:** `frontend/src/components/auth/AuthModal.tsx` (`loginStudent`)
* **Request Body:**
```json
{
  "nickname": "Asha",
  "pin": "1234"
}
```
* **Database Operations:** `SELECT FROM students WHERE LOWER(nickname) = ?`, constant-time PIN verification.
* **Error Responses:** `401 Unauthorized` (incorrect nickname or PIN).
* **Response (200 OK):** Identical to register `AuthResponse`.

#### `GET /api/auth/me`
* **Purpose:** Retrieve the currently authenticated student profile using JWT Bearer token.
* **Calling Frontend:** `frontend/src/api.ts` (`fetchCurrentStudent`)
* **Headers:** `Authorization: Bearer <token>`
* **Error Responses:** `401 Unauthorized` (missing/expired token).
* **Response (200 OK):** `StudentProfile` object.

---

### 2.3 Legacy Learner Management

#### `POST /api/learners`
* **Purpose:** Create an anonymous learner profile without PIN authentication.
* **Calling Frontend:** `frontend/src/pages/Welcome.tsx` (`createLearner`)
* **Request Body:**
```json
{
  "nickname": "Kavitha",
  "grade_band": "6-7"
}
```
* **Response (201 Created):**
```json
{
  "id": "e2a3b4c5-6789-41bc-9abc-1234567890ab",
  "nickname": "Kavitha",
  "grade_band": "6-7"
}
```

---

### 2.4 Curriculum Navigation (M01 / M02 / M04)

#### `GET /api/curriculum/subjects`
* **Purpose:** List all active Class 6 curriculum subjects with chapter counts and metadata.
* **Calling Frontend:** `frontend/src/components/curriculum/SubjectExplorer.tsx`
* **Response (200 OK):**
```json
{
  "subjects": [
    {
      "id": "science",
      "name": "Science",
      "code": "SCI-06",
      "icon": "Atom",
      "accent_color": "#22c55e",
      "display_order": 1,
      "chapter_count": 7,
      "terms_available": [1]
    },
    {
      "id": "mathematics",
      "name": "Mathematics",
      "code": "MATH-06",
      "icon": "Calculator",
      "accent_color": "#3b82f6",
      "display_order": 2,
      "chapter_count": 6,
      "terms_available": [1]
    }
  ]
}
```

#### `GET /api/curriculum/subjects/{subject_id}/terms/{term}`
* **Purpose:** List all chapters/units for a subject in a specific academic term.
* **Calling Frontend:** `frontend/src/components/curriculum/SubjectExplorer.tsx`
* **Response (200 OK):** Array of chapters with `chapter_number`, `title`, `description`, `textbook_pages`, and `concept_count`.

#### `GET /api/curriculum/chapters/{chapter_id}`
* **Purpose:** Retrieve full chapter details and nested concepts.
* **Calling Frontend:** `frontend/src/pages/ConceptViewer.tsx`
* **Response (200 OK):** Chapter object including array of concept summaries.

#### `GET /api/curriculum/concepts/{concept_id}/lesson`
* **Purpose:** Retrieve concept learning data with chapter metadata, key points, and previous/next sibling concept links.
* **Calling Frontend:** `frontend/src/pages/ConceptViewer.tsx` (`fetchConceptLesson`)
* **Response (200 OK):**
```json
{
  "id": "sci-ch02-c01",
  "chapter_id": "sci-ch02",
  "title": "Rest and Motion",
  "summary": "An object is in motion if its position changes relative to an observer over time.",
  "key_points": [
    "Motion is relative to the observer.",
    "Rest means no change of position over time."
  ],
  "display_order": 1,
  "index": 0,
  "total": 3,
  "chapter_title": "Force and Motion",
  "chapter_number": 2,
  "term": 1,
  "subject_id": "science",
  "subject_name": "Science",
  "prev_concept": null,
  "next_concept": {
    "id": "sci-ch02-c02",
    "title": "Types of Motion",
    "display_order": 2
  }
}
```

#### `POST /api/curriculum/resolve`
* **Purpose:** Resolve a natural language entity (e.g. *"Science Unit 2"*) into a verified curriculum entity and target URL.
* **Calling Frontend:** Voice navigation and Agent runtime.
* **Request Body:**
```json
{
  "query": "open science unit 2",
  "subject": null,
  "unit_number": null,
  "term": 1
}
```
* **Response (200 OK):**
```json
{
  "found": true,
  "subject_id": "science",
  "subject_name": "Science",
  "chapter_id": "sci-ch02",
  "chapter_title": "Force and Motion",
  "chapter_number": 2,
  "first_concept_id": "sci-ch02-c01",
  "target_url": "/concept/sci-ch02-c01",
  "error": null,
  "available_units": 7
}
```

#### `POST /api/curriculum/ask`
* **Purpose:** Grounded educational question answering over Class 6 curriculum.
* **Calling Frontend:** `frontend/src/api.ts` (`askCurriculumQuestion`)
* **Request Body:**
```json
{
  "question": "What is condensation?",
  "subject_id": "science",
  "concept_id": "sci-ch03-c02"
}
```
* **Response (200 OK):**
```json
{
  "question": "What is condensation?",
  "answer": "Condensation is the process where a gas turns into a liquid when cooled.",
  "supported": true,
  "source": {
    "subject_id": "science",
    "subject_name": "Science",
    "chapter_id": "sci-ch03",
    "chapter_title": "Matter Around Us",
    "concept_id": "sci-ch03-c02",
    "concept_title": "Changes of State"
  },
  "clarification": null
}
```

---

### 2.5 Legacy Content Endpoints

#### `GET /api/subjects`
* **Purpose:** List distinct subject IDs and display names from legacy lessons table.
* **Response (200 OK):** `{"subjects": [{"id": "science", "name": "Science", "language": "English"}]}`

#### `GET /api/lessons/{lesson_id}`
* **Purpose:** Retrieve legacy structured lesson content (summary, key points, vocabulary, activity).
* **Response (200 OK):** Lesson object or `404 Not Found`.

---

### 2.6 Adaptive Quiz Engine

#### `GET /api/quiz/next`
* **Purpose:** Retrieve the next unanswered question calibrated to the learner's ability.
* **Calling Frontend:** `frontend/src/pages/QuizView.tsx` (`getNextQuestion`)
* **Query Parameters:** `learner_id` (UUID, required), `subject` (string, default "science"), `concept_id` (optional), `chapter_id` (optional).
* **Response (200 OK):**
```json
{
  "question": {
    "id": "sci-q01",
    "lesson_id": "science-matter-basics",
    "topic": "States of Matter",
    "difficulty": "medium",
    "prompt": "Which state of matter has a definite shape and volume?",
    "choices": ["Liquid", "Gas", "Solid", "Plasma"],
    "hint": "Think of ice or a stone."
  },
  "message": "Question ready"
}
```
*Note: Correct answers and ratings are never exposed in the question response.*

#### `POST /api/quiz/answer`
* **Purpose:** Atomically evaluate an answer submission, update Elo rating, streaks, and progress.
* **Calling Frontend:** `frontend/src/pages/QuizView.tsx` (`submitAnswer`)
* **Request Body:**
```json
{
  "learner_id": "c1f7a28b-9e4a-4d2b-a01b-8e390c5031b2",
  "question_id": "sci-q01",
  "answer": "Solid"
}
```
* **Response (200 OK):**
```json
{
  "correct": true,
  "points_awarded": 15,
  "ability": 1016.0,
  "target_difficulty": "medium",
  "duplicate_submission": false,
  "explanation": "Solids maintain a fixed shape and volume because their particles are tightly packed.",
  "correct_answer": "Solid"
}
```

---

### 2.7 Learner Progress & Position

#### `GET /api/progress/{learner_id}`
* **Purpose:** Retrieve student points, ability rating, streaks, and topic/lesson mastery aggregations.
* **Calling Frontend:** `frontend/src/pages/ProgressView.tsx` (`getProgress`)
* **Response (200 OK):**
```json
{
  "learner_id": "c1f7a28b-9e4a-4d2b-a01b-8e390c5031b2",
  "ability": 1016.0,
  "points": 45,
  "correct_streak": 3,
  "incorrect_streak": 0,
  "target_difficulty": "hard",
  "topics": [
    {
      "topic": "States of Matter",
      "attempts": 3,
      "correct_answers": 3,
      "mastery_percent": 100.0
    }
  ],
  "lessons": [
    {
      "lesson_id": "science-matter-basics",
      "attempts": 3,
      "correct_answers": 3,
      "mastery_percent": 100.0
    }
  ]
}
```

#### `POST /api/progress/position`
* **Purpose:** Save the learner's active curriculum position for "resume where I left off".
* **Request Body:** `{"learner_id": "...", "subject_id": "science", "chapter_id": "sci-ch02", "concept_id": "sci-ch02-c01"}`
* **Response (200 OK):** `LearnerPositionResponse`

---

### 2.8 Voice Processing & Agent

#### `POST /api/voice/transcribe`
* **Purpose:** Transcribe short audio recordings without server-side retention.
* **Calling Frontend:** `frontend/src/useVoice.ts` (`transcribeAudio`)
* **Request:** Multipart form field `audio` (MIME `audio/wav`, `audio/x-wav`, or `audio/webm`; max 10MB).
* **Response (200 OK):**
```json
{
  "text": "open science unit two",
  "metadata": {
    "language": "en",
    "duration_seconds": 2.1,
    "model": "whisper-large-v3-turbo",
    "device": "groq"
  }
}
```

#### `POST /api/voice/interpret`
* **Purpose:** Classify transcribed text into an application command or educational question.
* **Calling Frontend:** `frontend/src/useVoice.ts` (`interpretVoice`)
* **Request Body:**
```json
{
  "text": "take me to science unit two",
  "context": {
    "active_quiz": false,
    "screen": "/dashboard",
    "recent_turns": ["learner: hello"]
  }
}
```
* **Response (200 OK):**
```json
{
  "intent": "command",
  "confidence": 0.94,
  "command": "OPEN_LESSON",
  "answer": null,
  "category": "application",
  "response": null,
  "clarification": null,
  "source": null
}
```

#### `POST /api/agent/run`
* **Purpose:** Execute multi-step AI browser agent reasoning loop (`openai/gpt-oss-120b`).
* **Request Body:** `AgentRunRequest` (prompt, context, max_steps).
* **Response (200 OK):** `AgentRunResponse` (run_id, status, steps, final_message, target_url).
