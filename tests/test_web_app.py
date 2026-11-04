from io import BytesIO
from types import SimpleNamespace

from web_app import app
import web_app
from job_description_parser import parse_job_description


def test_job_description_upload_extracts_text_without_saving_a_job():
    client = app.test_client()
    source = (
        b"Job Title: People Operations Analyst\n"
        b"Department: People Operations\n"
        b"Required Skills:\nPython\nSQL\n"
        b"Preferred Skills:\nGit\n"
        b"Qualifications:\nBachelor's degree in HR or a related field.\n"
        b"Experience:\n2+ years of recruiting experience."
    )
    response = client.post(
        "/api/job-description-file",
        data={"job_description": (BytesIO(source), "role.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    fields = response.get_json()
    assert fields["filename"] == "role.txt"
    assert fields["title"] == "People Operations Analyst"
    assert fields["department"] == "People Operations"
    assert "Python" in fields["required_skills"] and "SQL" in fields["required_skills"]
    assert fields["preferred_skills"] == ["Git"]
    assert "Bachelor's degree" in fields["qualifications"]
    assert "2+ years" in fields["experience"]
    assert "Python" in fields["description"]


def test_job_description_upload_rejects_unsupported_files():
    client = app.test_client()
    response = client.post(
        "/api/job-description-file",
        data={"job_description": (BytesIO(b"ignored"), "role.exe")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.get_json()["error"]


def test_job_description_parser_fills_fields_from_unlabeled_content():
    fields = parse_job_description(
        "Data Analyst\nUse Python and SQL to build reports.\n"
        "Bachelor's degree preferred. At least 3 years of experience required.",
        "role.txt",
    )

    assert fields["title"] == "Data Analyst"
    assert fields["department"] == "Data & Analytics (suggested)"
    assert "Python" in fields["required_skills"]
    assert "SQL" in fields["required_skills"]
    assert "Bachelor's degree" in fields["qualifications"]
    assert "3 years" in fields["experience"]


def test_job_description_parser_keeps_custom_role_skills():
    fields = parse_job_description(
        "Job Title: Customer Success Manager\n"
        "Department: Customer Success\n"
        "Required Skills:\nCustomer service, Salesforce, conflict resolution\n"
        "Preferred Skills:\nZendesk, workforce management\n"
        "Qualifications:\nAssociate degree or equivalent experience\n"
        "Experience:\n3+ years in customer success",
        "customer_success.txt",
    )

    assert fields["title"] == "Customer Success Manager"
    assert "Customer service" in fields["required_skills"]
    assert "Salesforce" in fields["required_skills"]
    assert "conflict resolution" in fields["required_skills"]
    assert "Zendesk" in fields["preferred_skills"]
    assert "workforce management" in fields["preferred_skills"]


def test_website_serves_the_local_workspace():
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"SmartHire AI | Recruitment Workspace" in response.data
    assert b'class="topbar"' not in response.data
    assert b"Private local workspace" not in response.data

def test_recruitment_pipeline_feature_is_removed():
    client=app.test_client()
    assert b"Recruitment pipeline" not in client.get("/").data
    assert client.post("/api/pipeline",json={}).status_code==404


def test_resume_upload_accepts_batches_larger_than_six(monkeypatch):
    saved = []
    monkeypatch.setattr(web_app, "list_candidates", lambda: [])
    monkeypatch.setattr(web_app, "_state", lambda: {"candidates": []})
    monkeypatch.setattr(web_app, "save_candidate", lambda record: saved.append(record) or f"candidate-{len(saved)}")
    monkeypatch.setattr(
        web_app,
        "parse_resume",
        lambda filename, content: SimpleNamespace(
            text=content.decode(), name=filename, email=None, phone=None,
            skills=[], education=[], projects=[], experience=[], warnings=[],
        ),
    )
    data = {
        "resumes": [
            (BytesIO(f"Resume content {index}".encode()), f"candidate-{index}.txt")
            for index in range(7)
        ]
    }

    response = app.test_client().post("/api/upload", data=data, content_type="multipart/form-data")

    assert response.status_code == 200
    assert len(response.get_json()["outcomes"]) == 7
    assert len(saved) == 7

def test_candidate_comparison_feature_is_removed(monkeypatch):
    job={"id":"job-1","title":"Data Engineer","description":"Python SQL APIs","required_skills":["Python","SQL"],"preferred_skills":[],"active":True}
    monkeypatch.setattr(web_app,"list_jobs",lambda:[job])
    client=app.test_client()
    assert b'data-page="compare"' not in client.get("/").data
    assert b"Compare candidates" not in client.get("/static/app.js").data
    assert client.post("/api/compare",json={}).status_code==404
    assert client.get("/api/reports/comparison.csv?job_id=job-1").status_code==404

def test_assistant_reviews_one_candidate_without_comparison_mode(monkeypatch):
    job={"id":"j","title":"Data Engineer","description":"Python SQL role","required_skills":["Python","SQL"],"preferred_skills":[],"active":True}
    people=[{"id":"c1","name":"Candidate One","resume_text":"Built Python service and SQL pipeline"},{"id":"c2","name":"Candidate Two","resume_text":"Built a Python script"}]
    monkeypatch.setattr(web_app,"list_candidates",lambda:people)
    monkeypatch.setattr(web_app,"list_jobs",lambda:[job])
    response=app.test_client().post("/api/assistant",json={"candidate_id":"c1","compare_candidate_id":"c2","job_id":"j","question":"Summarize this candidate's relevant project evidence"})
    assert response.status_code==200
    data=response.get_json()
    assert "Candidate Two" not in data["answer"]
    assert all("Candidate Two" not in item for item in data["evidence"])
    script=app.test_client().get("/static/app.js").data
    assert b"assistant-compare-candidate" not in script
    assert b"Compare two candidates for this role" not in script

def test_general_workspace_and_candidate_detail_do_not_return_resume_or_contact_data(monkeypatch):
    job={"id":"j","title":"Data Engineer","description":"Python SQL role","required_skills":["Python","SQL"],"preferred_skills":[],"active":True}
    candidate={"id":"c1","name":"Fictional Candidate","email":"private@example.test","phone":"555-123-4567","content_hash":"private-hash","resume_text":"PRIVATE_RESUME_SENTINEL\nBuilt Python and SQL pipelines\nEducation: Engineering","skills":["Python","SQL"],"warnings":[]}
    monkeypatch.setattr(web_app,"list_jobs",lambda:[job])
    monkeypatch.setattr(web_app,"list_candidates",lambda:[candidate])
    monkeypatch.setattr(web_app,"get_matches",lambda job_id:[])
    monkeypatch.setattr(web_app,"list_decisions",lambda job_id=None:[])
    monkeypatch.setattr(web_app,"decision_history",lambda:[])
    monkeypatch.setattr(web_app,"dashboard_data",lambda:{"candidates":1,"jobs":1,"shortlisted":0,"review":0})

    client=app.test_client()
    state_response=client.get("/api/state")
    detail_response=client.get("/api/candidates/c1")

    assert state_response.status_code==200
    assert detail_response.status_code==200
    assert b"PRIVATE_RESUME_SENTINEL" not in state_response.data
    assert b"private@example.test" not in state_response.data
    assert b"555-123-4567" not in state_response.data
    assert b"PRIVATE_RESUME_SENTINEL" not in detail_response.data
    assert b"private@example.test" not in detail_response.data
    assert "resume_text" not in state_response.get_json()["candidates"][0]
    assert "resume_text" not in state_response.get_json()["rows"][0]
    assert "candidate" not in detail_response.get_json()
