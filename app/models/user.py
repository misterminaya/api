"""
User model for Vailoo API.
Supports multiple roles: organizer, provider, admin.
"""
from enum import Enum
from peewee import (
    CharField,
    BooleanField,
    TextField,
)
from app.core.security import verify_password, get_password_hash
from .base import BaseModel


class UserRole(str, Enum):
    """User role enumeration."""
    ORGANIZER = "organizer"
    PROVIDER = "provider"
    ADMIN = "admin"


class User(BaseModel):
    """User model for authentication and authorization."""

    email = CharField(max_length=255, unique=True, index=True)
    password_hash = CharField(max_length=255)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    phone = CharField(max_length=20, null=True)
    role = CharField(
        max_length=20,
        default=UserRole.ORGANIZER.value,
        choices=[(role.value, role.name) for role in UserRole]
    )
    is_active = BooleanField(default=True)
    is_verified = BooleanField(default=False)
    profile_image = CharField(max_length=500, null=True)
    bio = TextField(null=True)

    class Meta:
        table_name = 'users'

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password: str) -> None:
        """Hash and set user password."""
        self.password_hash = get_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify user password."""
        return verify_password(password, self.password_hash)

    @classmethod
    def get_by_email(cls, email: str):
        """Get user by email address."""
        try:
            return cls.get(cls.email == email.lower())
        except cls.DoesNotExist:
            return None

    @classmethod
    def authenticate(cls, email: str, password: str):
        """Authenticate user with email and password."""
        user = cls.get_by_email(email)
        if user and user.check_password(password):
            return user
        return None

    @classmethod
    def create_user(
        cls,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: UserRole = UserRole.ORGANIZER,
        **kwargs
    ):
        """Create a new user with hashed password."""
        user = cls(
            email=email.lower().strip(),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role=role.value if isinstance(role, UserRole) else role,
            **kwargs
        )
        user.set_password(password)
        user.save()
        return user

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary."""
        data = {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "profile_image": self.profile_image,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if not include_sensitive:
            data.pop("is_active", None)

        return data
