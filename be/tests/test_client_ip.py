from starlette.requests import Request

from app.client_ip import get_client_ip
from app.config import Settings

FERNET_KEY = "0" * 43 + "="


def make_request(headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "headers": headers,
            "client": ("192.0.2.10", 1234),
        }
    )


def make_settings(client_ip_header: str = "") -> Settings:
    return Settings(
        TOTP_ENC_KEY=FERNET_KEY,
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="password",
        POSTGRES_DB="database",
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        CLIENT_IP_HEADER=client_ip_header,
    )


def test_configured_client_ip_header_uses_first_value() -> None:
    request = make_request(
        [(b"x-forwarded-for", b"203.0.113.5, 192.0.2.20")]
    )

    assert (
        get_client_ip(
            request,
            make_settings("x-forwarded-for"),
        )
        == "203.0.113.5"
    )


def test_unconfigured_client_ip_ignores_forwarded_header() -> None:
    request = make_request(
        [(b"x-forwarded-for", b"203.0.113.5")]
    )

    assert get_client_ip(request, make_settings()) == "192.0.2.10"
