import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request


logger = logging.getLogger("app.requests")


async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    started_at = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_id=%s method=%s path=%s status=500 duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            (perf_counter() - started_at) * 1000,
        )
        raise

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (perf_counter() - started_at) * 1000,
    )
    return response