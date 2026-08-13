# Integration Runtime

The public application host is the unchanged Intelligence FastAPI app decorated by `integration.main`.

Run from `E:\PROVEXA\integration-workspace` with the workspace on `PYTHONPATH`:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m integration.main
```

Phase 1 requires:

- `DATABASE_URL` using PostgreSQL.
- `REDIS_URL` using Redis.
- `JWT_SECRET` or `JWT_SECRET_KEY`.

The Phase 1 host adds these protected Platform routes without changing existing Intelligence paths:

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/candidate/evidence`
- `GET/PUT /api/v1/candidate`
- `POST /api/v1/integration/profile/analyze`
- `POST /api/v1/integration/interviews`
- `POST /api/v1/integration/interviews/{interview_id}/answers`
- `POST /api/v1/integration/interviews/{interview_id}/complete`
- `POST /api/v1/integration/courses`
- `POST /api/v1/integration/courses/{course_id}/progress`
- `POST /api/v1/integration/resumes/optimize`
- `GET /api/v1/integration/platform/jobs`
- `POST /api/v1/integration/platform/match`
- `GET /api/v1/readiness`
- `GET /api/v1/readiness/providers`
- `GET /api/v1/readiness/release`

For explicitly marked local development only, the runtime may use:

- `APP_ENV=development`
- `INTEGRATION_ALLOW_INMEMORY_SESSIONS=true`
- `INTEGRATION_ALLOW_SQLITE_TESTS=true` only for test processes, never as a production-like runtime.

The root environment file is not copied or auto-committed. Set variables through the process environment or the approved secure secret mechanism. The profile adapter invokes the existing Intelligence profile preparation workflow only through its explicit gateway, then validates and allowlists the returned context before persisting an integration-owned snapshot. Tests inject a fake gateway and do not require live AI providers.

The interview adapter uses the latest owned profile snapshot and selected Platform job as input to the unchanged Intelligence interview methods. Platform owns interview/session/answer persistence and authorization; Intelligence owns question generation and transcript evaluation. Only validated, allowlisted evaluation fields are persisted.

The learning adapters require a completed owned interview evaluation before course generation. Course modules and progress use Platform persistence. Resume optimization requires an explicitly selected owned CV evidence record and persists only that evidence reference plus validated Intelligence output.

The local golden path is covered by `tests/integration/test_phase5_golden_path.py` and uses fake Intelligence gateways. It does not require API keys or Experience Builder.

Provider readiness is configuration-only: it reports whether Gemini, Groq, GitHub, and Adzuna settings are present without making live calls or returning secret values. Platform job selection and candidate/job matching remain deterministic fallbacks when AI or external job providers are unavailable.

Phase 7 release readiness verifies the source manifest, forbidden artifacts, production-only fallback flags, and the composed route inventory. See `FINAL_RELEASE_CHECKLIST.md` and `LOCAL_RUNBOOK.md`.
