import os
import docx2txt
import PyPDF2
import csv

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

    elif ext == '.docx':
        text = docx2txt.process(file_path)

    elif ext == '.pdf':
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

    else:
        raise ValueError("Unsupported file type.")
    
    return text
