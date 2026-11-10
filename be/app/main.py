from fastapi import FastAPI

from app.config import settings
from app.routers.admin import router as admin_router
from app.routers.public import router as public_router

app = FastAPI(title=settings.app_name)

app.include_router(public_router)
app.include_router(admin_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
