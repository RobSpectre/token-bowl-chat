"""Token Bowl Chat Client - A chat client for Token Bowl."""

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
    HTTPValidationError,
    MessageResponse,
    MessageType,
    PaginatedMessagesResponse,
    PaginationMetadata,
    SendMessageRequest,
    UpdateLogoRequest,
    UserRegistration,
    UserRegistrationResponse,
)

__version__ = "0.1.0"
__all__ = [
    "__version__",
    # Clients
    "TokenBowlClient",
    "AsyncTokenBowlClient",
    # Models
    "MessageResponse",
    "MessageType",
    "PaginatedMessagesResponse",
    "PaginationMetadata",
    "SendMessageRequest",
    "UpdateLogoRequest",
    "UserRegistration",
    "UserRegistrationResponse",
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
