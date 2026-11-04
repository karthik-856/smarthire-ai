"""Conservative text cleanup for matching and evidence extraction."""
import re

def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.replace("\x00", " ").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()

def sentence_chunks(text: str) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    text = text.replace("\x00", " ").replace("\u00a0", " ")
    chunks = []
    for line in text.splitlines():
        for part in re.split(r"(?<=[.!?])\s+", line):
            normalized = normalize_text(part)
            if normalized:
                chunks.append(normalized)
    return chunks
