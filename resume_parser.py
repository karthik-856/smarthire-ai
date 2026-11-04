"""Local parsers for TXT, PDF, and DOCX resumes."""
from dataclasses import dataclass, field
from io import BytesIO
import re
from pathlib import Path
from config import MAX_UPLOAD_BYTES
from preprocessing import normalize_text
from skills import extract_skills

@dataclass
class ParsedResume:
    text: str
    name: str | None
    email: str | None
    phone: str | None
    skills: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

class ResumeParseError(ValueError):
    pass

def extract_document_text(filename: str, content: bytes, max_bytes: int = MAX_UPLOAD_BYTES) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in {".txt", ".pdf", ".docx"}:
        raise ResumeParseError("Unsupported file type. Upload PDF, DOCX, or TXT.")
    if len(content) > max_bytes:
        raise ResumeParseError(f"File exceeds the {max_bytes // (1024 * 1024)} MB upload limit.")
    if not content:
        raise ResumeParseError("The uploaded document is empty.")
    try:
        if ext == ".txt":
            text = content.decode("utf-8-sig", errors="replace")
        elif ext == ".pdf":
            from pypdf import PdfReader
            pages = PdfReader(BytesIO(content)).pages
            text = "\n".join(page.extract_text() or "" for page in pages)
        else:
            from docx import Document
            doc = Document(BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)
            text += "\n" + "\n".join(" | ".join(c.text for c in row.cells) for table in doc.tables for row in table.rows)
    except ImportError as exc:
        raise ResumeParseError(f"Parser dependency unavailable for {ext.upper()}; install requirements.txt.") from exc
    except Exception as exc:
        raise ResumeParseError(f"Could not read this {ext[1:].upper()} document: {exc}") from exc
    text = text.replace("\x00", " ").replace("\u00a0", " ").strip()
    if not normalize_text(text):
        if ext == ".pdf":
            raise ResumeParseError("No selectable text could be extracted. This may be a scanned PDF; OCR is not implemented.")
        raise ResumeParseError("No text could be extracted from this document.")
    return text


def parse_resume(filename: str, content: bytes, max_bytes: int = MAX_UPLOAD_BYTES) -> ParsedResume:
    warnings = []
    text = extract_document_text(filename, content, max_bytes)
    if Path(filename).suffix.lower() == ".pdf" and not normalize_text(text):
        warnings.append("No selectable text was found. Scanned PDFs are not OCR-processed.")
    # Preserve paragraph boundaries so evidence retrieval can cite a focused
    # resume passage instead of flattening the entire document into one chunk.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    phone_match = re.search(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)", text)
    name = next((line for line in lines[:5] if len(line) < 80 and not re.search(r"@|resume|curriculum vitae", line, re.I)), None)
    section_patterns = {
        "education": r"\b(?:education|academic background|qualifications)\b",
        "projects": r"\b(?:projects|selected work|portfolio)\b",
        "experience": r"\b(?:experience|employment|internship)\b",
    }
    result_sections = {}
    for key, pattern in section_patterns.items():
        result_sections[key] = [line for line in lines if re.search(pattern, line, re.I)]
    return ParsedResume(text, name, email_match.group(0) if email_match else None,
                        phone_match.group(0) if phone_match else None,
                        extract_skills(text), result_sections["education"], result_sections["projects"],
                        result_sections["experience"], warnings)
