# Architecture and data flow

1. Recruiter uses the local Flask website to save a job description and explicitly configures required/preferred skills.
2. Job descriptions can be entered in the role editor or imported from PDF, DOCX, or TXT. Multiple TXT, PDF, or DOCX resumes can be uploaded in a batch; each file is limited to 10 MB and the whole batch to 250 MB. Parsing happens locally in `resume_parser.py`; invalid, oversized, empty, or unreadable files return a clear error. Candidate content is deduplicated by a SHA-256 hash of extracted text.
3. `matching_engine.py` builds TF-IDF vectors for job and resume, computes cosine similarity, detects configured skill phrases, and combines components using the documented formula.
4. `database.py` persists candidate/job records and current match snapshots. Match refresh does not update recruiter decisions. The general `/api/state` response contains only fields used by the interface; it omits contact details, content hashes, and full resume text. Candidate detail responses provide retrieved evidence excerpts and generated questions rather than returning the parsed resume.
5. Candidate insights retrieve excerpts from resume evidence. `candidate_assistant.py` uses local TF-IDF retrieval and transparent rules; it does not call an LLM.
6. Recruiter decisions and every initial/update event are stored in SQLite. CSV output is generated from the selected job-specific result set.
7. Interview preparation uses deterministic prompts from the role's requirements and retrieved resume text.

The local database defaults to `data/smarthire.db`. Names, email addresses, and phone numbers are never included in matching text features; only resume text is compared with the job description. Resume paragraph boundaries are retained for focused evidence retrieval. This is a local demonstration, not an ATS.

The website entry point is `app.py`; Flask routes and JSON endpoints are in `web_app.py`, with the browser UI in `templates/` and `static/`. Job-description import uses `job_description_parser.py` to populate role fields from labeled sections, detect skills beyond the built-in vocabulary in explicit skill lists, and mark department classifications as suggestions. The server binds to `127.0.0.1` and is intended for local use.
