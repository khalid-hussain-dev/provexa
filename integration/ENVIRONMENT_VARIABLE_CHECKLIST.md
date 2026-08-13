# Environment Variable Checklist

Values are intentionally omitted. Populate them only through the local process environment or an ignored local environment file. Never commit or print secret values.

## Platform Builder variables

| Variable | Current use | Secret | Status |
|---|---|---:|---|
| `APP_NAME` | Platform application name | No | [ ] |
| `APP_ENV` | Development/production behavior | No | [ ] |
| `APP_DEBUG` | FastAPI debug mode | No | [ ] |
| `LOG_LEVEL` | Logging level | No | [ ] |
| `CORS_ORIGINS` | Platform allowed origins | No | [ ] |
| `DATABASE_URL` | SQLAlchemy persistence URL | Usually | [ ] |
| `REDIS_URL` | Redis cache/session URL; memory fallback if absent | Usually | [ ] |
| `REDIS_CONNECT_TIMEOUT_SECONDS` | Redis connection timeout | No | [ ] |
| `TRANSIENT_STATE_PREFIX` | Redis namespace | No | [ ] |
| `JWT_SECRET` | Preferred JWT signing secret | Yes | [ ] |
| `JWT_SECRET_KEY` | Backward-compatible JWT signing name | Yes | [ ] |
| `JWT_ACCESS_TOKEN_MINUTES` | Access-token lifetime | No | [ ] |
| `PENDING_2FA_TOKEN_MINUTES` | Pending 2FA-token lifetime | No | [ ] |
| `PASSWORD_RESET_TOKEN_MINUTES` | Password-reset-token lifetime | No | [ ] |
| `INTEGRATION_ALLOW_SQLITE_TESTS` | Explicit test-only SQLite escape hatch | No | [ ] |
| `INTEGRATION_ALLOW_INMEMORY_SESSIONS` | Explicit local/test-only memory-session escape hatch | No | [ ] |

## Intelligence Builder variables

| Variable | Current use | Secret | Status |
|---|---|---:|---|
| `GEMINI_API_KEY` | Required by current Intelligence settings; primary LLM path | Yes | [ ] |
| `GEMINI_MODEL` | Gemini model selection | No | [ ] |
| `GROQ_API_KEY` | Optional LLM fallback | Yes | [ ] |
| `GROQ_MODEL` | Groq model selection | No | [ ] |
| `GROQ_BASE_URL` | Groq-compatible endpoint | No | [ ] |
| `GITHUB_TOKEN` | GitHub profile/repository analysis | Yes | [ ] |
| `JOB_API_KEY` | Adzuna/job-provider credential | Yes | [ ] |
| `ADZUNA_APP_ID` | Adzuna application identifier | No | [ ] |
| `DATABASE_URL` | Declared by Intelligence settings; must not become a second persistence authority | Usually | [ ] |
| `REDIS_URL` | Declared by Intelligence settings; must not become a second cache authority | Usually | [ ] |

## Documented but not currently consumed by the copied modules

These names appear in shared project documentation and should be resolved before any future provider integration:

- `SESSION_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `JOB_PROVIDER_API_KEY`
- `NVIDIA_API_KEY`

They are not populated or interpreted by this setup phase.

## Environment safety checks

- [ ] No `.env` or `.env.*` file was copied into the integration workspace.
- [ ] No secret value appears in `SOURCE_MANIFEST.json`.
- [ ] No provider key is logged during startup or health checks.
- [ ] Integration tests use fake providers or safe local defaults.
- [ ] Production-like startup is blocked or clearly marked when required secrets are absent.
- [ ] `INTEGRATION_ALLOW_SQLITE_TESTS` is never enabled for a production-like process.
- [ ] `INTEGRATION_ALLOW_INMEMORY_SESSIONS` is never enabled for a production-like process.
