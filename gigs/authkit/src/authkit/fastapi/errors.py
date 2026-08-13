from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..errors import AuthKitError, error_envelope


def register_authkit_error_handler(app: FastAPI) -> None:
    @app.exception_handler(AuthKitError)
    async def authkit_error_handler(request: Request, exc: AuthKitError) -> JSONResponse:
        return JSONResponse(
            content=error_envelope(exc.code, exc.message, exc.details),
            status_code=exc.status_code,
        )
