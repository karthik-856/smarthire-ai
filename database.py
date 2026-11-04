"""SQLite persistence for local prototype records."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from config import DB_PATH

def connect(db_path=None):
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db(db_path=None):
    with connect(db_path) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,title TEXT NOT NULL,department TEXT,description TEXT NOT NULL,required_skills TEXT NOT NULL DEFAULT '[]',preferred_skills TEXT NOT NULL DEFAULT '[]',qualifications TEXT,experience TEXT,active INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY,name TEXT NOT NULL,email TEXT,phone TEXT,source TEXT NOT NULL,content_hash TEXT NOT NULL UNIQUE,resume_text TEXT NOT NULL,skills TEXT NOT NULL DEFAULT '[]',education TEXT NOT NULL DEFAULT '[]',projects TEXT NOT NULL DEFAULT '[]',experience TEXT NOT NULL DEFAULT '[]',warnings TEXT NOT NULL DEFAULT '[]',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS matches(job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,similarity REAL NOT NULL,coverage REAL,score REAL NOT NULL,required_matched TEXT NOT NULL,required_missing TEXT NOT NULL,preferred_detected TEXT NOT NULL,scoring_mode TEXT NOT NULL,label TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(job_id,candidate_id));
        CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,decision TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS decision_history(id TEXT PRIMARY KEY,decision_id TEXT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,old_decision TEXT,old_reason TEXT,new_decision TEXT NOT NULL,new_reason TEXT NOT NULL,changed_at TEXT NOT NULL);
        """)

def _now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def save_job(job, db_path=None):
    jid = job.get("id") or str(uuid.uuid4())
    with connect(db_path) as c:
        if job.get("active"):
            c.execute("UPDATE jobs SET active=0")
        c.execute("""INSERT INTO jobs(id,title,department,description,required_skills,preferred_skills,qualifications,experience,active,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,department=excluded.department,description=excluded.description,required_skills=excluded.required_skills,preferred_skills=excluded.preferred_skills,qualifications=excluded.qualifications,experience=excluded.experience,active=excluded.active""",
        (jid,job["title"],job.get("department",""),job["description"],json.dumps(job.get("required_skills",[])),json.dumps(job.get("preferred_skills",[])),job.get("qualifications",""),job.get("experience",""),int(job.get("active",False)),job.get("created_at",_now())))
    return jid

def list_jobs(db_path=None):
    with connect(db_path) as c: rows=c.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    return [{**dict(r),"required_skills":json.loads(r["required_skills"]),"preferred_skills":json.loads(r["preferred_skills"]),"active":bool(r["active"])} for r in rows]

def set_active_job(job_id, db_path=None):
    with connect(db_path) as c:
        c.execute("UPDATE jobs SET active=0")
        c.execute("UPDATE jobs SET active=1 WHERE id=?",(job_id,))

def save_candidate(candidate, db_path=None):
    cid=candidate.get("id") or str(uuid.uuid4())
    with connect(db_path) as c:
        c.execute("""INSERT OR IGNORE INTO candidates(id,name,email,phone,source,content_hash,resume_text,skills,education,projects,experience,warnings,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (cid,candidate.get("name") or "Name unavailable",candidate.get("email"),candidate.get("phone"),candidate.get("source","upload"),candidate["content_hash"],candidate["resume_text"],json.dumps(candidate.get("skills",[])),json.dumps(candidate.get("education",[])),json.dumps(candidate.get("projects",[])),json.dumps(candidate.get("experience",[])),json.dumps(candidate.get("warnings",[])),_now()))
        row=c.execute("SELECT id FROM candidates WHERE content_hash=?",(candidate["content_hash"],)).fetchone()
    return row["id"]

def list_candidates(db_path=None):
    with connect(db_path) as c: rows=c.execute("SELECT * FROM candidates ORDER BY created_at DESC").fetchall()
    keys=("skills","education","projects","experience","warnings")
    return [{**dict(r),**{k:json.loads(r[k]) for k in keys}} for r in rows]

def save_matches(job_id, ranked, db_path=None):
    with connect(db_path) as c:
        for r in ranked:
            c.execute("""INSERT INTO matches VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(job_id,candidate_id) DO UPDATE SET similarity=excluded.similarity,coverage=excluded.coverage,score=excluded.score,required_matched=excluded.required_matched,required_missing=excluded.required_missing,preferred_detected=excluded.preferred_detected,scoring_mode=excluded.scoring_mode,label=excluded.label,updated_at=excluded.updated_at""",
            (job_id,r["id"],r["similarity"],r["required_coverage"],r["score"],json.dumps(r["required_matched"]),json.dumps(r["required_missing"]),json.dumps(r["preferred_detected"]),r["scoring_mode"],r["label"],_now()))

def get_matches(job_id, db_path=None):
    with connect(db_path) as c:
        rows=c.execute("SELECT m.*,c.name,c.email,c.resume_text,c.skills,c.warnings FROM matches m JOIN candidates c ON c.id=m.candidate_id WHERE m.job_id=? ORDER BY m.score DESC,c.id",(job_id,)).fetchall()
    result=[]
    for r in rows:
        x=dict(r)
        for k in ("required_matched","required_missing","preferred_detected","skills","warnings"): x[k]=json.loads(x[k])
        result.append(x)
    return result

def save_decision(job_id,candidate_id,decision,reason,db_path=None):
    if decision not in {"Shortlisted","Review Required","Not Selected"}: raise ValueError("Choose a valid recruiter decision.")
    if not reason.strip(): raise ValueError("A job-related reason is required.")
    with connect(db_path) as c:
        row=c.execute("SELECT * FROM decisions WHERE job_id=? AND candidate_id=? ORDER BY created_at DESC LIMIT 1",(job_id,candidate_id)).fetchone()
        if row:
            c.execute("INSERT INTO decision_history VALUES(?,?,?,?,?,?,?)",(str(uuid.uuid4()),row["id"],row["decision"],row["reason"],decision,reason.strip(),_now()))
            c.execute("UPDATE decisions SET decision=?,reason=?,created_at=? WHERE id=?",(decision,reason.strip(),_now(),row["id"]))
            return row["id"]
        did=str(uuid.uuid4()); now=_now()
        c.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?)",(did,job_id,candidate_id,decision,reason.strip(),now))
        c.execute("INSERT INTO decision_history VALUES(?,?,?,?,?,?,?)",(str(uuid.uuid4()),did,None,None,decision,reason.strip(),now))
        return did

def list_decisions(job_id=None,db_path=None):
    with connect(db_path) as c:
        sql="SELECT d.*,c.name,j.title AS job_title FROM decisions d JOIN candidates c ON c.id=d.candidate_id JOIN jobs j ON j.id=d.job_id"
        rows=c.execute(sql+ (" WHERE d.job_id=?" if job_id else "")+" ORDER BY d.created_at DESC",(job_id,) if job_id else ()).fetchall()
    return [dict(r) for r in rows]

def decision_history(db_path=None):
    with connect(db_path) as c:
        return [dict(r) for r in c.execute("SELECT h.*,c.name,j.title AS job_title FROM decision_history h JOIN decisions d ON d.id=h.decision_id JOIN candidates c ON c.id=d.candidate_id JOIN jobs j ON j.id=d.job_id ORDER BY h.changed_at DESC, h.rowid DESC").fetchall()]

def dashboard_data(db_path=None):
    with connect(db_path) as c:
        counts={"candidates":c.execute("SELECT count(*) FROM candidates").fetchone()[0],"jobs":c.execute("SELECT count(*) FROM jobs WHERE active=1").fetchone()[0],"shortlisted":c.execute("SELECT count(*) FROM decisions WHERE decision='Shortlisted'").fetchone()[0],"review":c.execute("SELECT count(*) FROM decisions WHERE decision='Review Required'").fetchone()[0]}
    return counts

def delete_all_records(db_path=None):
    with connect(db_path) as c:
        c.execute("DELETE FROM decision_history"); c.execute("DELETE FROM decisions"); c.execute("DELETE FROM matches"); c.execute("DELETE FROM candidates"); c.execute("DELETE FROM jobs")
