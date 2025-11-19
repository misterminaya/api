"""
Vailoo API - Main Application
Platform connecting event providers with organizers.
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from peewee import OperationalError

from app.core.config import settings
from app.core.exceptions import (
    VailooException,
    vailoo_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from app.models import (
    database,
    User,
    Event,
    ProviderProfile,
    Service,
    Booking,
)
from app.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
)
from app.routers import (
    auth_router,
    users_router,
    events_router,
    providers_router,
    services_router,
    bookings_router,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Connect to database with retry
    max_retries = 10
    retry_delay = 3

    for attempt in range(max_retries):
        try:
            if database.is_closed():
                database.connect()

            # Create tables if they don't exist
            database.create_tables([
                User,
                Event,
                ProviderProfile,
                Service,
                Booking,
            ], safe=True)

            logger.info("Database connection established and tables ready")
            break

        except OperationalError as e:
            logger.warning(
                f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("Failed to connect to database after maximum retries")
                raise

    yield

    # Shutdown
    logger.info("Shutting down application")
    if not database.is_closed():
        database.close()
        logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add middleware (order matters - last added is first executed)
# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting
if not settings.DEBUG:
    app.add_middleware(RateLimitMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Exception handlers
app.add_exception_handler(VailooException, vailoo_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(events_router, prefix=settings.API_V1_PREFIX)
app.include_router(providers_router, prefix=settings.API_V1_PREFIX)
app.include_router(services_router, prefix=settings.API_V1_PREFIX)
app.include_router(bookings_router, prefix=settings.API_V1_PREFIX)


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - verifies database connection."""
    try:
        if database.is_closed():
            database.connect()

        # Simple query to verify connection
        database.execute_sql("SELECT 1")

        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not ready",
            "database": "disconnected",
            "error": str(e),
        }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "health": "/health",
        "api_prefix": settings.API_V1_PREFIX,
    }
