"""Explainable TF-IDF plus required-skill coverage matching."""
from dataclasses import dataclass, asdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from preprocessing import normalize_text
from skills import extract_skills

@dataclass
class MatchResult:
    similarity: float
    required_coverage: float | None
    score: float
    required_matched: list[str]
    required_missing: list[str]
    preferred_detected: list[str]
    scoring_mode: str
    label: str
    def to_dict(self): return asdict(self)

def _similarity(job_text: str, resume_text: str) -> float:
    job, resume = normalize_text(job_text), normalize_text(resume_text)
    if not job or not resume:
        return 0.0
    try:
        matrix = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit_transform([job, resume])
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0])
    except ValueError:
        return 0.0

def score_candidate(job_text: str, resume_text: str, required_skills=None, preferred_skills=None) -> MatchResult:
    required = list(dict.fromkeys(s.strip() for s in (required_skills or []) if s.strip()))
    preferred = list(dict.fromkeys(s.strip() for s in (preferred_skills or []) if s.strip()))
    present = extract_skills(resume_text, required + preferred) if required or preferred else []
    matched = [s for s in required if s.casefold() in {x.casefold() for x in present}]
    missing = [s for s in required if s.casefold() not in {x.casefold() for x in matched}]
    preferred_found = [s for s in preferred if s.casefold() in {x.casefold() for x in present}]
    sim = _similarity(job_text, resume_text)
    coverage = len(matched) / len(required) if required else None
    score = sim if coverage is None else 0.65 * sim + 0.35 * coverage
    score = min(1.0, max(0.0, score))
    label = "Strong Textual Match" if score >= .65 else "Partial Textual Match" if score >= .35 else "Limited Textual Match"
    return MatchResult(sim, coverage, score, matched, missing, preferred_found,
                       "Text similarity only (no required skills configured)" if coverage is None else "65% text similarity + 35% required skill coverage", label)

def rank_candidates(job_text: str, candidates: list[dict], required_skills=None, preferred_skills=None) -> list[dict]:
    rows = []
    for candidate in candidates:
        result = score_candidate(job_text, candidate.get("text", ""), required_skills, preferred_skills)
        rows.append({**candidate, **result.to_dict()})
    rows.sort(key=lambda c: (-c["score"], str(c.get("id", ""))))
    for i, row in enumerate(rows, 1): row["rank"] = i
    return rows
