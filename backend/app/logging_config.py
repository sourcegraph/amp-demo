import os
import contextvars
import structlog


trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("trace_id", default=None)
span_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("span_id", default=None)
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


def setup_logging() -> None:
    service_name = os.getenv("SERVICE_NAME", "linea-api")
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")
    environment = os.getenv("ENVIRONMENT", "development")

    def add_static_fields(logger: structlog.types.WrappedLogger, method_name: str, event_dict: structlog.types.EventDict) -> structlog.types.EventDict:
        event_dict["service_name"] = service_name
        event_dict["service_version"] = service_version
        event_dict["environment"] = environment
        return event_dict

    def add_trace_fields(logger: structlog.types.WrappedLogger, method_name: str, event_dict: structlog.types.EventDict) -> structlog.types.EventDict:
        event_dict["trace_id"] = trace_id_var.get()
        event_dict["span_id"] = span_id_var.get()
        event_dict["request_id"] = request_id_var.get()
        return event_dict

    import logging
    
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            add_static_fields,
            add_trace_fields,
            structlog.processors.add_log_level,
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(os.getenv("LOG_LEVEL", "INFO").upper())
        ),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
