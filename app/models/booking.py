"""
Booking model for Vailoo API.
Represents bookings between organizers and providers.
"""
from enum import Enum
from datetime import datetime
from peewee import (
    CharField,
    TextField,
    DateTimeField,
    DecimalField,
    ForeignKeyField,
    IntegerField,
)
from .base import BaseModel
from .user import User
from .event import Event
from .provider import Service, ProviderProfile


class BookingStatus(str, Enum):
    """Booking status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Booking(BaseModel):
    """Booking model for service reservations."""

    # Relationships
    event = ForeignKeyField(Event, backref='bookings', on_delete='CASCADE')
    service = ForeignKeyField(Service, backref='bookings', on_delete='CASCADE')
    organizer = ForeignKeyField(User, backref='bookings_made', on_delete='CASCADE')
    provider = ForeignKeyField(ProviderProfile, backref='bookings_received', on_delete='CASCADE')

    # Booking details
    status = CharField(
        max_length=20,
        default=BookingStatus.PENDING.value,
        choices=[(status.value, status.name) for status in BookingStatus]
    )

    # Pricing
    quoted_price = DecimalField(max_digits=12, decimal_places=2)
    final_price = DecimalField(max_digits=12, decimal_places=2, null=True)
    guest_count = IntegerField(null=True)

    # Notes and communication
    organizer_notes = TextField(null=True)
    provider_notes = TextField(null=True)

    # Timestamps for status changes
    confirmed_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
    cancelled_at = DateTimeField(null=True)
    cancellation_reason = TextField(null=True)

    class Meta:
        table_name = 'bookings'
        indexes = (
            (('event', 'service'), True),  # Unique: one service per event
            (('organizer', 'status'), False),
            (('provider', 'status'), False),
        )

    def confirm(self, provider_notes: str = None) -> None:
        """Confirm the booking."""
        self.status = BookingStatus.CONFIRMED.value
        self.confirmed_at = datetime.now()
        if provider_notes:
            self.provider_notes = provider_notes
        self.save()

    def reject(self, reason: str = None) -> None:
        """Reject the booking."""
        self.status = BookingStatus.REJECTED.value
        if reason:
            self.cancellation_reason = reason
        self.save()

    def cancel(self, reason: str = None, by_organizer: bool = True) -> None:
        """Cancel the booking."""
        self.status = BookingStatus.CANCELLED.value
        self.cancelled_at = datetime.now()
        if reason:
            prefix = "Organizer: " if by_organizer else "Provider: "
            self.cancellation_reason = prefix + reason
        self.save()

    def complete(self, final_price: float = None) -> None:
        """Mark booking as completed."""
        self.status = BookingStatus.COMPLETED.value
        self.completed_at = datetime.now()
        if final_price:
            self.final_price = final_price
        else:
            self.final_price = self.quoted_price
        self.save()

        # Update provider stats
        provider = self.provider
        provider.total_bookings += 1
        provider.save()

    @classmethod
    def get_by_organizer(cls, organizer_id: int, status: BookingStatus = None):
        """Get bookings by organizer."""
        query = cls.select().where(cls.organizer == organizer_id)
        if status:
            query = query.where(cls.status == status.value)
        return query.order_by(cls.created_at.desc())

    @classmethod
    def get_by_provider(cls, provider_id: int, status: BookingStatus = None):
        """Get bookings by provider."""
        query = cls.select().where(cls.provider == provider_id)
        if status:
            query = query.where(cls.status == status.value)
        return query.order_by(cls.created_at.desc())

    @classmethod
    def get_by_event(cls, event_id: int):
        """Get all bookings for an event."""
        return cls.select().where(cls.event == event_id).order_by(cls.created_at.asc())

    def to_dict(self, include_details: bool = False) -> dict:
        """Convert booking to dictionary."""
        data = {
            "id": self.id,
            "event_id": self.event.id,
            "service_id": self.service.id,
            "status": self.status,
            "quoted_price": float(self.quoted_price) if self.quoted_price else 0.0,
            "final_price": float(self.final_price) if self.final_price else None,
            "guest_count": self.guest_count,
            "organizer_notes": self.organizer_notes,
            "provider_notes": self.provider_notes,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancellation_reason": self.cancellation_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_details:
            data["event"] = {
                "id": self.event.id,
                "title": self.event.title,
                "start_date": self.event.start_date.isoformat() if self.event.start_date else None,
                "city": self.event.city,
            }
            data["service"] = {
                "id": self.service.id,
                "name": self.service.name,
                "category": self.service.category,
            }
            data["provider"] = {
                "id": self.provider.id,
                "business_name": self.provider.business_name,
            }
            data["organizer"] = {
                "id": self.organizer.id,
                "full_name": self.organizer.full_name,
            }

        return data
