"""
Booking schemas for Vailoo API.
"""
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.booking import BookingStatus


class BookingBase(BaseModel):
    """Base booking schema."""
    event_id: int
    service_id: int
    quoted_price: Decimal = Field(..., ge=0, decimal_places=2)
    guest_count: Optional[int] = Field(None, ge=1)
    organizer_notes: Optional[str] = Field(None, max_length=1000)


class BookingCreate(BookingBase):
    """Schema for creating a booking."""
    pass


class BookingUpdate(BaseModel):
    """Schema for updating a booking."""
    status: Optional[BookingStatus] = None
    provider_notes: Optional[str] = Field(None, max_length=1000)
    final_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    cancellation_reason: Optional[str] = Field(None, max_length=500)


class BookingConfirm(BaseModel):
    """Schema for confirming a booking."""
    provider_notes: Optional[str] = Field(None, max_length=1000)


class BookingCancel(BaseModel):
    """Schema for cancelling a booking."""
    reason: Optional[str] = Field(None, max_length=500)


class BookingComplete(BaseModel):
    """Schema for completing a booking."""
    final_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class BookingEventInfo(BaseModel):
    """Event info embedded in booking response."""
    id: int
    title: str
    start_date: datetime
    city: str


class BookingServiceInfo(BaseModel):
    """Service info embedded in booking response."""
    id: int
    name: str
    category: str


class BookingProviderInfo(BaseModel):
    """Provider info embedded in booking response."""
    id: int
    business_name: str


class BookingOrganizerInfo(BaseModel):
    """Organizer info embedded in booking response."""
    id: int
    full_name: str


class BookingResponse(BaseModel):
    """Schema for booking response."""
    id: int
    status: str
    quoted_price: float
    final_price: Optional[float]
    guest_count: Optional[int]
    organizer_notes: Optional[str]
    provider_notes: Optional[str]
    confirmed_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    event: Optional[BookingEventInfo] = None
    service: Optional[BookingServiceInfo] = None
    provider: Optional[BookingProviderInfo] = None
    organizer: Optional[BookingOrganizerInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    """Schema for list of bookings response."""
    success: bool = True
    data: List[BookingResponse]
    pagination: dict
