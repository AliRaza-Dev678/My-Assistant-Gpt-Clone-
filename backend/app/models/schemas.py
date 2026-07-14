from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    position: int
    created_at: datetime


class ConversationCreate(BaseModel):
    title: str = Field(default="New chat", min_length=1, max_length=80)


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=80)


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[MessageRead]
