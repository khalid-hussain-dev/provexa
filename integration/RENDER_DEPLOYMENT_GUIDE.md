# Render Deployment Guide

Date: 2026-08-13

This guide deploys the isolated integrated workspace only. It does not deploy
or modify `E:/PROVEXA/.provexa-review`, `E:/PROVEXA/crew-provexa`, or the root
standalone frontend.

## Architecture

Deploy three Render resources in the same region:

1. A Render Postgres database is the durable source of truth.
2. A Render Key Value instance is the Redis-compatible server-side session
   store.
3. A Python Web Service runs `integration.main:app` as the public API host.
4. A Render Static Site hosts `frontend/` and calls the public API origin.

The static site cannot use Render private-network hostnames. Its Vite API URL
must be the public HTTPS URL of the API Web Service. The API service may use
the database and Key Value **internal** connection URLs because those services
share a region.

## Before creating services

- Put `integration-workspace/` in an approved Git repository. This guide does
  not require a push; make that release decision separately.
- Confirm the repository does not contain `.env`, local caches, `venv/`, or
  generated build output. The workspace `.gitignore` excludes them.
- Use the included `.python-version` (`3.12`) so Render does not select a newer
  default runtime that has not been validated with the dependencies.
- Do not copy the local `.env` into Render or source control.

## 1. Create Postgres and Key Value

In the Render Dashboard, create a Postgres database and a Key Value instance
in the same region where the API will run. Keep Key Value external access
disabled unless an operational need requires it. Copy neither connection string
into source files; reference or paste them only in the API service environment.

## 2. Create the API Web Service

Create a **Python 3** Web Service from the approved repository.

| Setting | Value |
| --- | --- |
| Root Directory | `integration-workspace` |
| Build Command | `python -m pip install --upgrade pip && python -m pip install -r integration/requirements.txt` |
| Start Command | `uvicorn integration.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/v1/readiness` |
| Python runtime | Read from `.python-version` (`3.12`) |

Set these non-secret environment values:

| Key | Value |
| --- | --- |
| `APP_ENV` | `production` |
| `APP_DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `CORS_ORIGINS` | Exact static-site origin, for example `https://provexa-web.onrender.com` |
| `TRANSIENT_STATE_PREFIX` | A production-specific value such as `provexa-prod` |

Set these securely in the Render Environment screen or from linked Render
resources:

| Key | Source |
| --- | --- |
| `DATABASE_URL` | The Postgres **internal** connection URL. The composed host normalizes Render's standard PostgreSQL URL for Psycopg 3. |
| `REDIS_URL` | The Key Value **internal** connection URL. |
| `JWT_SECRET` | Generate a new long random secret in Render; never reuse the placeholder. |
| `GEMINI_API_KEY` and/or `GROQ_API_KEY` | Existing approved provider secret(s), required for live Intelligence operations. |
| `GITHUB_TOKEN`, `JOB_API_KEY`, `ADZUNA_APP_ID` | Only when enabling their corresponding live integrations. |

Never set `INTEGRATION_ALLOW_SQLITE_TESTS` or
`INTEGRATION_ALLOW_INMEMORY_SESSIONS` in production.

Wait for the service to become healthy, then request:

```text
GET https://<api-service>.onrender.com/api/v1/readiness
GET https://<api-service>.onrender.com/api/v1/readiness/providers
GET https://<api-service>.onrender.com/api/v1/readiness/release
```

`/readiness/providers` only confirms configuration; it does not call AI or job
providers. `/readiness/release` must report `ready` before user testing.

## 3. Create the frontend Static Site

Create a Render Static Site from the same repository.

| Setting | Value |
| --- | --- |
| Root Directory | `integration-workspace/frontend` |
| Build Command | `npm ci && npm run build` |
| Publish Directory | `dist` |

Set these build-time variables:

| Key | Value |
| --- | --- |
| `VITE_API_MODE` | `live` |
| `VITE_API_BASE_URL` | `https://<api-service>.onrender.com` |

`VITE_API_BASE_URL` is an origin only—do not add `/api/v1`. Vite embeds this
value into the static bundle at build time, so a changed API URL requires a new
frontend build. Add an SPA rewrite from `/*` to `/index.html` if the Render
static-site configuration exposes route rules.

After the static site has its URL, update the API service's `CORS_ORIGINS` to
that exact origin and redeploy the API. If using custom domains, add each exact
HTTPS origin as a comma-separated value.

## 4. Production smoke test

Use a newly created account and a real authenticator app:

1. Sign up and sign in.
2. Open the key icon in the workspace header, enroll the displayed TOTP key,
   and verify the current six-digit code.
3. Sign out and confirm a later sign-in requires the TOTP code.
4. Save a candidate and pasted CV text, add GitHub or portfolio evidence, and
   run profile analysis.
5. Select a job, complete every interview question, verify the verdict,
   generate a course, mark module progress, and produce the resume preview.
6. Reload the browser between key stages to confirm persisted data and
   server-side session behavior.

If a provider is unavailable, record the provider/readiness result and the API
response. Do not substitute demo mode for a failed live deployment.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Deploy never becomes healthy | Render logs; `DATABASE_URL`, `REDIS_URL`, and `JWT_SECRET`; `/api/v1/readiness`. |
| Frontend says API cannot be reached | The `VITE_API_BASE_URL` public origin, API deploy status, and `CORS_ORIGINS`. Rebuild the static site after changing Vite variables. |
| 500 on target jobs | API logs, `/api/v1/readiness`, and provider configuration. The UI shows this as a host-readiness error rather than an empty job set. |
| Sign-in works but 2FA cannot be completed | Ensure the API uses Redis, the browser time is correct, and test the six-digit code with the most recently displayed TOTP interval. |
| Database driver failure | Use Render's internal Postgres URL unchanged; `integration.main` converts the `postgresql://` or `postgres://` scheme to the installed Psycopg 3 driver form. |

## Render references

- [Deploy a FastAPI App](https://render.com/docs/deploy-fastapi)
- [Web Services and port binding](https://render.com/docs/web-services)
- [Static Sites](https://render.com/docs/static-sites)
- [Render Key Value](https://render.com/docs/key-value)
- [Environment Variables and Secrets](https://render.com/docs/configure-environment-variables)
- [Setting Your Python Version](https://render.com/docs/python-version)
