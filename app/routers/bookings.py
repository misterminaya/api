"""
Booking management endpoints for Vailoo API.
"""
import logging
from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_active_user
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.event import Event
from app.models.provider import ProviderProfile, Service
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingListResponse,
    BookingConfirm,
    BookingCancel,
    BookingComplete,
    BookingEventInfo,
    BookingServiceInfo,
    BookingProviderInfo,
    BookingOrganizerInfo,
)
from app.schemas.common import SuccessResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "",
    response_model=SuccessResponse[BookingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create booking",
    description="Create a booking request for a service."
)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new booking."""

    # Verify event exists and user owns it
    try:
        event = Event.get_by_id(booking_data.event_id)
    except Event.DoesNotExist:
        raise NotFoundException("Event", str(booking_data.event_id))

    if event.organizer_id != current_user.id:
        raise ForbiddenException("You can only create bookings for your own events")

    # Verify service exists
    try:
        service = Service.get_by_id(booking_data.service_id)
    except Service.DoesNotExist:
        raise NotFoundException("Service", str(booking_data.service_id))

    if not service.is_active:
        raise BadRequestException("This service is not currently available")

    # Check for duplicate booking
    existing = Booking.select().where(
        Booking.event == event.id,
        Booking.service == service.id,
        Booking.status.not_in([BookingStatus.CANCELLED.value, BookingStatus.REJECTED.value])
    ).exists()

    if existing:
        raise BadRequestException("A booking for this service already exists for this event")

    booking = Booking.create(
        event=event.id,
        service=service.id,
        organizer=current_user.id,
        provider=service.provider_id,
        quoted_price=booking_data.quoted_price,
        guest_count=booking_data.guest_count,
        organizer_notes=booking_data.organizer_notes,
    )

    logger.info(f"Booking created: {booking.id} for event {event.title}")

    return SuccessResponse(data=_booking_to_response(booking, include_details=True))


@router.get(
    "",
    response_model=BookingListResponse,
    summary="List bookings",
    description="Get bookings. Organizers see their bookings, providers see received bookings."
)
async def list_bookings(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: str = Query(None, alias="status"),
    as_provider: bool = Query(False),
    current_user: User = Depends(get_current_active_user)
):
    """List bookings for current user."""

    if as_provider:
        # Provider viewing received bookings
        profile = ProviderProfile.get_by_user(current_user.id)
        if not profile:
            raise ForbiddenException("You must have a provider profile")
        query = Booking.select().where(Booking.provider == profile.id)
    else:
        # Organizer viewing their bookings
        query = Booking.select().where(Booking.organizer == current_user.id)

    if status_filter:
        query = query.where(Booking.status == status_filter)

    total = query.count()
    bookings = list(query.order_by(Booking.created_at.desc()).paginate(page, limit))

    return BookingListResponse(
        data=[_booking_to_response(b, include_details=True) for b in bookings],
        pagination={
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    )


@router.get(
    "/event/{event_id}",
    response_model=BookingListResponse,
    summary="Get event bookings",
    description="Get all bookings for a specific event."
)
async def get_event_bookings(
    event_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get all bookings for an event."""

    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        raise NotFoundException("Event", str(event_id))

    # Check ownership
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Cannot view bookings for this event")

    bookings = list(Booking.get_by_event(event_id))

    return BookingListResponse(
        data=[_booking_to_response(b, include_details=True) for b in bookings],
        pagination={
            "total": len(bookings),
            "page": 1,
            "limit": len(bookings),
            "total_pages": 1
        }
    )


@router.get(
    "/{booking_id}",
    response_model=SuccessResponse[BookingResponse],
    summary="Get booking",
    description="Get booking details."
)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get booking by ID."""

    try:
        booking = Booking.get_by_id(booking_id)
    except Booking.DoesNotExist:
        raise NotFoundException("Booking", str(booking_id))

    # Check access
    profile = ProviderProfile.get_by_user(current_user.id)
    is_organizer = booking.organizer_id == current_user.id
    is_provider = profile and booking.provider_id == profile.id
    is_admin = current_user.role == UserRole.ADMIN.value

    if not is_organizer and not is_provider and not is_admin:
        raise ForbiddenException("Cannot access this booking")

    return SuccessResponse(data=_booking_to_response(booking, include_details=True))


@router.post(
    "/{booking_id}/confirm",
    response_model=SuccessResponse[BookingResponse],
    summary="Confirm booking",
    description="Provider confirms a booking request."
)
async def confirm_booking(
    booking_id: int,
    confirm_data: BookingConfirm,
    current_user: User = Depends(get_current_active_user)
):
    """Confirm a booking (provider only)."""

    try:
        booking = Booking.get_by_id(booking_id)
    except Booking.DoesNotExist:
        raise NotFoundException("Booking", str(booking_id))

    # Verify provider ownership
    profile = ProviderProfile.get_by_user(current_user.id)
    if not profile or booking.provider_id != profile.id:
        raise ForbiddenException("Only the provider can confirm this booking")

    if booking.status != BookingStatus.PENDING.value:
        raise BadRequestException(f"Cannot confirm booking with status: {booking.status}")

    booking.confirm(provider_notes=confirm_data.provider_notes)

    logger.info(f"Booking confirmed: {booking.id}")

    return SuccessResponse(data=_booking_to_response(booking, include_details=True))


@router.post(
    "/{booking_id}/reject",
    response_model=SuccessResponse[BookingResponse],
    summary="Reject booking",
    description="Provider rejects a booking request."
)
async def reject_booking(
    booking_id: int,
    cancel_data: BookingCancel,
    current_user: User = Depends(get_current_active_user)
):
    """Reject a booking (provider only)."""

    try:
        booking = Booking.get_by_id(booking_id)
    except Booking.DoesNotExist:
        raise NotFoundException("Booking", str(booking_id))

    # Verify provider ownership
    profile = ProviderProfile.get_by_user(current_user.id)
    if not profile or booking.provider_id != profile.id:
        raise ForbiddenException("Only the provider can reject this booking")

    if booking.status != BookingStatus.PENDING.value:
        raise BadRequestException(f"Cannot reject booking with status: {booking.status}")

    booking.reject(reason=cancel_data.reason)

    logger.info(f"Booking rejected: {booking.id}")

    return SuccessResponse(data=_booking_to_response(booking, include_details=True))


@router.post(
    "/{booking_id}/cancel",
    response_model=SuccessResponse[BookingResponse],
    summary="Cancel booking",
    description="Cancel a booking (organizer or provider)."
)
async def cancel_booking(
    booking_id: int,
    cancel_data: BookingCancel,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a booking."""

    try:
        booking = Booking.get_by_id(booking_id)
    except Booking.DoesNotExist:
        raise NotFoundException("Booking", str(booking_id))

    # Check access
    profile = ProviderProfile.get_by_user(current_user.id)
    is_organizer = booking.organizer_id == current_user.id
    is_provider = profile and booking.provider_id == profile.id

    if not is_organizer and not is_provider:
        raise ForbiddenException("Cannot cancel this booking")

    if booking.status in [BookingStatus.CANCELLED.value, BookingStatus.COMPLETED.value]:
        raise BadRequestException(f"Cannot cancel booking with status: {booking.status}")

    booking.cancel(reason=cancel_data.reason, by_organizer=is_organizer)

    logger.info(f"Booking cancelled: {booking.id}")

    return SuccessResponse(data=_booking_to_response(booking, include_details=True))


@router.post(
    "/{booking_id}/complete",
    response_model=SuccessResponse[BookingResponse],
    summary="Complete booking",
    description="Mark booking as completed after event."
)
async def complete_booking(
    booking_id: int,
    complete_data: BookingComplete,
    current_user: User = Depends(get_current_active_user)
):
    """Complete a booking (provider only)."""

    try:
        booking = Booking.get_by_id(booking_id)
    except Booking.DoesNotExist:
        raise NotFoundException("Booking", str(booking_id))

    # Verify provider ownership
    profile = ProviderProfile.get_by_user(current_user.id)
    if not profile or booking.provider_id != profile.id:
        raise ForbiddenException("Only the provider can complete this booking")

    if booking.status != BookingStatus.CONFIRMED.value:
        raise BadRequestException(f"Cannot complete booking with status: {booking.status}")

    final_price = float(complete_data.final_price) if complete_data.final_price else None
    booking.complete(final_price=final_price)

    logger.info(f"Booking completed: {booking.id}")

    return SuccessResponse(data=_booking_to_response(booking, include_details=True))


def _booking_to_response(
    booking: Booking,
    include_details: bool = False
) -> BookingResponse:
    """Convert Booking model to response schema."""
    event_info = None
    service_info = None
    provider_info = None
    organizer_info = None

    if include_details:
        event_info = BookingEventInfo(
            id=booking.event.id,
            title=booking.event.title,
            start_date=booking.event.start_date,
            city=booking.event.city,
        )
        service_info = BookingServiceInfo(
            id=booking.service.id,
            name=booking.service.name,
            category=booking.service.category,
        )
        provider_info = BookingProviderInfo(
            id=booking.provider.id,
            business_name=booking.provider.business_name,
        )
        organizer_info = BookingOrganizerInfo(
            id=booking.organizer.id,
            full_name=booking.organizer.full_name,
        )

    return BookingResponse(
        id=booking.id,
        status=booking.status,
        quoted_price=float(booking.quoted_price) if booking.quoted_price else 0.0,
        final_price=float(booking.final_price) if booking.final_price else None,
        guest_count=booking.guest_count,
        organizer_notes=booking.organizer_notes,
        provider_notes=booking.provider_notes,
        confirmed_at=booking.confirmed_at,
        completed_at=booking.completed_at,
        cancelled_at=booking.cancelled_at,
        cancellation_reason=booking.cancellation_reason,
        event=event_info,
        service=service_info,
        provider=provider_info,
        organizer=organizer_info,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )
