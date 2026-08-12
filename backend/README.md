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
- `POST /api/v1/auth/signup` - create an in-memory user and access token
- `POST /api/v1/auth/login` - authenticate and issue an access token
- `GET /api/v1/auth/me` - return the current user for a bearer token

Auth uses a temporary in-memory repository until database persistence is added. Set `JWT_SECRET_KEY` for token signing and `JWT_ACCESS_TOKEN_MINUTES` for access token lifetime.

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
