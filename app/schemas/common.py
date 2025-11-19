"""
Common schemas used across Vailoo API.
"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=10, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    success: bool = True
    data: List[T]
    pagination: dict = Field(
        ...,
        description="Pagination metadata"
    )

    @classmethod
    def create(
        cls,
        data: List[T],
        total: int,
        page: int,
        limit: int
    ):
        """Create paginated response with metadata."""
        total_pages = (total + limit - 1) // limit
        return cls(
            data=data,
            pagination={
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        )


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapper."""
    success: bool = True
    data: T


class MessageResponse(BaseModel):
    """Simple message response."""
    success: bool = True
    message: str


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str
    message: str
    details: Optional[List[dict]] = None


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    success: bool = False
    error: ErrorDetail
