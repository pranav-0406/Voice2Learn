# Voice2Learn

Voice2Learn is a voice-first adaptive learning assistant for children with mobility challenges.

## Backend setup (Windows PowerShell)

From the project root, create and activate a virtual environment:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the lightweight backend and test dependencies, then start the local API:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The backend is available at `http://localhost:8000`; check readiness at
`http://localhost:8000/api/health` and open the interactive API documentation at
`http://localhost:8000/docs`.

Run the automated backend checks from `backend` with:

```powershell
python -m pytest tests
```

To override the permitted development frontend origins, set a comma-separated
`VOICE2LEARN_CORS_ORIGINS` environment variable. The default permits the Vite
development servers at `http://localhost:5173` and `http://127.0.0.1:5173`.

SQLite is initialized and seeded with the sample Science lesson when the server
starts. By default the local database is `backend/data/voice2learn.sqlite3`.
Set `VOICE2LEARN_DATABASE_PATH` before starting the server to use a different
database file.

## Optional local speech-to-text

The server starts without loading a speech model. To enable local transcription,
install the optional provider after confirming that it supports your Python and
hardware setup:

```powershell
python -m pip install -r requirements-stt.txt
```

The defaults use the `small` model on CPU with `int8` compute. Configure
`VOICE2LEARN_STT_MODEL`, `VOICE2LEARN_STT_DEVICE`,
`VOICE2LEARN_STT_COMPUTE_TYPE`, and `VOICE2LEARN_STT_MAX_UPLOAD_BYTES` in your
environment. CUDA is optional and must be tested on the actual Windows machine;
the backend does not claim GPU support until the provider loads successfully.

With the server running and a short local WAV file available, test transcription:

```powershell
curl.exe -X POST http://localhost:8000/api/voice/transcribe -F "audio=@C:\path\to\sample.wav;type=audio/wav"
```
