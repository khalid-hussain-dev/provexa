# PROVEXA Backend

Minimal FastAPI platform foundation for PROVEXA.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

## Test

```bash
cd backend
pytest
```

## Endpoints

- `GET /api/v1/health` - liveness check
- `GET /api/v1/readiness` - readiness check
- `POST /api/v1/auth/signup` - create a user and return the contract signup status
- `POST /api/v1/auth/login` - authenticate and issue an access token
- `POST /api/v1/auth/logout` - revoke the current access token until expiry
- `POST /api/v1/auth/forgot-password` - issue a password reset token
- `POST /api/v1/auth/reset-password` - reset a password with a valid reset token
- `POST /api/v1/auth/2fa/setup` - create a TOTP secret for the current user
- `POST /api/v1/auth/2fa/verify` - verify a TOTP code and enable/complete 2FA
- `GET /api/v1/auth/me` - return the current user for a bearer token

Auth uses a temporary in-memory repository until database persistence is added. Set `JWT_SECRET_KEY` for token signing, `JWT_ACCESS_TOKEN_MINUTES` for access token lifetime, `PENDING_2FA_TOKEN_MINUTES` for pending 2FA login tokens, and `PASSWORD_RESET_TOKEN_MINUTES` for password reset expiry.

In development, `POST /api/v1/auth/forgot-password` returns the reset token directly so the hackathon demo can complete without email infrastructure. In non-development environments, the response remains accepted but does not expose the token; a delivery adapter should be connected later.

Errors use the contract envelope:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```
