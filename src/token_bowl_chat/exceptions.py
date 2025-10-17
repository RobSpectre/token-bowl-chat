"""Exceptions for Token Bowl Chat Client."""

from typing import Any


class TokenBowlError(Exception):
    """Base exception for all Token Bowl Chat Client errors."""

    def __init__(self, message: str, response: Any | None = None) -> None:
        """Initialize the error.

        Args:
            message: Error message
            response: Optional response object for context
        """
        self.message = message
        self.response = response
        super().__init__(message)


class AuthenticationError(TokenBowlError):
    """Raised when authentication fails (invalid or missing API key)."""


class ValidationError(TokenBowlError):
    """Raised when request validation fails."""


class NotFoundError(TokenBowlError):
    """Raised when a requested resource is not found."""


class ConflictError(TokenBowlError):
    """Raised when there's a conflict (e.g., username already exists)."""


class RateLimitError(TokenBowlError):
    """Raised when rate limit is exceeded."""


class ServerError(TokenBowlError):
    """Raised when the server returns a 5xx error."""


class NetworkError(TokenBowlError):
    """Raised when there's a network connectivity issue."""


class TimeoutError(TokenBowlError):
    """Raised when a request times out."""
