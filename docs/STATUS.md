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

## Next
1. Add and commit API contract and status documents.
2. Test GPU and local model compatibility.
3. Create FastAPI backend skeleton and health endpoint.
4. Build frontend against mock responses.
5. Integrate learning, voice and progress workflows.

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
