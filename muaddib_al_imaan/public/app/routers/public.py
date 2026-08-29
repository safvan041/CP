"""Public-facing routes: fiqha selection, chat UI, and chat API."""
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import FIQH_SCHOOLS, TOP_BOOKS
from app.database import get_db
from app.models import Book
from app.schemas import ChatRequest, ChatResponse, Reference
from public.app.services.chat import generate_chat_response
from public.app.services.embeddings import get_embedding_model
from public.app.services.vector_store import search_similar_chunks

router = APIRouter()
templates = Jinja2Templates(directory="public/templates")

# Pattern to detect a chain of references like "X narrated from Y from Z".
CHAIN_PATTERN = re.compile(
    r"(narrated|reported|related|transmitted|from)\b", re.IGNORECASE
)


def _extract_chain(text: str):
    """Return a reference chain if the chunk contains one, else None."""
    if CHAIN_PATTERN.search(text):
        # Return a trimmed snippet around the chain for display.
        return text.strip()
    return None


@router.get("/", response_class=HTMLResponse)
def fiqha_selection(request: Request):
    return templates.TemplateResponse(
        "public_select.html",
        {"request": request, "fiqhas": FIQH_SCHOOLS},
    )


@router.get("/chat/{fiqha}", response_class=HTMLResponse)
def chat_page(request: Request, fiqha: str):
    if fiqha not in FIQH_SCHOOLS:
        raise HTTPException(status_code=404, detail="Unknown fiqha")
    return templates.TemplateResponse(
        "public_chat.html",
        {"request": request, "fiqha": fiqha},
    )


@router.post("/api/chat", response_model=ChatResponse)
def chat_api(payload: ChatRequest, db: Session = Depends(get_db)):
    if payload.fiqha not in FIQH_SCHOOLS:
        raise HTTPException(status_code=400, detail="Unknown fiqha")

    model = get_embedding_model()
    chunks = search_similar_chunks(
        db, payload.message, payload.fiqha, model
    )

    if not chunks:
        return ChatResponse(
            response="No relevant information found for this fiqha.",
            references=[],
        )

    # Build references from the top books (ranked by admin-assigned rank).
    books = (
        db.query(Book)
        .filter(Book.fiqha == payload.fiqha, Book.status == "completed")
        .order_by(Book.rank.desc())
        .limit(TOP_BOOKS)
        .all()
    )

    references = [
        Reference(
            book_name=b.book_name,
            author_name=b.author_name,
            fiqha=b.fiqha,
            rank=b.rank,
            chain=_extract_chain(chunks[0]) if chunks else None,
        )
        for b in books
    ]

    context = "\n\n".join(chunks)
    answer = generate_chat_response(context, payload.message)

    return ChatResponse(response=answer, references=references)