# Voice2Learn Status

Last updated: 16 October 2026
Deadline: 21 October 2026
Feature freeze: 19 October 2026 night

## Locked decisions
- Local-first voice learning application.
- Frontend: React + Vite.
- Backend: Python + FastAPI.
- Speech recognition: faster-whisper, subject to GPU compatibility.
- Local LLM: Ollama, subject to performance testing.
- Retrieval: embeddings + FAISS, with a simpler fallback if needed.
- Database: SQLite.
- Demo audience: Classes 6-9.
- Main subject: Science.
- Privacy: nickname only; audio recordings are not stored.

## Completed
- GitHub repository created.
- SSH authentication configured.
- Initial project structure committed.
- FastAPI health endpoint and local CORS foundation added.
- SQLite-backed learner creation, Science subject listing, and a seeded Science lesson added.
- Adaptive Science quiz questions, answer evaluation, and persisted learner progress added.
- Optional lazy local speech-to-text interface and deterministic voice interpretation added.

## Next
1. Add and commit API contract and status documents.
2. Test GPU and local model compatibility.
3. Build frontend against the implemented local API and mock the remaining endpoints.
4. Test local Windows CPU/CUDA speech-recognition compatibility, then integrate the educational Q&A workflow.

## Risks
- RTX 5060 compatibility with the speech inference stack.
- GPU memory when running speech recognition and a local LLM.
- Speech recognition reliability in the demo environment.
- Time remaining before feature freeze.

## Working rules
- Work in small, reviewable changes.
- Keep API contracts synchronized.
- Commit working code before major changes.
- Never commit API keys, local databases or audio recordings.
