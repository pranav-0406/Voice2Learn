from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_expected_readiness_state() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "status": "ok",
        "message": "Voice2Learn backend is running",
        "stt_backend": "not_configured",
        "llm_backend": "not_configured",
        "retrieval_ready": False,
    }


def test_health_does_not_claim_unconfigured_components_are_ready() -> None:
    health = client.get("/api/health").json()

    assert health["stt_backend"] == "not_configured"
    assert health["llm_backend"] == "not_configured"
    assert health["retrieval_ready"] is False


def test_cors_allows_local_vite_origin() -> None:
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
