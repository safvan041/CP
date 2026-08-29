"""SQLAlchemy ORM models for Muaddin-al-imaan."""
import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    book_name = Column(String(255), nullable=False)
    author_name = Column(String(255), nullable=False)
    fiqha = Column(String(50), index=True, nullable=False)
    rank = Column(Integer, default=0, nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    chunks = relationship(
        "Chunk", back_populates="book", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), index=True, nullable=False)
    fiqha = Column(String(50), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(LargeBinary, nullable=False)

    book = relationship("Book", back_populates="chunks")