from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker

from app.api import auth, chat, documents
from app.core.config import Settings, settings as default_settings
from app.db.session import create_database_engine, initialize_database
from app.services.embeddings import EmbeddingService
from app.services.rag_service import RagService


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or default_settings
    engine = create_database_engine(app_settings.database_url)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        initialize_database(engine)
        yield
        engine.dispose()

    app = FastAPI(
        title="KnowledgePilot AI API",
        description="Document-grounded RAG assistant API.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.embedding_service = EmbeddingService(app_settings.embedding_model)
    app.state.rag_service = RagService(app_settings)

    origins = [origin.strip() for origin in app_settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(chat.router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
