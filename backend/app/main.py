
from fastapi import FastAPI

app = FastAPI(
    title="Voice2Learn API",
    description="Voice-first adaptive learning for children with mobility challenges",
    version="0.1.0",
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "Voice2Learn backend is running",
        "stt_backend": "not_configured",
        "llm_backend": "not_configured",
        "retrieval_ready": False,
    }
