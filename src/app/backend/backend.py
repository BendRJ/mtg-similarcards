import logging
import os

import psycopg
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.backend.routers import cards

logger = logging.getLogger(__name__)


def create_app(cors_origins: list[str]) -> FastAPI:
    """Build the backend-for-frontend app. cors_origins is an explicit allow-list, never '*'."""
    app = FastAPI(title="mtg-similarcards BFF")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET"],
    )

    @app.exception_handler(psycopg.Error)
    def database_error(request: Request, exc: psycopg.Error) -> JSONResponse:
        # psycopg messages can echo connection details: log them, never return them.
        logger.error("Database error on %s %s", request.method, request.url.path, exc_info=exc)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            content={"detail": "Database unavailable."})

    @app.get("/", name="Hello World", include_in_schema=False)
    def home():
        return {"hello": "World!"}

    app.include_router(cards.router)
    return app


def cors_origins_from_env() -> list[str]:
    """Read CORS_ORIGINS, a comma-separated list, e.g. "http://localhost:5173". Unset means none."""
    return [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]


app = create_app(cors_origins_from_env())
