from matching_engine import score_candidate,rank_candidates
from preprocessing import normalize_text
from skills import extract_skills

def test_normalize_and_phrase_skills():
    assert normalize_text(" Python\n\tSQL ")=="Python SQL"
    assert "machine learning" in extract_skills("Machine learning and NLP")
    assert "Java" not in extract_skills("JavaScript developer",["Java"])

def test_score_components_missing_and_empty():
    r=score_candidate("Python NLP", "Python project",["Python","NLP"])
    assert r.required_matched==["Python"] and r.required_missing==["NLP"]
    assert r.required_coverage==.5 and 0<=r.score<=1
    empty=score_candidate("","",[])
    assert empty.score==0 and empty.required_coverage is None

def test_score_matches_documented_weighted_formula():
    result=score_candidate("Python APIs SQL", "Python SQL project", ["Python","SQL"])
    assert abs(result.score-(.65*result.similarity+.35*result.required_coverage))<1e-12

def test_text_only_and_preferred_not_scored():
    no_skills=score_candidate("Python APIs", "Python APIs project",[])
    pref=score_candidate("Python APIs", "Python APIs project",[],["Python"])
    assert no_skills.score==pref.score and pref.preferred_detected==["Python"]

def test_ranking_tie_breaking_is_stable():
    ranked=rank_candidates("Python",[{"id":"b","text":"Python"},{"id":"a","text":"Python"}],[])
    assert [x["id"] for x in ranked]==["a","b"]
    assert [x["rank"] for x in ranked]==[1,2]
