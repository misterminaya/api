"""
Database configuration and base model for Vailoo API.
"""
from datetime import datetime
from peewee import (
    MySQLDatabase,
    Model,
    DateTimeField,
    SQL
)
from app.core.config import settings

# Database connection
database = MySQLDatabase(
    settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    charset='utf8mb4'
)


class BaseModel(Model):
    """Base model with common fields and configuration."""

    created_at = DateTimeField(
        default=datetime.now,
        constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')]
    )
    updated_at = DateTimeField(
        default=datetime.now,
        constraints=[SQL('DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')]
    )

    class Meta:
        database = database

    def save(self, *args, **kwargs):
        """Override save to update updated_at timestamp."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
