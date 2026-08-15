# Experience Integration Delta

Date: 2026-08-13

The root `E:/PROVEXA/frontend` remains the standalone Experience Builder
baseline. The files in `E:/PROVEXA/integration-workspace/frontend` below are
intentional integration-only changes made after the baseline copy. No original
Platform, Intelligence, or CrewAI source is included in this delta.

## Functional changes

- `src/components/TwoFactorSetup.jsx` — user-facing authenticator-key and TOTP
  enrollment modal.
- `src/components/Header.jsx` and `src/App.jsx` — exposes enrollment from the
  authenticated workspace and restores the verified user session.
- `src/services/api.js` — calls the mounted setup endpoint, supports a separate
  deployed API origin, preserves live failures, and models demo pending-2FA
  sign-in behavior.
- `src/services/api.test.js` — exercises demo and live adapter TOTP behavior.
- `src/components/WorkspaceErrorBoundary.jsx` — gives a recoverable UI state
  when an unexpected adapter payload would otherwise blank the current step.
- `src/components/OpportunityEngine.jsx`, `ProfileEvidenceHub.jsx`,
  `ReadinessVerdict.jsx`, and `InterviewArena.jsx` — safely display adapter
  values and isolate live job-loading failures from an empty-job result.
- `src/components/UI.jsx` and `src/index.css` — support precise retry/error and
  TOTP setup presentation.
- `.env.example` — documents the separate deployed frontend API origin.

## Host-boundary changes

- `integration/security.py` — accepts an authenticated enrollment session as
  well as a pending-2FA login session for the existing verification route.
- `integration/auth_router.py` — uses that session policy without changing the
  underlying Platform or Intelligence implementation.
- `integration/main.py` — loads only the ignored local workspace `.env`,
  normalizes standard PostgreSQL URLs for Psycopg 3, and makes
  `python -m integration.main` start Uvicorn.
- `integration/runtime.py` — rejects an unresolved database credential
  placeholder before startup.
- `integration/release_readiness.py` — recognizes the approved ignored
  workspace-root `.env` without reading or reporting its values.
- `integration/requirements.txt` and `.env.example` — declare host runtime and
  non-secret configuration requirements.

See `RENDER_DEPLOYMENT_GUIDE.md` for production deployment configuration.
