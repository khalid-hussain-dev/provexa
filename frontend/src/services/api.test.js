import assert from 'node:assert/strict';
import test from 'node:test';
import {
  clearSession,
  getCandidate,
  getCurrentUser,
  getApiMode,
  login,
  setApiMode,
} from './api.js';

test('demo mode is explicit and supplies a deterministic current user', async () => {
  setApiMode('demo');
  clearSession();
  assert.equal(getApiMode(), 'demo');
  assert.equal(await getCurrentUser(), null);
  await login({ email: 'anything@example.com', password: 'not-a-real-password' });
  const user = await getCurrentUser();
  assert.equal(user.email, 'demo@provexa.local');
  clearSession();
});

test('live protected requests attach the bearer token and preserve API errors', async () => {
  const originalFetch = globalThis.fetch;
  setApiMode('live');
  await loginLiveForTest();
  let requested;
  globalThis.fetch = async (url, options) => {
    requested = { url, options };
    return new Response(JSON.stringify({ id: 'candidate-1', name: 'Live Candidate', preferences: {} }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };
  const candidate = await getCandidate({ email: 'live@example.com' });
  assert.equal(candidate.name, 'Live Candidate');
  assert.equal(requested.url, '/api/v1/candidate');
  assert.equal(requested.options.headers.Authorization, 'Bearer test-token');

  globalThis.fetch = async () => new Response(JSON.stringify({ error: { code: 'NOT_FOUND', message: 'Candidate not found' } }), { status: 404 });
  await assert.rejects(() => getCandidate({ email: 'live@example.com' }), (error) => error.status === 404 && error.code === 'NOT_FOUND');
  globalThis.fetch = originalFetch;
  clearSession();
  setApiMode('demo');
});

async function loginLiveForTest() {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ access_token: 'test-token', token_type: 'bearer', requires_2fa: false }), { status: 200 });
  await login({ email: 'live@example.com', password: 'StrongPassword123!' });
  globalThis.fetch = originalFetch;
}
