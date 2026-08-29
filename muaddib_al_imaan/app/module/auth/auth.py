"""Authentication module for Muaddin-al-imaan.

Provides password hashing, session-based login/logout, and a FastAPI
dependency that protects admin routes.
"""
import hashlib
import hmac
import secrets
import time

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...config import ADMIN_PASSWORD, ADMIN_USERNAME, SECRET_KEY
from ...database import get_db
from ...models import AdminUser


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()
    return hmac.compare_digest(candidate, digest)


def _sign(value: str) -> str:
    return hmac.new(
        SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def create_session_token(username: str) -> str:
    payload = f"{username}:{int(time.time())}"
    return f"{payload}.{_sign(payload)}"


def verify_session_token(token: str) -> bool:
    try:
        payload, signature = token.rsplit(".", 1)
    except ValueError:
        return False
    if not hmac.compare_digest(signature, _sign(payload)):
        return False
    username, ts = payload.rsplit(":", 1)
    # Sessions valid for 24 hours.
    return time.time() - int(ts) < 86_400


def ensure_admin_user(db: Session) -> None:
    """Create the default admin user if none exists."""
    if db.query(AdminUser).filter_by(username=ADMIN_USERNAME).first():
        return
    db.add(
        AdminUser(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
        )
    )
    db.commit()


def authenticate(db: Session, username: str, password: str) -> bool:
    user = db.query(AdminUser).filter_by(username=username).first()
    if not user:
        return False
    return verify_password(password, user.password_hash)


def get_current_admin(
    request: Request, db: Session = Depends(get_db)
) -> str:
    """Dependency that requires a valid admin session cookie."""
    token = request.cookies.get("muaddin_session")
    if not token or not verify_session_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return token.rsplit(".", 1)[0].rsplit(":", 1)[0]