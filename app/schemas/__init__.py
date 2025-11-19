# Schemas module for Vailoo API
from .user import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from .auth import (
    Token,
    TokenRefresh,
    PasswordChange,
    PasswordReset,
)
from .event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
)
from .provider import (
    ProviderProfileCreate,
    ProviderProfileUpdate,
    ProviderProfileResponse,
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
)
from .booking import (
    BookingCreate,
    BookingUpdate,
    BookingResponse,
    BookingListResponse,
)
from .common import (
    PaginationParams,
    PaginatedResponse,
    SuccessResponse,
    MessageResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    # Auth
    "Token",
    "TokenRefresh",
    "PasswordChange",
    "PasswordReset",
    # Event
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "EventListResponse",
    # Provider
    "ProviderProfileCreate",
    "ProviderProfileUpdate",
    "ProviderProfileResponse",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ServiceListResponse",
    # Booking
    "BookingCreate",
    "BookingUpdate",
    "BookingResponse",
    "BookingListResponse",
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "SuccessResponse",
    "MessageResponse",
]
