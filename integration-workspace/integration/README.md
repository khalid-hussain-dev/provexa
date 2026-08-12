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
- `GET /api/v1/readiness`

For explicitly marked local development only, the runtime may use:

- `APP_ENV=development`
- `INTEGRATION_ALLOW_INMEMORY_SESSIONS=true`
- `INTEGRATION_ALLOW_SQLITE_TESTS=true` only for test processes, never as a production-like runtime.

The root environment file is not copied or auto-committed. Set variables through the process environment or the approved secure secret mechanism. The profile adapter invokes the existing Intelligence profile preparation workflow only through its explicit gateway, then validates and allowlists the returned context before persisting an integration-owned snapshot. Tests inject a fake gateway and do not require live AI providers.
