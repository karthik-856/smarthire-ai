"""Clearly fictional records for a repeatable local demonstration."""
import hashlib
from config import SAMPLE_JOB_TITLE, SAMPLE_REQUIRED_SKILLS, SAMPLE_PREFERRED_SKILLS
from database import init_db, save_job, save_candidate, set_active_job, list_jobs

SAMPLE_JOB_DESCRIPTION = """Azentio Software is seeking a Talent Acquisition Intern to support recruitment projects involving AI and large language models. The intern will assist with research, candidate communication, talent sourcing, and evaluation of responsible AI tools. Applicants should be able to use Python and SQL, understand NLP and machine learning fundamentals, communicate clearly, and solve problems. Prompt engineering experience is relevant. Qualifications and years of experience are not specified."""
SAMPLE_CANDIDATES = [
    {"name":"Aarav Mehta (Fictional)","resume_text":"Aarav Mehta is a fictional computer science student. Skills include Python, NLP, machine learning, scikit-learn, pandas, SQL, prompt engineering, communication and problem solving. Project: built a resume text classification prototype using TF-IDF and scikit-learn. Education: BSc Computer Science, expected 2027."},
    {"name":"Maya Iyer (Fictional)","resume_text":"Maya Iyer is a fictional software development student with Python, SQL, REST API, FastAPI, JavaScript, HTML, CSS, Git and testing experience. Project: implemented a candidate tracking API and tested endpoints. Education: BTech Information Technology, expected 2027. Interested in clear communication and collaborative problem solving."},
    {"name":"Rohan Das (Fictional)","resume_text":"Rohan Das is a fictional data analytics student. Skills: SQL, Excel, Power BI, data analysis, data visualization and communication. Project: built a dashboard for hiring funnel reporting from synthetic data. Education: BA Economics with analytics coursework, expected 2026. Used Python for introductory data cleaning."},
]

def load_samples(db_path=None):
    init_db(db_path)
    jobs=[j for j in list_jobs(db_path) if j["title"]==SAMPLE_JOB_TITLE]
    if jobs: jid=jobs[0]["id"]
    else:
        jid=save_job({"title":SAMPLE_JOB_TITLE,"department":"Talent Acquisition","description":SAMPLE_JOB_DESCRIPTION,"required_skills":SAMPLE_REQUIRED_SKILLS,"preferred_skills":SAMPLE_PREFERRED_SKILLS,"qualifications":"Not specified in the sample description.","experience":"Not specified in the sample description.","active":True},db_path)
    set_active_job(jid,db_path)
    for c in SAMPLE_CANDIDATES:
        text=c["resume_text"]
        save_candidate({**c,"source":"fictional sample","content_hash":hashlib.sha256(text.encode()).hexdigest(),"skills":[],"warnings":["Fictional demonstration profile; not a real applicant."]},db_path)
    return jid
