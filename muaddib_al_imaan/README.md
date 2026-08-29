# Muaddin-al-imaan

A FastAPI-based Islamic fiqh Q&A assistant. Users select their practicing
school of fiqh (Hanafi, Maliki, Hanbali, or Shafi), ask questions, and receive
answers grounded in the books uploaded by an admin — with references to the
top 3 books (ranked by the admin) and any chain of references preserved.

## Features

- **Two-layer UI**
  - **Public**: fiqh selection → chat-only interface (ChatGPT-style).
  - **Admin**: upload books with metadata (Book Name, Author/Imam, Fiqh, Rank)
    and generate embeddings.
- **Fiqh-scoped search**: queries are answered only from the selected fiqh's books.
- **References**: each answer shows the top 3 books (ranked by admin) and the
  full chain of references when present.
- **Storage**: books under `storage/Fiqha/{Hanafi,Maliki,Hanbali,Shafi}`;
  vectors stored in SQLite (`chunks.embedding`) plus a FAISS index per fiqh.
- **Auth**: proper auth module under `app/module/auth` (session cookie).

## Project structure

```
muaddin_al_imaan/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── module/auth/          # auth module
│   ├── services/             # file_reader, embeddings, vector_store, chat
│   └── routers/              # public + admin
├── static/                   # css + js (ChatGPT theme)
├── templates/                # public_select, public_chat, admin
├── storage/                  # Fiqha books, uploads, faiss_data
├── requirements.txt
└── .env
```

## Setup

```bash
cd muaddin_al_imaan
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000 for the public interface and
http://localhost:8000/admin for the admin panel.

Default admin credentials (override via `.env`):
- username: `admin`
- password: `admin123`

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Fiqh selection |
| GET | `/chat/{fiqha}` | Chat UI for a fiqh |
| POST | `/api/chat` | Query + answer with references |
| GET | `/admin` | Admin panel |
| POST | `/auth/login` | Admin login |
| POST | `/auth/logout` | Admin logout |
| POST | `/admin/upload` | Upload book + metadata |
| POST | `/admin/embed/{book_id}` | Generate embeddings |
| GET | `/admin/books` | List books |