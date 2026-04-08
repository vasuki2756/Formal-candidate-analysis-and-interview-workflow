import logging
import re
from typing import BinaryIO

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Preprocessing: Clean and normalize text"""
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?@\-]', '', text)
    text = text.strip()
    
    return text


def extract_text_from_file(file: BinaryIO, filename: str) -> str:
    ext = filename.lower().split('.')[-1]
    
    if ext == 'pdf':
        return _extract_pdf(file)
    elif ext in ['doc', 'docx']:
        return _extract_docx(file)
    elif ext == 'txt':
        return _extract_txt(file)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf(file: BinaryIO) -> str:
    try:
        from pypdf import PdfReader
        file.seek(0)
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return clean_text(text)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise ValueError(f"Failed to read PDF: {str(e)}")


def _extract_docx(file: BinaryIO) -> str:
    try:
        import docx
        file.seek(0)
        content = file.read()
        import io
        doc = docx.Document(io.BytesIO(content))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return clean_text(text)
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise ValueError(f"Failed to read DOCX: {str(e)}")


def _extract_txt(file: BinaryIO) -> str:
    file.seek(0)
    content = file.read().decode('utf-8', errors='ignore')
    return clean_text(content)