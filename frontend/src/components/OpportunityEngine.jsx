import { useEffect, useState } from 'react';
import { AlertTriangle, ArrowRight, Briefcase, Check, MapPin, Target, X } from 'lucide-react';
import { listJobs, matchJob } from '../services/api';
import { EmptyState, ErrorState, LoadingState, ProgressBar, StepHeader } from './UI';

export default function OpportunityEngine({ candidate, selectedJob, jobAnalysis, onSelectJob }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [matching, setMatching] = useState(null);

  useEffect(() => { loadJobs(); }, []);

  async function loadJobs() {
    setLoading(true);
    setError('');
    try {
      const response = await listJobs({ limit: 10 });
      const jobsWithMatches = await Promise.all((response.jobs || []).map(async (job) => {
        try {
          const analysis = await matchJob(job.job_id);
          return { ...job, analysis };
        } catch {
          return job;
        }
      }));
      setJobs(jobsWithMatches);
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setLoading(false);
    }
  }

  async function selectJob(job) {
    setMatching(job.job_id);
    setError('');
    try {
      const analysis = job.analysis || await matchJob(job.job_id);
      onSelectJob(job, analysis);
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setMatching(null);
    }
  }

  return (
    <div className="workspace-page">
      <StepHeader eyebrow="02 · Target job" title="Choose the opportunity worth proving." description={`Jobs are selected from the integrated Platform surface and matched against ${candidate.target_role || 'your candidate record'}.`}>
        <div className="step-count"><Target size={16} /> {jobs.length || '—'} opportunities</div>
      </StepHeader>
      {error && <ErrorState message={error} onRetry={loadJobs} />}
      {loading ? <LoadingState title="Finding target opportunities" message="Loading seeded or persisted Platform jobs and their match snapshots…" /> : jobs.length === 0 ? <EmptyState title="No opportunities available" message="The integrated Platform returned an empty job set." action={<button type="button" className="btn-secondary" onClick={loadJobs}>Reload jobs</button>} /> : (
        <div className="opportunity-layout">
          <section className="surface"><div className="section-heading"><Briefcase size={19} /><div><h2>Recommended opportunities</h2><p>Why the match exists stays visible beside the score.</p></div></div><div className="job-list">{jobs.map((job) => <JobCard key={job.job_id} job={job} active={selectedJob?.job_id === job.job_id} busy={matching === job.job_id} onSelect={() => selectJob(job)} />)}</div></section>
          <aside className="surface sticky-panel"><span className="eyebrow">Selected target</span>{selectedJob ? <><h2>{selectedJob.title}</h2><p>{selectedJob.company} · {selectedJob.location || 'Location not specified'}</p><div className="selected-score"><strong>{jobAnalysis?.readiness_score ?? '—'}</strong><span>readiness</span></div><p className="muted">Continue to the interview only after choosing the job you want to assess.</p></> : <><h2>Nothing selected</h2><p>Choose an opportunity to begin the candidate/job analysis leg of the golden path.</p></>}</aside>
        </div>
      )}
    </div>
  );
}

function JobCard({ job, active, busy, onSelect }) {
  const analysis = job.analysis;
  return <article className={`job-card ${active ? 'active' : ''}`}><div className="job-card-head"><div><span className="eyebrow">{job.source || 'Platform opportunity'}</span><h3>{job.title}</h3><p><strong>{job.company}</strong> · <MapPin size={13} /> {job.location || 'Location not specified'}</p></div><div className="job-score"><strong>{analysis?.match_score ?? '—'}</strong><span>match</span></div></div>{job.description && <p className="job-description">{job.description}</p>}{analysis && <><ProgressBar value={analysis.readiness_score} label="Readiness" /><div className="matrix-list">{(analysis.strengths || []).slice(0, 2).map((item, index) => <span key={`s-${index}`} className="matrix-row positive"><Check size={14} /> {item.skill || item}</span>)}{(analysis.gaps || []).slice(0, 2).map((item, index) => <span key={`g-${index}`} className="matrix-row caution"><AlertTriangle size={14} /> {item.skill || item}</span>)}</div></>}{!analysis && <div className="matrix-row caution"><X size={14} /> Match analysis unavailable</div>}<button type="button" className={active ? 'btn-primary btn-wide' : 'btn-secondary btn-wide'} onClick={onSelect} disabled={busy}>{busy ? 'Selecting…' : active ? 'Selected target' : 'Select and assess'} <ArrowRight size={15} /></button></article>;
}
