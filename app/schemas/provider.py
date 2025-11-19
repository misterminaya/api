"""
Provider and Service schemas for Vailoo API.
"""
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator
from app.models.provider import ServiceCategory
import re


class ProviderProfileBase(BaseModel):
    """Base provider profile schema."""
    business_name: str = Field(..., min_length=2, max_length=200)
    business_description: str = Field(..., min_length=10, max_length=2000)
    tax_id: Optional[str] = Field(None, max_length=50)
    business_phone: str = Field(..., max_length=20)
    business_email: EmailStr
    website: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = Field(None, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: str = Field(default="Mexico", max_length=100)
    service_area: Optional[str] = Field(None, max_length=500)

    @field_validator('business_phone')
    @classmethod
    def validate_phone(cls, v):
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v


class ProviderProfileCreate(ProviderProfileBase):
    """Schema for creating provider profile."""
    logo: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = Field(None, max_length=500)


class ProviderProfileUpdate(BaseModel):
    """Schema for updating provider profile."""
    business_name: Optional[str] = Field(None, min_length=2, max_length=200)
    business_description: Optional[str] = Field(None, min_length=10, max_length=2000)
    tax_id: Optional[str] = Field(None, max_length=50)
    business_phone: Optional[str] = Field(None, max_length=20)
    business_email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    service_area: Optional[str] = Field(None, max_length=500)
    logo: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = Field(None, max_length=500)

    @field_validator('business_phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v


class ProviderUserInfo(BaseModel):
    """User info embedded in provider response."""
    id: int
    full_name: str
    email: str


class ProviderProfileResponse(BaseModel):
    """Schema for provider profile response."""
    id: int
    business_name: str
    business_description: str
    tax_id: Optional[str]
    business_phone: str
    business_email: str
    website: Optional[str]
    address: Optional[str]
    city: str
    state: Optional[str]
    country: str
    service_area: Optional[str]
    is_verified: bool
    is_featured: bool
    rating: float
    total_reviews: int
    total_bookings: int
    logo: Optional[str]
    cover_image: Optional[str]
    user: Optional[ProviderUserInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Service schemas
class ServiceBase(BaseModel):
    """Base service schema."""
    name: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: ServiceCategory
    base_price: Decimal = Field(..., ge=0, decimal_places=2)
    price_unit: str = Field(default="event", max_length=50)
    min_guests: Optional[int] = Field(None, ge=1)
    max_guests: Optional[int] = Field(None, ge=1)
    lead_time_days: int = Field(default=7, ge=1, le=365)

    @field_validator('max_guests')
    @classmethod
    def max_greater_than_min(cls, v, info):
        if v is not None and 'min_guests' in info.data:
            if info.data['min_guests'] is not None and v < info.data['min_guests']:
                raise ValueError('max_guests must be greater than min_guests')
        return v


class ServiceCreate(ServiceBase):
    """Schema for creating a service."""
    is_active: bool = Field(default=True)


class ServiceUpdate(BaseModel):
    """Schema for updating a service."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    category: Optional[ServiceCategory] = None
    base_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    price_unit: Optional[str] = Field(None, max_length=50)
    min_guests: Optional[int] = Field(None, ge=1)
    max_guests: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    lead_time_days: Optional[int] = Field(None, ge=1, le=365)


class ServiceProviderInfo(BaseModel):
    """Provider info embedded in service response."""
    id: int
    business_name: str
    rating: float
    city: str


class ServiceResponse(BaseModel):
    """Schema for service response."""
    id: int
    name: str
    description: str
    category: str
    base_price: float
    price_unit: str
    min_guests: Optional[int]
    max_guests: Optional[int]
    is_active: bool
    lead_time_days: int
    provider: Optional[ServiceProviderInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """Schema for list of services response."""
    success: bool = True
    data: List[ServiceResponse]
    pagination: dict
