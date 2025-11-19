"""
Provider and Service models for Vailoo API.
Represents service providers and their offerings.
"""
from enum import Enum
from peewee import (
    CharField,
    TextField,
    DecimalField,
    ForeignKeyField,
    BooleanField,
    IntegerField,
)
from .base import BaseModel
from .user import User


class ServiceCategory(str, Enum):
    """Service category enumeration."""
    CATERING = "catering"
    PHOTOGRAPHY = "photography"
    VIDEOGRAPHY = "videography"
    MUSIC = "music"
    DECORATION = "decoration"
    VENUE = "venue"
    PLANNING = "planning"
    ENTERTAINMENT = "entertainment"
    TRANSPORTATION = "transportation"
    FLOWERS = "flowers"
    CAKE = "cake"
    LIGHTING = "lighting"
    SECURITY = "security"
    OTHER = "other"


class ProviderProfile(BaseModel):
    """Provider profile model for service providers."""

    user = ForeignKeyField(User, backref='provider_profile', unique=True, on_delete='CASCADE')

    # Business information
    business_name = CharField(max_length=200)
    business_description = TextField()
    tax_id = CharField(max_length=50, null=True)

    # Contact
    business_phone = CharField(max_length=20)
    business_email = CharField(max_length=255)
    website = CharField(max_length=500, null=True)

    # Location
    address = CharField(max_length=500, null=True)
    city = CharField(max_length=100)
    state = CharField(max_length=100, null=True)
    country = CharField(max_length=100, default="Mexico")
    service_area = CharField(max_length=500, null=True)  # Cities/regions they serve

    # Status
    is_verified = BooleanField(default=False)
    is_featured = BooleanField(default=False)

    # Stats
    rating = DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = IntegerField(default=0)
    total_bookings = IntegerField(default=0)

    # Media
    logo = CharField(max_length=500, null=True)
    cover_image = CharField(max_length=500, null=True)
    portfolio_images = TextField(null=True)  # JSON array of image URLs

    class Meta:
        table_name = 'provider_profiles'
        indexes = (
            (('city', 'is_verified'), False),
        )

    @classmethod
    def get_by_user(cls, user_id: int):
        """Get provider profile by user ID."""
        try:
            return cls.get(cls.user == user_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_verified_providers(cls, city: str = None):
        """Get verified provider profiles."""
        query = cls.select().where(cls.is_verified == True)
        if city:
            query = query.where(cls.city == city)
        return query.order_by(cls.rating.desc())

    def to_dict(self, include_user: bool = False) -> dict:
        """Convert provider profile to dictionary."""
        data = {
            "id": self.id,
            "business_name": self.business_name,
            "business_description": self.business_description,
            "business_phone": self.business_phone,
            "business_email": self.business_email,
            "website": self.website,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "service_area": self.service_area,
            "is_verified": self.is_verified,
            "is_featured": self.is_featured,
            "rating": float(self.rating) if self.rating else 0.0,
            "total_reviews": self.total_reviews,
            "total_bookings": self.total_bookings,
            "logo": self.logo,
            "cover_image": self.cover_image,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_user:
            data["user"] = {
                "id": self.user.id,
                "full_name": self.user.full_name,
                "email": self.user.email,
            }

        return data


class Service(BaseModel):
    """Service model for provider offerings."""

    provider = ForeignKeyField(ProviderProfile, backref='services', on_delete='CASCADE')

    name = CharField(max_length=200)
    description = TextField()
    category = CharField(
        max_length=50,
        choices=[(cat.value, cat.name) for cat in ServiceCategory]
    )

    # Pricing
    base_price = DecimalField(max_digits=12, decimal_places=2)
    price_unit = CharField(max_length=50, default="event")  # event, hour, person, etc.
    min_guests = IntegerField(null=True)
    max_guests = IntegerField(null=True)

    # Availability
    is_active = BooleanField(default=True)
    lead_time_days = IntegerField(default=7)  # Days notice required

    # Media
    images = TextField(null=True)  # JSON array of image URLs

    class Meta:
        table_name = 'services'
        indexes = (
            (('provider', 'category'), False),
            (('category', 'is_active'), False),
        )

    @classmethod
    def get_by_category(cls, category: ServiceCategory, city: str = None):
        """Get active services by category."""
        query = cls.select().join(ProviderProfile).where(
            cls.category == category.value,
            cls.is_active == True
        )
        if city:
            query = query.where(ProviderProfile.city == city)
        return query.order_by(cls.base_price.asc())

    @classmethod
    def get_by_provider(cls, provider_id: int):
        """Get services by provider."""
        return cls.select().where(
            cls.provider == provider_id
        ).order_by(cls.category.asc())

    def to_dict(self, include_provider: bool = False) -> dict:
        """Convert service to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "base_price": float(self.base_price) if self.base_price else 0.0,
            "price_unit": self.price_unit,
            "min_guests": self.min_guests,
            "max_guests": self.max_guests,
            "is_active": self.is_active,
            "lead_time_days": self.lead_time_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_provider:
            data["provider"] = {
                "id": self.provider.id,
                "business_name": self.provider.business_name,
                "rating": float(self.provider.rating) if self.provider.rating else 0.0,
                "city": self.provider.city,
            }

        return data
