"""CSV exports built from already filtered application records."""
from io import StringIO
import pandas as pd
from candidate_assistant import retrieve_evidence

def csv_bytes(rows, columns):
    df=pd.DataFrame(rows,columns=columns)
    return df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")

def ranking_csv(rows):
    cols=["rank","name","score","similarity","required_coverage","required_matched","required_missing","preferred_detected","decision"]
    clean=[]
    for r in rows:
        x=dict(r); x["score"]=round(float(x.get("score",0))*100,1); x["similarity"]=round(float(x.get("similarity",0))*100,1)
        x["required_coverage"]="Unavailable" if x.get("required_coverage") is None else round(float(x["required_coverage"])*100,1)
        for key in ("required_matched","required_missing","preferred_detected"): x[key]="; ".join(x.get(key,[]))
        clean.append(x)
    return csv_bytes(clean,cols)

def decisions_csv(rows): return csv_bytes(rows,["name","job_title","decision","reason","created_at"])
def skill_gaps_csv(rows):
    return csv_bytes([{"rank":r.get("rank"),"name":r.get("name"),"matched_required":"; ".join(r.get("required_matched",[])),"potential_gaps":"; ".join(r.get("required_missing",[]))} for r in rows],["rank","name","matched_required","potential_gaps"])

def candidate_summaries_csv(rows):
    summaries=[]
    for r in rows:
        text=r.get("text",r.get("resume_text",""))
        evidence=retrieve_evidence(" ".join(r.get("required_matched",[])) or r.get("name",""),text,top_k=2)
        summaries.append({"rank":r.get("rank"),"name":r.get("name"),"textual_relevance":round(float(r.get("score",0))*100,1),"relevance_label":r.get("label",""),"required_skills_detected":"; ".join(r.get("required_matched",[])),"potential_gaps_for_verification":"; ".join(r.get("required_missing",[])),"resume_evidence":" | ".join(evidence),"recruiter_decision":r.get("decision","Not recorded")})
    return csv_bytes(summaries,["rank","name","textual_relevance","relevance_label","required_skills_detected","potential_gaps_for_verification","resume_evidence","recruiter_decision"])
