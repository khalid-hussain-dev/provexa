import { AlertTriangle, ArrowRight, BookOpen, CheckCircle2, FileText } from 'lucide-react';
import { EmptyState, Notice, ProgressBar, StepHeader } from './UI';

export default function ReadinessVerdict({ selectedJob, jobAnalysis, interviewState, onGenerateCourse, onTailorResume }) {
  const result = interviewState?.evaluation?.result;
  if (!selectedJob || !interviewState || !result) {
    return <div className="workspace-page"><StepHeader eyebrow="04 · Readiness" title="Your verdict will appear here." description="Complete the target-job interview to receive a validated result." /><EmptyState title="Interview result not available" message="Return to the Interview step and complete every question before opening the readiness report." /></div>;
  }

  const verdict = result.verdict || 'Evaluation complete';
  return <div className="workspace-page"><StepHeader eyebrow="04 · Readiness" title="Know where you stand." description={`${selectedJob.title} · ${selectedJob.company}. The report keeps Platform match and Intelligence evaluation distinct.`}><span className="verdict-badge">{verdict}</span></StepHeader><div className="readiness-hero surface dark-surface"><div><span className="eyebrow">Interview evaluation</span><h2>{result.assessed_level || 'Readiness'} for {result.target_role || selectedJob.title}</h2><p>{result.interview_summary || 'The integrated Intelligence evaluator returned a validated interview result.'}</p></div><div className="hero-score"><strong>{Math.round(result.overall_score || 0)}</strong><span>overall score</span></div></div><div className="score-grid"><Score label="Role match" value={jobAnalysis?.match_score} /><Score label="Platform readiness" value={jobAnalysis?.readiness_score} /><Score label="Interview score" value={result.overall_score} /></div><div className="two-column-layout"><section className="surface"><div className="section-heading compact"><CheckCircle2 size={18} /><div><h2>What is working</h2><p>Signals returned by the evaluator.</p></div></div><List items={result.analysis?.strengths} empty="No strengths were returned." /></section><section className="surface"><div className="section-heading compact"><AlertTriangle size={18} /><div><h2>Where proof is thin</h2><p>Use these gaps to choose the next action.</p></div></div><List items={result.analysis?.weaknesses} empty="No weaknesses were returned." /></section></div><section className="surface action-surface"><div><span className="eyebrow">Next best action</span><h2>Turn the gap into new evidence.</h2><p>Generate the targeted learning path, then use the completed course to optimize an evidence-backed resume.</p></div><div className="action-buttons"><button type="button" className="btn-primary" onClick={onGenerateCourse}><BookOpen size={16} /> Generate learning path <ArrowRight size={15} /></button><button type="button" className="btn-secondary" onClick={onTailorResume}><FileText size={16} /> Open resume builder</button></div></section>{!result.verdict && <Notice tone="info">The integrated evaluation contract does not expose an application decision field. PROVEXA is showing “Evaluation complete” rather than inventing a verdict.</Notice>}</div>;
}

function Score({ label, value }) {
  const available = value !== undefined && value !== null;
  return <div className="surface score-card"><span className="meta-label">{label}</span><strong>{available ? `${Math.round(value)}` : '—'}</strong>{available && <ProgressBar value={value} />}</div>;
}

function List({ items, empty }) {
  return items?.length ? <ul className="report-list">{items.map((item, index) => <li key={`${displayItem(item)}-${index}`}>{displayItem(item)}</li>)}</ul> : <p className="muted">{empty}</p>;
}

function displayItem(item) {
  if (typeof item === 'string') return item;
  if (item && typeof item === 'object') return item.skill || item.skill_name || item.title || item.message || 'Assessment detail';
  return 'Assessment detail';
}
