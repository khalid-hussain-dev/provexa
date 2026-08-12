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
