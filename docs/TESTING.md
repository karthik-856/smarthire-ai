# Testing record

## Automated checks

- `.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp` — **30 passed**, including document parsing, matching formula consistency, focused evidence chunks, evidence-based interview questions, CSV export, resume and job-description uploads, privacy response checks, and regression checks confirming candidate comparison and the recruitment pipeline are removed.
- `node --check static/app.js` — passed.
- `.\.venv\Scripts\python.exe -m compileall -q app.py web_app.py database.py matching_engine.py candidate_assistant.py report_generator.py` — passed.
- `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` — all six declared packages were already installed and satisfied the project version ranges.

The PDF and DOCX parser packages are installed in the project environment. Flask, scikit-learn, pandas, and pytest are available in the active Python environment; all satisfy the versions in `requirements.txt`.

- Decision register integration was exercised in a temporary SQLite database using fictional demo candidates: blank reasons were rejected, a decision was created and updated, rematching preserved the decision, and both audit events were retained. A regression check confirms latest-first ordering when two history events share the same timestamp.

## Document smoke checks

- The provided DOCX job description was submitted through the local `/api/job-description-file` route. The route extracted its role title, suggested department, description, and six required skills.
- The provided PDF resume parsed successfully and its text was matched against that role in memory. The score was **10.4% textual relevance**, with one required skill detected and five not detected. This score is a text comparison only; it is not a hiring probability or decision.
- The resume was not added to the persistent demo database. Personal contact details were not printed in the check output.
- A separate Customer Success role with custom skills (Salesforce, customer service, conflict resolution, Zendesk) and a matching TXT resume produced **100% required-skill coverage**, confirming the workflow is not limited to Talent Acquisition.

## Browser review

The local Flask preview was opened at `http://127.0.0.1:5000/`. The redesigned hiring mark, Jobs & roles navigation, broader job-family examples, and the editable job-description upload area were verified in the browser. The preview remains local and is not deployed.

The interface supports PDF, DOCX, and TXT job descriptions and resumes. Text extraction can miss layout or context, and scanned-PDF OCR is not included. Recruiters must review extracted fields, evidence, and scores themselves.

## Enhancement checks

- Candidate comparison navigation, assistant mode, API route, and comparison CSV export have been removed.
- Interview question generation was checked for an evidence-linked skill already found in the resume and a missing skill explicitly described as unverified.
- Workspace API responses were checked to ensure general page state does not include full resume text, contact details, or content hashes; candidate detail responses return focused matching excerpts rather than the full document.
- Browser preview at `http://127.0.0.1:5000/` showed the refreshed navigation and readable page headings.
- The isolated end-to-end workflow used a temporary project-local SQLite database and synthetic resumes. It exercised job activation, uploads, matching, candidate evidence, assistant responses for one candidate, decision history, and job-filtered CSV reports. **All checks passed; the persistent workspace database was not changed.** Regression tests confirm removed features stay unavailable.

`pip check` reports conflicts from unrelated packages preinstalled in the shared environment (`streamlit`, `numba`, `pyopenssl`, and `spyder`). None are declared by this project's `requirements.txt` or required by the Flask website.
