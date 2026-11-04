const content = document.getElementById('page-content');
const notice = document.getElementById('notice');
let appState = null;
let currentPage = 'dashboard';
let selectedCandidateId = null;
let editingJobId = null;
let assistantHistory = [];

const pageNames = {dashboard:'Dashboard',jobs:'Jobs & roles',screening:'Resume screening',insights:'Candidate insights',assistant:'Recruiter assistant',decisions:'Decision register',reports:'Reports & export'};
document.querySelector('.sidebar-bottom [data-page="about"]')?.remove();
const esc = (v='') => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = n => `${(Number(n||0)*100).toFixed(1)}%`;
const activeJob = () => appState?.active_job || null;
const candidates = () => appState?.candidates || [];
const rows = () => appState?.rows || [];

async function api(path, options={}) {
  const response = await fetch(path, options);
  const type = response.headers.get('content-type') || '';
  const data = type.includes('application/json') ? await response.json() : null;
  if (!response.ok) throw new Error(data?.error || `Request failed (${response.status})`);
  return data;
}
function jsonOptions(body) { return {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}; }
function showNotice(message, type='success') {
  notice.textContent = message; notice.className = `notice ${type}`; notice.hidden = false;
  clearTimeout(showNotice.timer); showNotice.timer = setTimeout(()=>notice.hidden=true,5000);
}
function initials(name='?') { return name.split(/\s+/).filter(Boolean).slice(0,2).map(w=>w[0]).join('').toUpperCase(); }
function badge(decision) {
  const cls = decision==='Shortlisted'?'badge-green':decision==='Review Required'?'badge-amber':decision==='Not Selected'?'badge-red':'badge-gray';
  return `<span class="badge ${cls}">${esc(decision||'Not recorded')}</span>`;
}
function scoreMeter(score, detail='text relevance') {
  const value=Math.max(0,Math.min(100,Number(score||0)*100));
  return `<div class="score-meter"><div class="score-meter-top"><b>${value.toFixed(1)}%</b><span>${esc(detail)}</span></div><div class="score-track" role="progressbar" aria-label="Textual relevance" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${value.toFixed(1)}"><span style="width:${value}%"></span></div></div>`;
}
function head(eyebrow,title,subtitle,action='') { return `<div class="page-head"><div><div class="eyebrow">${esc(eyebrow)}</div><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div>${action?`<div class="page-actions">${action}</div>`:''}</div>`; }
function empty(title,body,button='') { return `<div class="empty"><b>${esc(title)}</b>${esc(body)}${button?`<div style="margin-top:12px">${button}</div>`:''}</div>`; }
function table(headers,body) { return `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${body||`<tr><td colspan="${headers.length}" class="decisions-empty">No records to display.</td></tr>`}</tbody></table></div>`; }
function cardMetric(label,value,note,icon){return `<article class="metric-card"><div class="metric-top"><span>${esc(label)}</span><span class="metric-icon">${icon}</span></div><div class="metric-value">${esc(value)}</div><div class="metric-note">${esc(note)}</div></article>`;}
function renderDashboard(){
  const c=appState.counts||{}, ranked=rows(), average=appState.average_score==null?'—':pct(appState.average_score);
  const action=`<button class="btn btn-outline" id="dashboard-refresh">↻ Refresh</button>`;
  const job=activeJob();
  const buckets=[0,20,40,60,80].map((start,i)=>({label:`${start}–${start+20}%`,count:ranked.filter(r=>r.score*100>=start&&(i===4?r.score*100<=100:r.score*100<start+20)).length}));const maxBucket=Math.max(1,...buckets.map(b=>b.count));
  const bars=ranked.length?buckets.map(b=>`<div class="bar-group"><span class="bar-value">${b.count}</span><div class="bar" style="height:${Math.max(5,b.count/maxBucket*72)}%"></div><span class="bar-label">${b.label}</span></div>`).join(''):'<div class="decisions-empty">Run matching to see candidate scores.</div>';
  const rankRows=ranked.slice(0,5).map(r=>`<tr><td><b>#${r.rank}</b></td><td class="td-name">${esc(r.name)}</td><td>${scoreMeter(r.score)}</td><td>${badge(r.decision)}</td></tr>`).join('');
  const decisions=(appState.decisions||[]).slice(0,5).map(d=>`<tr><td class="td-name">${esc(d.name)}</td><td>${esc(d.job_title)}</td><td>${badge(d.decision)}</td><td>${esc(d.reason)}</td></tr>`).join('');
  content.innerHTML=`${head('Overview','Recruitment overview','A transparent workspace for reviewing resume evidence against job requirements.',action)}
    ${job?`<div class="active-job"><div><div class="eyebrow">ACTIVE JOB</div><h3>${esc(job.title)}</h3><p>${esc(job.department||'No department')} · ${job.required_skills.length} configured required skills</p></div><button class="btn" id="go-screening">Run candidate screening <span>→</span></button></div>`:''}
    <div class="cards">${cardMetric('Candidates analyzed',ranked.length,'Matched against the active role','◉')}${cardMetric('Active roles',c.jobs||0,'Currently active job profiles','▤')}${cardMetric('Shortlisted',ranked.filter(r=>r.decision==='Shortlisted').length,'Recruiter decisions for active role','✓')}${cardMetric('Review required',ranked.filter(r=>r.decision==='Review Required').length,'Recruiter decisions for active role','!')}${cardMetric('Average relevance',average,'For the active role only','◌')}</div>
    ${!c.candidates&&!c.jobs?empty('Your workspace is ready','Load the fictional sample job and candidates to explore the full workflow.','<button class="btn btn-primary" id="load-samples-empty">Load fictional demo data</button>'):''}
    <div class="grid-two"><section class="panel"><div class="panel-head"><div><h2>Score distribution</h2><p>Candidates grouped into score ranges for the active job</p></div><span class="badge badge-blue">${ranked.length} candidates</span></div><div class="chart">${bars}</div><div class="chart-axis"><span>Lower relevance</span><span>Textual relevance</span><span>Higher relevance</span></div></section>
    <section class="panel"><div class="panel-head"><div><h2>Ranking overview</h2><p>Review candidates in score order</p></div><button class="small-link" data-goto="screening">View all</button></div>${ranked.length?table(['Rank','Candidate','Relevance','Decision'],rankRows):empty('No candidates matched yet','Load sample data or add resumes, then run matching.')}</section></div>
    <section class="panel"><div class="panel-head"><div><h2>Recent recruiter decisions</h2><p>Latest human-reviewed outcomes</p></div><button class="small-link" data-goto="decisions">Open register</button></div>${decisions.length?table(['Candidate','Job','Decision','Job-related reason'],decisions):empty('No decisions recorded','Recruiter decisions and reasons will appear here.')}</section>`;
  document.getElementById('dashboard-refresh')?.addEventListener('click',refresh);
  document.getElementById('go-screening')?.addEventListener('click',()=>navigate('screening'));
  document.getElementById('load-samples-empty')?.addEventListener('click',loadSamples);
}

function renderJobs(){
  const jobs=appState.jobs||[]; const current=jobs.find(j=>j.id===editingJobId)||(editingJobId?null:null);
  const job=current||{title:'',department:'',description:'',required_skills:[],preferred_skills:[],qualifications:'',experience:'',active:!jobs.length};
  const skillString=a=>(a||[]).join(', ');
  const jobItems=jobs.map(j=>`<div class="job-item"><div><h3>${esc(j.title)} ${j.active?'<span class="badge badge-green">Active</span>':''}</h3><p>${esc(j.department||'No department')} · ${(j.required_skills||[]).length} required skills · ${esc(j.id.slice(0,8))}</p></div><div class="job-right">${!j.active?`<button class="btn btn-soft btn-small" data-activate-job="${esc(j.id)}">Set active</button>`:''}<button class="btn btn-outline btn-small" data-edit-job="${esc(j.id)}">Edit</button></div></div>`).join('');
  content.innerHTML=`${head('Role setup','Jobs & roles','Create roles across any department. Add a job description file or enter the details, then review the extracted fields before saving.',`<button class="btn btn-soft" id="sample-job">＋ Load sample role</button>`)}
    <div class="grid-two"><section class="panel"><div class="panel-head"><h2>${current?'Edit saved role':'Create a role'}</h2>${current?`<button class="small-link" id="new-job">Create new</button>`:''}</div>
      <form id="job-form"><input type="hidden" name="id" value="${esc(job.id||'')}">
        <div class="form-grid"><div class="field"><label for="job-title">Job title <span class="muted">required</span></label><input id="job-title" name="title" required value="${esc(job.title)}" placeholder="e.g. Data Analyst, Product Designer, Sales Associate"></div><div class="field"><label for="job-department">Department or category</label><input id="job-department" name="department" value="${esc(job.department)}" placeholder="e.g. Analytics, Design, Sales"></div></div>
        <div class="field"><label for="job-document">Add a job-description file <small>PDF, DOCX, or TXT · up to ${appState.max_upload_mb} MB</small></label><div class="document-upload"><label class="document-pick" for="job-document"><span class="document-icon">↑</span><span><b>Choose a file</b><small>We’ll fill in role fields from the document</small></span><input id="job-document" type="file" accept=".pdf,.docx,.txt" hidden></label><span id="job-file-status" class="upload-status">Optional</span></div></div>
        <div class="field"><label for="job-description">Full job description <span class="muted">required</span></label><textarea class="tall" id="job-description" name="description" required placeholder="Describe the role and its requirements">${esc(job.description)}</textarea></div>
        <div class="form-grid"><div class="field"><label for="required-skills">Required skills <small>comma-separated</small></label><input id="required-skills" name="required_skills" value="${esc(skillString(job.required_skills))}" placeholder="Python, NLP, SQL"></div><div class="field"><label for="preferred-skills">Preferred skills <small>shown separately</small></label><input id="preferred-skills" name="preferred_skills" value="${esc(skillString(job.preferred_skills))}" placeholder="Git, pandas"></div></div>
        <div class="form-grid"><div class="field"><label for="qualifications">Minimum qualifications <small>optional</small></label><input id="qualifications" name="qualifications" value="${esc(job.qualifications)}"></div><div class="field"><label for="experience">Experience requirements <small>optional</small></label><input id="experience" name="experience" value="${esc(job.experience)}"></div></div>
        <label class="confirm-row" style="font-size:10px;color:#63778b"><input type="checkbox" name="active" ${job.active?'checked':''}> Make this the active job</label>
        <div class="form-actions"><button class="btn btn-primary" type="submit">Save role</button><span class="help-note">Only the skills you specify are used as requirements.</span></div>
      </form></section><section class="panel"><div class="panel-head"><div><h2>Saved jobs</h2><p>${jobs.length} saved role${jobs.length===1?'':'s'}</p></div></div>${jobs.length?`<div class="job-list">${jobItems}</div>`:empty('No saved jobs','Create a job or load the editable sample role.')}</section></div>`;
  document.getElementById('new-job')?.addEventListener('click',()=>{editingJobId=null;renderPage();});
  document.getElementById('sample-job').addEventListener('click',loadSamples);
  document.getElementById('job-form').addEventListener('submit',saveJobForm);
  document.getElementById('job-document').addEventListener('change',uploadJobDescription);
  document.querySelectorAll('[data-edit-job]').forEach(b=>b.onclick=()=>{editingJobId=b.dataset.editJob;renderPage();});
  document.querySelectorAll('[data-activate-job]').forEach(b=>b.onclick=async()=>{try{const d=await api(`/api/jobs/${b.dataset.activateJob}/active`,{method:'POST'});appState=d.state;showNotice(d.message);renderPage();}catch(e){showNotice(e.message,'error');}});
}

async function uploadJobDescription(event){
  const file=event.target.files?.[0];if(!file)return;
  const status=document.getElementById('job-file-status');status.className='upload-status is-loading';status.textContent=`Reading ${file.name}…`;
  const form=new FormData();form.append('job_description',file);
  try{const d=await api('/api/job-description-file',{method:'POST',body:form});
    document.getElementById('job-title').value=d.title||'';
    document.getElementById('job-department').value=d.department||'';
    document.getElementById('job-description').value=d.description||'';
    document.getElementById('required-skills').value=(d.required_skills||[]).join(', ');
    document.getElementById('preferred-skills').value=(d.preferred_skills||[]).join(', ');
    document.getElementById('qualifications').value=d.qualifications||'';
    document.getElementById('experience').value=d.experience||'';
    status.className='upload-status is-success';status.textContent=`Loaded ${d.filename}`;
    const missing=[];if(!d.department)missing.push('department');if(!d.required_skills?.length)missing.push('required skills');if(!d.preferred_skills?.length)missing.push('preferred skills');if(!d.qualifications)missing.push('qualifications');if(!d.experience)missing.push('experience');
    showNotice(missing.length?`Role fields filled from the document. Review the blank or suggested fields: ${missing.join(', ')}.`:'Role fields filled from the document. Review them before saving.');}
  catch(e){status.className='upload-status is-error';status.textContent=e.message;showNotice(e.message,'error');}
}

async function saveJobForm(event){
  event.preventDefault(); const f=new FormData(event.currentTarget);
  const job={id:f.get('id')||undefined,title:f.get('title'),department:f.get('department'),description:f.get('description'),required_skills:(f.get('required_skills')||'').split(',').map(s=>s.trim()).filter(Boolean),preferred_skills:(f.get('preferred_skills')||'').split(',').map(s=>s.trim()).filter(Boolean),qualifications:f.get('qualifications'),experience:f.get('experience'),active:f.has('active')};
  try{const d=await api('/api/jobs',jsonOptions(job));appState=d.state;editingJobId=d.job_id;showNotice(d.message);renderPage();}catch(e){showNotice(e.message,'error');}
}

function renderScreening(){
  const job=activeJob(), ranked=rows(); const jobOptions=(appState.jobs||[]).map(j=>`<option value="${esc(j.id)}" ${job?.id===j.id?'selected':''}>${esc(j.title)}</option>`).join('');
  const rowHtml=ranked.map(r=>`<tr data-score="${r.score*100}"><td><b>#${r.rank}</b></td><td><button class="candidate-title-link" data-inspect="${esc(r.id)}">${esc(r.name)}</button><div class="rank-meta">${esc(r.label||'Text match')}</div></td><td>${scoreMeter(r.score,`text ${pct(r.similarity)}`)}</td><td>${r.required_coverage==null?'Unavailable':pct(r.required_coverage)}</td><td>${r.required_matched?.length?`<div class="skill-list">${r.required_matched.map(s=>`<span class="skill-chip">${esc(s)}</span>`).join('')}</div>`:'<span class="muted">No skills detected</span>'}</td><td>${r.required_missing?.length?`<div class="skill-list">${r.required_missing.map(s=>`<span class="skill-chip missing">${esc(s)}</span>`).join('')}</div>`:'<span class="muted">—</span>'}</td><td>${r.preferred_detected?.length?esc(r.preferred_detected.join(', ')):'—'}</td><td>${badge(r.decision)}</td></tr>`).join('');
  content.innerHTML=`${head('Candidate review','Resume screening',job?`Review resume evidence against ${job.title}. Scores describe text relevance; recruiters make every decision.`:'Upload resumes, match their text to a saved job, and review the evidence.',`<select class="filter-control" id="screen-job" aria-label="Active job">${jobOptions||'<option value="">No saved jobs</option>'}</select><button class="btn btn-primary" id="run-match" ${job?'':'disabled'}>Run matching <span>→</span></button>`)}
    ${!job?empty('Create a job to begin','Save a job description before matching candidates.','<button class="btn btn-primary" data-goto="jobs">Create a job</button>'):''}
    <section class="panel resume-upload-panel"><div class="panel-head"><div><h2>Upload candidate resumes</h2><p>Multiple PDF, DOCX, or TXT files · up to ${appState.max_upload_mb} MB each and 250 MB per batch</p></div><span class="badge badge-blue">${candidates().length} saved</span></div><form id="upload-form"><label class="resume-dropzone" id="resume-dropzone" for="resume-files"><input id="resume-files" type="file" name="resumes" multiple accept=".pdf,.docx,.txt" hidden><span class="upload-icon">↑</span><strong>Drop resume files here</strong><span class="upload-drop-hint">or choose one or more files from your device</span><span class="btn btn-outline btn-small">Browse files</span></label><div class="upload-footer"><div id="selected-files" class="upload-list">No files selected yet.</div><button class="btn btn-primary" type="submit">Parse and save resumes</button></div></form><div id="upload-results"></div></section>
    <section class="panel"><div class="panel-head"><div><h2>Candidate ranking</h2><p>${ranked.length} candidate${ranked.length===1?'':'s'} · Formula: ${job?.required_skills?.length?'65% × text similarity + 35% × required skill coverage':'text similarity only'} · scores are not hiring probabilities.</p></div><div class="range-wrap">Minimum score <input id="min-score" type="range" min="0" max="100" value="0"><b id="range-value">0%</b></div></div>
      ${ranked.length?table(['Rank','Candidate','Relevance','Coverage','Required matched','Potential gaps','Preferred found','Decision'],rowHtml):empty('No ranking yet','Load fictional demo data or upload resumes, then run matching.')}</section>`;
  document.getElementById('run-match')?.addEventListener('click',runMatch);
  document.getElementById('screen-job')?.addEventListener('change',async e=>{if(!e.target.value)return;try{const d=await api(`/api/jobs/${e.target.value}/active`,{method:'POST'});appState=d.state;renderPage();}catch(x){showNotice(x.message,'error');}});
  document.getElementById('resume-files')?.addEventListener('change',e=>{const f=[...e.target.files];document.getElementById('selected-files').textContent=f.length?f.map(x=>`${x.name} · ${(x.size/1024/1024).toFixed(2)} MB`).join(' · '):'No files selected yet.';});
  const dropzone=document.getElementById('resume-dropzone');
  dropzone?.addEventListener('dragover',e=>{e.preventDefault();dropzone.classList.add('dragging');});
  dropzone?.addEventListener('dragleave',()=>dropzone.classList.remove('dragging'));
  dropzone?.addEventListener('drop',e=>{e.preventDefault();dropzone.classList.remove('dragging');const input=document.getElementById('resume-files');if(e.dataTransfer?.files?.length){input.files=e.dataTransfer.files;input.dispatchEvent(new Event('change',{bubbles:true}));}});
  document.getElementById('upload-form')?.addEventListener('submit',uploadFiles);
  document.getElementById('min-score')?.addEventListener('input',e=>{document.getElementById('range-value').textContent=`${e.target.value}%`;document.querySelectorAll('tr[data-score]').forEach(row=>row.hidden=Number(row.dataset.score)<Number(e.target.value));});
  document.querySelectorAll('[data-inspect]').forEach(b=>b.onclick=()=>{selectedCandidateId=b.dataset.inspect;navigate('insights');});
}

async function uploadFiles(event){
  event.preventDefault();const input=document.getElementById('resume-files');if(!input.files.length){showNotice('Choose at least one resume file.','error');return;}
  const fd=new FormData();[...input.files].forEach(f=>fd.append('resumes',f));
  try{const d=await api('/api/upload',{method:'POST',body:fd});appState=d.state;const out=d.outcomes.map(x=>`<div class="${x.status==='Error'?'warning':'evidence'}"><b>${esc(x.filename)}</b> · ${esc(x.status)}${x.error?` · ${esc(x.error)}`:''}${x.warnings?.length?`<br>${x.warnings.map(esc).join('<br>')}`:''}</div>`).join('');document.getElementById('upload-results').innerHTML=out;document.getElementById('resume-files').value='';document.getElementById('selected-files').textContent='';showNotice('Resume parsing finished. Review any warnings before matching.');}catch(e){showNotice(e.message,'error');}
}
async function runMatch(){try{const d=await api('/api/match',jsonOptions({job_id:document.getElementById('screen-job')?.value||undefined}));appState=d.state;showNotice(d.message);renderPage();}catch(e){showNotice(e.message,'error');}}

function renderInsights(){
  const ranked=rows();const id=selectedCandidateId&&ranked.some(r=>r.id===selectedCandidateId)?selectedCandidateId:ranked[0]?.id;selectedCandidateId=id;
  const chosen=ranked.find(r=>r.id===id);const c=candidates().find(x=>x.id===id);
  if(!chosen||!c){content.innerHTML=`${head('Candidate review','Candidate insights','Review matching components, cited resume evidence, and questions for follow-up.')}${empty('No candidate profile to show','Run matching or load fictional demo data to review candidate evidence.')}`;return;}
  const matched=chosen.required_matched||[],missing=chosen.required_missing||[],pref=chosen.preferred_detected||[];
  content.innerHTML=`${head('Candidate review','Candidate insights','Evidence and possible gaps are prompts for recruiter verification, not automatic conclusions.')}
    <div class="insight-layout"><aside class="panel"><div class="panel-head"><div><h2>Candidate list</h2><p>${ranked.length} ranked profiles</p></div></div><div class="candidate-pick">${ranked.map(r=>`<button class="${r.id===id?'active':''}" data-pick="${esc(r.id)}"><b>#${r.rank} · ${esc(r.name)}</b><small>${pct(r.score)} textual match · ${esc(r.decision)}</small></button>`).join('')}</div></aside>
    <div><section class="panel"><div class="panel-head"><div><h2>${esc(c.name)}</h2><p>${esc(chosen.label||'Textual relevance')} · label describes document match only</p></div>${badge(chosen.decision)}</div><div class="score-cards"><div class="score-box"><small>Overall relevance</small><b>${pct(chosen.score)}</b></div><div class="score-box"><small>TF-IDF text similarity</small><b>${pct(chosen.similarity)}</b></div><div class="score-box"><small>Required coverage</small><b>${chosen.required_coverage==null?'Unavailable':pct(chosen.required_coverage)}</b></div></div><div class="score-detail-meter">${scoreMeter(chosen.score,'overall textual relevance')}<p class="help-note">Formula: ${chosen.required_coverage==null?'100% × text similarity ('+pct(chosen.similarity)+')':'65% × text similarity ('+pct(chosen.similarity)+') + 35% × required coverage ('+pct(chosen.required_coverage)+')'} = ${pct(chosen.score)}. This describes text relevance only, not hiring probability.</p><p class="match-explanation">${matched.length} of ${activeJob()?.required_skills?.length||0} required skills were detected${missing.length?`; ${esc(missing.join(', '))} were not found in the resume text and need verification`:''}${pref.length?`; preferred skills found: ${esc(pref.join(', '))}`:''}.</p></div>
      <div class="grid-equal"><div><h2>Required skills detected</h2><div class="skill-list" style="margin-top:9px">${matched.length?matched.map(s=>`<span class="skill-chip">${esc(s)}</span>`).join(''):'<span class="muted">None detected</span>'}</div></div><div><h2>Potential gaps to verify</h2><div class="skill-list" style="margin-top:9px">${missing.length?missing.map(s=>`<span class="skill-chip missing">${esc(s)}</span>`).join(''):'<span class="muted">No configured gaps detected</span>'}</div></div></div><div style="margin-top:18px"><h2>Preferred skills found</h2><div class="skill-list" style="margin-top:9px">${pref.length?pref.map(s=>`<span class="skill-chip preferred">${esc(s)}</span>`).join(''):'<span class="muted">None detected</span>'}</div></div></section>
      <section class="panel"><div class="panel-head"><div><h2>Resume evidence</h2><p>Excerpts retrieved from the parsed resume text</p></div></div><div id="candidate-evidence">${c.warnings?.map(w=>`<div class="warning">${esc(w)}</div>`).join('')||''}</div></section>
      <section class="panel"><div class="panel-head"><div><h2>Interview preparation</h2><p>Questions use job requirements and resume evidence; unverified skills are framed as questions.</p></div><div class="form-actions"><button class="btn btn-outline btn-small" id="copy-interview">Copy questions</button><button class="btn btn-soft btn-small" id="download-interview">Export .txt</button></div></div><div id="interview-questions" class="interview-question-list"><div class="evidence">Preparing evidence-linked questions…</div></div><p class="help-note">Use only job-related prompts. A missing resume phrase is not proof the candidate lacks a skill.</p></section></div></div>`;
  document.querySelectorAll('[data-pick]').forEach(b=>b.onclick=()=>{selectedCandidateId=b.dataset.pick;renderPage();});
  api(`/api/candidates/${id}`).then(d=>{const box=document.getElementById('candidate-evidence');if(box){const snippets=d.evidence||[];box.innerHTML=`${c.warnings?.map(w=>`<div class="warning">${esc(w)}</div>`).join('')||''}${snippets.length?snippets.map(s=>`<div class="evidence">${esc(s)}</div>`).join(''):'<div class="empty">No resume evidence was retrieved for the configured requirements.</div>'}`;}
    const list=document.getElementById('interview-questions');if(list){list.innerHTML=(d.interview_questions||[]).map((q,i)=>`<article class="interview-question"><b>${i+1}. ${esc(q.question)}</b><p>${esc(q.why)}</p>${q.evidence?.length?q.evidence.map(x=>`<blockquote>${esc(x)}</blockquote>`).join(''):'<small>No directly matching resume excerpt; use this to verify requirements during interview.</small>'}</article>`).join('')||'<div class="empty">No questions available for this role yet.</div>';list.dataset.plain=(d.interview_questions||[]).map((q,i)=>`${i+1}. ${q.question}\nWhy: ${q.why}${q.evidence?.length?`\nEvidence: ${q.evidence.join(' ')}`:''}`).join('\n\n');}
  }).catch(()=>{});
  document.getElementById('copy-interview')?.addEventListener('click',async()=>{const text=document.getElementById('interview-questions')?.dataset.plain||'';if(!text){showNotice('Interview questions are still loading.','error');return;}try{await navigator.clipboard.writeText(text);showNotice('Interview questions copied.');}catch{showNotice('Clipboard access is unavailable in this browser.','error');}});
  document.getElementById('download-interview')?.addEventListener('click',()=>{const text=document.getElementById('interview-questions')?.dataset.plain||'';if(!text){showNotice('Interview questions are still loading.','error');return;}const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));a.download='interview-preparation.txt';a.click();URL.revokeObjectURL(a.href);});
}

function renderAssistant(){
  const ranked=rows(),candidateId=selectedCandidateId&&candidates().some(c=>c.id===selectedCandidateId)?selectedCandidateId:ranked[0]?.id;
  const selected=ranked.find(r=>r.id===candidateId);
  content.innerHTML=`${head('Recruiter workspace','Recruiter assistant','Ask focused questions about a candidate’s resume and the selected role. Responses include supporting excerpts for review.')}
    ${ranked.length?`<div class="assistant-layout"><aside class="assistant-context panel"><div class="assistant-context-head"><span class="assistant-orb">✳</span><div><h2>Review context</h2><p>Choose a candidate and role</p></div></div><div class="field"><label for="assistant-candidate">Candidate</label><select id="assistant-candidate">${ranked.map(r=>`<option value="${esc(r.id)}" ${r.id===candidateId?'selected':''}>#${r.rank} · ${esc(r.name)}</option>`).join('')}</select></div><div class="context-card"><small>ACTIVE ROLE</small><b>${esc(activeJob()?.title||'No active job')}</b><span>${(activeJob()?.required_skills||[]).length} required skills configured</span></div><div class="assistant-privacy"><span class="live-dot"></span>Local evidence search<br><small>No resume data is sent to an AI service.</small></div></aside>
      <section class="assistant-chat panel"><div class="assistant-chat-head"><div><span class="assistant-kicker">SMART HIRE ASSISTANT</span><h2>How can I help with this review?</h2><p>Answers are limited to resume text and the active job description.</p></div><span class="badge badge-green">Evidence grounded</span></div>
        <div class="assistant-prompts"><span class="prompt-label">QUICK QUESTIONS</span><div class="prompt-list"><button class="prompt-chip sample-question">Which required skills are evidenced?</button><button class="prompt-chip sample-question">What should I verify in an interview?</button><button class="prompt-chip sample-question">Summarize relevant project evidence</button><button class="prompt-chip sample-question">Suggest behavioral interview questions</button></div></div>
        <div id="assistant-result" class="assistant-result">${assistantHistory.length?assistantHistory.map(renderAssistantTurn).join(''):`<div class="assistant-welcome"><span class="assistant-avatar">✳</span><div><b>Ready to help you review ${esc(selected?.name||'this candidate')}</b><p>Choose a quick question or type your own. The response will show the resume excerpts it used.</p></div></div>`}</div>
        <form id="assistant-form" class="assistant-composer"><label class="sr-only" for="assistant-question">Ask a question</label><textarea id="assistant-question" rows="2" placeholder="Ask about skills, evidence, or interview follow-up…" required></textarea><div class="composer-footer"><span>Use job-related questions. Verify every answer with the source resume.</span><button class="btn btn-primary" type="submit">Ask assistant <span>→</span></button></div></form>
      </section></div><p class="assistant-disclaimer">This assistant uses local retrieval and transparent rules, not a generative model. Resume content is treated as untrusted data.</p>`:empty('No candidates available','Load fictional sample data or add resumes, then run matching.')}`;
  document.querySelectorAll('.sample-question').forEach(b=>b.onclick=()=>{document.getElementById('assistant-question').value=b.textContent;document.getElementById('assistant-form').requestSubmit();});
  document.getElementById('assistant-candidate')?.addEventListener('change',e=>{selectedCandidateId=e.target.value;assistantHistory=[];const name=candidates().find(c=>c.id===selectedCandidateId)?.name||'this candidate';document.getElementById('assistant-result').innerHTML=`<div class="assistant-welcome"><span class="assistant-avatar">✳</span><div><b>Ready to help you review ${esc(name)}</b><p>Choose a quick question or type your own. The response will show the resume excerpts it used.</p></div></div>`;});
  document.getElementById('assistant-form')?.addEventListener('submit',askAssistant);
}
function renderAssistantTurn(turn){return `<article class="assistant-turn"><div class="response-question"><span>YOU ASKED</span><p>${esc(turn.question)}</p></div><div class="response-answer"><span class="assistant-avatar">✳</span><div><small>RESPONSE</small><p>${esc(turn.answer)}</p></div></div><details class="response-evidence" ${turn.open?'open':''}><summary>Supporting resume evidence <span>${turn.evidence.length} excerpt${turn.evidence.length===1?'':'s'}</span></summary>${turn.evidence.length?turn.evidence.map((x,i)=>`<blockquote><b>${i+1}</b>${esc(x)}</blockquote>`).join(''):'<div class="evidence-empty">No matching excerpt was found. Check the source resume directly before drawing conclusions.</div>'}</details><div class="response-note">${esc(turn.mode)} · Verify the cited text before making a decision.</div></article>`;}
async function askAssistant(event){event.preventDefault();const target=document.getElementById('assistant-result'),submit=document.querySelector('#assistant-form button[type="submit"]');const question=document.getElementById('assistant-question').value.trim();if(!question)return;target.className='assistant-result is-loading';target.innerHTML='<div class="assistant-thinking"><span class="thinking-dots">•••</span><span>Searching the selected resume for evidence…</span></div>';if(submit){submit.disabled=true;submit.textContent='Searching…';}
  try{const d=await api('/api/assistant',jsonOptions({candidate_id:document.getElementById('assistant-candidate').value,job_id:activeJob()?.id,question}));assistantHistory.push({question,answer:d.answer,evidence:d.evidence||[],mode:d.mode,open:assistantHistory.length===0});target.className='assistant-result';target.innerHTML=assistantHistory.map(renderAssistantTurn).join('');document.getElementById('assistant-question').value='';target.scrollIntoView({block:'nearest',behavior:'smooth'});}catch(e){target.className='assistant-result';target.innerHTML=`<div class="warning">${esc(e.message)}</div>`;}finally{if(submit){submit.disabled=false;submit.innerHTML='Ask assistant <span>→</span>';}}
}

function renderDecisions(){
  const people=candidates(),jobs=appState.jobs||[];const selectedJob=activeJob();
  const ds=(appState.decisions||[]).map(d=>`<tr><td class="td-name">${esc(d.name)}</td><td>${esc(d.job_title)}</td><td>${badge(d.decision)}</td><td>${esc(d.reason)}</td><td>${esc(new Date(d.created_at).toLocaleString())}</td></tr>`).join('');
  const hist=(appState.history||[]).map(h=>`<article class="history-card"><div class="history-card-head"><div><b>${esc(h.name)}</b><small>${esc(h.job_title)}</small></div><div class="history-card-meta"><div class="history-states">${h.old_decision?badge(h.old_decision):'<span class="badge badge-gray">New decision</span>'}<span class="history-arrow">→</span>${badge(h.new_decision)}</div><time>${esc(new Date(h.changed_at).toLocaleString())}</time></div></div><div class="history-reasons"><div><small>Previous reason</small><p>${esc(h.old_reason||'First recorded decision')}</p></div><div><small>Updated reason</small><p>${esc(h.new_reason)}</p></div></div></article>`).join('');
  content.innerHTML=`${head('Human review','Decision register','Record recruiter decisions with a job-related reason. Updates are retained in the audit history.')}
    ${people.length&&jobs.length?`<section class="panel"><div class="panel-head"><div><h2>Record a decision</h2><p>ML scores never change saved decisions automatically</p></div></div><form id="decision-form" class="decision-form"><div class="field"><label for="decision-job">Job</label><select id="decision-job">${jobs.map(j=>`<option value="${esc(j.id)}" ${selectedJob?.id===j.id?'selected':''}>${esc(j.title)}</option>`).join('')}</select></div><div class="field"><label for="decision-candidate">Candidate</label><select id="decision-candidate">${people.map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('')}</select></div><div class="field"><label for="decision-value">Recruiter decision</label><select id="decision-value"><option>Shortlisted</option><option selected>Review Required</option><option>Not Selected</option></select></div><div></div><div class="field full"><label for="decision-reason">Job-related reason <span class="muted">required</span></label><textarea id="decision-reason" required placeholder="Explain the decision using job-related evidence."></textarea></div><div class="field full"><div class="form-actions"><button class="btn btn-primary" type="submit">Save recruiter decision</button></div></div></form></section>
    <section class="panel"><div class="panel-head"><div><h2>Decision history</h2><p>${(appState.history||[]).length} recorded event(s)</p></div></div><div class="decision-history-list">${hist||'<div class="decisions-empty">No history yet. The first saved decision starts the audit trail.</div>'}</div></section>
    <section class="panel"><div class="panel-head"><div><h2>Current decisions</h2><p>${(appState.decisions||[]).length} current recruiter record(s)</p></div></div>${ds?table(['Candidate','Job','Decision','Job-related reason','Updated'],ds):empty('No decisions saved yet','Use the form to record a recruiter decision.')}</section>`:empty('Add job and candidate records','Create a job and add resumes before recording decisions.')}`;
  document.getElementById('decision-form')?.addEventListener('submit',saveDecisionForm);
}
async function saveDecisionForm(event){event.preventDefault();try{const d=await api('/api/decisions',jsonOptions({job_id:document.getElementById('decision-job').value,candidate_id:document.getElementById('decision-candidate').value,decision:document.getElementById('decision-value').value,reason:document.getElementById('decision-reason').value}));appState=d.state;showNotice(d.message);renderPage();}catch(e){showNotice(e.message,'error');}}

function renderReports(){
  const job=activeJob(),ranked=rows(),decisions=(appState.decisions||[]).filter(d=>!job||d.job_id===job.id);
  const links=[['ranking','Candidate ranking','Rank, relevance components, skills, and current decisions'],['gaps','Skill gap analysis','Required skills detected and potential gaps'],['summaries','Candidate summaries','Job-specific evidence excerpts and recruiter context'],['decisions','Recruiter decisions','Saved human decisions and job-related reasons']];
  content.innerHTML=`${head('Data export','Reports & export','Create UTF-8 CSV reports from the selected job and actual records.',job?`<span class="badge badge-blue">${esc(job.title)}</span>`:'')}
    ${job?`<div class="panel"><div class="panel-head"><div><h2>Available downloads</h2><p>${ranked.length} ranked candidates · ${decisions.length} saved decision(s)</p></div></div><div class="job-list">${links.map(([kind,title,description])=>`<div class="job-item"><div><h3>${esc(title)}</h3><p>${esc(description)}</p></div><a class="btn btn-outline btn-small" href="/api/reports/${kind}.csv?job_id=${encodeURIComponent(job.id)}">Download CSV <span>↓</span></a></div>`).join('')}</div></div>
    <section class="panel"><div class="panel-head"><div><h2>Recruitment summary</h2><p>Calculated from this job's saved records</p></div></div><div class="assistant-answer">Job: <b>${esc(job.title)}</b><br>Candidates ranked: <b>${ranked.length}</b><br>Average relevance: <b>${ranked.length?pct(ranked.reduce((sum,r)=>sum+r.score,0)/ranked.length):'—'}</b><br>Shortlisted: <b>${ranked.filter(r=>r.decision==='Shortlisted').length}</b><br>Review required: <b>${ranked.filter(r=>r.decision==='Review Required').length}</b><br><br>Scores indicate text relevance only and require recruiter review.</div></section>`:empty('No job to report on','Save a job description to generate reports.')}`;
}

function renderAbout(){
  content.innerHTML=`${head('Transparency','About & model transparency','A local prototype for recruiter-led resume review.')}
    <div class="transparency-grid"><section class="panel"><div class="panel-head"><h2>How matching works</h2></div><p class="help-note" style="font-size:11px">Job and resume text are compared using scikit-learn TF-IDF vectors and cosine similarity. Configured skill phrases are detected with boundary-aware matching. Required skill coverage is the fraction of listed required skills found in resume text.</p><div class="formula">Overall relevance = <strong>65%</strong> × text similarity<br>+ <strong>35%</strong> × required skill coverage<br><span style="color:#aebed0;font:10px 'DM Sans',sans-serif">With no required skills, text similarity alone is used. Preferred skills are shown separately.</span></div><p class="help-note" style="margin-top:12px">A score is not a hiring probability or an objective measure of candidate worth. Text overlap is only one input for human review.</p></section>
    <section class="panel"><div class="panel-head"><h2>Responsible use and privacy</h2></div><ul class="help-note" style="font-size:10px;line-height:2"><li>Resume text and contact fields are processed and stored locally.</li><li>Names and contact details are not matching features.</li><li>No protected characteristics are inferred.</li><li>Recruiters make and explain every hiring decision.</li><li>Resume content is treated as untrusted data, never as instructions.</li><li>No generative LLM, paid API, or external service is used.</li></ul></section></div>
    <section class="panel"><div class="panel-head"><h2>Limitations</h2></div><p class="help-note" style="font-size:10px;line-height:1.8">PDF/DOCX extraction depends on optional parser packages. Scanned PDF OCR is not implemented. Text extraction may miss layout and context. Skill vocabulary matching can miss synonyms and proficiency. TF-IDF favors wording overlap. SmartHire AI is a local demonstration prototype, not a production applicant tracking system.</p></section>
    <details class="panel danger-zone"><summary>Clear local prototype records</summary><p class="warning">This permanently deletes all jobs, candidates, matches, decisions, and decision history from the local prototype database.</p><form id="clear-form"><label class="confirm-row"><input id="clear-check" type="checkbox"> I understand this permanently deletes local records.</label><div class="form-grid"><div class="field"><label for="clear-phrase">Type DELETE to confirm</label><input id="clear-phrase" autocomplete="off"></div></div><button class="btn btn-danger" type="submit">Delete all local records</button></form></details>`;
  document.getElementById('clear-form').addEventListener('submit',clearRecords);
}
async function clearRecords(event){event.preventDefault();try{const d=await api('/api/clear',jsonOptions({confirmed:document.getElementById('clear-check').checked,phrase:document.getElementById('clear-phrase').value}));appState=d.state;showNotice(d.message);renderPage();}catch(e){showNotice(e.message,'error');}}

function renderPage(){
  if(!appState)return;
  document.querySelectorAll('.nav-item[data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===currentPage));
  ({dashboard:renderDashboard,jobs:renderJobs,screening:renderScreening,insights:renderInsights,assistant:renderAssistant,decisions:renderDecisions,reports:renderReports}[currentPage]||renderDashboard)();
  document.querySelectorAll('[data-goto]').forEach(b=>b.onclick=()=>navigate(b.dataset.goto));
}
function navigate(page){currentPage=page;renderPage();history.replaceState(null,'',`#${page}`);window.scrollTo({top:0,behavior:'smooth'});}
async function refresh(){try{appState=await api('/api/state');renderPage();showNotice('Workspace data refreshed.','info');}catch(e){showNotice(e.message,'error');}}
async function loadSamples(){try{const d=await api('/api/samples',jsonOptions({}));appState=d.state;editingJobId=null;showNotice(d.message);navigate('dashboard');}catch(e){showNotice(e.message,'error');}}
document.getElementById('navigation').addEventListener('click',e=>{const button=e.target.closest('[data-page]');if(button)navigate(button.dataset.page);});
window.addEventListener('hashchange',()=>{const page=location.hash.slice(1);if(pageNames[page])navigate(page);});
async function boot(){try{appState=await api('/api/state');const requested=location.hash.slice(1);if(pageNames[requested])currentPage=requested;renderPage();}catch(e){content.innerHTML=empty('Website could not load',e.message);}}
boot();
