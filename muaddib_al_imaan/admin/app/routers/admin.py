"""Admin routes: login, upload, embed, and book listing."""
import os
import shutil
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import FIQH_SCHOOLS, MAX_UPLOAD_SIZE, UPLOAD_DIR
from app.database import get_db
from app.models import Book
from app.module.auth import (
    authenticate,
    create_session_token,
    get_current_admin,
)
from app.schemas import BookOut
from public.app.services.embeddings import get_embedding_model
from public.app.services.file_reader import iter_text_chunks
from public.app.services.vector_store import embed_and_store

router = APIRouter()
templates = Jinja2Templates(directory="admin/templates")


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(
        "admin.html", {"request": request, "fiqhas": FIQH_SCHOOLS}
    )


@router.post("/auth/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if not authenticate(db, username, password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_session_token(username)
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie("muaddin_session", token, httponly=True)
    return response


@router.post("/auth/logout")
def logout():
    response = RedirectResponse(url="/admin", status_code=303)
    response.delete_cookie("muaddin_session")
    return response


@router.post("/admin/upload")
async def upload_book(
    book_name: str = Form(...),
    author_name: str = Form(...),
    fiqha: str = Form(...),
    rank: int = Form(0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    if fiqha not in FIQH_SCHOOLS:
        raise HTTPException(status_code=400, detail="Unknown fiqha")

    os.makedirs(str(UPLOAD_DIR), exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".txt", ".pdf", ".docx"):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(str(UPLOAD_DIR), filename)

    size = 0
    with open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                out.close()
                os.remove(dest)
                raise HTTPException(
                    status_code=413, detail="File exceeds 50MB limit"
                )
            out.write(chunk)

    book = Book(
        book_name=book_name,
        author_name=author_name,
        fiqha=fiqha,
        rank=rank,
        file_path=dest,
        status="pending",
    )
    db.add(book)
    db.commit()
    db.refresh(book)

    return JSONResponse({"id": book.id, "status": book.status})


@router.post("/admin/embed/{book_id}")
def embed_book(
    book_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.status = "processing"
    db.commit()

    try:
        model = get_embedding_model()
        count = embed_and_store(
            db, book, iter_text_chunks(book.file_path), model
        )
        book.status = "completed"
        book.error_message = None
        db.commit()
        return {"id": book.id, "status": "completed", "chunks": count}
    except Exception as e:
        book.status = "failed"
        book.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/books", response_model=list[BookOut])
def list_books(
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    return db.query(Book).order_by(Book.created_at.desc()).all()