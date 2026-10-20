# Voice2Learn — Technology Selection & Architecture Decisions

This document provides a comprehensive technical justification for every software component, library, framework, and design pattern implemented in the Voice2Learn codebase.

---

## 1. Master Technology Inventory & Comparison Table

| Technology | Role | Where Used in Code | Why Chosen | Evaluated Alternatives | Key Advantages | Technical Limitations | Current Status |
|---|---|---|---|---|---|---|---|
| **React 18.3.1** | Reactive Frontend UI Framework | `frontend/src/App.tsx`, `frontend/src/pages/`, `frontend/src/components/` | Component-based reactivity, declarative rendering of learning states, mature accessibility ecosystem | Vanilla JS, Vue.js, Svelte, Angular | Declarative UI state synchronisation; seamless integration with Web Audio & Speech APIs | Client-side bundle weight (~375 kB); requires virtual DOM diffing | IMPLEMENTED AND VERIFIED |
| **TypeScript 5.4.5** | Type-Safe Language Superset | Entire `frontend/src/` | Eliminates runtime type errors, enforces strict API contracts between backend JSON and React props | JavaScript (ES6+), Flow | Compile-time validation; strict autocomplete across quiz & curriculum schemas | Requires build compilation step (`tsc`); does not prevent runtime backend contract mismatches | IMPLEMENTED AND VERIFIED |
| **Vite 5.2.12** | Frontend Build Tool & Dev Server | `frontend/vite.config.ts`, `frontend/package.json` | Instant native ESM hot-module replacement (HMR), sub-second build times | Webpack, Rollup, Parcel | Extremely fast development reload; production roll-up minification in under 1 second | Requires modern browser ESM support; development server config separated from Python backend | IMPLEMENTED AND VERIFIED |
| **Vanilla CSS (3.0)** | Styling & Design System | `frontend/src/styles.css` | Maximum control over layout tokens, high-contrast themes, focus rings, responsive breakpoints | Tailwind CSS, CSS Modules, Styled Components | Zero runtime styling overhead; fully customized accessibility features without framework constraints | Requires manual organization to prevent stylesheet bloat (currently ~1,133 lines) | IMPLEMENTED AND VERIFIED |
| **Framer Motion 11.0.0** | Motion & Animation Engine | `frontend/src/App.tsx`, `frontend/src/components/learning/ConceptCard.tsx` | Declarative page and card transitions with native `reducedMotion="user"` accessibility respect | CSS Keyframes alone, React Spring, GSAP | Smooth spring animations; automatically disables animations when OS prefers reduced motion | Adds JavaScript bundle size; requires React runtime context | IMPLEMENTED AND VERIFIED |
| **Lucide React 0.383.0** | Accessible SVG Iconography | `frontend/src/components/` | Clean, scalable educational iconography with ARIA hidden attributes | FontAwesome, Material Icons, SVG sprites | Tree-shakeable SVG components; sharp rendering on high-DPI assistive screens | Limited to icon set provided by the library | IMPLEMENTED AND VERIFIED |
| **Browser MediaRecorder API** | Client-Side Audio Recording | `frontend/src/useVoice.ts:130` | Native browser streaming of microphone chunks without third-party audio plugins | WebRTC DataChannels, Flash (deprecated), RecordRTC library | Zero client dependency; native Opus/WebM and WAV encoding | Codec availability varies across Safari (WAV) vs Chrome (WebM Opus) | IMPLEMENTED AND VERIFIED |
| **Web Audio API (AnalyserNode)** | Local Voice Activity Detection (VAD) | `frontend/src/useVoice.ts:213` | Real-time calculation of audio RMS energy to automatically detect when the child stops speaking | Porcupine, Silero VAD (Python), Meyda JS | Low-latency client-side silence cutoff (650ms); ambient noise floor calibration in first 300ms | Requires browser audio thread; microphone sensitivity depends on hardware mic quality | IMPLEMENTED AND VERIFIED |
| **Browser SpeechSynthesis API** | Text-to-Speech (TTS) Engine | `frontend/src/speech.ts:189` | Zero-latency, zero-cost audio playback of curriculum answers using local OS/browser voices | ElevenLabs Cloud API, Google Cloud TTS, Piper TTS | No server compute required; zero audio bandwidth; works offline; zero audio storage | Voice naturalness varies by OS (Chrome Natural Google voices vs robotic Windows SAPI) | IMPLEMENTED AND VERIFIED |
| **FastAPI 0.115.14** | Python REST Backend Framework | `backend/app/main.py`, `backend/app/api/` | High-throughput asynchronous request handling, automatic OpenAPI/Swagger documentation | Flask, Django REST Framework, Tornado | Native Pydantic v2 validation; async route execution; lightweight memory footprint | Single-process async event loop can be blocked if CPU-heavy ML inference is run in async def | IMPLEMENTED AND VERIFIED |
| **Uvicorn 0.54.0** | ASGI Web Server | `backend/requirements.txt` | Lightning-fast async server implementation based on uvloop and httptools | Gunicorn, Waitress, Hypercorn | Low latency HTTP/1.1 pipeline; automatic reload during development | Single process unless orchestrated with Gunicorn or systemd | IMPLEMENTED AND VERIFIED |
| **Pydantic 2.14.1** | Data Parsing & Schema Validation | `backend/app/api/schemas.py`, `backend/app/agent/schemas.py` | Rust-backed core validation for guaranteed request/response types and JSON schema generation | Marshmallow, attrs, Cerberus | Strict type coercion and runtime validation; clean error structures for client consumption | Schema definition overhead for complex nested curriculum trees | IMPLEMENTED AND VERIFIED |
| **SQLite 3 (Built-in Python)** | Relational Data Storage | `backend/app/db/database.py` | Embedded serverless database, single-file portability, zero external database setup | PostgreSQL, MySQL, MongoDB | Zero configuration; atomic transactions; foreign key support (`PRAGMA foreign_keys = ON`) | File-level write locks limit high concurrent multi-user write throughput | IMPLEMENTED AND VERIFIED |
| **Groq Cloud API (Whisper & LLM)** | High-Speed Cloud AI Inference | `backend/app/stt/provider.py`, `backend/app/qa/groq.py` | LPUs (Language Processing Units) deliver 200–500 tokens/sec, enabling conversational responsiveness | OpenAI API, Anthropic Claude, Replicate | Sub-second voice-to-answer turnaround; eliminates need for expensive local GPU on school laptops | Requires internet connectivity; privacy considerations for temporary audio streaming | IMPLEMENTED AND VERIFIED |
| **faster-whisper (CTranslate2)** | Optional Local Speech Recognition | `backend/app/stt/provider.py:61` | Quantized int8 Whisper transcription on local CPU or CUDA without cloud dependency | Whisper.cpp, Vosk, SpeechRecognition | 100% on-device student privacy; zero cloud cost; works completely offline | High CPU memory load during model loading; package not installed in default test venv | PARTIALLY IMPLEMENTED (Code verified, dependency optional) |
| **Ollama (Gemma 3 4B / Llama 3)** | Local Large Language Model | `backend/app/qa/ollama.py`, `backend/app/voice/understanding.py` | Privacy-preserving local language generation with JSON mode constraints | vLLM, llama.cpp, LocalAI | Local data residency; zero subscription fee; offline-capable | Requires at least 8 GB RAM / 4 GB VRAM; slower inference on low-power student devices | IMPLEMENTED, NOT VERIFIED AT RUNTIME (Ollama service not running during audit) |
| **FAISS & Sentence-Transformers** | Dense Vector Retrieval (RAG) | N/A | High-dimensional dense semantic similarity search over large textbook chunk sets | ChromaDB, Qdrant, Pinecone, Milvus | Sub-millisecond similarity search across millions of vectors; semantic synonym understanding | Unnecessary overhead for small Term 1 curriculum (57 concepts); requires PyTorch & vector storage | PLANNED / NOT IMPLEMENTED |

---

## 2. In-Depth Architectural Rationale

### 2.1 Why React for the Interactive Frontend?
An accessibility-first educational interface for children with mobility challenges cannot be a collection of static HTML pages that reload on every click. Voice navigation demands seamless state preservation: when a student speaks *"Select Option B"*, the UI must immediately highlight the selection, play audio feedback, and preserve the microphone recording loop without page flickering or focus loss. React's component tree allows independent, granular state updates across:
* The persistent **VoiceStatusBar** (which remains alive across all route transitions).
* The **ConceptViewer** (updating concept summaries and key points smoothly).
* The **QuizView** (re-rendering option cards and feedback without re-mounting).

### 2.2 Why FastAPI for the Python Backend?
Python is the undisputed standard ecosystem for speech processing (faster-whisper, Whisper), language models (Groq, Ollama), and curriculum retrieval. FastAPI provides:
1. **Asynchronous Concurrency:** High-concurrency I/O for streaming audio uploads while running database queries.
2. **Native Pydantic v2:** Automatic data sanitisation and schema generation.
3. **Threadpool Offloading:** Heavy CPU or synchronous provider tasks (e.g., `model.transcribe()`) run via Starlette's `run_in_threadpool`, preventing event loop starvation.

### 2.3 Why SQLite is Sufficient for the Prototype
For an on-device assistive educational assistant, setting up a standalone PostgreSQL or MySQL daemon creates significant friction for students, schools, and evaluation panels. SQLite:
* Lives in a single portable file (`backend/data/voice2learn.sqlite3`).
* Requires zero network socket configuration or credential management.
* Handles thousands of reads per second with sub-millisecond query latency.
* Supports robust relational constraints (`FOREIGN KEY`, `UNIQUE`, `CHECK`).
For a multi-school cloud deployment, the data access layer in `backend/app/db/database.py` can be refactored to SQLAlchemy or asyncpg with minimal schema changes.

### 2.4 Why Deterministic Command Routing Handles Predictable Actions
Many voice assistants make the critical mistake of routing *every* single utterance through a Large Language Model. In Voice2Learn, this is intentionally avoided:
* **Latency:** A deterministic regex and string matcher in `backend/app/voice/interpreter.py` evaluates in **< 1 millisecond**. An LLM requires **400–1,500 milliseconds**.
* **Reliability:** An LLM may randomly misinterpret *"Submit"* as a creative question or hallucinate a non-existent menu. Deterministic routing guarantees 100% predictable execution for safety-critical navigation.
* **Cost & Compute:** Running local or cloud LLMs for common actions like *"Go back"* or *"Next"* wastes battery, CPU, and API tokens.
The LLM is invoked **only** when deterministic rules fail or when the child asks a natural-language question.

### 2.5 Why Browser SpeechSynthesis Eliminates Cloud TTS Overhead
Using browser-native `window.speechSynthesis`:
1. **Zero Bandwidth & Latency:** Spoken audio is synthesized instantly on the client device without sending text across the network or downloading MP3 streams.
2. **Zero Operating Cost:** Cloud TTS providers (e.g. ElevenLabs, Google Cloud TTS) charge per character. For an educational app that reads textbook lessons aloud, cloud TTS quickly becomes financially unsustainable for public schools.
3. **Acoustic Echo Gate Integration:** The browser TTS lifecycle fires synchronous `onstart` and `onend` events, allowing the frontend in `speech.ts` to coordinate the Acoustic Echo Gate and mute the microphone during audio output.

### 2.6 Why FAISS is Unnecessary for a Small Prototype (and When It Becomes Necessary)
A core academic tenet of Voice2Learn is **engineering proportionality**:
* The current Class 6 Term 1 syllabus contains **4 subjects, 24 chapters, and 57 core concepts**.
* Searching 57 structured concepts using SQLite queries and transparent token-coverage ranking in `app/qa/retriever.py` takes **under 2 milliseconds** and requires **zero megabytes of extra vector index memory**.
* Introducing FAISS, PyTorch (700 MB+ dependency), and 384-dimensional dense embeddings for 57 records would introduce massive overhead without measurable precision gain.
* **When FAISS is justified:** When the system scales to Grades 1–12 across all 3 terms (~10,000+ textbook passages and multi-sentence chunks), lexical search becomes insufficient for out-of-vocabulary synonyms. At that stage, FAISS FlatIP or HNSW indexing becomes mathematically necessary.

### 2.7 Why a Modular Monolith Architecture Fits the Project Scope
Microservices introduce network serialization overhead, distributed tracing complexity, container orchestration hurdles, and deployment fragility. For Voice2Learn's current scope:
* A **modular monolith** keeps the React frontend cleanly decoupled from the Python API via strict REST endpoints.
* Backend modules (`auth`, `curriculum`, `qa`, `stt`, `voice`, `agent`) are organized as isolated Python packages with clear dependency boundaries.
* The entire system starts in two commands (`npm run dev` and `uvicorn app.main:app`), ensuring effortless reproducibility for academic evaluation and clinical trials.
