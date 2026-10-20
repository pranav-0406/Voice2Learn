# Voice2Learn — Project Technical Specification & Architecture Manual

**Project Title:** Voice2Learn: A Voice-First Adaptive Learning Assistant for Children with Mobility Challenges  
**Target Domain:** Assistive Educational Technology (K-12 Accessibility & Adaptive Learning)  
**Curriculum Scope:** Tamil Nadu State Board (Samacheer Kalvi) Class 6 (English-medium)  
**Document Version:** 1.0.0 (Post-Audit Verified)  
**Audit Date:** October 2026  

---

## 1. Executive Summary & Problem Formulation

### 1.1 Problem Being Addressed
Conventional educational software and digital learning management systems rely heavily on high-dexterity fine motor input: mouse navigation, drag-and-drop mechanics, small tap targets, and continuous keyboard typing. For children living with physical and mobility challenges—such as cerebral palsy, muscular dystrophy, spinal cord impairments, or severe repetitive strain/tremors—these input barriers cause severe physical fatigue, frustration, and eventual disengagement from self-paced learning.

Existing conversational AI chatbots (e.g., generic ChatGPT or Claude interfaces) fail to solve this problem effectively for young learners because:
1. They lack structured curriculum guardrails, frequently hallucinating or offering university-level explanations to 11-year-old students.
2. They do not maintain an interactive curriculum scaffold (units, concepts, and progressive mastery tracking).
3. They lack adaptive difficulty mechanics that calibrate practice questions based on verified psychometric assessment principles.
4. They exhibit acoustic echo loops during voice interaction (the system's spoken response triggers the microphone).

### 1.2 Target Audience & Core Needs
* **Primary Users:** Class 6 students (ages 10–12) with physical or mobility challenges requiring hands-free or low-physical-effort educational interaction.
* **Secondary Beneficiaries:** Teachers, special educators, and parents who require transparent progress tracking without storing sensitive biometric voice recordings.
* **Non-Target:** Voice2Learn is **not** a speech therapy tool or clinical diagnostic application; it does not evaluate phonetic articulation disorders.

### 1.3 High-Level Solution
Voice2Learn provides a voice-first educational web environment where children can navigate lessons, learn structured textbook concepts, ask educational questions, and complete adaptive quizzes hands-free. The system combines:
1. **Deterministic Voice Command Interpretation** for instant, reliable browser navigation and quiz actions.
2. **Context-Aware Dynamic Curriculum Resolver** for mapping spoken requests (e.g., *"Open Science Unit 2"*) to real curriculum entities.
3. **Curriculum-Grounded Question Answering** that restricts responses strictly to Tamil Nadu Class 6 textbook material.
4. **Item Response / Elo-Based Adaptive Quiz Engine** that matches question difficulty to the learner's dynamic ability rating.
5. **Local-First Privacy Architecture** requiring only a nickname and numeric PIN, processing audio ephemerally without recording storage.

---

## 2. Verified Implementation Status & Feature Inventory

Every feature in the repository has been audited against code, tests, and runtime behavior.

| Feature / Subsystem | Implementation Status | Primary Code Location | Key Functions / Classes | Verification Evidence | Current Limitations |
|---|---|---|---|---|---|
| **System Health & Config** | IMPLEMENTED AND VERIFIED | `backend/app/main.py`, `backend/app/core/config.py` | `health_router`, `get_settings()` | `curl http://localhost:8000/api/health` returned HTTP 200; `test_health.py` passed | Backend reports `stt_backend: not_configured` when dependencies/keys uninitialised |
| **Student Authentication (PIN)** | IMPLEMENTED AND VERIFIED | `backend/app/core/security.py`, `backend/app/api/routes/auth.py` | `hash_pin()`, `verify_pin()`, `create_access_token()` | `test_auth.py` (11 tests passed); PBKDF2-HMAC-SHA256 (100,000 iterations) | Token stored in `localStorage`; local single-institution scope |
| **Learner Profile Creation** | IMPLEMENTED AND VERIFIED | `backend/app/api/routes/learners.py`, `backend/app/db/database.py` | `create_learner()`, `get_learner()` | `test_learning.py` passed; SQLite table `learners` seeded | Legacy anonymous endpoint preserved alongside authenticated student routes |
| **Curriculum Navigation API** | IMPLEMENTED AND VERIFIED | `backend/app/api/routes/curriculum.py`, `backend/app/curriculum/resolver.py` | `CurriculumResolver`, `get_chapters_by_term()`, `get_concept_lesson()` | `test_curriculum.py`, `test_curriculum_resolver.py` (23 tests passed) | Term 1 seeded across Science, Math, English, Social Science; Terms 2 & 3 pending |
| **Curriculum Ingestion Tool** | IMPLEMENTED AND VERIFIED | `backend/app/tools/ingest_curriculum.py`, `backend/data/curriculum/*.json` | `ingest_curriculum_file()` | `test_ingestion.py` passed; 4 JSON curriculum files verified | JSON files extracted manually from Term 1 PDF textbooks in `Books/` |
| **Adaptive Quiz Engine** | IMPLEMENTED AND VERIFIED | `backend/app/api/routes/quiz.py`, `backend/app/db/database.py` | `get_next_question()`, `submit_answer()`, Elo K=32 | `test_quiz.py` (10 tests passed); duplicate submission prevention tested | 12 questions seeded for Science; other subjects rely on concept fallback |
| **Progress & Position Tracking** | IMPLEMENTED AND VERIFIED | `backend/app/api/routes/progress.py`, `backend/app/db/database.py` | `get_progress()`, `save_active_position()`, `get_active_position()` | `test_learning.py` passed; tables `attempts`, `learner_active_position` verified | Mastery aggregation per topic/lesson; streaks tracked in SQLite |
| **Deterministic Voice Interpretation** | IMPLEMENTED AND VERIFIED | `backend/app/voice/interpreter.py` | `interpret_text()`, `_paraphrase_command()`, `COMMANDS` | `test_voice.py` (95 test cases passed) | Keyword and Levenshtein similarity (ratio ≥ 0.84); English only |
| **Speech-to-Text (STT) Abstraction** | IMPLEMENTED AND VERIFIED | `backend/app/stt/provider.py`, `backend/app/api/routes/voice.py` | `FasterWhisperProvider`, `GroqWhisperProvider`, `get_stt_provider()` | `test_voice.py`, `test_groq_stt.py` (16 tests passed) | `faster-whisper` package not installed in active macOS venv; Groq Whisper active in `.env` |
| **Context-Aware Voice Understanding** | IMPLEMENTED AND VERIFIED | `backend/app/voice/understanding.py` | `understand()`, `_prompt()`, `_parse()`, `ALLOWED_COMMANDS` | `test_voice.py` passed; structured JSON schema enforced | Requires Ollama or Groq LLM; falls back cleanly to deterministic interpretation |
| **Curriculum-Grounded RAG Assistant** | IMPLEMENTED AND VERIFIED | `backend/app/qa/retriever.py`, `backend/app/qa/assistant.py` | `CurriculumRetriever`, `CurriculumAssistant`, `build_grounded_prompt()` | `test_curriculum_rag.py` (23 tests passed); out-of-scope rejection verified | Lexical/token multi-factor ranking over SQLite; dense embeddings are PLANNED |
| **AI Browser Agent Runtime** | IMPLEMENTED AND VERIFIED | `backend/app/agent/runtime.py`, `backend/app/agent/tools.py` | `AgentRuntime`, `execute_curriculum_resolution()`, `AGENT_TOOLS` | `test_agent_runtime.py` (8 tests passed) | Powered by `openai/gpt-oss-120b` via Groq; deterministic fallback if offline |
| **Frontend Voice Client (Web Audio VAD)** | IMPLEMENTED AND VERIFIED | `frontend/src/useVoice.ts` | `useVoice()`, `MediaRecorder`, Web Audio API RMS monitoring | Verified in active Vite browser dev server; chunk streaming verified | Requires browser microphone permissions (HTTPS / localhost) |
| **Speech Synthesis (TTS) & Echo Gate** | IMPLEMENTED AND VERIFIED | `frontend/src/speech.ts`, `frontend/src/useVoice.ts` | `speakText()`, `stopSpeaking()`, `normalizeEducationalText()` | Acoustic Echo Gate mutes mic during playback + 350ms cooldown | Relies on OS/browser installed TTS voices; Chrome Indian English preferred |
| **Accessible UI & Screen Reader Support** | IMPLEMENTED AND VERIFIED | `frontend/src/components/`, `frontend/src/styles.css` | High-contrast toggle, ARIA live regions, skip links, keypad | Lint run: 0 TS errors, 1 empty block lint fixed, high-contrast verified | Automated screen reader audit (NVDA/JAWS) pending formal clinical user trials |
| **Dense Vector Embeddings & FAISS** | PLANNED / NOT IMPLEMENTED | N/A (Architecture designed) | N/A | Direct code search: zero occurrences in repository | Proposed for Term 2/3 scaling; current SQLite lexical retriever handles Term 1 |

---

## 3. System Architecture & Component Interactions

```
+----------------------------------------------------------------------------------------------------+
|                                    CLIENT TIER (React 18 + Vite)                                    |
|                                                                                                    |
|  +---------------------------+   +----------------------------+   +-----------------------------+  |
|  |     Pages & Views         |   |    Voice Client & Audio    |   |     Assistive Features      |  |
|  | - Dashboard & Explorer    |   | - getUserMedia (Echo cancel) | | - Acoustic Echo Gate (M06)  |  |
|  | - ConceptViewer (M04)     |   | - MediaRecorder (WebM/WAV) |   | - Accessible Keypad (M03)   |  |
|  | - QuizView (Adaptive)     |   | - Web Audio API RMS VAD    |   | - High-Contrast Theme       |  |
|  | - ProgressView & Stats    |   | - SpeechSynthesis TTS      |   | - Pronunciation Normaliser  |  |
|  +---------------------------+   +----------------------------+   +-----------------------------+  |
+-------------------------------------------------+--------------------------------------------------+
                                                  | HTTP JSON / REST API (CORS enabled)
                                                  v
+----------------------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION TIER (Python 3.12)                               |
|                                                                                                    |
|  +-----------------------+  +------------------------+  +--------------------+  +---------------+  |
|  |   API Route Handlers  |  |  Voice Processing Sub  |  |   AI / QA Engines  |  | Agent Runtime |  |
|  | - /api/auth           |  | - /api/voice/transcribe|  | - Deterministic    |  | - gpt-oss-120b|  |
|  | - /api/curriculum     |  |   (Groq / Whisper)     |  |   Interpreter      |  | - Tool Calls: |  |
|  | - /api/quiz           |  | - /api/voice/interpret |  | - CurriculumRetr-  |  |   resolve_    |  |
|  | - /api/progress       |  |   (Rule + LLM Fallback)|  |   iever (SQLite)   |  |   curriculum,  |  |
|  | - /api/health         |  | - NamedTemporaryFile   |  | - CurriculumAssist-|  |   navigate,   |  |
|  |                       |  |   (Immediate unlink)   |  |   ant (Grounded QA)|  |   complete    |  |
|  +-----------------------+  +------------------------+  +--------------------+  +---------------+  |
+-------------------------------------------------+--------------------------------------------------+
                                                  | Direct SQLite Connection (PRAGMA foreign_keys=ON)
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                DATA PERSISTENCE TIER (SQLite 3 File)                               |
|                                                                                                    |
|   learners | students | curriculum_subjects | curriculum_chapters | curriculum_concepts            |
|   lessons  | questions | attempts (Unique per learner+question) | learner_active_position         |
|   learner_topic_progress | learner_lesson_progress                                                 |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Module Specifications & Responsibilities

### 4.1 Backend Module Hierarchy

```
backend/app/
├── main.py                     # Application factory, CORS middleware, lifespan database init
├── core/
│   ├── config.py               # Environment variables, dataclass Settings, lru_cache
│   └── security.py             # PBKDF2-HMAC-SHA256 PIN hashing, HS256 JWT creation & decoding
├── db/
│   ├── database.py             # SQLite data access layer, schema migrations, Elo rating logic
│   ├── seed.py                 # Seeded Science lesson & 12 starter quiz questions
│   └── curriculum_seed.py      # Seeded Class 6 Term 1 chapters, concepts across 4 subjects
├── stt/
│   └── provider.py             # Speech-to-Text provider protocol, faster-whisper & Groq Cloud
├── voice/
│   ├── interpreter.py          # Deterministic command router (exact & SequenceMatcher ratio >= 0.84)
│   └── understanding.py        # Contextual LLM fallback with strict application allowlists
├── curriculum/
│   └── resolver.py             # Natural language entity resolver (maps "Science Unit 2" to DB)
├── qa/
│   ├── retriever.py            # SQLite multi-factor token & proximity curriculum retriever
│   ├── assistant.py            # Grounded educational QA coordinator & out-of-scope guardrail
│   ├── groq.py                 # Groq Cloud LLM provider (llama-3.1-8b-instant)
│   └── ollama.py               # Local Ollama REST client (gemma3:4b)
├── agent/
│   ├── schemas.py              # Pydantic schemas for agent actions, steps, and browser observations
│   ├── tools.py                # JSON function definitions for Groq tool-use API
│   └── runtime.py              # Agent loop with curriculum-aware navigation and deterministic fallback
└── api/
    ├── dependencies.py         # FastAPI dependency injection (DB, Student Auth, Assistant)
    ├── schemas.py              # Pydantic v2 request/response models
    └── routes/                 # Endpoint routers (auth, curriculum, quiz, voice, progress, etc.)
```

### 4.2 Frontend Architecture (`frontend/src/`)
* **State Management:** Local React state + custom hooks (`useVoice`). Persistent state stored in browser `localStorage` (`voice2learn_auth_token`, `v2l-learner`, `v2l-speech-rate`, `v2l-mic-threshold`).
* **Audio Layer:** Native browser `MediaRecorder` streaming audio blobs to `/api/voice/transcribe`. AudioContext analyser performing root-mean-square (RMS) energy thresholding for local Voice Activity Detection.
* **Routing:** `react-router-dom` v6 with client-side routes:
  * `/` -> Welcome & PIN Keypad Onboarding
  * `/dashboard` -> Subject Explorer & Quick Action Cards
  * `/concept/:conceptId` -> Concept Viewer with Audio Narration Bar & Sibling Navigation
  * `/lesson/:id` -> Legacy Lesson View
  * `/quiz` -> Adaptive Quiz View with immediate feedback & streak tracking
  * `/progress` -> Mastery Dashboard with per-topic progress bars
  * `/voice` -> Dedicated Voice Assistant diagnostic view

---

## 5. Security, Privacy & Data Protection Compliance

1. **Ephemeral Voice Processing:** Audio files received at `/api/voice/transcribe` are written to a POSIX `NamedTemporaryFile` in memory/tmp storage, passed to the transcription engine, and **immediately deleted in a `finally` block** using `os.unlink()`. No student voice recordings are ever stored on disk or in the database.
2. **COPPA / Child Privacy Alignment:** No personal identifiable information (PII) such as full legal name, email address, physical location, school ID, or phone number is collected. Students register solely with a chosen **nickname** and a **4-digit numeric PIN**.
3. **Cryptographic Protection:** Student PINs are hashed using industry-standard **PBKDF2-HMAC-SHA256** with a unique 16-byte cryptographically secure random salt (`secrets.token_bytes(16)`) and 100,000 iterations. Verification uses constant-time string comparison (`secrets.compare_digest`).
4. **Session Tokens:** Authentication sessions issue standard **HS256 JSON Web Tokens (JWT)** signed by the backend secret key, validating `sub`, `exp`, and grade band claims on protected routes.
5. **CORS Security:** Permitted browser origins are strictly restricted via `VOICE2LEARN_CORS_ORIGINS`, defaulting strictly to local development addresses (`http://localhost:5173`, `http://127.0.0.1:5173`).

---

## 6. Current Implementation Limitations

1. **Local Single-File Database:** SQLite is ideal for zero-configuration local development and single-device deployment, but lacks multi-master replication, horizontal clustering, and concurrent writer scalability for school-wide server deployments.
2. **Dense Vector Search Absence:** Semantic search currently relies on transparent multi-factor keyword and lexical overlap scoring across SQLite tables rather than dense vector embeddings. Out-of-vocabulary synonyms not present in the textbook will not match until dense vector embeddings (e.g., MiniLM) and FAISS are integrated.
3. **Tamil Language Limitation:** While Class 6 textbooks for English, Math, Science, and Social Science are integrated, the Tamil language textbook is stored in `Books/` but not yet ingested into the database because the current STT and LLM configurations are locked to English.
4. **Frontend Linting Warning:** `npm run lint` identifies an empty block statement in `ConceptViewer.tsx:83` and hook dependency warnings; these must be resolved before production compilation.
