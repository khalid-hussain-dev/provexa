import { useEffect, useMemo, useState } from 'react';
import Header from './components/Header';
import LandingAuth from './components/LandingAuth';
import ProfileEvidenceHub from './components/ProfileEvidenceHub';
import OpportunityEngine from './components/OpportunityEngine';
import InterviewArena from './components/InterviewArena';
import ReadinessVerdict from './components/ReadinessVerdict';
import PersonalizedCourse from './components/PersonalizedCourse';
import ResumeTailor from './components/ResumeTailor';
import SubscriptionDemo from './components/SubscriptionDemo';
import TwoFactorSetup from './components/TwoFactorSetup';
import WorkspaceErrorBoundary from './components/WorkspaceErrorBoundary';
import { LoadingState, Notice } from './components/UI';
import {
  analyzeProfile,
  clearSession,
  createEvidence,
  getApiMode,
  getCandidate,
  getCurrentUser,
  getAccessToken,
  login,
  logout,
  normalizeCandidate,
  setupTwoFactor,
  signup,
  updateCandidate,
  verifyTwoFactor,
} from './services/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [candidate, setCandidate] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [activeTab, setActiveTab] = useState('profile');
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobAnalysis, setJobAnalysis] = useState(null);
  const [profileAnalysis, setProfileAnalysis] = useState(null);
  const [interviewState, setInterviewState] = useState(null);
  const [course, setCourse] = useState(null);
  const [resumeResult, setResumeResult] = useState(null);
  const [isSubscriptionOpen, setSubscriptionOpen] = useState(false);
  const [isTwoFactorOpen, setTwoFactorOpen] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState('');
  const [pendingTwoFactor, setPendingTwoFactor] = useState(false);
  const [bootState, setBootState] = useState('loading');
  const mode = getApiMode();

  useEffect(() => {
    let cancelled = false;
    async function restoreSession() {
      try {
        if (!getAccessToken()) {
          if (!cancelled) setBootState('ready');
          return;
        }
        const currentUser = await getCurrentUser();
        if (!cancelled && currentUser) await enterWorkspace(currentUser);
      } catch {
        clearSession();
      } finally {
        if (!cancelled) setBootState('ready');
      }
    }
    restoreSession();
    return () => { cancelled = true; };
  }, []);

  async function enterWorkspace(currentUser) {
    const loadedCandidate = await getCandidate(currentUser);
    setUser(currentUser);
    setCandidate(normalizeCandidate(loadedCandidate, currentUser));
    setActiveTab('profile');
  }

  async function handleLogin(payload) {
    setAuthBusy(true);
    setAuthError('');
    try {
      const result = await login(payload);
      if (result.requires_2fa) {
        setPendingTwoFactor(true);
        return;
      }
      await enterWorkspace(await getCurrentUser());
    } catch (error) {
      setAuthError(error.message);
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleSignup(payload) {
    setAuthBusy(true);
    setAuthError('');
    try {
      await signup(payload);
      await handleLogin({ email: payload.email, password: payload.password });
    } catch (error) {
      setAuthError(error.message);
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleVerifyTwoFactor(code) {
    setAuthBusy(true);
    setAuthError('');
    try {
      await verifyTwoFactor(code);
      setPendingTwoFactor(false);
      await enterWorkspace(await getCurrentUser());
    } catch (error) {
      setAuthError(error.message);
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleLogout() {
    try {
      await logout();
    } finally {
      setUser(null);
      setCandidate(null);
      setEvidence([]);
      setSelectedJob(null);
      setInterviewState(null);
      setCourse(null);
      setResumeResult(null);
      setActiveTab('profile');
    }
  }

  async function beginTwoFactorSetup() {
    return setupTwoFactor();
  }

  async function confirmTwoFactorSetup(code) {
    await verifyTwoFactor(code);
    const currentUser = await getCurrentUser();
    if (!currentUser) throw new Error('Your authenticated session could not be restored after two-factor verification.');
    setUser(currentUser);
    return currentUser;
  }

  async function persistCandidate(nextCandidate) {
    const saved = await updateCandidate(nextCandidate);
    setCandidate(normalizeCandidate(saved, user));
    return saved;
  }

  async function persistEvidence(payload) {
    const stored = await createEvidence(payload);
    const record = { ...payload, ...stored };
    setEvidence((current) => [...current, record]);
    return record;
  }

  async function runProfileAnalysis() {
    const result = await analyzeProfile();
    setProfileAnalysis(result);
    return result;
  }

  const workspaceContent = useMemo(() => {
    if (!candidate) return <div className="workspace-page"><LoadingState title="Preparing candidate workspace" message="Restoring the authenticated candidate record…" /></div>;
    if (activeTab === 'profile') {
      return <ProfileEvidenceHub candidate={candidate} evidence={evidence} onSaveCandidate={persistCandidate} onCreateEvidence={persistEvidence} onAnalyze={runProfileAnalysis} profileAnalysis={profileAnalysis} onNext={() => setActiveTab('opportunities')} />;
    }
    if (activeTab === 'opportunities') {
      return <OpportunityEngine candidate={candidate} selectedJob={selectedJob} jobAnalysis={jobAnalysis} onSelectJob={(job, analysis) => { setSelectedJob(job); setJobAnalysis(analysis); setActiveTab('interview'); }} />;
    }
    if (activeTab === 'interview') {
      return <InterviewArena candidate={candidate} selectedJob={selectedJob} onComplete={(result) => { setInterviewState(result); setActiveTab('verdict'); }} />;
    }
    if (activeTab === 'verdict') {
      return <ReadinessVerdict candidate={candidate} selectedJob={selectedJob} jobAnalysis={jobAnalysis} interviewState={interviewState} onGenerateCourse={() => setActiveTab('course')} onTailorResume={() => setActiveTab('resume')} />;
    }
    if (activeTab === 'course') {
      return <PersonalizedCourse selectedJob={selectedJob} interviewState={interviewState} course={course} onCourseReady={setCourse} onTailorResume={() => setActiveTab('resume')} />;
    }
    return <ResumeTailor candidate={candidate} selectedJob={selectedJob} evidence={evidence} course={course} resumeResult={resumeResult} onResumeReady={setResumeResult} />;
  }, [activeTab, candidate, course, evidence, interviewState, jobAnalysis, profileAnalysis, resumeResult, selectedJob, user]);

  if (bootState === 'loading') return <LoadingState title="Opening PROVEXA" message="Checking the current candidate session…" />;

  if (!user || !candidate) {
    return <LandingAuth mode={mode} busy={authBusy} error={authError} pendingTwoFactor={pendingTwoFactor} onLogin={handleLogin} onSignup={handleSignup} onVerifyTwoFactor={handleVerifyTwoFactor} onContinueDemo={() => handleLogin({ email: 'demo@provexa.local', password: 'demo-password' })} />;
  }

  return (
    <div className="app-shell">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} user={user} mode={mode} onOpenSubscription={() => setSubscriptionOpen(true)} onOpenTwoFactor={() => setTwoFactorOpen(true)} onLogout={handleLogout} />
      <main className="app-main">
        {mode === 'demo' && <Notice tone="info"><strong>Demo mode:</strong> seeded responses are clearly marked and isolated from live API calls.</Notice>}
        <WorkspaceErrorBoundary resetKey={activeTab} onRecover={() => setActiveTab('profile')}>
          {workspaceContent}
        </WorkspaceErrorBoundary>
      </main>
      <footer className="app-footer"><span>PROVEXA · From potential to proof</span><span>PostgreSQL truth · Redis session state</span></footer>
      <SubscriptionDemo isOpen={isSubscriptionOpen} onClose={() => setSubscriptionOpen(false)} />
      <TwoFactorSetup isOpen={isTwoFactorOpen} user={user} mode={mode} onBegin={beginTwoFactorSetup} onVerify={confirmTwoFactorSetup} onClose={() => setTwoFactorOpen(false)} />
    </div>
  );
}
