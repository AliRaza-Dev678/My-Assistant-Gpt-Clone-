from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from tortoise import connections
from tortoise.contrib.fastapi import RegisterTortoise

from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.core.config import Settings, get_settings
from app.core.database import build_tortoise_config
from app.repositories.conversations import ConversationRepository
from app.services.assistant import AssistantService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with RegisterTortoise(
            app=app,
            config=build_tortoise_config(settings),
            generate_schemas=settings.generate_schemas,
            use_tz=True,
            timezone="UTC",
        ):
            yield

    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.repository = ConversationRepository()
    app.state.assistant = AssistantService(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["system"])
    async def health():
        try:
            await connections.get("default").execute_query("SELECT 1")
        except Exception:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "database": "disconnected",
                },
            )

        return {
            "status": "ok",
            "assistant": "Ali Raza's Assistant",
            "model": settings.groq_model,
            "configured": bool(settings.groq_api_key),
            "database": "connected",
        }

    app.include_router(conversations_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    return app


app = create_app()
