import io
import re
from typing import List, Tuple

def parse_file(contents: bytes, filename: str) -> List[Tuple[str, str]]:
    """
    Parse the manuscript file into chapters.
    Supports .txt, .docx, and .pdf files.
    Returns a list of (chapter_title, chapter_text) tuples.
    """
    ext = filename.split('.')[-1].lower()
    if ext == "txt":
        raw_text = contents.decode("utf-8", errors="ignore")
    elif ext == "docx":
        from docx import Document
        doc = Document(io.BytesIO(contents))
        raw_text = "\n".join(para.text for para in doc.paragraphs)
    elif ext == "pdf":
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(contents))
        pages = [page.extract_text() for page in reader.pages]
        raw_text = "\n".join(filter(None, pages))
    else:
        raise ValueError(f"Unsupported file extension: .{ext}")
    # Split into chapters at lines starting with 'Chapter'
    parts = re.split(r'(?m)(?=^Chapter\b)', raw_text)
    chapters: List[Tuple[str, str]] = []
    for idx, part in enumerate(parts):
        text = part.strip()
        if not text:
            continue
        lines = text.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        chapters.append((title or f"Chapter {idx+1}", body))
    if not chapters:
        chapters = [("Chapter 1", raw_text)]
    return chapters