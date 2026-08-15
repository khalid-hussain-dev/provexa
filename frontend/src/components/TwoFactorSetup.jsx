import { useEffect, useState } from 'react';
import { CheckCircle2, Copy, KeyRound, ShieldCheck, X } from 'lucide-react';
import { Notice } from './UI';

export default function TwoFactorSetup({ isOpen, user, mode, onBegin, onVerify, onClose }) {
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setSetup(null);
    setCode('');
    setBusy(false);
    setError('');
    setCopied(false);
    setCompleted(false);
  }, [isOpen]);

  if (!isOpen) return null;

  async function begin() {
    setBusy(true);
    setError('');
    try {
      setSetup(await onBegin());
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setBusy(false);
    }
  }

  async function copySecret() {
    try {
      await navigator.clipboard?.writeText(setup.secret);
      setCopied(true);
    } catch {
      setError('Copy is unavailable in this browser. Select the authenticator key and copy it manually.');
    }
  }

  async function verify(event) {
    event.preventDefault();
    if (!code.trim()) return;
    setBusy(true);
    setError('');
    try {
      await onVerify(code.trim());
      setCompleted(true);
    } catch (operationError) {
      setError(operationError.message);
    } finally {
      setBusy(false);
    }
  }

  const accountName = user?.email || 'your PROVEXA account';
  return <div className="modal-backdrop" role="presentation" onClick={onClose}>
    <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="two-factor-title" onClick={(event) => event.stopPropagation()}>
      <button type="button" className="icon-button modal-close" onClick={onClose} aria-label="Close two-factor authentication"><X size={18} /></button>
      {completed || user?.two_factor_enabled ? <div className="modal-success"><ShieldCheck size={42} /><h2 id="two-factor-title">Two-factor authentication is active</h2><p>Future sign-ins require the time-based code from your authenticator app.</p><button type="button" className="btn-primary" onClick={onClose}>Return to workspace</button></div> : <>
        <span className="eyebrow">Account security</span>
        <h2 id="two-factor-title">Enable two-factor authentication</h2>
        <p className="muted">Use an authenticator app to protect {accountName}. The setup key is shown only for this enrollment flow.</p>
        {mode === 'demo' && <Notice tone="info">Demo mode accepts the verification code <strong>123456</strong> and never contacts an external provider.</Notice>}
        {error && <Notice tone="error">{error}</Notice>}
        {!setup ? <div className="modal-actions"><button type="button" className="btn-secondary" onClick={onClose}>Cancel</button><button type="button" className="btn-primary" onClick={begin} disabled={busy}><KeyRound size={16} /> {busy ? 'Preparing setup…' : 'Generate setup key'}</button></div> : <form className="auth-form two-factor-form" onSubmit={verify}>
          <div className="two-factor-step"><span>1</span><div><strong>Add PROVEXA to your authenticator app</strong><p>Enter this account and key manually. Use time-based one-time passwords with six digits.</p></div></div>
          <label className="form-label" htmlFor="two-factor-secret">Authenticator key</label>
          <div className="secret-control"><input id="two-factor-secret" className="form-input mono-input" value={setup.secret} readOnly /><button type="button" className="icon-button" onClick={copySecret} aria-label="Copy authenticator key"><Copy size={16} /></button></div>
          {copied && <Notice tone="success">Authenticator key copied. Keep it private.</Notice>}
          <div className="two-factor-step"><span>2</span><div><strong>Enter the current six-digit code</strong><p>Verification activates 2FA and replaces this session with a protected session.</p></div></div>
          <label className="form-label" htmlFor="enrollment-two-factor-code">Authentication code</label>
          <input id="enrollment-two-factor-code" className="form-input mono-input" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))} required />
          <div className="modal-actions"><button type="button" className="btn-secondary" onClick={onClose}>Cancel</button><button type="submit" className="btn-primary" disabled={busy || code.length !== 6}><CheckCircle2 size={16} /> {busy ? 'Verifying…' : 'Verify and enable'}</button></div>
        </form>}
      </>}
    </section>
  </div>;
}
