from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.database import check_database, initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Anywhere Door API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )
    application.include_router(api_router, prefix="/api/v1")

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "database": "ok" if check_database() else "error"}

    return application


app = create_app()
