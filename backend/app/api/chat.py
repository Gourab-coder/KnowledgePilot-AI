import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from openai import APIError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.documents import get_embedding_service
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
)
from app.db.models import Conversation, Document, Message, User
from app.db.session import get_db
from app.services.rag_service import RagService
from app.services.embeddings import EmbeddingService

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


def get_rag_service(
    request: Request,
    embeddings: EmbeddingService = Depends(get_embedding_service),
) -> RagService:
    service: RagService = request.app.state.rag_service
    service.embedding_service = embeddings
    return service


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rag: RagService = Depends(get_rag_service),
) -> ChatResponse:
    if payload.conversation_id is not None:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.id == payload.conversation_id,
                Conversation.user_id == user.id,
            )
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")

    if payload.document_ids:
        accessible_ids = set(
            db.scalars(
                select(Document.id).where(
                    Document.user_id == user.id,
                    Document.id.in_(payload.document_ids),
                )
            )
        )
        if accessible_ids != set(payload.document_ids):
            raise HTTPException(status_code=404, detail="One or more documents were not found.")

    try:
        retrieved = rag.retrieve(db, user.id, payload.question, payload.document_ids)
        answer = rag.answer(payload.question, retrieved)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except APIError as exc:
        logger.warning("Groq API request failed with status %s.", exc.status_code)
        raise HTTPException(
            status_code=502,
            detail=(
                f"Groq API request failed (HTTP {exc.status_code}). "
                "Check GROQ_API_KEY, account access, and GROQ_MODEL."
            ),
        ) from exc

    if payload.conversation_id is None:
        conversation = Conversation(user_id=user.id)
        db.add(conversation)
        db.flush()
    else:
        conversation = db.get(Conversation, payload.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")

    citations = rag.citations(retrieved)
    db.add_all(
        [
            Message(conversation_id=conversation.id, role="user", content=payload.question),
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                citations=citations,
            ),
        ]
    )
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    return ChatResponse(
        conversation_id=conversation.id,
        answer=answer,
        citations=citations,
    )


@router.get("/api/v1/conversations", response_model=list[ConversationResponse])
def list_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Conversation]:
    return list(
        db.scalars(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
        )
    )


@router.get(
    "/api/v1/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_conversation_messages(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Message]:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at, Message.id)
        )
    )
