"""
Event schemas for Vailoo API.
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.models.event import EventStatus


class EventBase(BaseModel):
    """Base event schema with common fields."""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    event_type: str = Field(..., min_length=2, max_length=100)

    # Location
    venue_name: Optional[str] = Field(None, max_length=200)
    address: str = Field(..., min_length=5, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: str = Field(default="Mexico", max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)

    # Date and time
    start_date: datetime
    end_date: datetime

    # Capacity and budget
    expected_guests: int = Field(default=0, ge=0, le=100000)
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

    @field_validator('end_date')
    @classmethod
    def end_after_start(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @field_validator('start_date')
    @classmethod
    def start_in_future(cls, v):
        if v <= datetime.now():
            raise ValueError('Event start date must be in the future')
        return v


class EventCreate(EventBase):
    """Schema for creating an event."""
    is_public: bool = Field(default=False)
    cover_image: Optional[str] = Field(None, max_length=500)


class EventUpdate(BaseModel):
    """Schema for updating an event."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    event_type: Optional[str] = Field(None, min_length=2, max_length=100)
    venue_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    expected_guests: Optional[int] = Field(None, ge=0, le=100000)
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    status: Optional[EventStatus] = None
    is_public: Optional[bool] = None
    cover_image: Optional[str] = Field(None, max_length=500)


class EventOrganizerInfo(BaseModel):
    """Organizer info embedded in event response."""
    id: int
    full_name: str
    email: str


class EventResponse(BaseModel):
    """Schema for event response."""
    id: int
    title: str
    description: str
    event_type: str
    venue_name: Optional[str]
    address: str
    city: str
    state: Optional[str]
    country: str
    postal_code: Optional[str]
    start_date: datetime
    end_date: datetime
    expected_guests: int
    budget: Optional[float]
    status: str
    is_public: bool
    cover_image: Optional[str]
    is_upcoming: bool
    duration_hours: float
    organizer: Optional[EventOrganizerInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Schema for list of events response."""
    success: bool = True
    data: List[EventResponse]
    pagination: dict
