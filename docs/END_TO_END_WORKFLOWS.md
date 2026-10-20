# Voice2Learn — End-to-End Technical Workflows

This document traces the complete execution paths of Voice2Learn's core workflows through the codebase. It details exact files, functions, API routes, data structures, and failure recovery mechanisms, with Mermaid sequence diagrams.

---

## Workflow A: Voice Command Execution

This workflow traces a hands-free navigation command (e.g., *"Open Science Unit 2"*, *"Show my progress"*, or *"Next concept"*).

```mermaid
sequenceDiagram
    autonumber
    actor Learner as Child
    participant Browser as React Frontend (useVoice.ts)
    participant AudioAPI as Web Audio API / MediaRecorder
    participant STTRoute as Backend (/api/voice/transcribe)
    participant STT as Groq / Whisper Provider
    participant InterpRoute as Backend (/api/voice/interpret)
    participant Interpreter as Rule Interpreter / LLM
    participant Router as Frontend Navigation (App.tsx)

    Learner->>Browser: Speaks voice command
    Browser->>AudioAPI: getUserMedia & MediaRecorder start
    AudioAPI->>AudioAPI: Web Audio Analyser computes RMS energy
    Note over AudioAPI: VAD detects speech pause (>=650ms)<br/>or duration limit (4500ms)
    AudioAPI->>Browser: Emits audio Blob (WebM/WAV)
    Browser->>STTRoute: POST /api/voice/transcribe (multipart audio)
    STTRoute->>STTRoute: Writes NamedTemporaryFile (ephemeral)
    STTRoute->>STT: transcribe(audio_path)
    STT-->>STTRoute: TranscriptionResult(text="open science unit two")
    STTRoute->>STTRoute: os.unlink(audio_path) [Immediate Cleanup]
    STTRoute-->>Browser: JSON { text: "open science unit two", metadata: {...} }
    Browser->>InterpRoute: POST /api/voice/interpret { text, context }
    InterpRoute->>Interpreter: interpret_text("open science unit two")
    Note over Interpreter: Rule-based matcher identifies<br/>Unit mention & calls CurriculumResolver
    Interpreter-->>InterpRoute: Interpretation(intent="command", command="OPEN_LESSON", ...)
    InterpRoute-->>Browser: VoiceInterpretResponse(command, confidence=0.96)
    Browser->>Router: Dispatches action -> navigates to /concept/sci-ch02-c01
    Browser->>Learner: Plays browser SpeechSynthesis audio confirmation
```

### Technical Step-by-Step Breakdown:
1. **Microphone Capture:** `frontend/src/useVoice.ts` requests browser permission via `navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } })`.
2. **Real-Time Voice Activity Detection (VAD):** An `AudioContext` with an `AnalyserNode` (`fftSize = 512`) calculates root-mean-square (RMS) energy in `monitorSilence()`. Ambient background noise is calibrated during the first 300ms. Once speech is detected (`rms >= dynamicThreshold`), a 650ms continuous silence (`SILENCE_DURATION_MS`) triggers `next.stop()`.
3. **Audio Upload:** The recorded audio blob is packaged into a `FormData` payload and POSTed to `/api/voice/transcribe` (`frontend/src/api.ts:133`).
4. **Ephemeral Transcription:** In `backend/app/api/routes/voice.py:44`, the audio stream is written to a POSIX `NamedTemporaryFile`. The configured provider (`GroqWhisperProvider` or `FasterWhisperProvider`) transcribes the file. In a guaranteed `finally:` block, `os.unlink()` removes the temporary audio file.
5. **Deterministic Command Classification:** The transcribed string is passed to `backend/app/voice/interpreter.py:interpret_text()`. Text is normalised (lowercased, punctuation removed). The command parser checks:
   - Command dictionary (`COMMANDS`, `ALIASES`)
   - Choice pattern regexes (`SELECT_OPTION_A`, etc.)
   - Politeness prefix stripping (*"Can you please open..."*)
   - SequenceMatcher string similarity (Levenshtein distance ratio >= 0.84 with 0.04 margin).
6. **Optional Contextual LLM Fallback:** If the deterministic interpreter returns `intent: unknown`, `backend/app/voice/understanding.py:understand()` sends a structured prompt with the current route, recent turns, and an allowlist of 26 valid commands. If confidence is below 0.7 or the command is invalid on the current screen (e.g., trying to submit a quiz answer from the Dashboard), the command is rejected with a clarification prompt.
7. **Frontend Action Dispatch:** `frontend/src/components/voice/VoiceStatusBar.tsx` receives the validated command and dispatches the corresponding navigation event via `react-router-dom`'s `useNavigate()`.

---

## Workflow B: Educational Question Answering

This workflow traces a student asking an academic question (e.g., *"What is evaporation?"*, *"Why do sea turtles travel?"*).

```mermaid
sequenceDiagram
    autonumber
    actor Learner as Child
    participant UI as React UI (VoiceView / Persistent Bar)
    participant Backend as FastAPI (/api/curriculum/ask or /api/voice/interpret)
    participant Resolver as CurriculumRetriever (SQLite)
    participant Guardrail as Curriculum Scope & Relevance Check
    participant LLM as Groq LLM (llama-3.1-8b) / Direct Summary
    participant TTS as Browser SpeechSynthesis (speech.ts)

    Learner->>UI: "What are the three states of matter?"
    UI->>Backend: POST /api/curriculum/ask { question, subject_id, concept_id }
    Backend->>Resolver: retrieve(query, context, limit=2)
    Resolver->>Resolver: tokenize_query (removes stop words)
    Resolver->>Resolver: Queries SQLite curriculum_concepts & lessons
    Resolver->>Resolver: Multi-factor scoring (Title, Body, Proximity)
    Resolver-->>Guardrail: Scored candidate documents
    alt Score < 3.5 OR Term Coverage < 0.35
        Guardrail-->>Backend: is_supported = False
        Backend-->>UI: "That topic is outside our Class 6 curriculum..."
    else Score >= 3.5 AND Coverage >= 0.35
        Guardrail->>LLM: build_grounded_prompt(query, evidence)
        LLM-->>Backend: JSON { supported: true, response: "Matter exists as solid, liquid, and gas..." }
        Backend-->>UI: CurriculumAskResponse(answer, supported=True, source=...)
    end
    UI->>UI: Displays answer text card & curriculum source citation
    UI->>TTS: speakText(answer)
    Note over TTS: Normalises units & fractions<br/>Emits tts-speaking-change (mutes mic)
    TTS->>Learner: Speaks answer in clear English voice
```

### Technical Step-by-Step Breakdown:
1. **Input Submission:** Question text arrives either via voice transcription or text entry in `frontend/src/pages/VoiceView.tsx` or `frontend/src/components/voice/VoiceStatusBar.tsx`.
2. **Query Normalisation & Anaphora Resolution:** In `backend/app/qa/assistant.py:168`, follow-up queries containing pronouns (e.g., *"Why does it melt?"*) are enriched with the active screen's concept or chapter title (e.g., *"States of Matter Why does it melt?"*).
3. **Curriculum Retrieval:** `CurriculumRetriever.retrieve()` in `backend/app/qa/retriever.py:97` tokenises the search query, excludes stop words, and scores all SQLite curriculum concepts and seeded lessons:
   - Exact title match: +12.0
   - Exact body phrase: +7.0
   - Token in title: +3.0 per term
   - Token in summary/key points: +1.5 per term
   - Term coverage bonus: `coverage * 4.0`
   - Active screen/concept proximity boost: +4.0
4. **Relevance Thresholding & Guardrail:** The top candidate must achieve `score >= 3.5` and `coverage >= 0.35`. If it fails, the query is classified as unsupported and receives `OUT_OF_SCOPE_MESSAGE` without calling an LLM.
5. **Grounded Answer Synthesis:**
   - **Online Mode:** The retrieved text chunks are formatted into a strict system prompt instructing `llama-3.1-8b-instant` or `gemma3:4b` to answer in under 35 words using only the supplied facts.
   - **Offline / LLM-Failure Fallback:** If the LLM provider times out or is unconfigured, `generate_direct_summary_answer()` extracts the most relevant stored key point or summary directly from the SQLite database.
6. **Spoken Output & Acoustic Echo Gate:** The answer is rendered in the UI. `frontend/src/speech.ts:speakText()` passes the text through `normalizeEducationalText()` (converting `1/2` to *"one half"*, `km/h` to *"kilometers per hour"*, etc.) and emits a `tts-speaking-change` event. The voice listener immediately suspends recording to prevent the computer's speaker from triggering the microphone.

---

## Workflow C: Proposed Future RAG Pipeline (Planned / Not Implemented)

> [!NOTE]
> This section details the planned architecture for expanding Voice2Learn to multi-term and multi-grade curricula. It is **not currently implemented** in the repository.

```mermaid
graph TD
    A[Raw Textbook PDFs in Books/] -->|PDF Text Extraction & OCR| B[Text Chunking & Recursive Splitter]
    B -->|Metadata Tagging: Subject, Grade, Term, Unit| C[Enriched Curriculum Chunks]
    C -->|Sentence-Transformers e.g. all-MiniLM-L6-v2| D[Dense Vector Embeddings 384-d]
    D -->|Index Construction| E[FAISS Index FlatIP / HNSW]
    
    F[Student Spoken Query] -->|Embedding Model| G[Query Vector 384-d]
    G -->|FAISS Index Search with Cosine Similarity| H[Top-K Candidate Chunks]
    H -->|Metadata Hard Filter: Class 6, Subject| I[Filtered Approved Chunks]
    I -->|Cosine Score >= Threshold e.g. 0.72| J{Relevance Check}
    J -- No --> K[Safe Rejection: Outside Approved Syllabus]
    J -- Yes --> L[Prompt Construction with Retrieved Context]
    L -->|Local Ollama / Gemma 3 4B| M[Constrained JSON Generation]
    M -->|Hallucination & Guardrail Verification| N[Final Spoken & Visual Answer]
```

---

## Workflow D: Quiz & Adaptive Learning Engine

This workflow traces question retrieval, answer evaluation, Elo-based ability adjustment, and database persistence.

```mermaid
sequenceDiagram
    autonumber
    actor Learner as Child
    participant UI as React QuizView (QuizView.tsx)
    participant NextQRoute as Backend (/api/quiz/next)
    participant AnswerRoute as Backend (/api/quiz/answer)
    participant DB as SQLite Database (database.py)

    UI->>NextQRoute: GET /api/quiz/next?learner_id=UUID&subject=science
    NextQRoute->>DB: get_next_question(learner_id, subject_id, concept_id)
    DB->>DB: Reads learner.ability and learner.target_difficulty
    DB->>DB: Filters out questions already in attempts table
    DB->>DB: Selects question closest to learner.ability in target band
    DB-->>NextQRoute: Question prompt, choices, difficulty (No answer key)
    NextQRoute-->>UI: JSON { question: {...}, message: "Question ready" }
    
    Learner->>UI: Speaks "Select option B" or clicks choice
    Learner->>UI: Speaks "Submit answer"
    UI->>AnswerRoute: POST /api/quiz/answer { learner_id, question_id, answer }
    AnswerRoute->>DB: submit_answer(learner_id, question_id, answer, ...)
    DB->>DB: Check duplicate submission in attempts
    DB->>DB: Normalise submitted answer & compare with accepted_answers
    Note over DB: Computes expected score & Elo ability:<br/>R_new = R_old + 32 * (Actual - Expected)
    Note over DB: Streak calculation:<br/>>=2 correct -> difficulty elevates<br/>>=2 incorrect -> difficulty lowers
    DB->>DB: INSERT INTO attempts (Atomic transaction)
    DB->>DB: UPDATE learners (ability, points, streaks, target_difficulty)
    DB->>DB: Upsert learner_topic_progress & learner_lesson_progress
    DB-->>AnswerRoute: { correct, points_awarded, ability, target_difficulty, explanation }
    AnswerRoute-->>UI: JSON { correct, points_awarded, ability, ... }
    UI->>UI: Displays feedback, awards points, updates streak pill
```

### Detailed Elo Rating Mathematics:
The ability update implemented in `backend/app/db/database.py:772` is:
$$E = \frac{1}{1 + 10^{\frac{R_{\text{question}} - R_{\text{learner}}}{400}}}$$
$$R_{\text{new}} = R_{\text{learner}} + K \times (S - E)$$
Where:
* $R_{\text{learner}}$ is the learner's current ability rating (defaults to 1000.0).
* $R_{\text{question}}$ is the static calibrated difficulty rating of the question (e.g., Easy = 900, Medium = 1000, Hard = 1100).
* $E$ is the expected probability of the student answering correctly.
* $S$ is the actual outcome: $1.0$ for correct, $0.0$ for incorrect.
* $K = 32$ is the sensitivity factor.

---

## Workflow E: Learner Onboarding & Session Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Learner as Child
    participant Welcome as React Welcome Screen
    participant AuthRoute as Backend (/api/auth/register or /login)
    participant Security as app.core.security
    participant DB as SQLite Database
    participant LocalStorage as Browser localStorage
    participant AppShell as Authenticated Shell (App.tsx)

    Learner->>Welcome: Enters nickname "Asha" & 4-digit PIN "2026"
    Welcome->>AuthRoute: POST /api/auth/register { nickname: "Asha", pin: "2026", grade_band: "6-7" }
    AuthRoute->>Security: hash_pin("2026")
    Security->>Security: PBKDF2-HMAC-SHA256 (100,000 iterations, random salt)
    AuthRoute->>DB: create_student(id, nickname, pin_hash, ...)
    DB->>DB: Inserts into students and learners tables
    AuthRoute->>Security: create_access_token({ sub, nickname, grade_band })
    Security-->>AuthRoute: HS256 JWT Token
    AuthRoute-->>Welcome: JSON { access_token, student: { id, nickname, ... } }
    Welcome->>LocalStorage: Saves access_token and learner profile
    Welcome->>AppShell: Triggers state transition -> navigates to /dashboard
```
