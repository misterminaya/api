# Routers module for Vailoo API
from .auth import router as auth_router
from .users import router as users_router
from .events import router as events_router
from .providers import router as providers_router
from .services import router as services_router
from .bookings import router as bookings_router

__all__ = [
    "auth_router",
    "users_router",
    "events_router",
    "providers_router",
    "services_router",
    "bookings_router",
]
