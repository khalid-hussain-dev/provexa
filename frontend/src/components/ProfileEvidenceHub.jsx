import { useMemo, useState } from 'react';
import { ArrowRight, FileText, Github, Globe, Linkedin, Save, ShieldCheck, Upload } from 'lucide-react';
import { ErrorState, LoadingState, Notice, ProgressBar, StepHeader, SuccessMessage } from './UI';

export default function ProfileEvidenceHub({ candidate, evidence, onSaveCandidate, onCreateEvidence, onAnalyze, profileAnalysis, onNext }) {
  const [form, setForm] = useState(() => ({
    name: candidate.name || '',
    target_role: candidate.target_role || '',
    experience_years: candidate.experience_years || 0,
    summary: candidate.summary || '',
    location: candidate.location || '',
    skills: (candidate.skills || []).join(', '),
    github_url: candidate.github_url || '',
    linkedin_url: candidate.linkedin_url || '',
    portfolio_url: candidate.portfolio_url || '',
    cv_text: '',
  }));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [fileName, setFileName] = useState('');

  const skills = useMemo(() => form.skills.split(',').map((item) => item.trim()).filter(Boolean), [form.skills]);
  const context = profileAnalysis?.profile_context;
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setSuccess('');
    try {
      const savedCandidate = await onSaveCandidate({ ...candidate, ...form, skills, experience_years: Number(form.experience_years || 0) });
      if (form.cv_text.trim() && !evidence.some((item) => item.source_type === 'CV' && item.content === form.cv_text.trim())) {
        await onCreateEvidence({ source_type: 'CV', title: fileName || 'Candidate CV', content: form.cv_text.trim(), external_url: null, metadata: { file_name: fileName || null } });
      }
      if (form.github_url && !evidence.some((item) => item.source_type === 'GITHUB' && item.external_url === form.github_url)) {
        await onCreateEvidence({ source_type: 'GITHUB', title: 'GitHub profile', content: null, external_url: form.github_url, metadata: {} });
      }
      if (form.portfolio_url && !evidence.some((item) => item.source_type === 'PORTFOLIO' && item.external_url === form.portfolio_url)) {
        await onCreateEvidence({ source_type: 'PORTFOLIO', title: 'Portfolio', content: null, external_url: form.portfolio_url, metadata: {} });
      }
      await onAnalyze();
      setSuccess(`Evidence saved for ${savedCandidate?.name || form.name}. Profile context is ready for matching.`);
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setBusy(false);
    }
  }

  function handleFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    if (file.type === 'text/plain' || file.name.toLowerCase().endsWith('.txt')) {
      file.text().then((text) => update('cv_text', text)).catch(() => setError('The text file could not be read. Paste the CV content instead.'));
    } else {
      setError('PDF and DOCX files are recorded by filename only in this frontend. Paste the text content so the integrated resume evidence contract can use it.');
    }
  }

  return (
    <div className="workspace-page">
      <StepHeader eyebrow="01 · Evidence" title="Make your capability legible." description="Store the source material first. PROVEXA uses it to build an auditable profile context rather than inventing qualifications.">
        <div className="step-count"><ShieldCheck size={16} /> Candidate-scoped</div>
      </StepHeader>
      {error && <ErrorState message={error} onRetry={() => setError('')} />}
      {success && <SuccessMessage>{success}</SuccessMessage>}
      <div className="two-column-layout">
        <form className="surface form-surface" onSubmit={handleSubmit}>
          <div className="section-heading"><FileText size={18} /><div><h2>Candidate record</h2><p>Saved to the authenticated candidate profile.</p></div></div>
          <div className="form-grid two-up">
            <Field label="Name" value={form.name} onChange={(value) => update('name', value)} required />
            <Field label="Email" value={candidate.email} readOnly />
          </div>
          <div className="form-grid two-up">
            <Field label="Target role" value={form.target_role} onChange={(value) => update('target_role', value)} required />
            <Field label="Experience (years)" type="number" value={form.experience_years} onChange={(value) => update('experience_years', value)} min="0" step="0.5" />
          </div>
          <Field label="Location" value={form.location} onChange={(value) => update('location', value)} />
          <label className="form-label" htmlFor="candidate-summary">Summary</label>
          <textarea id="candidate-summary" className="form-textarea" rows="3" value={form.summary} onChange={(event) => update('summary', event.target.value)} />
          <label className="form-label" htmlFor="candidate-skills">Claimed skills</label>
          <input id="candidate-skills" className="form-input mono-input" value={form.skills} onChange={(event) => update('skills', event.target.value)} placeholder="Python, FastAPI, PostgreSQL" />

          <div className="subsection"><div className="section-heading compact"><Upload size={17} /><div><h3>Evidence sources</h3><p>CV content is required for evidence-backed resume optimization.</p></div></div>
            <label className="upload-control" htmlFor="cv-file"><Upload size={18} /><span>{fileName || 'Choose a TXT, PDF, or DOCX file'}</span><input id="cv-file" type="file" accept=".txt,.pdf,.docx" onChange={handleFile} /></label>
            <label className="form-label" htmlFor="cv-text">CV text / evidence notes</label>
            <textarea id="cv-text" className="form-textarea mono-input" rows="7" value={form.cv_text} onChange={(event) => update('cv_text', event.target.value)} placeholder="Paste the candidate’s source CV text here…" />
            <div className="form-grid two-up">
              <Field label="GitHub URL" value={form.github_url} onChange={(value) => update('github_url', value)} icon={<Github size={14} />} />
              <Field label="Portfolio URL" value={form.portfolio_url} onChange={(value) => update('portfolio_url', value)} icon={<Globe size={14} />} />
            </div>
            <Field label="LinkedIn URL" value={form.linkedin_url} onChange={(value) => update('linkedin_url', value)} icon={<Linkedin size={14} />} />
          </div>
          <div className="form-actions"><span className="muted small-text">{evidence.length} evidence record{evidence.length === 1 ? '' : 's'} in this session</span><button className="btn-primary" type="submit" disabled={busy}>{busy ? 'Saving and analyzing…' : 'Save and analyze'} <Save size={16} /></button></div>
        </form>

        <aside className="side-stack">
          <div className="surface dark-surface"><div className="section-heading compact"><ShieldCheck size={18} /><div><h2>Profile context</h2><p>Validated fields from the integrated Intelligence adapter.</p></div></div>
            {busy ? <LoadingState title="Analyzing evidence" message="The integrated profile adapter is preparing a validated context…" /> : context ? <ProfileContext context={context} /> : <Notice tone="neutral">Add evidence and run analysis to see the candidate context.</Notice>}
          </div>
          <div className="surface"><div className="section-heading compact"><FileText size={18} /><div><h2>Evidence inventory</h2><p>Only records created for this candidate are shown.</p></div></div>
            {evidence.length === 0 ? <Notice tone="neutral">No evidence stored yet.</Notice> : <ul className="evidence-list">{evidence.map((item) => <li key={item.evidence_id}><span className="evidence-icon"><FileText size={14} /></span><span><strong>{item.title}</strong><small>{item.source_type}{item.external_url ? ` · ${item.external_url}` : ''}</small></span></li>)}</ul>}
          </div>
          <button className="btn-secondary btn-wide" type="button" onClick={onNext}>Continue to target opportunities <ArrowRight size={16} /></button>
        </aside>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', readOnly = false, required = false, min, step, icon }) {
  return <div className="field-wrap"><label className="form-label" htmlFor={`field-${label.toLowerCase().replaceAll(' ', '-')}`}>{icon}{label}</label><input id={`field-${label.toLowerCase().replaceAll(' ', '-')}`} className="form-input" type={type} value={value ?? ''} onChange={(event) => onChange?.(event.target.value)} readOnly={readOnly} required={required} min={min} step={step} /></div>;
}

function ProfileContext({ context }) {
  const skills = context.all_skills || [];
  return <div className="context-stack"><div><span className="meta-label">Primary domain</span><strong>{displayContextItem(context.primary_domain, 'Not classified')}</strong></div><div><span className="meta-label">Summary</span><p>{displayContextItem(context.candidate_summary, 'No summary returned.')}</p></div><div><span className="meta-label">Skills found</span><div className="tag-list">{skills.length ? skills.map((skill, index) => <span className="tag" key={`skill-${index}`}>{displayContextItem(skill)}</span>) : <span className="muted">None returned</span>}</div></div><div><span className="meta-label">Potential weaknesses</span><ul className="plain-list">{(context.potential_weaknesses || []).map((item, index) => <li key={`weakness-${index}`}>{displayContextItem(item)}</li>)}</ul></div><ProgressBar value={context.domain_confidence || 0} label="Domain confidence" /></div>;
}

function displayContextItem(item, fallback = 'Not specified') {
  if (typeof item === 'string' || typeof item === 'number') return String(item);
  if (!item || typeof item !== 'object') return fallback;
  return item.name || item.skill || item.title || item.description || item.summary || fallback;
}
