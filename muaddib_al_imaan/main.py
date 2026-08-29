"""FastAPI application entry point for Muaddib-al-imaan."""
import logging
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import FIQHA_DIR, STORAGE_ROOT, UPLOAD_DIR, FAISS_DIR
from app.database import Base, SessionLocal, engine
from app.module.auth import ensure_admin_user
from public.app.routers import public
from admin.app.routers import admin

logging.basicConfig(level=logging.INFO)

# Ensure storage directories exist.
for directory in (STORAGE_ROOT, FIQHA_DIR, UPLOAD_DIR, FAISS_DIR):
    os.makedirs(str(directory), exist_ok=True)

# Create tables and seed the default admin user.
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    ensure_admin_user(db)

app = FastAPI(title="Muaddib-al-imaan")

app.mount("/static", StaticFiles(directory="admin/static"), name="static")

app.include_router(public.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}