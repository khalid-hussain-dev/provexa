import { useState } from 'react';
import { Download, FileText, LockKeyhole, Sparkles } from 'lucide-react';
import { buildExportFile, optimizeResume } from '../services/api';
import { ErrorState, EmptyState, LoadingState, Notice, StepHeader } from './UI';

export default function ResumeTailor({ candidate, selectedJob, evidence, course, resumeResult, onResumeReady }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const cvEvidence = evidence.find((item) => item.source_type === 'CV' && item.evidence_id);

  async function handleOptimize() {
    if (!course?.course_id || !cvEvidence?.evidence_id) return;
    setLoading(true);
    setError('');
    try {
      onResumeReady(await optimizeResume({ courseId: course.course_id, evidenceId: cvEvidence.evidence_id }));
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingState title="Optimizing the resume" message="The integrated adapter is preserving the selected CV evidence reference while tailoring the document." />;
  return <div className="workspace-page"><StepHeader eyebrow="06 · Resume" title="Present the proof clearly." description={`Evidence-backed tailoring for ${selectedJob?.title || candidate.target_role || 'your target role'}.`}><div className="step-count"><LockKeyhole size={16} /> Evidence lock</div></StepHeader>{error && <ErrorState message={error} onRetry={() => setError('')} />}{!course || !cvEvidence ? <EmptyState title="Resume optimization is not ready" message={!cvEvidence ? 'Add and analyze a text CV in Evidence first.' : 'Complete at least one course module before optimizing the resume.'} /> : <><section className="surface resume-toolbar"><div><span className="eyebrow">Owned source</span><strong>{cvEvidence.title}</strong><p className="muted">Course: {course.title} · Evidence ID: {cvEvidence.evidence_id}</p></div><button type="button" className="btn-primary" onClick={handleOptimize}><Sparkles size={16} /> Optimize with verified evidence</button></section>{resumeResult ? <div className="resume-grid"><ResumePane title="Source evidence" text={resumeResult.result?.original_resume_text || ''} /><ResumePane title="Tailored preview" text={resumeResult.result?.updated_resume_text || ''} accent /><section className="surface resume-notes"><div className="section-heading compact"><FileText size={17} /><div><h2>Tailoring record</h2><p>What changed at the integration boundary.</p></div></div><p>{resumeResult.result?.summary_of_changes || 'No summary returned.'}</p><div className="tag-list">{(resumeResult.result?.injected_skills || []).map((skill) => <span className="tag" key={skill}>{skill}</span>)}</div><button type="button" className="btn-secondary" onClick={() => buildExportFile(resumeResult.result?.updated_resume_text || '', 'provexa-tailored-resume.txt')}><Download size={15} /> Export text preview</button><Notice tone="info">Export is generated locally in the browser. No new backend route is introduced.</Notice></section></div> : <section className="empty-resume surface"><FileText size={38} /><h2>Your tailored document is waiting.</h2><p>Run the optimizer to view a side-by-side preview backed by the selected CV evidence.</p></section>}</>}</div>;
}

function ResumePane({ title, text, accent = false }) {
  return <article className={`resume-pane ${accent ? 'accent' : ''}`}><div className="resume-pane-title">{title}</div><div className="resume-paper">{text || 'No resume text returned.'}</div></article>;
}
