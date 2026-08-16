import { AlertCircle, CheckCircle2, RotateCcw } from 'lucide-react';

export function Spinner({ size = 24, label = 'Loading' }) {
  return (
    <span className="spinner" role="status" aria-label={label} style={{ width: size, height: size }}>
      <span />
      <span />
      <span />
    </span>
  );
}

export function LoadingState({ title = 'Loading', message = 'Preparing your workspace…' }) {
  return (
    <div className="state-panel" role="status" aria-live="polite">
      <Spinner size={32} label={title} />
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

export function ErrorState({ title = 'Something needs attention', message, onRetry, retryLabel = 'Try again' }) {
  return (
    <div className="state-panel state-error" role="alert">
      <AlertCircle size={28} aria-hidden="true" />
      <h3>{title}</h3>
      <p>{message || 'The operation could not be completed.'}</p>
      {onRetry && (
        <button type="button" className="btn-secondary" onClick={onRetry}>
          <RotateCcw size={15} aria-hidden="true" /> {retryLabel}
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, message, action }) {
  return (
    <div className="state-panel">
      <h3>{title}</h3>
      <p>{message}</p>
      {action}
    </div>
  );
}

export function SuccessMessage({ children }) {
  return (
    <div className="notice notice-success" role="status">
      <CheckCircle2 size={17} aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

export function Notice({ children, tone = 'neutral' }) {
  return <div className={`notice notice-${tone}`}>{children}</div>;
}

export function StepHeader({ eyebrow, title, description, children }) {
  return (
    <div className="step-header">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {children}
    </div>
  );
}

export function ProgressBar({ value, label }) {
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="progress-wrap">
      {label && <div className="progress-label"><span>{label}</span><strong>{safeValue}%</strong></div>}
      <div className="progress-track" aria-label={label || 'Progress'} role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={safeValue}>
        <div className="progress-fill" style={{ width: `${safeValue}%` }} />
      </div>
    </div>
  );
}
