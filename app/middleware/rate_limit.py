"""
Rate limiting middleware for Vailoo API.
Implements a sliding window rate limiter using in-memory storage.
"""
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.

    For production, replace in-memory storage with Redis for distributed systems.
    """

    def __init__(self, app, requests_limit: int = None, window_seconds: int = None):
        super().__init__(app)
        self.requests_limit = requests_limit or settings.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW
        # In-memory storage: {client_id: [(timestamp, weight), ...]}
        self.requests: Dict[str, List[Tuple[float, int]]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier from request."""
        # Use X-Forwarded-For header if behind proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"

    def _clean_old_requests(self, client_id: str, current_time: float) -> None:
        """Remove requests outside the current window."""
        cutoff_time = current_time - self.window_seconds
        self.requests[client_id] = [
            (ts, weight) for ts, weight in self.requests[client_id]
            if ts > cutoff_time
        ]

    def _get_request_count(self, client_id: str) -> int:
        """Get total request count for client in current window."""
        return sum(weight for _, weight in self.requests[client_id])

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""

        # Skip rate limiting for health check endpoints
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)

        client_id = self._get_client_id(request)
        current_time = time.time()

        # Clean old requests
        self._clean_old_requests(client_id, current_time)

        # Check rate limit
        request_count = self._get_request_count(client_id)

        if request_count >= self.requests_limit:
            # Calculate retry after time
            if self.requests[client_id]:
                oldest_request = min(ts for ts, _ in self.requests[client_id])
                retry_after = int(oldest_request + self.window_seconds - current_time)
            else:
                retry_after = self.window_seconds

            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later."
                    }
                },
                headers={
                    "Retry-After": str(max(1, retry_after)),
                    "X-RateLimit-Limit": str(self.requests_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + retry_after))
                }
            )

        # Record request
        self.requests[client_id].append((current_time, 1))

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self.requests_limit - self._get_request_count(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.requests_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))

        return response
