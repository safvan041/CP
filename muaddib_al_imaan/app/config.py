"""Application configuration loaded from environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (parent of app/).
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# --- NVIDIA API configuration ---
NVIDIA_API_KEY = _env("NVIDIA_API_KEY")
NVIDIA_BASE_URL = _env("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_CHAT_MODEL = _env("NVIDIA_CHAT_MODEL", "openai/gpt-oss-20b")

NVIDIA_EMBEDDING_API_KEY = _env("NVIDIA_EMBEDDING_API_KEY", NVIDIA_API_KEY)
NVIDIA_EMBEDDING_BASE_URL = _env("NVIDIA_EMBEDDING_BASE_URL", NVIDIA_BASE_URL)
NVIDIA_EMBEDDING_MODEL = _env(
    "NVIDIA_EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b"
)

# --- Storage ---
STORAGE_ROOT = Path(_env("STORAGE_ROOT", str(BASE_DIR / "storage")))
FIQHA_DIR = STORAGE_ROOT / "Fiqha"
UPLOAD_DIR = STORAGE_ROOT / "uploads"
FAISS_DIR = STORAGE_ROOT / "faiss_data"

# The four supported schools of fiqh.
FIQH_SCHOOLS = ["Hanafi", "Maliki", "Hanbali", "Shafi"]

# --- Database ---
DATABASE_URL = _env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'muaddin.db'}")

# --- Auth ---
SECRET_KEY = _env("SECRET_KEY", "change-me-in-production")
SESSION_COOKIE_NAME = "muaddin_session"
ADMIN_USERNAME = _env("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "admin123")

# --- Limits ---
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
CHUNK_SIZE = 4000
CHUNK_OVERLAP = 400
EMBEDDING_BATCH_SIZE = 8
TOP_K = 5
TOP_BOOKS = 3