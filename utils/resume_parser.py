import os
import re

import docx2txt
import pdfplumber


ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def is_allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def extract_text(file_path: str) -> str:
    _, ext = os.path.splitext(file_path.lower())
    if ext == ".pdf":
        return _extract_pdf_text(file_path)
    if ext == ".docx":
        return _extract_docx_text(file_path)
    raise ValueError("Unsupported file type")


def _extract_pdf_text(file_path: str) -> str:
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return clean_text("\n".join(text_parts))


def _extract_docx_text(file_path: str) -> str:
    text = docx2txt.process(file_path) or ""
    return clean_text(text)


def clean_text(text: str) -> str:
    # Preserve line breaks for section detection; normalize spaces within lines.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)

