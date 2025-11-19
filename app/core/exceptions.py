"""
Custom exceptions and exception handlers for Vailoo API.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class VailooException(Exception):
    """Base exception for Vailoo API."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class NotFoundException(VailooException):
    """Resource not found exception."""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(message, status.HTTP_404_NOT_FOUND, "NOT_FOUND")


class UnauthorizedException(VailooException):
    """Unauthorized access exception."""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED")


class ForbiddenException(VailooException):
    """Forbidden access exception."""
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "FORBIDDEN")


class BadRequestException(VailooException):
    """Bad request exception."""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, "BAD_REQUEST")


class ConflictException(VailooException):
    """Conflict exception (e.g., duplicate resource)."""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_409_CONFLICT, "CONFLICT")


class RateLimitException(VailooException):
    """Rate limit exceeded exception."""
    def __init__(self):
        super().__init__(
            "Rate limit exceeded. Please try again later.",
            status.HTTP_429_TOO_MANY_REQUESTS,
            "RATE_LIMIT_EXCEEDED"
        )


async def vailoo_exception_handler(request: Request, exc: VailooException) -> JSONResponse:
    """Handle custom Vailoo exceptions."""
    logger.error(f"VailooException: {exc.error_code} - {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'
        errors.append({
            "field": field or "request",
            "message": error["msg"]
        })

    logger.warning(f"Validation error: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )
