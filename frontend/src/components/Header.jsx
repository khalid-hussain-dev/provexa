import { LogOut, ShieldCheck, Sparkles } from 'lucide-react';

const TABS = [
  ['profile', 'Evidence'],
  ['opportunities', 'Target job'],
  ['interview', 'Interview'],
  ['verdict', 'Readiness'],
  ['course', 'Learning path'],
  ['resume', 'Resume'],
];

export default function Header({ activeTab, setActiveTab, candidate, user, mode, onOpenSubscription, onLogout }) {
  return (
    <header className="app-header">
      <div className="header-inner">
        <button className="brand-button" type="button" onClick={() => setActiveTab('profile')} aria-label="Go to PROVEXA workspace">
          <span className="brand-wordmark">PROVEXA</span>
          <span className="brand-tagline">From potential to proof</span>
        </button>
        <nav className="workspace-tabs" aria-label="Workspace steps">
          {TABS.map(([id, label], index) => (
            <button key={id} type="button" className={activeTab === id ? 'active' : ''} onClick={() => setActiveTab(id)} aria-current={activeTab === id ? 'step' : undefined}>
              <span>0{index + 1}</span>{label}
            </button>
          ))}
        </nav>
        <div className="header-actions">
          <span className={`mode-pill ${mode === 'demo' ? 'demo' : ''}`}><Sparkles size={13} /> {mode === 'demo' ? 'Demo' : 'Live'}</span>
          <button type="button" className="btn-secondary small-button" onClick={onOpenSubscription}>Pro demo</button>
          <button type="button" className="user-button" onClick={onLogout} title="Sign out">
            <ShieldCheck size={15} /> <span>{user?.name || candidate?.name || 'Account'}</span><LogOut size={14} />
          </button>
        </div>
      </div>
    </header>
  );
}
