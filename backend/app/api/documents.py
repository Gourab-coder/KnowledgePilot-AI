import logging
import uuid
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas import DocumentResponse
from app.db.models import Document, DocumentChunk, User
from app.db.session import get_db
from app.services.pdf_processor import create_chunks, extract_pdf_pages
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    embeddings: EmbeddingService = Depends(get_embedding_service),
) -> Document:
    settings = request.app.state.settings
    content = file.file.read(settings.max_upload_size_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="The PDF exceeds the upload size limit.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Only valid PDF files are accepted.")

    try:
        pages = extract_pdf_pages(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    chunk_data = create_chunks(pages, settings.chunk_size, settings.chunk_overlap)
    try:
        chunk_embeddings = embeddings.embed_many(
            [str(chunk["text"]) for chunk in chunk_data]
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"Embedding service unavailable: {exc}") from exc

    original_name = PurePosixPath((file.filename or "document.pdf").replace("\\", "/")).name
    safe_filename = "".join(
        character for character in original_name if character.isprintable() and character not in "\r\n"
    )[:255]
    if not safe_filename:
        safe_filename = "document.pdf"

    document_id = uuid.uuid4()
    upload_dir = Path(settings.upload_dir).resolve()
    storage_path = upload_dir / f"{document_id}.pdf"
    upload_dir.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(content)

    document = Document(
        id=document_id,
        user_id=user.id,
        filename=safe_filename,
        storage_path=str(storage_path),
        status="completed",
        page_count=len(pages),
    )
    document.chunks = [
        DocumentChunk(
            user_id=user.id,
            chunk_index=index,
            page_number=int(chunk["page_number"]),
            content=str(chunk["text"]),
            embedding=chunk_embeddings[index],
        )
        for index, chunk in enumerate(chunk_data)
    ]
    db.add(document)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        try:
            storage_path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Could not remove an uncommitted uploaded PDF.")
        raise HTTPException(status_code=500, detail="Could not save the uploaded document.") from exc
    db.refresh(document)
    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Document]:
    return list(
        db.scalars(
            select(Document)
            .where(Document.user_id == user.id)
            .order_by(Document.created_at.desc())
        )
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    document = db.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    document = db.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    storage_path = Path(document.storage_path).resolve()
    upload_dir = Path(request.app.state.settings.upload_dir).resolve()
    if storage_path.parent != upload_dir or storage_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=500, detail="Stored document path is invalid.")

    db.delete(document)
    db.commit()
    try:
        storage_path.unlink(missing_ok=True)
    except OSError as exc:
        logger.exception("Document was deleted from the database, but its file could not be removed.")
        raise HTTPException(
            status_code=500, detail="Document records were deleted, but file cleanup failed."
        ) from exc
