"""
Request logging middleware for Vailoo API.
Provides structured logging for all HTTP requests.
"""
import time
import logging
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response details."""

        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]

        # Add request ID to state for use in handlers
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Get client IP
        client_ip = request.headers.get(
            "X-Forwarded-For",
            request.client.host if request.client else "unknown"
        )
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- Client: {client_ip}"
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- Error: {str(e)} - {process_time:.2f}ms"
            )
            raise

        # Calculate processing time
        process_time = (time.time() - start_time) * 1000

        # Log response
        log_level = logging.INFO if response.status_code < 400 else logging.WARNING
        logger.log(
            log_level,
            f"[{request_id}] {request.method} {request.url.path} "
            f"- Status: {response.status_code} - {process_time:.2f}ms"
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response
