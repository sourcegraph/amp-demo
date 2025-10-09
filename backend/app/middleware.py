import binascii
import os
import time
from typing import Callable, Awaitable
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .logging_config import trace_id_var, span_id_var, request_id_var


logger = structlog.get_logger()


def _gen_hex(n_bytes: int) -> str:
    return binascii.b2a_hex(os.urandom(n_bytes)).decode()


def parse_traceparent(tp: str | None) -> tuple[str | None, str | None]:
    if not tp:
        return None, None
    try:
        parts = tp.split("-")
        if len(parts) == 4 and parts[0] == "00":
            return parts[1], parts[2]
    except Exception:
        pass
    return None, None


class TraceLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        incoming_tp = request.headers.get("traceparent")
        trace_id, parent_span = parse_traceparent(incoming_tp)
        if not trace_id:
            trace_id = _gen_hex(16)
        span_id = _gen_hex(8)
        
        trace_id_var.set(trace_id)
        span_id_var.set(span_id)
        request_id_var.set(trace_id)

        start = time.perf_counter()
        bound = logger.bind(http_method=request.method, http_path=str(request.url.path))
        bound.info("request_started")

        response: Response | None = None
        try:
            response = await call_next(request)
        except Exception as exc:
            bound.error("unhandled_exception", error_type=type(exc).__name__)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            bound = bound.bind(duration_ms=duration_ms)

        response.headers["X-Request-ID"] = trace_id
        response.headers["traceparent"] = f"00-{trace_id}-{span_id}-01"
        response.headers["Access-Control-Expose-Headers"] = "X-Request-ID, traceparent, Content-Type"

        status_code = getattr(response, "status_code", None)
        bound.bind(http_status_code=status_code).info("request_completed")
        return response
