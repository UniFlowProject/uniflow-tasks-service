import logging
from collections.abc import Sequence
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pydantic_core import ErrorDetails
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.error import (
    DomainError,
    ForbiddenError,
    InvalidStatusTransitionError,
    TaskNotFoundError,
    TaskNotModifiableError,
)
from src.infrastructure.http.schemas import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

VALIDATION_ERROR = "VALIDATION_ERROR"


class UnauthorizedError(Exception):
    """The gateway did not provide a usable caller identity."""


# (status, code) per domain error; the first matching entry wins.
_DOMAIN_ERROR_MAP: list[tuple[type[DomainError], HTTPStatus, str]] = [
    (TaskNotFoundError, HTTPStatus.NOT_FOUND, "TASK_NOT_FOUND"),
    (ForbiddenError, HTTPStatus.FORBIDDEN, "FORBIDDEN"),
    (TaskNotModifiableError, HTTPStatus.CONFLICT, "TASK_NOT_MODIFIABLE"),
    (InvalidStatusTransitionError, HTTPStatus.CONFLICT, "INVALID_STATUS_TRANSITION"),
]
_DEFAULT_DOMAIN_ERROR = (HTTPStatus.BAD_REQUEST, "DOMAIN_ERROR")


def _error_response(
    status: int, code: str, message: str, details: list[ErrorDetail] | None = None
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status, content=body.model_dump(mode="json", exclude_none=True))


def _details(errors: Sequence[ErrorDetails]) -> list[ErrorDetail]:
    return [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"] if part != "body"),
            message=error["msg"],
        )
        for error in errors
    ]


def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
    status, code = next(
        (
            (status, code)
            for error_type, status, code in _DOMAIN_ERROR_MAP
            if isinstance(exc, error_type)
        ),
        _DEFAULT_DOMAIN_ERROR,
    )
    return _error_response(status, code, str(exc))


def _handle_unauthorized(_: Request, exc: UnauthorizedError) -> JSONResponse:
    return _error_response(HTTPStatus.UNAUTHORIZED, "UNAUTHORIZED", str(exc))


def _handle_request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        HTTPStatus.UNPROCESSABLE_ENTITY, VALIDATION_ERROR, "Invalid request", _details(exc.errors())
    )


def _handle_domain_validation(_: Request, exc: ValidationError) -> JSONResponse:
    return _error_response(
        HTTPStatus.UNPROCESSABLE_ENTITY, VALIDATION_ERROR, "Invalid task data", _details(exc.errors())
    )


def _handle_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = HTTPStatus(exc.status_code).name
    return _error_response(exc.status_code, code, str(exc.detail))


def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return _error_response(
        HTTPStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "Internal server error"
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(UnauthorizedError, _handle_unauthorized)
    app.add_exception_handler(RequestValidationError, _handle_request_validation)
    app.add_exception_handler(ValidationError, _handle_domain_validation)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected)
