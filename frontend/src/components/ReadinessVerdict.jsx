import { AlertTriangle, ArrowRight, BookOpen, CheckCircle2, FileText } from 'lucide-react';
import { EmptyState, Notice, ProgressBar, StepHeader } from './UI';

export default function ReadinessVerdict({ selectedJob, jobAnalysis, interviewState, onGenerateCourse, onTailorResume }) {
  const result = interviewState?.evaluation?.result;

  if (!selectedJob || !interviewState || !result) {
    return (
      <div className="workspace-page">
        <StepHeader
          eyebrow="04 · Readiness"
          title="Your verdict will appear here."
          description="Complete the target-job interview to receive a validated result."
        />
        <EmptyState
          title="Interview result not available"
          message="Return to the Interview step and complete every question before opening the readiness report."
        />
      </div>
    );
  }

  const verdict = formatVerdict(result.verdict);
  const levelLabel = formatAssessmentLevel(result.assessed_level);
  const interviewScore = roundScore(result.overall_score);
  const roleMatchScore = roundScore(result.role_match_percentage ?? jobAnalysis?.match_score);
  const platformReadinessScore = roundScore(jobAnalysis?.readiness_score);
  const strengths = pickItems(result.analysis?.strengths, result.strengths);
  const weaknesses = pickItems(result.analysis?.weaknesses, result.gaps);
  const recommendations = Array.isArray(result.recommendations) ? result.recommendations : [];
  const summaryText =
    result.interview_summary ||
    `The interview is complete. The score gives a validated snapshot of your readiness for ${result.target_role || selectedJob.title}.`;
  const nextAction = buildNextAction({
    result,
    selectedJob,
    recommendations,
    weaknesses,
    jobAnalysis,
  });

  return (
    <div className="workspace-page">
      <StepHeader
        eyebrow="04 · Readiness"
        title="Know where you stand."
        description={`${selectedJob.title} · ${selectedJob.company}. The report keeps Platform match and Intelligence evaluation distinct.`}
      >
        <span className="verdict-badge">{verdict}</span>
      </StepHeader>

      <div className="readiness-hero surface dark-surface">
        <div>
          <span className="eyebrow">Interview evaluation</span>
          <h2>
            {levelLabel} for {result.target_role || selectedJob.title}
          </h2>
          <p>{summaryText}</p>
        </div>
        <div className="hero-score">
          <strong>{interviewScore}</strong>
          <span>overall score</span>
        </div>
      </div>

      <div className="score-grid">
        <Score label="Role match" value={roleMatchScore} />
        <Score label="Platform readiness" value={platformReadinessScore} />
        <Score label="Interview score" value={interviewScore} />
      </div>

      <div className="two-column-layout">
        <section className="surface">
          <div className="section-heading compact">
            <CheckCircle2 size={18} />
            <div>
              <h2>What is working</h2>
              <p>Signals returned by the evaluator.</p>
            </div>
          </div>
          <List
            items={strengths}
            empty={
              interviewScore >= 70
                ? 'The evaluator did not name strengths, but the score shows credible interview performance.'
                : 'No strengths were returned, so the score and next action are the clearest signals to follow.'
            }
          />
        </section>

        <section className="surface">
          <div className="section-heading compact">
            <AlertTriangle size={18} />
            <div>
              <h2>Where proof is thin</h2>
              <p>Use these gaps to choose the next action.</p>
            </div>
          </div>
          <List
            items={weaknesses}
            empty={
              recommendations.length
                ? 'The evaluator did not return named weaknesses, but the recommendations below still point to the next improvement.'
                : 'No weaknesses were returned. Use the score and learning path to keep sharpening the evidence.'
            }
          />
        </section>
      </div>

      <section className="surface action-surface">
        <div>
          <span className="eyebrow">Next best action</span>
          <h2>{nextAction.title}</h2>
          <p>{nextAction.description}</p>
        </div>
        <div className="action-buttons">
          <button type="button" className="btn-primary" onClick={onGenerateCourse}>
            <BookOpen size={16} /> Generate learning path <ArrowRight size={15} />
          </button>
          <button type="button" className="btn-secondary" onClick={onTailorResume}>
            <FileText size={16} /> Open resume builder
          </button>
        </div>
      </section>

      {!result.verdict && (
        <Notice tone="info">
          The integrated evaluation contract does not expose an application decision field. PROVEXA is showing
          “Evaluation complete” rather than inventing a verdict.
        </Notice>
      )}
    </div>
  );
}

function Score({ label, value }) {
  const available = value !== undefined && value !== null;
  const safeValue = available ? roundScore(value) : null;

  return (
    <div className="surface score-card">
      <span className="meta-label">{label}</span>
      <strong>{available ? `${safeValue}` : '—'}</strong>
      {available && <ProgressBar value={safeValue} />}
    </div>
  );
}

function List({ items, empty }) {
  return items?.length ? (
    <ul className="report-list">
      {items.map((item, index) => (
        <li key={`${displayItem(item)}-${index}`}>{displayItem(item)}</li>
      ))}
    </ul>
  ) : (
    <p className="muted">{empty}</p>
  );
}

function displayItem(item) {
  if (typeof item === 'string') return item;
  if (item && typeof item === 'object') {
    return (
      item.skill ||
      item.skill_name ||
      item.competency ||
      item.title ||
      item.action ||
      item.message ||
      'Assessment detail'
    );
  }
  return 'Assessment detail';
}

function pickItems(primary, fallback) {
  if (Array.isArray(primary) && primary.length) return primary;
  if (Array.isArray(fallback) && fallback.length) return fallback;
  return [];
}

function roundScore(value) {
  return Math.max(0, Math.min(100, Math.round(Number(value) || 0)));
}

function formatVerdict(value) {
  if (!value) return 'Evaluation complete';
  const normalized = String(value)
    .toLowerCase()
    .replace(/_/g, ' ')
    .trim();
  if (normalized === 'apply with caution') return 'Apply with caution';
  if (normalized === 'not ready') return 'Not ready yet';
  if (normalized === 'apply') return 'Ready to apply';
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatAssessmentLevel(value) {
  if (!value) return 'Readiness review';
  const normalized = String(value).replace(/_/g, ' ').trim();
  return `${titleCase(normalized)}-level readiness`;
}

function titleCase(value) {
  return value
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

function buildNextAction({ result, selectedJob, recommendations, weaknesses, jobAnalysis }) {
  const firstRecommendation = recommendations.find(Boolean);
  if (firstRecommendation) {
    const title = firstRecommendation.competency ? `Strengthen ${firstRecommendation.competency}` : 'Strengthen the weakest area';
    const description =
      firstRecommendation.action ||
      firstRecommendation.description ||
      'Use the learning path to turn this gap into stronger proof.';
    return { title, description };
  }

  if (weaknesses.length) {
    return {
      title: 'Turn the weakest signal into new evidence.',
      description: `Focus the learning path on the areas that scored lowest for ${result.target_role || selectedJob.title}.`,
    };
  }

  if ((result.overall_score || 0) >= 80) {
    return {
      title: 'You are close. Tighten the proof and export the resume.',
      description:
        'The interview looks solid, so the next best move is to sharpen supporting evidence and finish the resume step.',
    };
  }

  if ((jobAnalysis?.readiness_score || 0) >= 50) {
    return {
      title: 'Build one more layer of evidence.',
      description:
        'The role match is promising, but the interview is still asking for clearer proof. Use the learning path before retrying.',
    };
  }

  return {
    title: 'Turn the gap into new evidence.',
    description:
      'Generate the targeted learning path, then use the completed course to optimize an evidence-backed resume.',
  };
}
