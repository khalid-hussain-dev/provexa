# Experience Builder Integration Status

Date: 2026-08-13

## Scope

The Experience Builder baseline has been copied into:

`E:/PROVEXA/integration-workspace/frontend`

The root `E:/PROVEXA/frontend` remains the known-good Experience Builder baseline. No files were changed in the original Platform Builder, Intelligence Builder, or `crew-provexa` workspaces.

## Connected API surface

The copied frontend API client uses the mounted composed host routes:

- Authentication: `/api/v1/auth/signup`, `/login`, `/2fa/verify`, `/me`, `/logout`
- Candidate: `/api/v1/candidate`, `/api/v1/candidate/evidence`
- Profile: `/api/v1/integration/profile/analyze`
- Jobs: `/api/v1/integration/platform/jobs`, `/api/v1/integration/platform/match`
- Interviews: `/api/v1/integration/interviews`, `/{interview_id}/answers`, `/{interview_id}/complete`
- Learning: `/api/v1/integration/courses`, `/courses/{course_id}/progress`
- Resume: `/api/v1/integration/resumes/optimize`

Authentication tokens are held in session storage and attached as bearer tokens for protected requests. Demo mode is explicitly selected with `VITE_API_MODE=demo`; live mode propagates API and network errors to the UI.

## Deliberate frontend-local behavior

- Resume text preview/export is generated in the browser.
- Subscription/payment is a demonstration only.
- PDF and DOCX files are recorded by filename; pasted CV text is required for evidence-backed optimization.
- No new backend route was introduced for these behaviors.

## Verification state

The source copy and manifest are verified: 22 files, 0 SHA-256 mismatches. `node_modules`, `dist`, secrets, caches, and generated artifacts were excluded.

Static and local contract verification is complete: the copied frontend passes lint, its adapter tests pass, the production build passes, the integration suite passes 27/27, the copied Platform baseline passes 34/34, and Python compilation passes.

Live browser verification against provisioned PostgreSQL, Redis, and AI providers remains pending. Do not describe those external runtime dependencies as verified until the composed host and frontend are run together with those services.

## Next safe action

When execution becomes available, install frontend dependencies inside this copied frontend only, run the frontend lint/build/tests, start the composed host, and perform the golden-path smoke test. Any contract mismatch should be fixed in the copied frontend adapter or an explicitly approved integration boundary; do not modify Intelligence workflow behavior.
