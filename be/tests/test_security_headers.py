from fastapi import Response
from fastapi.testclient import TestClient

from app.config import settings
from app.main import create_app

EXPECTED_SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
}


def assert_security_headers(response) -> None:
    for name, value in EXPECTED_SECURITY_HEADERS.items():
        assert response.headers[name] == value


def test_health_has_security_headers(client: TestClient) -> None:
    response = client.get("/health")

    assert_security_headers(response)


def test_unauthorized_admin_response_has_security_headers(
    client: TestClient,
) -> None:
    response = client.get("/api/admin/blocks")

    assert response.status_code == 401
    assert_security_headers(response)


def test_unauthorized_auth_me_response_is_not_cached(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


def test_unauthorized_admin_blocks_response_is_not_cached(
    client: TestClient,
) -> None:
    response = client.get("/api/admin/blocks")

    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


def test_public_blocks_response_is_not_marked_no_store(client: TestClient) -> None:
    response = client.get("/api/public/blocks")

    assert response.headers.get("cache-control") != "no-store"


def test_production_app_hides_api_documentation() -> None:
    production_settings = settings.model_copy(update={"app_env": "production"})
    client = TestClient(create_app(production_settings))

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_route_header_is_not_overwritten() -> None:
    app = create_app(settings.model_copy(update={"app_env": "development"}))

    @app.get("/custom-header")
    def custom_header() -> Response:
        return Response(
            content="ok",
            headers={"X-Frame-Options": "SAMEORIGIN"},
        )

    response = TestClient(app).get("/custom-header")

    assert response.headers["x-frame-options"] == "SAMEORIGIN"
