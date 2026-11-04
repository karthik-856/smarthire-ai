"""Configurable, boundary-safe skill detection."""
import re
from config import SKILL_VOCABULARY
from preprocessing import normalize_text

def extract_skills(text: str, vocabulary=None) -> list[str]:
    source = normalize_text(text)
    found = []
    for skill in (vocabulary or SKILL_VOCABULARY):
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        if re.search(pattern, source, flags=re.IGNORECASE):
            found.append(skill)
    return found
