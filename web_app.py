"""Local Flask website for SmartHire AI (no Streamlit or hosted deployment)."""
import hashlib
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file, abort
from config import MAX_UPLOAD_BYTES, MAX_UPLOAD_BATCH_BYTES, MAX_UPLOAD_MB
from database import (init_db, list_jobs, list_candidates, set_active_job, save_job,
                      save_candidate, save_matches, get_matches, save_decision,
                      list_decisions, decision_history, dashboard_data, delete_all_records)
from resume_parser import extract_document_text, parse_resume, ResumeParseError
from job_description_parser import parse_job_description
from matching_engine import rank_candidates
from candidate_assistant import answer_question, retrieve_evidence, interview_questions
from report_generator import ranking_csv, skill_gaps_csv, decisions_csv, candidate_summaries_csv
from sample_data import load_samples

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BATCH_BYTES
init_db()

def _active_job(jobs=None):
    jobs = jobs if jobs is not None else list_jobs()
    return next((job for job in jobs if job["active"]), jobs[0] if jobs else None)

def _ranked_rows(job):
    if not job: return []
    saved = get_matches(job["id"])
    if saved:
        rows = saved
        for r in rows:
            r["id"] = r["candidate_id"]
            r["required_coverage"] = r["coverage"]
    else:
        rows = rank_candidates(job["description"], [{"id":c["id"],"name":c["name"],"text":c["resume_text"]} for c in list_candidates()], job["required_skills"], job["preferred_skills"])
    decisions = {d["candidate_id"]: d["decision"] for d in list_decisions(job["id"])}
    for index, row in enumerate(rows, 1):
        row["rank"] = index
        row["decision"] = decisions.get(row["id"], "Not recorded")
        row["text"] = row.get("resume_text", row.get("text", ""))
    return rows

def _state():
    jobs = list_jobs(); candidates = list_candidates(); job = _active_job(jobs)
    rows = _ranked_rows(job)
    decisions = list_decisions()
    counts = dashboard_data()
    scores = [r["score"] for r in rows]
    public_candidates = [{"id": c["id"], "name": c["name"], "warnings": c.get("warnings", [])}
                         for c in candidates]
    row_fields = ("id", "name", "score", "similarity", "required_coverage", "required_matched",
                  "required_missing", "preferred_detected", "scoring_mode", "label", "rank", "decision")
    public_rows = [{key: row.get(key) for key in row_fields} for row in rows]
    return {"jobs":jobs,"active_job":job,"candidates":public_candidates,"rows":public_rows,
            "decisions":decisions,"history":decision_history(),"counts":counts,
            "average_score":sum(scores)/len(scores) if scores else None,
            "max_upload_mb":MAX_UPLOAD_MB}

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/state")
def state(): return jsonify(_state())

@app.post("/api/samples")
def samples():
    job_id = load_samples()
    job = next(j for j in list_jobs() if j["id"] == job_id)
    rows = rank_candidates(job["description"], [{"id":c["id"],"name":c["name"],"text":c["resume_text"]} for c in list_candidates()], job["required_skills"], job["preferred_skills"])
    save_matches(job_id, rows)
    return jsonify({"message":"Sample job and three fictional candidates are ready.","state":_state()})

@app.post("/api/jobs")
def create_or_update_job():
    data = request.get_json(force=True)
    if not str(data.get("title", "")).strip() or not str(data.get("description", "")).strip():
        return jsonify(error="Job title and full description are required."), 400
    data["title"] = data["title"].strip(); data["description"] = data["description"].strip()
    data["required_skills"] = [s.strip() for s in data.get("required_skills", []) if s.strip()]
    data["preferred_skills"] = [s.strip() for s in data.get("preferred_skills", []) if s.strip()]
    job_id = save_job(data)
    return jsonify({"message":"Job description saved.","job_id":job_id,"state":_state()})

@app.post("/api/job-description-file")
def parse_job_description_file():
    uploaded = request.files.get("job_description")
    if not uploaded or not uploaded.filename:
        return jsonify(error="Choose a PDF, DOCX, or TXT job-description file."), 400
    content = uploaded.read(MAX_UPLOAD_BYTES + 1)
    try:
        text = extract_document_text(uploaded.filename, content)
    except ResumeParseError as exc:
        return jsonify(error=str(exc)), 400
    fields = parse_job_description(text, uploaded.filename)
    return jsonify({"filename": Path(uploaded.filename).name, **fields})

@app.post("/api/jobs/<job_id>/active")
def activate_job(job_id):
    if not any(j["id"] == job_id for j in list_jobs()): abort(404)
    set_active_job(job_id)
    return jsonify({"message":"Active job changed.","state":_state()})

@app.post("/api/upload")
def upload_resumes():
    files = request.files.getlist("resumes")
    if not files: return jsonify(error="Choose one or more PDF, DOCX, or TXT resumes."), 400
    outcomes=[]
    known = {c["content_hash"] for c in list_candidates()}
    for file in files:
        if not file.filename: continue
        content = file.read(MAX_UPLOAD_BYTES + 1)
        try:
            parsed = parse_resume(file.filename, content)
            digest = hashlib.sha256(parsed.text.encode()).hexdigest()
            duplicate = digest in known
            cid = save_candidate({"name":parsed.name or Path(file.filename).stem[:80],"email":parsed.email,"phone":parsed.phone,"source":Path(file.filename).name,"content_hash":digest,"resume_text":parsed.text,"skills":parsed.skills,"education":parsed.education,"projects":parsed.projects,"experience":parsed.experience,"warnings":parsed.warnings})
            known.add(digest)
            outcomes.append({"filename":Path(file.filename).name,"candidate_id":cid,"status":"Duplicate already saved" if duplicate else "Parsed and saved","warnings":parsed.warnings})
        except ResumeParseError as exc:
            outcomes.append({"filename":Path(file.filename).name,"status":"Error","error":str(exc)})
    return jsonify({"outcomes":outcomes,"state":_state()})

@app.post("/api/match")
def match():
    jobs=list_jobs(); requested=(request.get_json(silent=True) or {}).get("job_id")
    job=next((j for j in jobs if j["id"] == requested),None) if requested else _active_job(jobs)
    if not job: return jsonify(error="Save or load a job before matching candidates."), 400
    candidates=list_candidates()
    rows=rank_candidates(job["description"],[{"id":c["id"],"name":c["name"],"text":c["resume_text"]} for c in candidates],job["required_skills"],job["preferred_skills"])
    save_matches(job["id"],rows)
    return jsonify({"message":f"Matching complete for {len(rows)} candidate(s). Saved recruiter decisions were preserved.","state":_state()})

@app.post("/api/assistant")
def assistant():
    data=request.get_json(force=True); question=str(data.get("question","")).strip()
    candidate=next((c for c in list_candidates() if c["id"]==data.get("candidate_id")),None)
    jobs=list_jobs(); job=next((j for j in jobs if j["id"]==data.get("job_id")),None) if data.get("job_id") else _active_job(jobs)
    if not candidate: return jsonify(error="Select a candidate first."),400
    if not question: return jsonify(error="Enter a recruitment-related question."),400
    return jsonify(answer_question(question,candidate["resume_text"],job["description"] if job else "",job["required_skills"] if job else []))

@app.post("/api/decisions")
def decisions():
    data=request.get_json(force=True)
    try:
        save_decision(data.get("job_id",""),data.get("candidate_id",""),data.get("decision",""),str(data.get("reason","")))
    except ValueError as exc: return jsonify(error=str(exc)),400
    return jsonify({"message":"Decision saved and history updated.","state":_state()})

@app.get("/api/candidates/<candidate_id>")
def candidate_detail(candidate_id):
    c=next((x for x in list_candidates() if x["id"]==candidate_id),None)
    if not c: abort(404)
    job=_active_job()
    evidence=retrieve_evidence(" ".join(job["required_skills"]) if job else "",c["resume_text"],top_k=4)
    questions=interview_questions(c["resume_text"],job["description"] if job else "",job["required_skills"] if job else [],job["preferred_skills"] if job else [])
    return jsonify({"evidence":evidence,"interview_questions":questions})

@app.get("/api/reports/<kind>.csv")
def report(kind):
    jobs=list_jobs(); job_id=request.args.get("job_id"); job=next((j for j in jobs if j["id"]==job_id),None) if job_id else _active_job(jobs)
    if not job: return jsonify(error="Select a job before exporting."),400
    rows=_ranked_rows(job)
    if kind=="ranking": content=ranking_csv(rows); filename="candidate_ranking.csv"
    elif kind=="gaps": content=skill_gaps_csv(rows); filename="candidate_skill_gaps.csv"
    elif kind=="summaries": content=candidate_summaries_csv(rows); filename="candidate_summaries.csv"
    elif kind=="decisions": content=decisions_csv(list_decisions(job["id"])); filename="recruiter_decisions.csv"
    else: abort(404)
    from io import BytesIO
    return send_file(BytesIO(content),mimetype="text/csv; charset=utf-8",as_attachment=True,download_name=filename)

@app.post("/api/clear")
def clear_records():
    data=request.get_json(force=True)
    if data.get("confirmed") is not True or data.get("phrase") != "DELETE":
        return jsonify(error="Confirm the checkbox and enter DELETE to clear local prototype records."),400
    delete_all_records()
    return jsonify({"message":"Local prototype records were cleared.","state":_state()})

@app.errorhandler(413)
def too_large(_): return jsonify(error=f"The total upload batch is too large. Keep each file under {MAX_UPLOAD_MB} MB and the combined batch under 250 MB."),413

if __name__ == "__main__":
    print("SmartHire AI local website: http://127.0.0.1:5000")
    app.run(host="127.0.0.1",port=5000,debug=False)
