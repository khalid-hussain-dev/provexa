const configuredApiHost = import.meta.env?.VITE_API_BASE_URL?.trim().replace(/\/$/, '');
const API_BASE = configuredApiHost ? `${configuredApiHost}/api/v1` : '/api/v1';
const TOKEN_KEY = 'provexa_access_token';
const DEFAULT_MODE = import.meta.env?.VITE_API_MODE === 'demo' ? 'demo' : 'live';

export class ApiError extends Error {
  constructor(message, { status = 0, code = 'API_ERROR', details = null } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

let apiMode = DEFAULT_MODE;
let accessToken = readSessionToken();

export const DEMO_USER = {
  id: '00000000-0000-0000-0000-000000000001',
  name: 'Demo Candidate',
  email: 'demo@provexa.local',
  is_active: true,
  two_factor_enabled: false,
};

export const DEFAULT_CANDIDATE = {
  id: '00000000-0000-0000-0000-000000000002',
  name: DEMO_USER.name,
  email: DEMO_USER.email,
  headline: 'Backend Engineer',
  summary: 'Builds evidence-backed backend services with Python and FastAPI.',
  location: 'Remote',
  preferences: {
    target_role: 'Backend Engineer',
    experience_years: 3,
    skills: ['Python', 'FastAPI', 'PostgreSQL', 'Testing'],
  },
};

const DEMO_JOBS = [
  {
    job_id: '00000000-0000-0000-0000-000000000101',
    title: 'Backend Developer',
    company: 'Example Inc',
    location: 'Remote',
    source: 'demo-provider',
    description: 'Build FastAPI services with PostgreSQL, Redis, Docker, and pytest.',
    requirements: ['Python', 'FastAPI', 'PostgreSQL', 'Redis', 'Docker', 'Testing'],
  },
  {
    job_id: '00000000-0000-0000-0000-000000000102',
    title: 'Full Stack Engineer',
    company: 'Acme Labs',
    location: 'Lahore',
    source: 'demo-provider',
    description: 'Work across React, FastAPI, and PostgreSQL to ship product features.',
    requirements: ['React', 'FastAPI', 'PostgreSQL'],
  },
  {
    job_id: '00000000-0000-0000-0000-000000000103',
    title: 'Platform Engineer',
    company: 'ByteWorks',
    location: 'Remote',
    source: 'demo-provider',
    description: 'Operate backend infrastructure with Python, Kubernetes, Docker, and Redis.',
    requirements: ['Python', 'Docker', 'Kubernetes', 'Redis'],
  },
];

const DEMO_QUESTIONS = [
  {
    question_id: '00000000-0000-0000-0000-000000000201',
    question: 'Describe a backend service you shipped and the trade-offs you made around reliability.',
    category: 'Backend architecture',
    difficulty: 'medium',
  },
  {
    question_id: '00000000-0000-0000-0000-000000000202',
    question: 'How would you test an API that writes to PostgreSQL and uses Redis for transient state?',
    category: 'Testing and data',
    difficulty: 'medium',
  },
  {
    question_id: '00000000-0000-0000-0000-000000000203',
    question: 'What evidence would convince a hiring team that you can operate this system in production?',
    category: 'Evidence and operations',
    difficulty: 'advanced',
  },
];

let demoEvidence = [];
let demoInterview = null;
let demoCourse = null;
let demoTwoFactorEnabled = false;
let demoTwoFactorPending = false;

export function getApiMode() {
  return apiMode;
}

export function setApiMode(mode) {
  apiMode = mode === 'demo' ? 'demo' : 'live';
}

export function isDemoMode() {
  return apiMode === 'demo';
}

export function getAccessToken() {
  return accessToken;
}

export function clearSession() {
  accessToken = null;
  demoTwoFactorPending = false;
  try {
    globalThis.sessionStorage?.removeItem(TOKEN_KEY);
  } catch {
    // Storage can be unavailable in privacy-restricted browsers.
  }
}

export function normalizeCandidate(candidate, user = null) {
  const preferences = candidate?.preferences || {};
  return {
    ...DEFAULT_CANDIDATE,
    ...candidate,
    email: user?.email || candidate?.email || DEFAULT_CANDIDATE.email,
    name: candidate?.name || user?.name || DEFAULT_CANDIDATE.name,
    target_role: preferences.target_role || candidate?.headline || '',
    experience_years: Number(preferences.experience_years || 0),
    skills: Array.isArray(preferences.skills) ? preferences.skills : [],
    github_url: preferences.github_url || '',
    linkedin_url: preferences.linkedin_url || '',
    portfolio_url: preferences.portfolio_url || '',
  };
}

export async function signup(payload) {
  if (isDemoMode()) {
    return { user_id: DEMO_USER.id, requires_2fa_setup: false };
  }
  return request('/auth/signup', { method: 'POST', body: payload, auth: false });
}

export async function login(payload) {
  if (isDemoMode()) {
    demoTwoFactorPending = demoTwoFactorEnabled;
    const token = demoTwoFactorPending ? 'demo-pending-2fa-token' : 'demo-session-token';
    saveToken(token);
    return { access_token: token, token_type: 'bearer', requires_2fa: demoTwoFactorPending };
  }
  const result = await request('/auth/login', { method: 'POST', body: payload, auth: false });
  saveToken(result.access_token);
  return result;
}

export async function verifyTwoFactor(code) {
  if (isDemoMode()) {
    if (code !== '123456') {
      throw new ApiError('Use the demo verification code 123456.', { status: 401, code: 'AUTHENTICATION_ERROR' });
    }
    demoTwoFactorEnabled = true;
    demoTwoFactorPending = false;
    saveToken('demo-session-token');
    return { authenticated: true, access_token: 'demo-session-token', token_type: 'bearer' };
  }
  const result = await request('/auth/2fa/verify', {
    method: 'POST',
    body: { code },
  });
  saveToken(result.access_token);
  return result;
}

export async function setupTwoFactor() {
  if (isDemoMode()) {
    return {
      secret: 'JBSWY3DPEHPK3PXP',
      provisioning_uri: 'otpauth://totp/PROVEXA:demo%40provexa.local?secret=JBSWY3DPEHPK3PXP&issuer=PROVEXA&digits=6',
    };
  }
  return request('/auth/2fa/setup', { method: 'POST' });
}

export async function getCurrentUser() {
  if (isDemoMode()) {
    return accessToken && !demoTwoFactorPending ? { ...DEMO_USER, two_factor_enabled: demoTwoFactorEnabled } : null;
  }
  if (!accessToken) return null;
  return request('/auth/me');
}

export async function logout() {
  if (isDemoMode()) {
    clearSession();
    return { status: 'logged_out' };
  }
  try {
    return await request('/auth/logout', { method: 'POST' });
  } finally {
    clearSession();
  }
}

export async function getCandidate(user) {
  if (isDemoMode()) return normalizeCandidate(DEFAULT_CANDIDATE, user || DEMO_USER);
  const candidate = await request('/candidate');
  return normalizeCandidate(candidate, user);
}

export async function updateCandidate(candidate) {
  const payload = {
    name: candidate.name,
    headline: candidate.target_role || candidate.headline || null,
    summary: candidate.summary || null,
    location: candidate.location || null,
    preferences: {
      ...(candidate.preferences || {}),
      target_role: candidate.target_role || '',
      experience_years: Number(candidate.experience_years || 0),
      skills: candidate.skills || [],
      github_url: candidate.github_url || '',
      linkedin_url: candidate.linkedin_url || '',
      portfolio_url: candidate.portfolio_url || '',
    },
  };
  if (isDemoMode()) return normalizeCandidate({ ...candidate, ...payload });
  return normalizeCandidate(await request('/candidate', { method: 'PUT', body: payload }), {
    email: candidate.email,
    name: candidate.name,
  });
}

export async function createEvidence(payload) {
  if (isDemoMode()) {
    const evidence = {
      evidence_id: `demo-evidence-${demoEvidence.length + 1}`,
      status: 'stored',
      ...payload,
    };
    demoEvidence.push(evidence);
    return evidence;
  }
  return request('/candidate/evidence', { method: 'POST', body: payload });
}

export async function analyzeProfile() {
  if (isDemoMode()) {
    return {
      analysis_id: '00000000-0000-0000-0000-000000000301',
      status: 'completed',
      source_evidence_ids: demoEvidence.map((item) => item.evidence_id),
      profile_context: {
        candidate_summary: DEFAULT_CANDIDATE.summary,
        primary_domain: 'Backend Engineering',
        all_skills: ['Python', 'FastAPI', 'PostgreSQL', 'Testing'],
        technical_strengths: ['API design', 'Service reliability'],
        potential_weaknesses: ['Production orchestration'],
        interview_readiness: 'medium',
        recommended_interview_depth: 'intermediate',
      },
    };
  }
  return request('/integration/profile/analyze', { method: 'POST' });
}

export async function listJobs({ page = 1, limit = 10 } = {}) {
  if (isDemoMode()) return { jobs: DEMO_JOBS, page, limit, total: DEMO_JOBS.length };
  return request(`/integration/platform/jobs?page=${page}&limit=${limit}`);
}

export async function matchJob(jobId) {
  if (isDemoMode()) {
    const index = DEMO_JOBS.findIndex((job) => job.job_id === jobId);
    const matchScore = Math.max(68, 88 - Math.max(index, 0) * 8);
    return {
      analysis_id: `demo-analysis-${index + 1}`,
      match_score: matchScore,
      readiness_score: matchScore - 6,
      strengths: [{ skill: 'API delivery', evidence: 'CV and project evidence' }],
      gaps: [{ skill: 'Production orchestration', importance: 70, candidate_score: 42 }],
      recommendations: ['Complete the targeted readiness path.'],
      evidence_summary: ['CV evidence stored for this candidate.'],
    };
  }
  return request('/integration/platform/match', { method: 'POST', body: { job_id: jobId } });
}

export async function createInterview({ jobId, numQuestions = 3 }) {
  if (isDemoMode()) {
    demoInterview = { interview_id: 'demo-interview-1', nextIndex: 0 };
    return {
      interview_id: demoInterview.interview_id,
      status: 'CREATED',
      total_questions: Math.min(numQuestions, DEMO_QUESTIONS.length),
      first_question: DEMO_QUESTIONS[0],
      job_id: jobId,
    };
  }
  return request('/integration/interviews', {
    method: 'POST',
    body: { job_id: jobId, num_questions: numQuestions },
  });
}

export async function answerInterview({ interviewId, questionId, answer, confidence }) {
  if (isDemoMode()) {
    const currentIndex = demoInterview?.nextIndex || 0;
    const nextIndex = currentIndex + 1;
    if (demoInterview) demoInterview.nextIndex = nextIndex;
    return {
      interview_id: interviewId,
      question_id: questionId,
      status: 'RECORDED',
      next_question: DEMO_QUESTIONS[nextIndex] || null,
      answer_recorded: Boolean(answer && confidence),
    };
  }
  return request(`/integration/interviews/${interviewId}/answers`, {
    method: 'POST',
    body: { question_id: questionId, answer, confidence },
  });
}

export async function completeInterview(interviewId) {
  if (isDemoMode()) {
    return {
      evaluation_id: 'demo-evaluation-1',
      interview_id: interviewId,
      status: 'COMPLETED',
      result: {
        candidate_name: DEMO_USER.name,
        target_role: DEFAULT_CANDIDATE.preferences.target_role,
        overall_score: 82,
        assessed_level: 'mid',
        role_match_percentage: 84,
        verdict: 'APPLY_WITH_CAUTION',
        analysis: {
          strengths: ['Clear API reasoning', 'Evidence-backed delivery examples'],
          weaknesses: ['Production orchestration depth'],
          improvement_areas: ['Add deployment and observability evidence'],
        },
      },
    };
  }
  return request(`/integration/interviews/${interviewId}/complete`, { method: 'POST' });
}

export async function generateCourse(interviewId) {
  if (isDemoMode()) {
    demoCourse = {
      course_id: 'demo-course-1',
      status: 'GENERATED',
      title: 'Backend Readiness Sprint',
      target_role: DEFAULT_CANDIDATE.preferences.target_role,
      current_score: 82,
      target_score: 95,
      modules: [
        {
          module_id: 'demo-module-1',
          sequence: 1,
          title: 'Testing Foundations',
          objective: 'Build reliable integration tests around API and persistence boundaries.',
          content: { skill_name: 'Testing', code_example: 'def test_api_ownership(): ...' },
          challenge: { validation_exercise: 'Describe an ownership test for a protected endpoint.' },
        },
        {
          module_id: 'demo-module-2',
          sequence: 2,
          title: 'Production Service Design',
          objective: 'Make service boundaries and failure modes explicit.',
          content: { skill_name: 'System Design', code_example: 'request -> service -> repository' },
          challenge: { validation_exercise: 'Outline a resilient API request flow.' },
        },
      ],
      interview_id: interviewId,
    };
    return demoCourse;
  }
  return request('/integration/courses', { method: 'POST', body: { interview_id: interviewId } });
}

export async function updateCourseProgress({ courseId, moduleId, completionPercent, assessmentScore = null }) {
  if (isDemoMode()) return { progress_id: `demo-progress-${moduleId}`, status: 'updated' };
  return request(`/integration/courses/${courseId}/progress`, {
    method: 'POST',
    body: {
      module_id: moduleId,
      completion_percent: completionPercent,
      assessment_score: assessmentScore,
    },
  });
}

export async function optimizeResume({ courseId, evidenceId }) {
  if (isDemoMode()) {
    return {
      resume_id: 'demo-resume-1',
      version: 1,
      evidence_references: [evidenceId],
      result: {
        original_resume_text: 'Demo Candidate\nBackend Engineer\nPython, FastAPI, PostgreSQL',
        updated_resume_text: 'Demo Candidate\nBackend Engineer\n\nEvidence-backed strengths\n- Python and FastAPI service delivery\n- PostgreSQL data workflows\n- Testing and reliability foundations',
        injected_skills: ['Testing', 'System Design'],
        summary_of_changes: 'Reordered verified evidence and highlighted the completed readiness path.',
      },
      course_id: courseId,
    };
  }
  return request('/integration/resumes/optimize', {
    method: 'POST',
    body: { course_id: courseId, evidence_id: evidenceId },
  });
}

export function buildExportFile(text, filename = 'provexa-resume.txt') {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  if (auth && !accessToken) {
    throw new ApiError('Sign in to continue.', { status: 401, code: 'AUTH_REQUIRED' });
  }

  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && accessToken) headers.Authorization = `Bearer ${accessToken}`;

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    throw new ApiError('The API could not be reached. Check that the integrated host is running.', {
      code: 'NETWORK_ERROR',
      details: error instanceof Error ? error.message : null,
    });
  }

  const payload = await parseResponse(response);
  if (!response.ok) {
    throw new ApiError(apiFailureMessage(response.status, payload), {
      status: response.status,
      code: payload?.error?.code || 'HTTP_ERROR',
      details: payload?.error?.details || null,
    });
  }
  return payload;
}

function apiFailureMessage(status, payload) {
  const message = payload?.error?.message || payload?.detail || `Request failed (${status}).`;
  if (status >= 500 && message === 'Internal server error') {
    return 'The integrated host could not complete this request. Verify PostgreSQL, Redis, and the API readiness endpoint before retrying.';
  }
  return message;
}

async function parseResponse(response) {
  if (response.status === 204) return null;
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}

function saveToken(token) {
  accessToken = token;
  try {
    globalThis.sessionStorage?.setItem(TOKEN_KEY, token);
  } catch {
    // Keep the token in memory when session storage is unavailable.
  }
}

function readSessionToken() {
  try {
    return globalThis.sessionStorage?.getItem(TOKEN_KEY) || null;
  } catch {
    return null;
  }
}
