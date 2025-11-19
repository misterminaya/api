"""
User schemas for Vailoo API.
"""
import re
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = Field(default=UserRole.ORGANIZER)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, v):
        return v.lower().strip()

    @field_validator('first_name', 'last_name')
    @classmethod
    def capitalize_name(cls, v):
        return v.strip().title()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        # Remove spaces and dashes for validation
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        from app.core.security import validate_password_strength
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str

    @field_validator('email')
    @classmethod
    def normalize_email(cls, v):
        return v.lower().strip()


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    profile_image: Optional[str] = Field(None, max_length=500)

    @field_validator('first_name', 'last_name')
    @classmethod
    def capitalize_name(cls, v):
        if v is None:
            return v
        return v.strip().title()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str]
    role: str
    is_verified: bool
    profile_image: Optional[str]
    bio: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for list of users response."""
    success: bool = True
    data: List[UserResponse]
    pagination: dict
