# core/utils/file_reader.py

import os
# Libraries for different file types
try:
    import PyPDF2 # For PDF processing
except ImportError:
    PyPDF2 = None
    print("Warning: PyPDF2 not installed. PDF files will not be processed.")

try:
    from docx import Document # For DOCX processing (Note: docx2txt is replaced by python-docx's Document for file-like objects)
except ImportError:
    Document = None
    print("Warning: python-docx not installed. DOCX files will not be processed.")

# Remove import csv if you don't use it or handle CSVs

# Change function signature: it expects a Django FileField object now
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

    # Get file extension from the file's name property
    file_extension = os.path.splitext(file_field_object.name)[1].lower()
    extracted_text = ""

    # Using .open('rb') allows reading from any backend that django-storages supports (including GCS).
    try:
        with file_field_object.open('rb') as f: # Open the file from cloud storage in binary read mode
            if file_extension == '.txt':
                # For text files, read binary and decode to UTF-8
                extracted_text = f.read().decode('utf-8', errors='ignore')
            elif file_extension == '.pdf':
                if PyPDF2:
                    try:
                        # PyPDF2.PdfReader can directly read from a file-like object
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            page_text = page.extract_text()
                            if page_text:
                                extracted_text += page_text
                    except Exception as e:
                        print(f"Error processing PDF: {file_field_object.name} - {e}")
                        extracted_text = f"Error: Could not read PDF content. Please ensure PyPDF2 is installed and the file is valid. ({e})"
                else:
                    extracted_text = "Error: PyPDF2 not available. Cannot process PDF files."
            elif file_extension == '.docx':
                # For DOCX, you typically use python-docx's Document(file_like_object)
                # docx2txt often expects a filesystem path directly.
                if Document:
                    try:
                        document = Document(f) # python-docx Document can take a file-like object
                        extracted_text = "\n".join([paragraph.text for paragraph in document.paragraphs])
                    except Exception as e:
                        print(f"Error processing DOCX: {file_field_object.name} - {e}")
                        extracted_text = f"Error: Could not read DOCX content. Please ensure python-docx is installed and the file is valid. ({e})"
                else:
                    extracted_text = "Error: python-docx not available. Cannot process DOCX files."
            else:
                extracted_text = f"Error: Unsupported file type: {file_extension}"
    except Exception as e:
        print(f"Error opening or reading file from storage: {file_field_object.name} - {e}")
        extracted_text = f"Error: Could not access file from storage: {e}"

    return extracted_text