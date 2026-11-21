
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SessionCreateResponse(BaseModel):
    session_id: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Message cannot be empty or contain only whitespace.")

        return value


class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: datetime


class ChatResponse(BaseModel):
    session_id: str
    message: MessageResponse


class MessageHistoryResponse(BaseModel):
    session_id: str
    messages: list[MessageResponse]
    total_messages: int
