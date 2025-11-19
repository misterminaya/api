"""
Event model for Vailoo API.
Represents events created by organizers.
"""
from enum import Enum
from datetime import datetime
from peewee import (
    CharField,
    TextField,
    DateTimeField,
    IntegerField,
    DecimalField,
    ForeignKeyField,
    BooleanField,
)
from .base import BaseModel
from .user import User


class EventStatus(str, Enum):
    """Event status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Event(BaseModel):
    """Event model for Vailoo platform."""

    organizer = ForeignKeyField(User, backref='events', on_delete='CASCADE')
    title = CharField(max_length=200)
    description = TextField()
    event_type = CharField(max_length=100)  # wedding, corporate, birthday, etc.

    # Location
    venue_name = CharField(max_length=200, null=True)
    address = CharField(max_length=500)
    city = CharField(max_length=100)
    state = CharField(max_length=100, null=True)
    country = CharField(max_length=100, default="Mexico")
    postal_code = CharField(max_length=20, null=True)

    # Date and time
    start_date = DateTimeField()
    end_date = DateTimeField()

    # Capacity and budget
    expected_guests = IntegerField(default=0)
    budget = DecimalField(max_digits=12, decimal_places=2, null=True)

    # Status and visibility
    status = CharField(
        max_length=20,
        default=EventStatus.DRAFT.value,
        choices=[(status.value, status.name) for status in EventStatus]
    )
    is_public = BooleanField(default=False)

    # Media
    cover_image = CharField(max_length=500, null=True)

    class Meta:
        table_name = 'events'
        indexes = (
            (('organizer', 'status'), False),
            (('city', 'start_date'), False),
        )

    @property
    def is_upcoming(self) -> bool:
        """Check if event is in the future."""
        return self.start_date > datetime.now()

    @property
    def duration_hours(self) -> float:
        """Calculate event duration in hours."""
        if self.end_date and self.start_date:
            delta = self.end_date - self.start_date
            return delta.total_seconds() / 3600
        return 0

    @classmethod
    def get_by_organizer(cls, organizer_id: int, status: EventStatus = None):
        """Get events by organizer."""
        query = cls.select().where(cls.organizer == organizer_id)
        if status:
            query = query.where(cls.status == status.value)
        return query.order_by(cls.start_date.desc())

    @classmethod
    def get_public_events(cls, city: str = None, event_type: str = None):
        """Get public upcoming events."""
        query = cls.select().where(
            cls.is_public == True,
            cls.status == EventStatus.PUBLISHED.value,
            cls.start_date > datetime.now()
        )

        if city:
            query = query.where(cls.city == city)
        if event_type:
            query = query.where(cls.event_type == event_type)

        return query.order_by(cls.start_date.asc())

    def to_dict(self, include_organizer: bool = False) -> dict:
        """Convert event to dictionary."""
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "venue_name": self.venue_name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "expected_guests": self.expected_guests,
            "budget": float(self.budget) if self.budget else None,
            "status": self.status,
            "is_public": self.is_public,
            "cover_image": self.cover_image,
            "is_upcoming": self.is_upcoming,
            "duration_hours": self.duration_hours,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_organizer:
            data["organizer"] = {
                "id": self.organizer.id,
                "full_name": self.organizer.full_name,
                "email": self.organizer.email,
            }

        return data
