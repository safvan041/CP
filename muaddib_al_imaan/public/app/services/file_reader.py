"""Streaming text extraction from uploaded files (.txt, .pdf, .docx)."""
import logging
import os

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None
    logger.warning("pypdf not installed. PDF files will not be processed.")

try:
    from docx import Document
except ImportError:
    Document = None
    logger.warning("python-docx not installed. DOCX files will not be processed.")

from app.config import CHUNK_OVERLAP, CHUNK_SIZE


def iter_text_chunks(file_path, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Yield overlapping text chunks from a file path.

    Args:
        file_path: Path to the uploaded file.
        chunk_size: Maximum characters per chunk.
        overlap: Number of overlapping characters between chunks.

    Yields:
        str: Overlapping text chunks suitable for embedding.
    """
    if overlap >= chunk_size:
        raise ValueError("Chunk overlap must be smaller than chunk size.")

    file_extension = os.path.splitext(str(file_path))[1].lower()

    with open(file_path, "rb") as file_handle:
        if file_extension == ".txt":
            buffer = ""
            for raw_bytes in iter(lambda: file_handle.read(1024 * 1024), b""):
                buffer += raw_bytes.decode("utf-8", errors="ignore")
                while len(buffer) >= chunk_size:
                    yield buffer[:chunk_size].strip()
                    buffer = buffer[chunk_size - overlap:]
            if buffer.strip():
                yield buffer.strip()

        elif file_extension == ".pdf":
            if not PdfReader:
                raise ValueError("pypdf is not available. Cannot process PDF files.")
            reader = PdfReader(file_handle)
            buffer = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    buffer += page_text + "\n"
                    while len(buffer) >= chunk_size:
                        yield buffer[:chunk_size].strip()
                        buffer = buffer[chunk_size - overlap:]
            if buffer.strip():
                yield buffer.strip()

        elif file_extension == ".docx":
            if not Document:
                raise ValueError(
                    "python-docx is not available. Cannot process DOCX files."
                )
            document = Document(file_handle)
            buffer = ""
            for paragraph in document.paragraphs:
                buffer += paragraph.text + "\n"
                while len(buffer) >= chunk_size:
                    yield buffer[:chunk_size].strip()
                    buffer = buffer[chunk_size - overlap:]
            if buffer.strip():
                yield buffer.strip()

        else:
            raise ValueError(f"Unsupported file type: {file_extension}")


def extract_text_from_file(file_path):
    return "\n".join(iter_text_chunks(file_path))