"""Pydantic request/response schemas."""
from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    fiqha: str


class Reference(BaseModel):
    book_name: str
    author_name: str
    fiqha: str
    rank: int
    chain: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    references: List[Reference] = []


class LoginRequest(BaseModel):
    username: str
    password: str


class BookOut(BaseModel):
    id: int
    book_name: str
    author_name: str
    fiqha: str
    rank: int
    status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True