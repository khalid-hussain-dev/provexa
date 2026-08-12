from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import ConflictError
from app.core.exception_handlers import register_exception_handlers


def _client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/conflict")
    async def conflict() -> None:
        raise ConflictError("Already exists", {"resource": "example"})

    @app.get("/items/{item_id}")
    async def item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    return TestClient(app)


def test_app_error_uses_contract_envelope() -> None:
    response = _client().get("/conflict")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "CONFLICT",
            "message": "Already exists",
            "details": {"resource": "example"},
        }
    }


def test_validation_error_uses_contract_envelope() -> None:
    response = _client().get("/items/not-an-int")

    body = response.json()
    assert response.status_code == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Validation failed"
    assert "errors" in body["error"]["details"]
