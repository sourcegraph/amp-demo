import traceback
from typing import Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

from .logging_config import trace_id_var, span_id_var


logger = structlog.get_logger()

DOCS_BASE = "https://docs.lineasupply.com/errors"

RETRYABLE_CODES = {
    "CONFLICT.VERSION_MISMATCH",
    "RATE_LIMIT.EXCEEDED",
    "SERVER.INTERNAL_ERROR",
    "SERVER.BAD_GATEWAY",
    "SERVER.UNAVAILABLE",
    "SERVER.GATEWAY_TIMEOUT",
}

DEFAULT_CODE_BY_STATUS = {
    400: "VALIDATION.INVALID_FIELDS",
    401: "AUTH.INVALID_TOKEN",
    403: "AUTH.INSUFFICIENT_PERMISSIONS",
    404: "RESOURCE.NOT_FOUND",
    409: "CONFLICT.DUPLICATE",
    422: "VALIDATION.UNPROCESSABLE",
    429: "RATE_LIMIT.EXCEEDED",
    500: "SERVER.INTERNAL_ERROR",
    502: "SERVER.BAD_GATEWAY",
    503: "SERVER.UNAVAILABLE",
    504: "SERVER.GATEWAY_TIMEOUT",
}


def problem_response(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    code: str,
    instance: str | None = None,
    details: dict[str, Any] | None = None
) -> JSONResponse:
    trace_id = trace_id_var.get()
    span_id = span_id_var.get()
    payload: dict[str, Any] = {
        "type": f"{DOCS_BASE}/{code.lower().replace('.', '-')}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance or str(request.url.path),
        "code": code,
        "request_id": trace_id,
        "trace_id": trace_id,
    }
    if details:
        payload["details"] = details
    resp = JSONResponse(payload, status_code=status, media_type="application/problem+json")
    resp.headers["X-Request-ID"] = trace_id or ""
    resp.headers["traceparent"] = f"00-{trace_id or ''}-{span_id or ''}-01"
    return resp


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.error("validation_error", error_code="VALIDATION.INVALID_FIELDS", error_stack=str(exc))
    fields = [
        {"field": ".".join(map(str, e.get("loc", []))), "error": e.get("msg", "")}
        for e in exc.errors()
    ]
    return problem_response(
        request,
        status=400,
        title="Validation Error",
        detail="Request body contains invalid fields",
        code="VALIDATION.INVALID_FIELDS",
        details={"fields": fields},
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = DEFAULT_CODE_BY_STATUS.get(exc.status_code, "SERVER.INTERNAL_ERROR")
    title = exc.detail if isinstance(exc.detail, str) else "Error"
    logger.warning("http_exception", error_code=code, http_status_code=exc.status_code)
    return problem_response(
        request,
        status=exc.status_code,
        title=title,
        detail=title,
        code=code,
    )


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "server_error",
        error_code="SERVER.INTERNAL_ERROR",
        error_type=type(exc).__name__,
        error_stack="".join(traceback.format_exception(exc))
    )
    return problem_response(
        request,
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred",
        code="SERVER.INTERNAL_ERROR",
    )
