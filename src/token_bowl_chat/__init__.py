"""Token Bowl Chat Client - A chat client for Token Bowl."""

from .agent import TokenBowlAgent
from .async_client import AsyncTokenBowlClient
from .client import TokenBowlClient
from .exceptions import (
    AuthenticationError,
    ConflictError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    TokenBowlError,
    ValidationError,
)
from .models import (
    AdminMessageUpdate,
    AdminUpdateUserRequest,
    HTTPValidationError,
    MessageResponse,
    MessageType,
    PaginatedMessagesResponse,
    PaginationMetadata,
    PublicUserProfile,
    Role,
    SendMessageRequest,
    StytchAuthenticateRequest,
    StytchAuthenticateResponse,
    StytchLoginRequest,
    StytchLoginResponse,
    UnreadCountResponse,
    UpdateLogoRequest,
    UpdateUsernameRequest,
    UpdateWebhookRequest,
    UserProfileResponse,
    UserRegistration,
    UserRegistrationResponse,
)
from .websocket_client import TokenBowlWebSocket

__version__ = "1.1.9"
__all__ = [
    "__version__",
    # Clients
    "TokenBowlClient",
    "AsyncTokenBowlClient",
    "TokenBowlWebSocket",
    "TokenBowlAgent",
    # Models
    "MessageResponse",
    "MessageType",
    "Role",
    "PaginatedMessagesResponse",
    "PaginationMetadata",
    "SendMessageRequest",
    "UpdateLogoRequest",
    "UpdateUsernameRequest",
    "UpdateWebhookRequest",
    "UserRegistration",
    "UserRegistrationResponse",
    "UserProfileResponse",
    "PublicUserProfile",
    "UnreadCountResponse",
    "StytchLoginRequest",
    "StytchLoginResponse",
    "StytchAuthenticateRequest",
    "StytchAuthenticateResponse",
    "AdminUpdateUserRequest",
    "AdminMessageUpdate",
    "HTTPValidationError",
    # Exceptions
    "TokenBowlError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "TimeoutError",
]
