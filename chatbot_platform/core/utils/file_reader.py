# core/utils/file_reader.py

import os
import logging # Import the logging module

logger = logging.getLogger(__name__) # Get a logger instance for this module

# Libraries for different file types
try:
    # Prefer 'pypdf' over 'PyPDF2' as it's the actively maintained fork
    from pypdf import PdfReader 
except ImportError:
    PdfReader = None
    logger.warning("pypdf not installed. PDF files will not be processed.")

try:
    from docx import Document # For DOCX processing
except ImportError:
    Document = None
    logger.warning("python-docx not installed. DOCX files will not be processed.")

CHUNK_SIZE = 4000
CHUNK_OVERLAP = 400


def iter_text_chunks(file_field_object, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Extracts text content from a Django FileField object (e.g., kb.file).
    It handles .txt, .pdf, and .docx files by opening them in binary mode from storage.

    Args:
        file_field_object: A Django FileField instance (e.g., kb.file from a model instance).

    Yields:
        str: Overlapping text chunks suitable for embedding.
    """
    if not file_field_object:
        return "Error: No file object provided."

    file_extension = os.path.splitext(file_field_object.name)[1].lower()
    if overlap >= chunk_size:
        raise ValueError("Chunk overlap must be smaller than chunk size.")

    try:
        with file_field_object.open('rb') as file_handle:
            if file_extension == '.txt':
                buffer = ""
                for raw_bytes in iter(lambda: file_handle.read(1024 * 1024), b''):
                    buffer += raw_bytes.decode('utf-8', errors='ignore')
                    while len(buffer) >= chunk_size:
                        yield buffer[:chunk_size].strip()
                        buffer = buffer[chunk_size - overlap:]
                if buffer.strip():
                    yield buffer.strip()
            elif file_extension == '.pdf':
                if PdfReader:
                    try:
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
                    except Exception as e:
                        logger.error(f"Error processing PDF: {file_field_object.name} - {e}", exc_info=True)
                        raise ValueError(f"Could not read PDF content: {e}") from e
                else:
                    raise ValueError("pypdf is not available. Cannot process PDF files.")
            elif file_extension == '.docx':
                if Document:
                    try:
                        document = Document(file_handle)
                        buffer = ""
                        for paragraph in document.paragraphs:
                            buffer += paragraph.text + "\n"
                            while len(buffer) >= chunk_size:
                                yield buffer[:chunk_size].strip()
                                buffer = buffer[chunk_size - overlap:]
                        if buffer.strip():
                            yield buffer.strip()
                    except Exception as e:
                        logger.error(f"Error processing DOCX: {file_field_object.name} - {e}", exc_info=True)
                        raise ValueError(f"Could not read DOCX content: {e}") from e
                else:
                    raise ValueError("python-docx is not available. Cannot process DOCX files.")
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
    except Exception as e:
        logger.error(f"Error opening or reading file from storage: {file_field_object.name} - {e}", exc_info=True)
        raise ValueError(f"Could not access file from storage: {e}") from e


def extract_text_from_file(file_field_object):
    return "\n".join(iter_text_chunks(file_field_object))