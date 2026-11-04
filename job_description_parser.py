"""Conservative, local extraction of common job-description fields."""
import re
from pathlib import Path

from skills import extract_skills


_HEADINGS = {
    "required": r"required\s+(?:skills|competencies|qualifications)|must[- ]have(?:\s+skills)?|core\s+(?:skills|competencies)|technical\s+skills|requirements",
    "preferred": r"preferred\s+(?:skills|qualifications)?|nice\s+to\s+have|desirable\s+skills?|bonus\s+skills?",
    "qualifications": r"minimum\s+qualifications?|education(?:al)?\s+requirements?|education|certifications?|qualifications",
    "experience": r"experience(?:\s+requirements?)?|years\s+of\s+experience",
    "department": r"department|team|business\s+unit|function",
    "responsibilities": r"key\s+responsibilities|responsibilities|what\s+you(?:'ll|\s+will)\s+do",
    "about": r"about\s+(?:the\s+)?(?:role|job|position)|role\s+overview|job\s+overview",
}
_ANY_HEADING = re.compile(
    r"^\s*(?:" + "|".join(f"(?:{pattern})" for pattern in _HEADINGS.values()) + r")\s*(?::|[-–—])?\s*(.*)$",
    re.I,
)


def _clean_lines(text: str) -> list[str]:
    lines = []
    for line in text.replace("\r", "\n").split("\n"):
        line = re.sub(r"^\s*[•●▪◦*\-]+\s*", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return lines


def _field_section(lines: list[str], pattern: str) -> str:
    values = []
    collecting = False
    for line in lines:
        match = _ANY_HEADING.match(line)
        if match:
            heading = line.split(":", 1)[0].split("–", 1)[0].strip()
            collecting = bool(re.fullmatch(pattern, heading, re.I))
            inline_value = match.group(1).strip()
            if collecting and inline_value:
                values.append(inline_value)
            continue
        if collecting:
            values.append(line)
    return ", ".join(values).strip()


def _skills_from_section(section: str) -> list[str]:
    known = extract_skills(section)
    found = list(known)
    seen = {skill.casefold() for skill in found}
    for part in re.split(r"[,;|]+", section.replace(" and ", ", ").replace("; and ", ", ")):
        candidate = re.sub(r"^(?:and|or)\s+", "", part.strip(), flags=re.I)
        candidate = re.sub(r"^(?:proficiency\s+in|proficient\s+in|experience\s+with|knowledge\s+of|ability\s+to\s+use|strong|excellent|good)\s+", "", candidate, flags=re.I)
        candidate = candidate.strip(" .:–—-\t")
        words = candidate.split()
        if not candidate or len(candidate) > 65 or len(words) > 5 or re.search(r"[.!?\d]", candidate):
            continue
        if extract_skills(candidate):
            continue
        if candidate.casefold() not in seen:
            found.append(candidate)
            seen.add(candidate.casefold())
    return found


def _label_value(lines: list[str], pattern: str) -> str:
    expression = re.compile(r"^\s*(?:" + pattern + r")\s*[:\-–—]\s*(.+?)\s*$", re.I)
    for line in lines[:18]:
        match = expression.match(line)
        if match:
            return match.group(1).strip()
    return ""


def _suggest_department(text: str) -> str:
    source = text.casefold()
    groups = [
        ("People & Talent", ("talent acquisition", "recruitment", "human resources", " hr ", "people operations")),
        ("Healthcare & Clinical", ("healthcare", "clinical", "patient care", "nurse", "physician")),
        ("Education", ("teacher", "educator", "faculty", "instructor", "curriculum")),
        ("Legal & Compliance", ("legal counsel", "compliance", "paralegal", "attorney")),
        ("Customer Support", ("customer support", "customer service", "customer success", "help desk")),
        ("IT & Systems", ("it support", "systems administrator", "network administrator", "cybersecurity", "cloud engineer")),
        ("Data & Analytics", ("data analyst", "data scientist", "analytics", "business intelligence", "machine learning")),
        ("Software Engineering", ("software engineer", "software developer", "engineering", "backend", "frontend", "devops")),
        ("Product & Design", ("product manager", "product design", "ux designer", "user experience")),
        ("Marketing & Communications", ("marketing", "communications", "content strategy", "brand manager")),
        ("Finance", ("finance", "accounting", "financial analyst", "payroll")),
        ("Sales", ("sales representative", "account executive", "business development")),
        ("Operations", ("operations", "supply chain", "logistics")),
    ]
    padded = f" {source} "
    for department, signals in groups:
        if any(signal in padded for signal in signals):
            return f"{department} (suggested)"
    return ""


def parse_job_description(text: str, filename: str) -> dict:
    """Return editable role fields; only infer a department when its context is clear."""
    lines = _clean_lines(text)
    title = _label_value(lines, r"job\s+title|position\s+title|role\s+title|position|role")
    if not title:
        first = next((line for line in lines[:5] if line.casefold() not in {"job description", "job posting", "position description"}), "")
        title = first if len(first) <= 100 else ""
    if not title:
        title = Path(filename).stem.replace("_", " ").replace("-", " ").strip()

    department = _label_value(lines, r"department|team|business\s+unit|function")
    if not department:
        department = _suggest_department(f"{title} {' '.join(lines)}")

    required_text = _field_section(lines, _HEADINGS["required"])
    preferred_text = _field_section(lines, _HEADINGS["preferred"])
    # Some documents use a standalone "Skills" section without marking each item required.
    if not required_text:
        required_text = _field_section(lines, r"skills|competencies|technical\s+skills")
    required_skills = _skills_from_section(required_text) if required_text else extract_skills(" ".join(lines))
    preferred_skills = _skills_from_section(preferred_text) if preferred_text else []
    preferred_set = {skill.casefold() for skill in preferred_skills}
    required_skills = [skill for skill in required_skills if skill.casefold() not in preferred_set]

    qualifications = _field_section(lines, _HEADINGS["qualifications"])
    if not qualifications:
        qualifications = " ".join(
            line for line in lines
            if re.search(r"\b(?:bachelor|master|degree|diploma|certification|graduate|education)\b", line, re.I)
        )
    experience = _field_section(lines, _HEADINGS["experience"])
    if not experience:
        experience = " ".join(
            line for line in lines
            if re.search(r"\b(?:\d+\+?\s+years?|entry[- ]level|internship|intern)\b", line, re.I)
        )

    return {
        "title": title,
        "department": department,
        "description": text.strip(),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "qualifications": qualifications,
        "experience": experience,
    }
