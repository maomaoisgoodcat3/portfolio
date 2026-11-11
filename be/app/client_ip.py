from fastapi import Request

from app.config import Settings, settings


def get_client_ip(request: Request, app_settings: Settings | None = None) -> str:
    config = app_settings or settings
    if config.client_ip_header:
        forwarded = request.headers.get(config.client_ip_header)
        if forwarded is not None:
            return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else ""
