# Phase 7 Final Release Checklist

Scope: `integration-workspace` only. Experience Builder is excluded.

## Verified locally

- [x] Intelligence remains the host application.
- [x] Original Intelligence routes remain available at their original paths.
- [x] Platform authentication and ownership boundaries are covered by integration tests.
- [x] PostgreSQL is required outside explicit test-only SQLite mode.
- [x] Redis is required for production-like server-side sessions.
- [x] Profile, interview, course, and resume adapters use validated boundaries.
- [x] Platform job selection and deterministic matching are available under a non-conflicting prefix.
- [x] Full golden-path test passes with fake Intelligence providers.
- [x] Provider readiness reports configuration state without live calls or secret values.
- [x] Source manifest verification passes.
- [x] No environment files, databases, caches, or virtual environments remain in the workspace.
- [x] Original source repositories remain untouched.

## Explicitly not claimed

- Live Gemini/Groq/GitHub/Adzuna calls were not performed.
- PostgreSQL and Redis production instances were not provisioned by this phase.
- Experience Builder and frontend/UI work are excluded.
- GitHub publication of Phase 7 is pending explicit approval.

## Release endpoint

`GET /api/v1/readiness/release` returns manifest, forbidden-artifact, production-flag, and provider-configuration status without returning secret values.
