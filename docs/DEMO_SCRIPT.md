# SmartHire AI website demonstration script (7 minutes)

This walkthrough follows the current local website pages: Dashboard, Jobs & roles, Resume screening, Candidate insights, Recruiter assistant, Decision register, and Reports & export. It uses the fictional sample role and profiles. It does not include candidate comparison or a recruitment pipeline.

## Before recording

- Start the local website with `python app.py`, then open `http://127.0.0.1:5000`.
- Use only the fictional sample role and candidates for the demonstration.
- If the workspace is empty, load the fictional demo data from the Dashboard’s empty-state button or the **Load sample role** button in **Jobs & roles**. This loads the sample role and three fictional profiles.
- Have a decision reason ready to enter. Saving it changes the local demo database.
- The timestamps include brief pauses to navigate and let screens load. Speak at a relaxed pace.

## 0:00–0:45 — Introduce SmartHire AI

**On screen:** Dashboard.

**Say:**

“Hello, and welcome. This is SmartHire AI, a local recruitment workspace for reviewing resume text against job requirements.

In the next few minutes, I’ll show how a recruiter can set up a role, screen resumes, inspect evidence, prepare interview questions, record a human decision, and export a report.

This demonstration uses fictional records. SmartHire AI is a prototype to support review. Its scores describe text relevance, and recruiters make the hiring decisions.”

## 0:45–1:25 — Dashboard and fictional demo data

**On screen:** If the workspace is empty, choose **Load fictional demo data**. Let the Dashboard refresh. Point out the active role and overview cards.

**Say:**

“I’ve loaded the fictional sample role, Talent Acquisition Intern – AI and LLM, and three sample profiles. The Dashboard gives a quick view of the active job, candidate count, saved recruiter decisions, and average textual relevance.

The score distribution and ranking overview help orient the recruiter to the current role. They are a summary; the next step is to review the role requirements and the evidence behind each result.”

## 1:25–2:10 — Set up a role

**On screen:** Open **Jobs & roles**. Show the sample role, required skills, preferred skills, and job description. Do not edit or save unless you intend to change the demo data.

**Say:**

“In Jobs & roles, recruiters can create and edit roles across departments. They can type in a job description or import a PDF, DOCX, or TXT file. Imported details fill the form as suggestions, so the recruiter can review and change them before saving.

For this example, the role has required skills such as Python, NLP, machine learning, SQL, prompt engineering, communication, and problem solving. Preferred skills are listed separately. Only the skills explicitly entered as required skills count toward required-skill coverage.”

## 2:10–3:10 — Upload and screen resumes

**On screen:** Open **Resume screening**. Point out the resume upload area, selected job, **Run matching** button, and candidate ranking. With sample data already loaded, click **Run matching** once.

**Say:**

“Resume screening accepts multiple PDF, DOCX, or TXT files at once. The sample profiles are already loaded, so I’ll run matching for the active role.

The results show a ranked list with a textual relevance score, required-skill coverage, detected required skills, potential gaps, preferred skills found, and any recruiter decision already recorded. A minimum-score control can filter the visible rows.

The score combines 65 percent text similarity and 35 percent required-skill coverage. Text similarity is based on wording overlap between the job description and resume. Skill coverage is the fraction of configured required skill phrases found in the resume text.

These results are not hiring probabilities. A potential gap means the resume text did not provide a matching phrase; it does not prove the candidate lacks that skill.”

## 3:10–4:15 — Inspect one candidate’s evidence

**On screen:** Select Aarav Mehta (Fictional) from the ranking, or use the first listed candidate if names differ. Open **Candidate insights** from the selected row. Show score components, evidence, skills, and interview preparation.

**Say:**

“I’ll open one fictional profile to see the evidence in context. Candidate Insights shows the match components, resume excerpts, skills detected, potential gaps, and any parsing warnings.

For this profile, we can inspect the project description and the skill phrases the system found. We should check those excerpts against the resume rather than relying only on the score. If a requirement has no matching excerpt, that is something to verify in a conversation, not a conclusion about the person.

This page also prepares interview questions tied to the role and resume. Questions can ask a candidate to explain a skill mentioned in the resume or to describe experience with a requirement that was not found in the text. I can copy the questions or export them to a text file for interview preparation.”

## 4:15–5:05 — Ask the Recruiter Assistant

**On screen:** Open **Recruiter assistant**. Select the same candidate if needed. Choose the quick question **Which required skills are evidenced?** Submit it and show the evidence area.

**Say:**

“The Recruiter Assistant focuses on one selected candidate and the active role. I’ll ask which required skills are evidenced, then review the answer alongside its supporting resume excerpts.

The assistant uses local text retrieval and transparent Python rules. It does not call a generative language model or an external AI service. The answer is a starting point for review; the recruiter should verify it against the source evidence.”

## 5:05–6:20 — Record a recruiter decision

**On screen:** Open **Decision register**. Select the active job and a fictional candidate. Choose **Review Required**, enter a job-related reason, and click **Save recruiter decision**. Show the resulting current decision and history.

**Say:**

“The Decision Register records the recruiter’s decision and the reason for it. Available decisions are Shortlisted, Review Required, and Not Selected. Each reason should be tied to the role and the evidence reviewed.

Here are examples of job-related reasons for the three outcomes:

- **Review Required — Maya Iyer:** ‘The resume documents Python, SQL, and API testing. Matching text for NLP, machine learning, and prompt engineering was not found, so verify those required skills in an interview before deciding.’
- **Shortlisted — Aarav Mehta:** ‘The resume documents the listed required skills and describes a TF-IDF resume-classification project. Shortlist for an interview to verify the candidate’s contribution and depth of experience.’
- **Not Selected — Rohan Das:** ‘After follow-up, the candidate did not demonstrate the required NLP, machine-learning, and prompt-engineering experience for this role. The decision reflects the confirmed role requirements and the evidence reviewed.’ Use this reason only if that follow-up has actually happened.

I’ll demonstrate saving a Review Required decision. I’ll enter: ‘Verify the candidate’s experience with NLP, machine learning, and prompt engineering in an interview before making a final decision.’ After saving, the decision appears in the register. If a recruiter later updates it, the history preserves the earlier and newer outcomes and reasons. Matching does not change decisions automatically.”

## 6:20–6:45 — Export reports

**On screen:** Open **Reports & export**. Show the four available CSV downloads. Download the candidate ranking or decision report if appropriate for the recording.

**Say:**

“Reports & export provides CSV downloads for candidate ranking, skill-gap analysis, candidate summaries, and recruiter decisions. The decision report includes the recorded decision and its job-related reason. These files are generated for the selected role and can support further recruiter review.”

## 6:45–7:00 — Close

**On screen:** Leave the report page visible or return to the Dashboard.

**Say:**

“That completes the SmartHire AI walkthrough: role setup, resume screening, evidence review, interview preparation, recruiter decisions, and report export.

This prototype processes documents locally. Text extraction can miss context, and scanned-PDF OCR is not included. Recruiters should verify the evidence and remain responsible for every decision. Thank you for watching.”

## Recording checklist

- [ ] Use only the fictional sample role and candidates.
- [ ] Show each current page in the sequence above.
- [ ] Run matching and explain the score as textual relevance, not hiring probability.
- [ ] Open one candidate at a time and show the source evidence.
- [ ] Show interview questions and the assistant’s supporting excerpts.
- [ ] Save a decision with a job-related reason.
- [ ] Explain the example reasons for Review Required, Shortlisted, and Not Selected.
- [ ] Show the available report downloads.
- [ ] Mention that scanned-PDF OCR is not included.
- [ ] Keep the demo focused on the current website pages and features.
