import csv,io
from report_generator import ranking_csv,skill_gaps_csv,decisions_csv,candidate_summaries_csv
from candidate_assistant import answer_question
from candidate_assistant import interview_questions
from preprocessing import sentence_chunks

def test_sentence_chunks_preserve_resume_paragraph_boundaries():
    chunks=sentence_chunks("PRIVATE_RESUME_SENTINEL\nBuilt a Python parser.\nManaged SQL reports")
    assert chunks==["PRIVATE_RESUME_SENTINEL","Built a Python parser.","Managed SQL reports"]

def test_csv_exports_have_columns_and_data():
    row={"rank":1,"name":"Fictional","score":.8,"similarity":.7,"required_coverage":.5,"required_matched":["Python"],"required_missing":["SQL"],"preferred_detected":[],"decision":"Review Required"}
    parsed=list(csv.DictReader(io.StringIO(ranking_csv([row]).decode("utf-8-sig"))))
    assert parsed[0]["name"]=="Fictional" and parsed[0]["score"]=="80.0"
    assert "potential_gaps" in next(csv.DictReader(io.StringIO(skill_gaps_csv([row]).decode("utf-8-sig")))).keys()
    assert decisions_csv([]).decode("utf-8-sig").startswith("name,job_title")
    summary=next(csv.DictReader(io.StringIO(candidate_summaries_csv([{**row,"text":"Python parser project evidence."}]).decode("utf-8-sig"))))
    assert summary["name"]=="Fictional" and "Python" in summary["resume_evidence"]

def test_assistant_uses_resume_evidence_and_handles_missing():
    text="Built a Python parser for synthetic resumes."
    result=answer_question("What evidence supports Python experience?",text,"Python role",["Python","SQL"])
    assert "Python" in result["answer"] and result["evidence"]
    missing=answer_question("What requirements need verification?",text,"",["Python","SQL"])
    assert "SQL" in missing["answer"]

def test_assistant_cites_only_resume_text_not_job_requirements():
    resume="Built a Python parser for synthetic resumes."
    result=answer_question("What evidence supports Python experience?",resume,"Python role requires SQL and hiring analytics.",["Python","SQL"])
    assert result["evidence"]
    assert all("Job requirement:" not in excerpt for excerpt in result["evidence"])
    assert all("hiring analytics" not in excerpt for excerpt in result["evidence"])

def test_assistant_interview_prompt_returns_interview_questions():
    result=answer_question("What should I verify in an interview?","Python project work.","role",["Python","SQL"])
    assert "Suggested job-related questions" in result["answer"]
    assert "specific contribution" in result["answer"]

def test_interview_questions_distinguish_evidence_from_unverified_skills():
    items=interview_questions("Built a Python parser for resumes.","Python and SQL role",["Python","SQL"],limit=5)
    assert len(items)>=2
    assert items[0]["evidence"] and "Python" in items[0]["question"]
    assert "not proof" in items[1]["why"]

