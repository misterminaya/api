"""
Authentication endpoints for Vailoo API.
Handles registration, login, token refresh, and password management.
"""
import logging
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
)
from app.core.exceptions import (
    BadRequestException,
    UnauthorizedException,
    ConflictException,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import Token, TokenRefresh, PasswordChange
from app.schemas.common import SuccessResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email verification pending."
)
async def register(user_data: UserCreate):
    """Register a new user account."""

    # Check if email already exists
    existing_user = User.get_by_email(user_data.email)
    if existing_user:
        raise ConflictException("Email address is already registered")

    # Create user
    user = User.create_user(
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        phone=user_data.phone,
    )

    logger.info(f"New user registered: {user.email} (role: {user.role})")

    return SuccessResponse(
        data=UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
            is_verified=user.is_verified,
            profile_image=user.profile_image,
            bio=user.bio,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and return access and refresh tokens."
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return tokens."""

    user = User.authenticate(form_data.username, form_data.password)

    if not user:
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    # Create tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info(f"User logged in: {user.email}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get new access token using refresh token."
)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token using refresh token."""

    payload = decode_token(token_data.refresh_token)

    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid token type")

    user_id = payload.get("sub")
    try:
        user = User.get_by_id(int(user_id))
    except User.DoesNotExist:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    # Create new tokens
    new_token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(new_token_data)
    refresh_token = create_refresh_token(new_token_data)

    logger.info(f"Token refreshed for user: {user.email}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change current user's password."
)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user)
):
    """Change user's password."""

    # Verify current password
    if not current_user.check_password(password_data.current_password):
        raise BadRequestException("Current password is incorrect")

    # Check new password is different
    if password_data.current_password == password_data.new_password:
        raise BadRequestException("New password must be different from current password")

    # Update password
    current_user.set_password(password_data.new_password)
    current_user.save()

    logger.info(f"Password changed for user: {current_user.email}")

    return MessageResponse(message="Password changed successfully")


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Get current user",
    description="Get profile of currently authenticated user."
)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's profile."""

    return SuccessResponse(
        data=UserResponse(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            full_name=current_user.full_name,
            phone=current_user.phone,
            role=current_user.role,
            is_verified=current_user.is_verified,
            profile_image=current_user.profile_image,
            bio=current_user.bio,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
        )
    )
