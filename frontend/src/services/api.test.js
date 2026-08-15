import assert from 'node:assert/strict';
import test from 'node:test';
import {
  clearSession,
  getCandidate,
  getCurrentUser,
  getApiMode,
  login,
  setApiMode,
  setupTwoFactor,
  verifyTwoFactor,
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

test('two-factor setup supports enrollment and a verified demo login challenge', async () => {
  setApiMode('demo');
  clearSession();
  await login({ email: 'anything@example.com', password: 'not-a-real-password' });
  const setup = await setupTwoFactor();
  assert.equal(setup.secret, 'JBSWY3DPEHPK3PXP');
  await assert.rejects(() => verifyTwoFactor('000000'), (error) => error.status === 401);
  await verifyTwoFactor('123456');
  assert.equal((await getCurrentUser()).two_factor_enabled, true);

  clearSession();
  const pendingLogin = await login({ email: 'anything@example.com', password: 'not-a-real-password' });
  assert.equal(pendingLogin.requires_2fa, true);
  assert.equal(await getCurrentUser(), null);
  await verifyTwoFactor('123456');
  assert.equal((await getCurrentUser()).two_factor_enabled, true);
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
  globalThis.fetch = async () => new Response(JSON.stringify({ error: { code: 'INTERNAL_ERROR', message: 'Internal server error' } }), { status: 500 });
  await assert.rejects(
    () => getCandidate({ email: 'live@example.com' }),
    (error) => error.status === 500 && error.message.includes('Verify PostgreSQL, Redis'),
  );
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

test('live two-factor setup uses the authenticated integrated API route', async () => {
  const originalFetch = globalThis.fetch;
  setApiMode('live');
  await loginLiveForTest();
  let requested;
  globalThis.fetch = async (url, options) => {
    requested = { url, options };
    return new Response(JSON.stringify({ secret: 'SECRET', provisioning_uri: 'otpauth://totp/PROVEXA:test' }), { status: 200 });
  };
  const setup = await setupTwoFactor();
  assert.equal(setup.secret, 'SECRET');
  assert.equal(requested.url, '/api/v1/auth/2fa/setup');
  assert.equal(requested.options.method, 'POST');
  assert.equal(requested.options.headers.Authorization, 'Bearer test-token');
  globalThis.fetch = originalFetch;
  clearSession();
  setApiMode('demo');
});
