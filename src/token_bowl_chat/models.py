"""Data models for Token Bowl Chat Client.

This module contains all the Pydantic models that correspond to the
OpenAPI schema definitions for the Token Bowl Chat Server API.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class MessageType(str, Enum):
    """Type of message."""

    ROOM = "room"
    DIRECT = "direct"
    SYSTEM = "system"


class UserRegistration(BaseModel):
    """Request model for user registration."""

    username: str = Field(..., min_length=1, max_length=50)
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)
    logo: str | None = None

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        """Validate webhook URL format."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("webhook_url must be a valid HTTP(S) URL")
        return v


class UserRegistrationResponse(BaseModel):
    """Response model for user registration."""

    username: str
    api_key: str
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)
    logo: str | None = None


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""

    content: str = Field(..., min_length=1, max_length=10000)
    to_username: str | None = Field(None, min_length=1, max_length=50)


class MessageResponse(BaseModel):
    """Response model for messages."""

    id: str
    from_username: str
    to_username: str | None
    content: str
    message_type: MessageType
    timestamp: str

    @property
    def timestamp_dt(self) -> datetime:
        """Parse timestamp string to datetime object."""
        return datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))


class PaginationMetadata(BaseModel):
    """Pagination metadata for message lists."""

    total: int
    offset: int
    limit: int
    has_more: bool


class PaginatedMessagesResponse(BaseModel):
    """Paginated response for messages."""

    messages: list[MessageResponse]
    pagination: PaginationMetadata


class ValidationError(BaseModel):
    """Validation error details."""

    loc: list[str | int]
    msg: str
    type: str


class HTTPValidationError(BaseModel):
    """HTTP validation error response."""

    detail: list[ValidationError]


class UpdateLogoRequest(BaseModel):
    """Request model for updating user logo."""

    logo: str | None = None
