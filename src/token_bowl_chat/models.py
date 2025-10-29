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


class Role(str, Enum):
    """User roles for authorization."""

    ADMIN = "admin"  # Full CRUD access to all resources
    MEMBER = "member"  # Default role - can send/receive messages, update own profile
    VIEWER = "viewer"  # Read-only access - cannot send DMs or update profile
    BOT = "bot"  # Automated agents - can send room messages only


class UserRegistration(BaseModel):
    """Request model for user registration."""

    username: str = Field(..., min_length=1, max_length=50)
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)
    logo: str | None = None
    role: Role | None = None
    viewer: bool = False
    admin: bool = False
    bot: bool = False
    emoji: str | None = None

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        """Validate webhook URL format."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("webhook_url must be a valid HTTP(S) URL")
        return v


class UserRegistrationResponse(BaseModel):
    """Response model for user registration."""

    id: str  # UUID as string
    username: str
    api_key: str
    role: Role
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)
    logo: str | None = None
    viewer: bool = False
    admin: bool = False
    bot: bool = False
    emoji: str | None = None


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""

    content: str = Field(..., min_length=1, max_length=10000)
    to_username: str | None = Field(None, min_length=1, max_length=50)


class MessageResponse(BaseModel):
    """Response model for messages."""

    id: str
    from_user_id: str  # User UUID as string
    from_username: str
    from_user_logo: str | None = None
    from_user_emoji: str | None = None
    from_user_bot: bool = False
    to_user_id: str | None = None  # User UUID as string
    to_username: str | None = None
    content: str
    message_type: MessageType
    description: str = ""
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


class UpdateWebhookRequest(BaseModel):
    """Request model for updating user webhook URL."""

    webhook_url: str | None = Field(None, min_length=1, max_length=2083)

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        """Validate webhook URL format."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("webhook_url must be a valid HTTP(S) URL")
        return v


class UpdateUsernameRequest(BaseModel):
    """Request model for updating username."""

    username: str = Field(..., min_length=1, max_length=50)


class UnreadCountResponse(BaseModel):
    """Response model for unread message counts."""

    unread_room_messages: int
    unread_direct_messages: int
    total_unread: int


class UserProfileResponse(BaseModel):
    """Response model for user profile."""

    id: str  # UUID as string
    username: str
    role: Role
    email: str | None = None
    api_key: str
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)
    logo: str | None = None
    viewer: bool = False
    admin: bool = False
    bot: bool = False
    emoji: str | None = None
    created_at: str


class PublicUserProfile(BaseModel):
    """Public user profile (no sensitive information)."""

    id: str  # UUID as string
    username: str
    role: Role
    logo: str | None = None
    emoji: str | None = None
    bot: bool = False
    viewer: bool = False


class StytchLoginRequest(BaseModel):
    """Request model for Stytch magic link login/signup."""

    email: str = Field(..., min_length=3, max_length=255)
    username: str | None = Field(None, min_length=1, max_length=50)


class StytchLoginResponse(BaseModel):
    """Response model for Stytch magic link send."""

    message: str
    email: str


class StytchAuthenticateRequest(BaseModel):
    """Request model for Stytch magic link authentication."""

    token: str = Field(..., min_length=1)


class StytchAuthenticateResponse(BaseModel):
    """Response model for Stytch authentication."""

    username: str
    session_token: str
    api_key: str


class AdminUpdateUserRequest(BaseModel):
    """Admin request model for updating any user's profile."""

    username: str | None = None
    email: str | None = None
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)
    logo: str | None = None
    viewer: bool | None = None
    admin: bool | None = None
    bot: bool | None = None
    emoji: str | None = None

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        """Validate webhook URL format."""
        if v is not None and v != "" and not v.startswith(("http://", "https://")):
            raise ValueError("webhook_url must be a valid HTTP(S) URL")
        return v


class AdminMessageUpdate(BaseModel):
    """Admin request model for updating message content."""

    content: str = Field(..., min_length=1, max_length=10000)


class CreateBotRequest(BaseModel):
    """Request model for creating a bot."""

    username: str = Field(..., min_length=1, max_length=50)
    emoji: str | None = None
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        """Validate webhook URL format."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("webhook_url must be a valid HTTP(S) URL")
        return v


class CreateBotResponse(BaseModel):
    """Response model for bot creation."""

    id: str  # UUID as string
    username: str
    api_key: str
    created_by_id: str  # UUID as string
    created_by: str  # Creator username
    emoji: str | None = None
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)


class BotProfileResponse(BaseModel):
    """Response model for bot profile."""

    id: str  # UUID as string
    username: str
    api_key: str
    created_by_id: str  # UUID as string
    created_by: str  # Creator username
    emoji: str | None = None
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)
    created_at: str


class UpdateBotRequest(BaseModel):
    """Request model for updating a bot."""

    emoji: str | None = None
    webhook_url: str | None = Field(None, min_length=1, max_length=2083)

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        """Validate webhook URL format."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("webhook_url must be a valid HTTP(S) URL")
        return v


class AssignRoleRequest(BaseModel):
    """Request model for assigning a role to a user (admin only)."""

    role: Role


class AssignRoleResponse(BaseModel):
    """Response model for role assignment."""

    username: str
    role: Role
    message: str


class InviteUserRequest(BaseModel):
    """Request to invite a user by email."""

    email: str = Field(..., description="Email address to invite")
    role: Role = Field(
        default=Role.MEMBER, description="Role to assign to the invited user"
    )
    signup_url: str = Field(
        ...,
        description="URL to redirect to after clicking magic link (e.g., https://app.example.com/signup)",
    )


class InviteUserResponse(BaseModel):
    """Response after sending invitation."""

    email: str
    role: Role
    message: str


# Conversation models


class CreateConversationRequest(BaseModel):
    """Request model for creating a conversation."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    message_ids: list[str] = Field(default_factory=list)


class UpdateConversationRequest(BaseModel):
    """Request model for updating a conversation."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    message_ids: list[str] | None = None


class ConversationResponse(BaseModel):
    """Response model for conversations."""

    id: str
    title: str | None = None
    description: str | None = None
    message_ids: list[str]
    created_by_username: str
    created_at: str


class PaginatedConversationsResponse(BaseModel):
    """Paginated response for conversations."""

    conversations: list[ConversationResponse]
    total: int
    limit: int
    offset: int
