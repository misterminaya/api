"""
Event management endpoints for Vailoo API.
"""
import logging
from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_active_user, get_optional_current_user
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.user import User, UserRole
from app.models.event import Event, EventStatus
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    EventOrganizerInfo,
)
from app.schemas.common import SuccessResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "",
    response_model=SuccessResponse[EventResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create event",
    description="Create a new event. Only organizers can create events."
)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new event."""

    # Only organizers and admins can create events
    if current_user.role not in [UserRole.ORGANIZER.value, UserRole.ADMIN.value]:
        raise ForbiddenException("Only organizers can create events")

    event = Event.create(
        organizer=current_user.id,
        title=event_data.title,
        description=event_data.description,
        event_type=event_data.event_type,
        venue_name=event_data.venue_name,
        address=event_data.address,
        city=event_data.city,
        state=event_data.state,
        country=event_data.country,
        postal_code=event_data.postal_code,
        start_date=event_data.start_date,
        end_date=event_data.end_date,
        expected_guests=event_data.expected_guests,
        budget=event_data.budget,
        is_public=event_data.is_public,
        cover_image=event_data.cover_image,
    )

    logger.info(f"Event created: {event.title} by {current_user.email}")

    return SuccessResponse(data=_event_to_response(event, include_organizer=True))


@router.get(
    "",
    response_model=EventListResponse,
    summary="List events",
    description="Get paginated list of events. Public events visible to all."
)
async def list_events(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    city: str = Query(None),
    event_type: str = Query(None),
    status_filter: str = Query(None, alias="status"),
    my_events: bool = Query(False),
    current_user: User = Depends(get_optional_current_user)
):
    """List events with filters."""

    if my_events:
        if not current_user:
            raise ForbiddenException("Authentication required to view your events")
        query = Event.select().where(Event.organizer == current_user.id)
    else:
        # Public events only for non-authenticated or non-owner
        query = Event.select().where(
            Event.is_public == True,
            Event.status == EventStatus.PUBLISHED.value
        )

    if city:
        query = query.where(Event.city == city)
    if event_type:
        query = query.where(Event.event_type == event_type)
    if status_filter:
        query = query.where(Event.status == status_filter)

    total = query.count()
    events = list(query.order_by(Event.start_date.desc()).paginate(page, limit))

    return EventListResponse(
        data=[_event_to_response(event, include_organizer=True) for event in events],
        pagination={
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    )


@router.get(
    "/{event_id}",
    response_model=SuccessResponse[EventResponse],
    summary="Get event",
    description="Get event details by ID."
)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_optional_current_user)
):
    """Get event by ID."""

    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        raise NotFoundException("Event", str(event_id))

    # Check access - public events or owner
    is_owner = current_user and event.organizer_id == current_user.id
    is_admin = current_user and current_user.role == UserRole.ADMIN.value

    if not event.is_public and not is_owner and not is_admin:
        raise ForbiddenException("Cannot access this event")

    return SuccessResponse(data=_event_to_response(event, include_organizer=True))


@router.put(
    "/{event_id}",
    response_model=SuccessResponse[EventResponse],
    summary="Update event",
    description="Update event details. Only owner can update."
)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update event."""

    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        raise NotFoundException("Event", str(event_id))

    # Check ownership
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Cannot update this event")

    # Update fields
    update_data = event_data.model_dump(exclude_unset=True)

    # Handle status changes
    if 'status' in update_data:
        new_status = update_data['status']
        if isinstance(new_status, EventStatus):
            update_data['status'] = new_status.value

    for field, value in update_data.items():
        setattr(event, field, value)

    event.save()

    logger.info(f"Event updated: {event.title}")

    return SuccessResponse(data=_event_to_response(event, include_organizer=True))


@router.delete(
    "/{event_id}",
    response_model=MessageResponse,
    summary="Cancel event",
    description="Cancel an event. Only owner can cancel."
)
async def cancel_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel event."""

    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        raise NotFoundException("Event", str(event_id))

    # Check ownership
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Cannot cancel this event")

    if event.status == EventStatus.CANCELLED.value:
        raise BadRequestException("Event is already cancelled")

    event.status = EventStatus.CANCELLED.value
    event.save()

    logger.info(f"Event cancelled: {event.title}")

    return MessageResponse(message="Event cancelled successfully")


@router.post(
    "/{event_id}/publish",
    response_model=SuccessResponse[EventResponse],
    summary="Publish event",
    description="Publish a draft event to make it visible."
)
async def publish_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Publish event."""

    try:
        event = Event.get_by_id(event_id)
    except Event.DoesNotExist:
        raise NotFoundException("Event", str(event_id))

    # Check ownership
    if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise ForbiddenException("Cannot publish this event")

    if event.status != EventStatus.DRAFT.value:
        raise BadRequestException(f"Cannot publish event with status: {event.status}")

    event.status = EventStatus.PUBLISHED.value
    event.save()

    logger.info(f"Event published: {event.title}")

    return SuccessResponse(data=_event_to_response(event, include_organizer=True))


def _event_to_response(event: Event, include_organizer: bool = False) -> EventResponse:
    """Convert Event model to EventResponse schema."""
    organizer_info = None
    if include_organizer:
        organizer_info = EventOrganizerInfo(
            id=event.organizer.id,
            full_name=event.organizer.full_name,
            email=event.organizer.email,
        )

    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        venue_name=event.venue_name,
        address=event.address,
        city=event.city,
        state=event.state,
        country=event.country,
        postal_code=event.postal_code,
        start_date=event.start_date,
        end_date=event.end_date,
        expected_guests=event.expected_guests,
        budget=float(event.budget) if event.budget else None,
        status=event.status,
        is_public=event.is_public,
        cover_image=event.cover_image,
        is_upcoming=event.is_upcoming,
        duration_hours=event.duration_hours,
        organizer=organizer_info,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
