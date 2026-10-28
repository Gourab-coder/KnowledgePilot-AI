import math
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Document, DocumentChunk
from app.services.embeddings import EmbeddingService
from app.services.groq_client import GroqClient

UNCERTAINTY_ANSWER = "I couldn't find an answer to that question in the selected documents."


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    filename: str
    similarity: float


class RagService:
    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService | None = None,
        groq_client: GroqClient | None = None,
    ):
        self.settings = settings
        self.embedding_service = embedding_service or EmbeddingService(settings.embedding_model)
        self.groq_client = groq_client or GroqClient(settings.groq_api_key, settings.groq_model)

    def retrieve(
        self,
        db: Session,
        user_id: uuid.UUID,
        question: str,
        document_ids: list[uuid.UUID] | None,
    ) -> list[RetrievedChunk]:
        query_embedding = self.embedding_service.embed(question)
        statement = (
            select(DocumentChunk, Document.filename)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                DocumentChunk.user_id == user_id,
                Document.user_id == user_id,
                Document.status == "completed",
            )
        )
        if document_ids:
            statement = statement.where(Document.id.in_(document_ids))

        if db.bind is not None and db.bind.dialect.name == "postgresql":
            distance = DocumentChunk.embedding.cosine_distance(query_embedding)
            rows = db.execute(
                statement.add_columns(distance.label("distance"))
                .order_by(distance)
                .limit(self.settings.retrieval_top_k)
            ).all()
            return [
                RetrievedChunk(
                    chunk,
                    filename,
                    max(0.0, min(1.0, 1.0 - float(distance_value))),
                )
                for chunk, filename, distance_value in rows
                if 1.0 - float(distance_value) >= self.settings.retrieval_similarity_threshold
            ]

        rows = db.execute(statement).all()
        scored = [
            RetrievedChunk(chunk, filename, self._cosine_similarity(query_embedding, chunk.embedding))
            for chunk, filename in rows
        ]
        return [
            item
            for item in sorted(scored, key=lambda item: item.similarity, reverse=True)[
                : self.settings.retrieval_top_k
            ]
            if item.similarity >= self.settings.retrieval_similarity_threshold
        ]

    def answer(self, question: str, retrieved: list[RetrievedChunk]) -> str:
        if not retrieved:
            return UNCERTAINTY_ANSWER
        context = "\n\n".join(
            f"[Document: {item.filename}; page {item.chunk.page_number}]\n"
            f"{item.chunk.content}"
            for item in retrieved
        )
        return self.groq_client.generate_grounded_answer(question, context)

    @staticmethod
    def citations(retrieved: list[RetrievedChunk]) -> list[dict[str, object]]:
        return [
            {
                "chunk_id": str(item.chunk.id),
                "document_id": str(item.chunk.document_id),
                "filename": item.filename,
                "page_number": item.chunk.page_number,
                "excerpt": item.chunk.content[:500],
                "similarity": round(item.similarity, 4),
            }
            for item in retrieved
        ]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return max(-1.0, min(1.0, dot / (left_norm * right_norm)))
