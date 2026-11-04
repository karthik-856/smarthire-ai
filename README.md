# SmartHire AI

SmartHire AI is a local Flask hiring workspace for recruiter-led resume screening across departments and job families. It matches resume text with a role description, surfaces skill evidence and potential gaps, and records human recruiter decisions. It is a demonstration prototype, not a production applicant tracking system. The website runs on your computer and is not deployed to Streamlit or a hosting service.

## Features

- Create and edit any number of roles across departments, with required and preferred skills, or import a PDF, DOCX, or TXT file. Uploading a job description fills its title, department, skills, qualifications, experience, and description fields wherever those details appear; extracted suggestions remain editable.
- Upload multiple TXT, PDF, and DOCX resumes in a batch; each file can be up to 10 MB and a batch up to 250 MB. There is no fixed candidate-count or job-role count. Scanned PDFs are reported because OCR is not implemented.
- Match each resume to a selected job with scikit-learn TF-IDF and cosine similarity plus configurable vocabulary-based skill coverage.
- Rank candidates deterministically with visible relevance meters; inspect evidence, warnings, and potential gaps.
- Ask scoped questions about one selected candidate and role through a recruiter assistant that keeps the conversation, cites resume-only excerpts, and uses local TF-IDF retrieval and transparent Python rules; no paid API or generative LLM is used.
- Keep parsed resume text and contact details on the server side of the local app; the general workspace response sends only the profile fields needed by the visible pages. Evidence views return focused excerpts for recruiter review.
- Prepare deterministic, role-specific interview questions grounded in resume evidence and requirements to verify; copy or export the set as TXT.
- Record Shortlisted, Review Required, or Not Selected decisions with reasons and a change history.
- Export ranking, skill gaps, evidence-based candidate summaries, and decisions as UTF-8 CSV.
- Load three clearly fictional sample candidates and a sample job idempotently.

## Run the website

Python 3.10 or newer is recommended. From this folder, run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000). Stop the local server with Ctrl+C. This starts the website only on your own computer; no deployment step is included. The SQLite database is stored in `data/smarthire.db` by default. Set `SMARTHIRE_DB_PATH` to change its location.

## Architecture

`app.py` starts the Flask website in `web_app.py`. The browser interface is in `templates/` and `static/`. The web routes call the resume parser (`resume_parser.py`), matching engine (`matching_engine.py`), local assistant (`candidate_assistant.py`), report functions (`report_generator.py`), and SQLite persistence layer (`database.py`). See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Matching formula

When required skills are configured:

`overall relevance = 0.65 × TF-IDF cosine similarity + 0.35 × required skill coverage`

Required coverage is the fraction of listed required skills found in resume text. Without configured required skills, the score is text similarity alone and coverage is unavailable. Preferred skills are displayed separately. Scores describe textual relevance, not probability of hiring or candidate worth.

Candidate Insights shows the score components and weighted contribution. A missing skill phrase means the resume does not provide matching text; it is not proof the candidate lacks that skill. Recruiters record and explain decisions in the Decision Register.

## Example workflow

Start the website, select **Load fictional demo data**, open **Resume Screening**, and run matching for the active sample job. Review candidate evidence in **Candidate Insights**, prepare interview questions, ask the **Recruiter Assistant** about one candidate and role, record a job-related decision, then download reports.

## Privacy and responsible use

Documents are processed locally and are not sent to external services. Names and contact details are excluded from matching features. The prototype does not infer sensitive traits or automate hiring decisions. Resume content is treated as untrusted data. Human review is required.

## Limitations

Text extraction can miss layout or context; scanned PDF OCR, authentication, access control, retention policies, production monitoring, advanced skill synonym handling, candidate comparison, a recruitment pipeline, and validated hiring-specific evaluation are out of scope. Candidate comparison and the recruitment pipeline were removed from this requested website scope. Do not use real applicant data without appropriate privacy and security controls.

## Verification

See [docs/TESTING.md](docs/TESTING.md) for executed tests and [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for a walkthrough of the local website.
