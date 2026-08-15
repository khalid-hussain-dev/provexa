# Experience Builder Integration Status

Date: 2026-08-13

## Scope

The Experience Builder baseline has been copied into:

`E:/PROVEXA/integration-workspace/frontend`

The root `E:/PROVEXA/frontend` remains the known-good Experience Builder baseline. No files were changed in the original Platform Builder, Intelligence Builder, or `crew-provexa` workspaces.

## Connected API surface

The copied frontend API client uses the mounted composed host routes:

- Authentication: `/api/v1/auth/signup`, `/login`, `/2fa/setup`, `/2fa/verify`, `/me`, `/logout`
- Candidate: `/api/v1/candidate`, `/api/v1/candidate/evidence`
- Profile: `/api/v1/integration/profile/analyze`
- Jobs: `/api/v1/integration/platform/jobs`, `/api/v1/integration/platform/match`
- Interviews: `/api/v1/integration/interviews`, `/{interview_id}/answers`, `/{interview_id}/complete`
- Learning: `/api/v1/integration/courses`, `/courses/{course_id}/progress`
- Resume: `/api/v1/integration/resumes/optimize`

Authentication tokens are held in session storage and attached as bearer tokens for protected requests. Demo mode is explicitly selected with `VITE_API_MODE=demo`; live mode propagates API and network errors to the UI.

The workspace header now includes a user-facing TOTP enrollment flow. It calls
the mounted setup route, presents the returned authenticator key only during
enrollment, and verifies a six-digit code through the composed host. The
integration security boundary accepts both an authenticated enrollment session
and the deliberately limited pending-login session; it issues a new protected
session after verification.

## Deliberate frontend-local behavior

- Resume text preview/export is generated in the browser.
- Subscription/payment is a demonstration only.
- PDF and DOCX files are recorded by filename; pasted CV text is required for evidence-backed optimization.
- No new backend route was introduced for these behaviors.

## Baseline and verification state

The root `E:/PROVEXA/frontend` remains the standalone baseline. The copied
frontend now contains documented integration-only deltas for TOTP enrollment,
live-host diagnostics, deployment API configuration, and display robustness;
it is therefore no longer expected to be byte-identical to the root baseline.
The original baseline manifest remains an audit record, and
`EXPERIENCE_INTEGRATION_DELTA.md` lists the intentional differences.

Static and local contract verification is complete: the copied frontend passes
lint, 4 adapter tests, and a production build. The composed integration suite
passes 28 tests, including TOTP enrollment, pending-login verification, and the
full fake-gateway golden path. The copied Platform and Intelligence source
trees remain untouched by this work.

Live browser verification against provisioned PostgreSQL, Redis, and AI providers remains pending. Do not describe those external runtime dependencies as verified until the composed host and frontend are run together with those services.

## Next safe action

The remaining task is operational verification: install the declared composed
host dependencies, replace the local PostgreSQL placeholder in the ignored
`.env`, start the host, and perform the browser golden-path smoke test in live
mode. Any contract mismatch must remain in the copied frontend adapter or an
explicit integration boundary; do not modify Intelligence workflow behavior.
