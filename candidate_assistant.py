"""Evidence-grounded local question answering; no generative model is claimed."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from preprocessing import sentence_chunks, normalize_text
from skills import extract_skills

def retrieve_evidence(question: str, resume_text: str, job_text: str = "", top_k: int = 3) -> list[str]:
    chunks = sentence_chunks(resume_text) + [f"Job requirement: {x}" for x in sentence_chunks(job_text)]
    if not chunks or not normalize_text(question): return []
    try:
        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform([question] + chunks)
        sims = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
        return [chunks[i] for i in sorted(range(len(sims)), key=lambda j: (-sims[j], j))[:top_k] if sims[i] > 0]
    except ValueError: return []

def answer_question(question: str, resume_text: str, job_text: str = "", required_skills=None) -> dict:
    q = normalize_text(question).lower()
    skills = required_skills or []
    # Supporting excerpts must come from the candidate's resume. Job text can
    # guide the rules, but should never be presented as candidate evidence.
    evidence = retrieve_evidence(question, resume_text)
    found = extract_skills(resume_text, skills) if skills else extract_skills(resume_text)
    if any(x in q for x in ("interview", "question")):
        if "behavior" in q:
            focus = skills[:3] or ["the role's stated responsibilities"]
            prompts = [{"question":f"Tell me about a time you had to learn or apply {skill} while working with others. What steps did you take and what was the outcome?","why":f"{skill} is relevant to the selected job; this prompt explores collaboration and learning without assuming prior experience.","evidence":retrieve_evidence(skill,resume_text,top_k=1) if skill in skills else []} for skill in focus]
            prompts.append({"question":"Describe a time priorities changed during a project. How did you decide what to do next and communicate it?","why":"Explores prioritization and communication in a job-related work context.","evidence":[]})
            prompts=prompts[:5]
        else:
            prompts = interview_questions(resume_text, job_text, skills, limit=5)
        answer = "Suggested job-related questions: " + " ".join(f"{i+1}. {item['question']} Why: {item['why']}" for i,item in enumerate(prompts))
    elif "skill" in q:
        answer = "Detected skills: " + (", ".join(found) if found else "No configured skills were detected in the resume text.")
    elif any(x in q for x in ("gap", "missing", "verify", "requirement")):
        missing = [s for s in skills if s.casefold() not in {x.casefold() for x in found}]
        answer = "Potentially unverified required skills: " + (", ".join(missing) if missing else "No configured required skill gaps were detected.")
    else:
        answer = "Relevant resume evidence: " + (" ".join(evidence) if evidence else "I could not find supporting evidence in the available resume or job text.")
    return {"answer": answer, "evidence": evidence, "mode": "Local TF-IDF retrieval and transparent Python rules; no generative LLM is installed."}

def interview_questions(resume_text: str, job_text: str = "", required_skills=None, preferred_skills=None, limit: int = 5) -> list[dict]:
    """Create deterministic interview prompts tied to explicit role/resume evidence."""
    required = list(dict.fromkeys(str(s).strip() for s in (required_skills or []) if str(s).strip()))
    preferred = list(dict.fromkeys(str(s).strip() for s in (preferred_skills or []) if str(s).strip()))
    detected = {s.casefold() for s in extract_skills(resume_text, required + preferred)}
    questions = []
    for skill in required:
        found = skill.casefold() in detected
        if found:
            question = f"The resume mentions {skill}. What was your specific contribution, and how did you validate the result?"
            rationale = f"{skill} is a required role skill and appears in the resume text; confirm depth and ownership."
            evidence = retrieve_evidence(skill, resume_text, top_k=1)
        else:
            question = f"This role requires {skill}. Can you describe your experience with it, or how you would approach a task that uses it?"
            rationale = f"{skill} is required, but matching text was not found. This is unverified evidence, not proof the skill is absent."
            evidence = []
        questions.append({"question":question,"why":rationale,"evidence":evidence})
        if len(questions) >= limit: return questions
    for skill in preferred:
        if skill.casefold() in detected and len(questions) < limit:
            questions.append({"question":f"The resume mentions preferred skill {skill}. How have you applied it in work or a project?","why":f"{skill} is preferred for this role and appears in the resume text.","evidence":retrieve_evidence(skill,resume_text,top_k=1)})
    if len(questions) < limit:
        evidence = retrieve_evidence("project experience responsibilities results", resume_text, top_k=1)
        questions.append({"question":"Describe a project or work example most relevant to this role, your contribution, and the outcome.","why":"Connect the candidate's documented experience to the job description without assuming unlisted experience.","evidence":evidence})
    if len(questions) < limit and job_text:
        questions.append({"question":"Tell me about a time you worked with others to deliver work under competing priorities. What did you do?","why":"A job-related behavioral prompt to explore collaboration and prioritization; assess against the role's stated needs.","evidence":[]})
    return questions[:limit]
