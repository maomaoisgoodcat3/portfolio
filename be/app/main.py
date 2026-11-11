from fastapi import FastAPI

from app.config import Settings, get_settings
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.public import router as public_router
from app.security_headers import SecurityHeadersMiddleware


def create_app(settings: Settings) -> FastAPI:
    docs_url = "/docs" if settings.app_env == "development" else None
    redoc_url = "/redoc" if settings.app_env == "development" else None
    openapi_url = "/openapi.json" if settings.app_env == "development" else None
    app = FastAPI(
        title=settings.app_name,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.state.settings = settings
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(public_router)
    app.include_router(chat_router)
    app.include_router(admin_router)
    app.include_router(auth_router)

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app(get_settings())
