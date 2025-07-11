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

# Function to extract text from a Django FileField object
def extract_text_from_file(file_field_object):
    """
    Extracts text content from a Django FileField object (e.g., kb.file).
    It handles .txt, .pdf, and .docx files by opening them in binary mode from storage.

    Args:
        file_field_object: A Django FileField instance (e.g., kb.file from a model instance).

    Returns:
        str: The extracted text content, or an error message if unsupported/failed.
    """
    if not file_field_object:
        return "Error: No file object provided."

    file_extension = os.path.splitext(file_field_object.name)[1].lower()
    extracted_text = ""

    try:
        # Use .open('rb') to read from any backend that django-storages supports (GCS, local, etc.).
        with file_field_object.open('rb') as f: # Open the file from storage in binary read mode
            if file_extension == '.txt':
                # For text files, read binary and decode to UTF-8
                extracted_text = f.read().decode('utf-8', errors='ignore')
            elif file_extension == '.pdf':
                if PdfReader: # Check for the 'pypdf' import alias now
                    try:
                        # pypdf.PdfReader can directly read from a file-like object
                        reader = PdfReader(f)
                        for page in reader.pages:
                            page_text = page.extract_text()
                            if page_text:
                                extracted_text += page_text
                    except Exception as e:
                        logger.error(f"Error processing PDF: {file_field_object.name} - {e}", exc_info=True)
                        extracted_text = f"Error: Could not read PDF content. Please ensure pypdf is installed and the file is valid. ({e})"
                else:
                    extracted_text = "Error: pypdf not available. Cannot process PDF files."
            elif file_extension == '.docx':
                if Document: # Check for the 'python-docx' import alias
                    try:
                        document = Document(f) # python-docx Document can take a file-like object
                        extracted_text = "\n".join([paragraph.text for paragraph in document.paragraphs])
                    except Exception as e:
                        logger.error(f"Error processing DOCX: {file_field_object.name} - {e}", exc_info=True)
                        extracted_text = f"Error: Could not read DOCX content. Please ensure python-docx is installed and the file is valid. ({e})"
                else:
                    extracted_text = "Error: python-docx not available. Cannot process DOCX files."
            else:
                extracted_text = f"Error: Unsupported file type: {file_extension}"
    except Exception as e:
        logger.error(f"Error opening or reading file from storage: {file_field_object.name} - {e}", exc_info=True)
        extracted_text = f"Error: Could not access file from storage: {e}"

    return extracted_text.strip() # Strip leading/trailing whitespace from the final text