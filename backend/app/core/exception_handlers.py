import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import AppError, ErrorCode, error_envelope, http_status_message
from app.core.logging import redact

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "application error",
            extra={"extra_fields": {"path": request.url.path, "code": exc.code, "status_code": exc.status_code}},
        )
        return JSONResponse(status_code=exc.status_code, content=error_envelope(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = {"errors": redact(exc.errors())}
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_envelope(ErrorCode.VALIDATION_ERROR, "Validation failed", details),
        )

    @app.exception_handler(HTTPException)
    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code = _code_for_status(exc.status_code)
        message = exc.detail if isinstance(exc.detail, str) else http_status_message(exc.status_code)
        return JSONResponse(status_code=exc.status_code, content=error_envelope(code, message, {}))

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unexpected server error", extra={"extra_fields": {"path": request.url.path}})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_envelope(ErrorCode.INTERNAL_SERVER_ERROR, "Internal server error", {}),
        )


def _code_for_status(status_code: int) -> str:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return ErrorCode.AUTHENTICATION_ERROR
    if status_code == status.HTTP_403_FORBIDDEN:
        return ErrorCode.AUTHORIZATION_ERROR
    if status_code == status.HTTP_404_NOT_FOUND:
        return ErrorCode.NOT_FOUND
    if status_code == status.HTTP_409_CONFLICT:
        return ErrorCode.CONFLICT
    return ErrorCode.INTERNAL_SERVER_ERROR if status_code >= 500 else "REQUEST_ERROR"
