"""
User management endpoints for Vailoo API.
"""
import logging
from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_active_user
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User, UserRole
from app.schemas.user import UserUpdate, UserResponse, UserListResponse
from app.schemas.common import SuccessResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
    description="Get paginated list of users. Admin only."
)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role: str = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    """List all users (admin only)."""

    if current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Admin access required")

    query = User.select()

    if role:
        query = query.where(User.role == role)

    total = query.count()
    users = list(query.order_by(User.created_at.desc()).paginate(page, limit))

    return UserListResponse(
        data=[
            UserResponse(
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
            for user in users
        ],
        pagination={
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    )


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserResponse],
    summary="Get user by ID",
    description="Get user details by ID."
)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID."""

    # Users can only view their own profile unless admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Cannot view other users' profiles")

    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        raise NotFoundException("User", str(user_id))

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


@router.put(
    "/{user_id}",
    response_model=SuccessResponse[UserResponse],
    summary="Update user",
    description="Update user profile."
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update user profile."""

    # Users can only update their own profile unless admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Cannot update other users' profiles")

    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        raise NotFoundException("User", str(user_id))

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.save()

    logger.info(f"User profile updated: {user.email}")

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


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Deactivate user",
    description="Deactivate user account."
)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate user account."""

    # Users can only deactivate their own account unless admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Cannot deactivate other users' accounts")

    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        raise NotFoundException("User", str(user_id))

    user.is_active = False
    user.save()

    logger.info(f"User deactivated: {user.email}")

    return MessageResponse(message="User account deactivated successfully")
