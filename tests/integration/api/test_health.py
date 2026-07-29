from fastapi.testclient import TestClient

from evalforge.core.config import Environment, Settings
from evalforge.main import create_app


def create_test_settings() -> Settings:
    return Settings(
        _env_file=None,
        app_name="EvalForge Test",
        app_version="0.1.0-test",
        environment=Environment.TEST,
        debug=False,
    )


def create_test_client() -> TestClient:
    return TestClient(create_app(create_test_settings()))


def test_health_endpoint_returns_service_information() -> None:
    with create_test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "EvalForge Test",
        "version": "0.1.0-test",
        "environment": "test",
    }


def test_liveness_endpoint_returns_alive() -> None:
    with create_test_client() as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "service": "EvalForge Test",
        "version": "0.1.0-test",
    }


def test_readiness_endpoint_returns_ready_after_startup() -> None:
    with create_test_client() as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "EvalForge Test",
        "version": "0.1.0-test",
    }


def test_readiness_endpoint_returns_503_when_not_ready() -> None:
    with create_test_client() as client:
        client.app.state.ready = False
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "EvalForge Test",
        "version": "0.1.0-test",
    }


def test_application_lifespan_controls_readiness() -> None:
    application = create_app(create_test_settings())

    assert application.state.ready is False

    with TestClient(application):
        assert application.state.ready is True

    assert application.state.ready is False


def test_openapi_uses_injected_application_settings() -> None:
    with create_test_client() as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["title"] == "EvalForge Test"
    assert document["info"]["version"] == "0.1.0-test"
    assert "/health" in document["paths"]
    assert "/health/live" in document["paths"]
    assert "/health/ready" in document["paths"]


def test_health_endpoint_generates_request_id() -> None:
    with create_test_client() as client:
        response = client.get("/health")

    request_id = response.headers["x-request-id"]

    assert response.status_code == 200
    assert len(request_id) == 32
    assert request_id.isalnum()


def test_health_endpoint_preserves_valid_request_id() -> None:
    with create_test_client() as client:
        response = client.get(
            "/health",
            headers={"X-Request-ID": "req-integration-001"},
        )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-integration-001"


def test_health_endpoint_replaces_invalid_request_id() -> None:
    with create_test_client() as client:
        response = client.get(
            "/health",
            headers={"X-Request-ID": "invalid request id"},
        )

    request_id = response.headers["x-request-id"]

    assert response.status_code == 200
    assert request_id != "invalid request id"
    assert len(request_id) == 32
