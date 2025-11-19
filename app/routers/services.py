"""
Service management endpoints for Vailoo API.
"""
import logging
from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_active_user, get_optional_current_user
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User, UserRole
from app.models.provider import ProviderProfile, Service, ServiceCategory
from app.schemas.provider import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
    ServiceProviderInfo,
)
from app.schemas.common import SuccessResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/services", tags=["Services"])


@router.post(
    "",
    response_model=SuccessResponse[ServiceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create service",
    description="Create a new service for provider's profile."
)
async def create_service(
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new service."""

    # Get provider profile
    profile = ProviderProfile.get_by_user(current_user.id)
    if not profile:
        raise ForbiddenException("You must have a provider profile to create services")

    service = Service.create(
        provider=profile.id,
        name=service_data.name,
        description=service_data.description,
        category=service_data.category.value,
        base_price=service_data.base_price,
        price_unit=service_data.price_unit,
        min_guests=service_data.min_guests,
        max_guests=service_data.max_guests,
        is_active=service_data.is_active,
        lead_time_days=service_data.lead_time_days,
    )

    logger.info(f"Service created: {service.name} by {profile.business_name}")

    return SuccessResponse(data=_service_to_response(service, include_provider=True))


@router.get(
    "",
    response_model=ServiceListResponse,
    summary="List services",
    description="Get paginated list of services with filters."
)
async def list_services(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: str = Query(None),
    city: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    provider_id: int = Query(None),
    current_user: User = Depends(get_optional_current_user)
):
    """List services with filters."""

    query = Service.select().join(ProviderProfile).where(Service.is_active == True)

    if category:
        query = query.where(Service.category == category)

    if city:
        query = query.where(ProviderProfile.city == city)

    if min_price is not None:
        query = query.where(Service.base_price >= min_price)

    if max_price is not None:
        query = query.where(Service.base_price <= max_price)

    if provider_id:
        query = query.where(Service.provider == provider_id)

    total = query.count()
    services = list(query.order_by(Service.base_price.asc()).paginate(page, limit))

    return ServiceListResponse(
        data=[_service_to_response(s, include_provider=True) for s in services],
        pagination={
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    )


@router.get(
    "/my-services",
    response_model=ServiceListResponse,
    summary="Get my services",
    description="Get all services for current provider."
)
async def get_my_services(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Get services for current provider."""

    profile = ProviderProfile.get_by_user(current_user.id)
    if not profile:
        raise ForbiddenException("You must have a provider profile")

    query = Service.select().where(Service.provider == profile.id)
    total = query.count()
    services = list(query.order_by(Service.created_at.desc()).paginate(page, limit))

    return ServiceListResponse(
        data=[_service_to_response(s, include_provider=False) for s in services],
        pagination={
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    )


@router.get(
    "/categories",
    summary="List service categories",
    description="Get all available service categories."
)
async def list_categories():
    """List all service categories."""
    return {
        "success": True,
        "data": [
            {"value": cat.value, "name": cat.name.replace("_", " ").title()}
            for cat in ServiceCategory
        ]
    }


@router.get(
    "/{service_id}",
    response_model=SuccessResponse[ServiceResponse],
    summary="Get service",
    description="Get service by ID."
)
async def get_service(
    service_id: int,
    current_user: User = Depends(get_optional_current_user)
):
    """Get service by ID."""

    try:
        service = Service.get_by_id(service_id)
    except Service.DoesNotExist:
        raise NotFoundException("Service", str(service_id))

    return SuccessResponse(data=_service_to_response(service, include_provider=True))


@router.put(
    "/{service_id}",
    response_model=SuccessResponse[ServiceResponse],
    summary="Update service",
    description="Update service. Only owner can update."
)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update service."""

    try:
        service = Service.get_by_id(service_id)
    except Service.DoesNotExist:
        raise NotFoundException("Service", str(service_id))

    # Check ownership
    profile = ProviderProfile.get_by_user(current_user.id)
    is_owner = profile and service.provider_id == profile.id
    is_admin = current_user.role == UserRole.ADMIN.value

    if not is_owner and not is_admin:
        raise ForbiddenException("Cannot update this service")

    # Update fields
    update_data = service_data.model_dump(exclude_unset=True)

    if 'category' in update_data and update_data['category']:
        update_data['category'] = update_data['category'].value

    for field, value in update_data.items():
        setattr(service, field, value)

    service.save()

    logger.info(f"Service updated: {service.name}")

    return SuccessResponse(data=_service_to_response(service, include_provider=True))


@router.delete(
    "/{service_id}",
    response_model=MessageResponse,
    summary="Delete service",
    description="Delete service. Only owner can delete."
)
async def delete_service(
    service_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete service."""

    try:
        service = Service.get_by_id(service_id)
    except Service.DoesNotExist:
        raise NotFoundException("Service", str(service_id))

    # Check ownership
    profile = ProviderProfile.get_by_user(current_user.id)
    is_owner = profile and service.provider_id == profile.id
    is_admin = current_user.role == UserRole.ADMIN.value

    if not is_owner and not is_admin:
        raise ForbiddenException("Cannot delete this service")

    service_name = service.name
    service.delete_instance()

    logger.info(f"Service deleted: {service_name}")

    return MessageResponse(message="Service deleted successfully")


def _service_to_response(
    service: Service,
    include_provider: bool = False
) -> ServiceResponse:
    """Convert Service model to response schema."""
    provider_info = None
    if include_provider:
        provider_info = ServiceProviderInfo(
            id=service.provider.id,
            business_name=service.provider.business_name,
            rating=float(service.provider.rating) if service.provider.rating else 0.0,
            city=service.provider.city,
        )

    return ServiceResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        category=service.category,
        base_price=float(service.base_price) if service.base_price else 0.0,
        price_unit=service.price_unit,
        min_guests=service.min_guests,
        max_guests=service.max_guests,
        is_active=service.is_active,
        lead_time_days=service.lead_time_days,
        provider=provider_info,
        created_at=service.created_at,
        updated_at=service.updated_at,
    )
