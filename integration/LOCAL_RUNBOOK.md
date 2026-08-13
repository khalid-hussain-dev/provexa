# Local Integration Runbook

Run commands from `E:\PROVEXA\integration-workspace`.

## Experience Builder

The isolated frontend is under `frontend\` and is independent from the Platform and Intelligence source directories.

```powershell
cd frontend
npm install
$env:VITE_API_MODE = "demo"
npm run dev
```

Use `$env:VITE_API_MODE = "live"` when the composed FastAPI host is running on port 8000. Vite proxies `/api` requests to that host.

Frontend checks:

```powershell
npm run lint
npm test
npm run build
```

The frontend adapter uses only the mounted `/api/v1/auth/*`, `/api/v1/candidate*`, and `/api/v1/integration/*` routes. It does not call Intelligence providers directly.

## Test-only validation

```powershell
$env:APP_ENV = "testing"
$env:DATABASE_URL = "sqlite:///./provexa_phase7_test.db"
$env:INTEGRATION_ALLOW_SQLITE_TESTS = "true"
$env:JWT_SECRET = "test-only-secret"
python -m pytest -q tests\integration
python -m pytest -q backend\tests
python -m compileall -q services integration
```

The test suite injects fake Intelligence gateways and does not require AI provider keys.

## Production-like startup requirements

Set these through the process environment or a secure secret manager:

- `APP_ENV=production`
- `DATABASE_URL` using PostgreSQL
- `REDIS_URL` using Redis
- `JWT_SECRET` or `JWT_SECRET_KEY`
- at least one AI provider key when invoking live Intelligence workflows: `GEMINI_API_KEY` or `GROQ_API_KEY`

Do not enable `INTEGRATION_ALLOW_SQLITE_TESTS` or `INTEGRATION_ALLOW_INMEMORY_SESSIONS`.

## Readiness checks

- `GET /api/v1/readiness`
- `GET /api/v1/readiness/providers`
- `GET /api/v1/readiness/release`

The provider and release checks are configuration/integrity checks only; they do not make live provider calls.

## Current verification boundary

The copied frontend has passed lint, adapter tests, and production build. The integration suite and copied Platform baseline have passed with local test dependencies. A browser-level live golden-path run against PostgreSQL, Redis, and live AI providers remains an operational deployment check, not a source integration change.
