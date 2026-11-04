from database import init_db,save_job,list_jobs,save_candidate,list_candidates,save_decision,list_decisions,decision_history,save_matches,get_matches,delete_all_records

def records(tmp_path):
    path=tmp_path/"test.db"; init_db(path)
    jid=save_job({"title":"Engineer","description":"Python role","required_skills":["Python"],"active":True},path)
    cid=save_candidate({"name":"Fictional","content_hash":"hash-1","resume_text":"Python project"},path)
    return path,jid,cid

def test_job_candidate_persist_and_duplicate(tmp_path):
    path,jid,cid=records(tmp_path)
    assert list_jobs(path)[0]["id"]==jid
    assert list_candidates(path)[0]["id"]==cid
    assert save_candidate({"name":"Duplicate","content_hash":"hash-1","resume_text":"Python project"},path)==cid
    assert len(list_candidates(path))==1

def test_match_and_decision_audit(tmp_path,monkeypatch):
    path,jid,cid=records(tmp_path)
    save_matches(jid,[{"id":cid,"similarity":.8,"required_coverage":1,"score":.87,"required_matched":["Python"],"required_missing":[],"preferred_detected":[],"scoring_mode":"test","label":"Strong"}],path)
    assert get_matches(jid,path)[0]["score"]==.87
    monkeypatch.setattr("database._now",lambda:"2026-01-01T00:00:00+00:00")
    save_decision(jid,cid,"Review Required","Check project ownership",path)
    save_decision(jid,cid,"Shortlisted","Project meets role needs",path)
    assert list_decisions(jid,path)[0]["decision"]=="Shortlisted"
    history=decision_history(path)
    assert len(history)==2
    assert history[0]["old_decision"]=="Review Required"
    assert history[0]["new_decision"]=="Shortlisted"

def test_sample_data_is_idempotent(tmp_path):
    from sample_data import load_samples
    path=tmp_path/"samples.db"
    jid=load_samples(path); load_samples(path)
    assert len(list_jobs(path))==1 and len(list_candidates(path))==3
    assert list_jobs(path)[0]["id"]==jid and list_jobs(path)[0]["active"]

def test_explicit_database_clear(tmp_path):
    path,jid,cid=records(tmp_path)
    delete_all_records(path)
    assert list_jobs(path)==[] and list_candidates(path)==[]


