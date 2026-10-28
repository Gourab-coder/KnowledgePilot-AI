import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if (
            normalized.count("@") != 1
            or any(character.isspace() for character in normalized)
            or "." not in normalized.rsplit("@", 1)[1]
        ):
            raise ValueError("Enter a valid email address.")
        return normalized


class LoginRequest(RegisterRequest):
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    page_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None
    document_ids: list[uuid.UUID] | None = Field(default=None, max_length=50)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question must not be blank.")
        return value.strip()


class CitationResponse(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page_number: int
    excerpt: str
    similarity: float


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    answer: str
    citations: list[CitationResponse]


class ConversationResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    citations: list[CitationResponse]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
