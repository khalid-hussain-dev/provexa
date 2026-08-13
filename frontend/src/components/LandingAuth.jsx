import { useState } from 'react';
import { ArrowRight, CheckCircle2, LockKeyhole, ShieldCheck } from 'lucide-react';
import { Notice } from './UI';

export default function LandingAuth({ mode, busy, error, pendingTwoFactor, onLogin, onSignup, onVerifyTwoFactor, onContinueDemo }) {
  const [formMode, setFormMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState(mode === 'demo' ? 'demo@provexa.local' : '');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');

  const submitAuth = (event) => {
    event.preventDefault();
    if (formMode === 'signup') {
      onSignup({ name, email, password });
    } else {
      onLogin({ email, password });
    }
  };

  return (
    <main className="landing-shell">
      <section className="landing-copy">
        <div className="brand-mark">PROVEXA <span>VANTERIX</span></div>
        <span className="eyebrow">Career intelligence instrument</span>
        <h1>From potential<br /><em>to proof.</em></h1>
        <p className="landing-lede">Understand what you can prove, what the opportunity demands, and the next move that makes you ready.</p>
        <div className="proof-chain" aria-label="PROVEXA evidence journey">
          {['Evidence', 'Assessment', 'Proof', 'Readiness'].map((item, index) => (
            <span key={item}><b>0{index + 1}</b>{item}</span>
          ))}
        </div>
      </section>

      <section className="auth-panel" aria-labelledby="auth-title">
        <div className="panel-heading">
          <span className="eyebrow">Candidate workspace</span>
          <h2 id="auth-title">Build your readiness record.</h2>
          <p>Sign in to continue your evidence-backed path.</p>
        </div>

        {mode === 'demo' && (
          <Notice tone="info">Demo mode is active. No backend or provider calls are required.</Notice>
        )}
        {error && <Notice tone="error">{error}</Notice>}

        {pendingTwoFactor ? (
          <form onSubmit={(event) => { event.preventDefault(); onVerifyTwoFactor(code); }} className="auth-form">
            <div className="auth-callout"><ShieldCheck size={20} /><span>Two-factor verification is required by the integrated host.</span></div>
            <label className="form-label" htmlFor="two-factor-code">Authentication code</label>
            <input id="two-factor-code" className="form-input" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={(event) => setCode(event.target.value)} required />
            <button className="btn-primary btn-wide" type="submit" disabled={busy}>{busy ? 'Verifying…' : 'Verify and continue'} <ArrowRight size={16} /></button>
          </form>
        ) : (
          <>
            <div className="auth-tabs" role="tablist" aria-label="Authentication mode">
              <button type="button" role="tab" aria-selected={formMode === 'login'} className={formMode === 'login' ? 'active' : ''} onClick={() => setFormMode('login')}>Sign in</button>
              <button type="button" role="tab" aria-selected={formMode === 'signup'} className={formMode === 'signup' ? 'active' : ''} onClick={() => setFormMode('signup')}>Create account</button>
            </div>
            <form onSubmit={submitAuth} className="auth-form">
              {formMode === 'signup' && (
                <>
                  <label className="form-label" htmlFor="signup-name">Name</label>
                  <input id="signup-name" className="form-input" value={name} onChange={(event) => setName(event.target.value)} required />
                </>
              )}
              <label className="form-label" htmlFor="auth-email">Email</label>
              <input id="auth-email" className="form-input" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
              <label className="form-label" htmlFor="auth-password">Password</label>
              <input id="auth-password" className="form-input" type="password" autoComplete={formMode === 'signup' ? 'new-password' : 'current-password'} minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required />
              <button className="btn-primary btn-wide" type="submit" disabled={busy}>{busy ? 'Working…' : formMode === 'signup' ? 'Create account' : 'Sign in'} <ArrowRight size={16} /></button>
            </form>
            {mode === 'demo' && (
              <button type="button" className="demo-link" onClick={onContinueDemo} disabled={busy}><LockKeyhole size={14} /> Enter seeded demo workspace</button>
            )}
          </>
        )}

        <div className="auth-footnote"><CheckCircle2 size={15} /> Your data remains scoped to the authenticated candidate.</div>
      </section>
    </main>
  );
}
