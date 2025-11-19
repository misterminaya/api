"""
Provider profile management endpoints for Vailoo API.
"""
import logging
from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_active_user, get_optional_current_user
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ConflictException,
)
from app.models.user import User, UserRole
from app.models.provider import ProviderProfile
from app.schemas.provider import (
    ProviderProfileCreate,
    ProviderProfileUpdate,
    ProviderProfileResponse,
    ProviderUserInfo,
)
from app.schemas.common import SuccessResponse, MessageResponse, PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.post(
    "",
    response_model=SuccessResponse[ProviderProfileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create provider profile",
    description="Create provider profile for current user. Only providers can create profiles."
)
async def create_provider_profile(
    profile_data: ProviderProfileCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create provider profile."""

    # Only providers can create profiles
    if current_user.role != UserRole.PROVIDER.value:
        raise ForbiddenException("Only providers can create provider profiles")

    # Check if profile already exists
    existing = ProviderProfile.get_by_user(current_user.id)
    if existing:
        raise ConflictException("Provider profile already exists")

    profile = ProviderProfile.create(
        user=current_user.id,
        business_name=profile_data.business_name,
        business_description=profile_data.business_description,
        tax_id=profile_data.tax_id,
        business_phone=profile_data.business_phone,
        business_email=profile_data.business_email,
        website=profile_data.website,
        address=profile_data.address,
        city=profile_data.city,
        state=profile_data.state,
        country=profile_data.country,
        service_area=profile_data.service_area,
        logo=profile_data.logo,
        cover_image=profile_data.cover_image,
    )

    logger.info(f"Provider profile created: {profile.business_name}")

    return SuccessResponse(data=_profile_to_response(profile, include_user=True))


@router.get(
    "",
    response_model=PaginatedResponse[ProviderProfileResponse],
    summary="List providers",
    description="Get paginated list of provider profiles."
)
async def list_providers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    city: str = Query(None),
    verified_only: bool = Query(False),
    current_user: User = Depends(get_optional_current_user)
):
    """List provider profiles."""

    query = ProviderProfile.select()

    if city:
        query = query.where(ProviderProfile.city == city)

    if verified_only:
        query = query.where(ProviderProfile.is_verified == True)

    total = query.count()
    profiles = list(query.order_by(ProviderProfile.rating.desc()).paginate(page, limit))

    return PaginatedResponse.create(
        data=[_profile_to_response(p, include_user=True) for p in profiles],
        total=total,
        page=page,
        limit=limit
    )


@router.get(
    "/me",
    response_model=SuccessResponse[ProviderProfileResponse],
    summary="Get my provider profile",
    description="Get current user's provider profile."
)
async def get_my_provider_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's provider profile."""

    profile = ProviderProfile.get_by_user(current_user.id)
    if not profile:
        raise NotFoundException("Provider profile")

    return SuccessResponse(data=_profile_to_response(profile, include_user=True))


@router.get(
    "/{provider_id}",
    response_model=SuccessResponse[ProviderProfileResponse],
    summary="Get provider profile",
    description="Get provider profile by ID."
)
async def get_provider_profile(
    provider_id: int,
    current_user: User = Depends(get_optional_current_user)
):
    """Get provider profile by ID."""

    try:
        profile = ProviderProfile.get_by_id(provider_id)
    except ProviderProfile.DoesNotExist:
        raise NotFoundException("Provider profile", str(provider_id))

    return SuccessResponse(data=_profile_to_response(profile, include_user=True))


@router.put(
    "/{provider_id}",
    response_model=SuccessResponse[ProviderProfileResponse],
    summary="Update provider profile",
    description="Update provider profile. Only owner can update."
)
async def update_provider_profile(
    provider_id: int,
    profile_data: ProviderProfileUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update provider profile."""

    try:
        profile = ProviderProfile.get_by_id(provider_id)
    except ProviderProfile.DoesNotExist:
        raise NotFoundException("Provider profile", str(provider_id))

    # Check ownership
    if profile.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Cannot update this profile")

    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    profile.save()

    logger.info(f"Provider profile updated: {profile.business_name}")

    return SuccessResponse(data=_profile_to_response(profile, include_user=True))


@router.delete(
    "/{provider_id}",
    response_model=MessageResponse,
    summary="Delete provider profile",
    description="Delete provider profile. Only owner can delete."
)
async def delete_provider_profile(
    provider_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete provider profile."""

    try:
        profile = ProviderProfile.get_by_id(provider_id)
    except ProviderProfile.DoesNotExist:
        raise NotFoundException("Provider profile", str(provider_id))

    # Check ownership
    if profile.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Cannot delete this profile")

    business_name = profile.business_name
    profile.delete_instance()

    logger.info(f"Provider profile deleted: {business_name}")

    return MessageResponse(message="Provider profile deleted successfully")


def _profile_to_response(
    profile: ProviderProfile,
    include_user: bool = False
) -> ProviderProfileResponse:
    """Convert ProviderProfile model to response schema."""
    user_info = None
    if include_user:
        user_info = ProviderUserInfo(
            id=profile.user.id,
            full_name=profile.user.full_name,
            email=profile.user.email,
        )

    return ProviderProfileResponse(
        id=profile.id,
        business_name=profile.business_name,
        business_description=profile.business_description,
        tax_id=profile.tax_id,
        business_phone=profile.business_phone,
        business_email=profile.business_email,
        website=profile.website,
        address=profile.address,
        city=profile.city,
        state=profile.state,
        country=profile.country,
        service_area=profile.service_area,
        is_verified=profile.is_verified,
        is_featured=profile.is_featured,
        rating=float(profile.rating) if profile.rating else 0.0,
        total_reviews=profile.total_reviews,
        total_bookings=profile.total_bookings,
        logo=profile.logo,
        cover_image=profile.cover_image,
        user=user_info,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
