"""Asynchronous client for Token Bowl Chat Server."""

from typing import Optional
from uuid import uuid4

import httpx

from .exceptions import (
    AuthenticationError,
    ConflictError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .models import (
    MessageResponse,
    PaginatedMessagesResponse,
    SendMessageRequest,
    UserRegistration,
    UserRegistrationResponse,
)


class AsyncTokenBowlClient:
    """Asynchronous client for Token Bowl Chat Server.

    This client provides a Pythonic async interface to the Token Bowl Chat Server
    API with full type hints and error handling.

    Example:
        >>> async with AsyncTokenBowlClient(base_url="http://localhost:8000") as client:
        ...     response = await client.register()
        ...     client.api_key = response.api_key
        ...     await client.send_message("Hello, world!")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the async Token Bowl client.

        Args:
            base_url: Base URL of the Token Bowl server
            api_key: API key for authentication (can be set later)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "AsyncTokenBowlClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers including authentication if available.

        Returns:
            Dictionary of HTTP headers

        Raises:
            AuthenticationError: If API key is required but not set
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _handle_response(self, response: httpx.Response) -> None:
        """Handle HTTP response errors.

        Args:
            response: HTTP response object

        Raises:
            AuthenticationError: For 401 errors
            NotFoundError: For 404 errors
            ConflictError: For 409 errors
            ValidationError: For 422 errors
            RateLimitError: For 429 errors
            ServerError: For 5xx errors
        """
        if response.status_code < 400:
            return

        try:
            error_data = response.json()
            error_message = str(error_data)
        except Exception:
            error_message = response.text or f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise AuthenticationError(error_message, response)
        elif response.status_code == 404:
            raise NotFoundError(error_message, response)
        elif response.status_code == 409:
            raise ConflictError(error_message, response)
        elif response.status_code == 422:
            raise ValidationError(error_message, response)
        elif response.status_code == 429:
            raise RateLimitError(error_message, response)
        elif response.status_code >= 500:
            raise ServerError(error_message, response)
        else:
            response.raise_for_status()

    async def _request(
        self,
        method: str,
        path: str,
        requires_auth: bool = False,
        **kwargs: object,
    ) -> httpx.Response:
        """Make an async HTTP request.

        Args:
            method: HTTP method
            path: API endpoint path
            requires_auth: Whether this endpoint requires authentication
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response object

        Raises:
            AuthenticationError: If auth is required but API key not set
            NetworkError: For network connectivity issues
            TimeoutError: For request timeouts
        """
        url = f"{self.base_url}{path}"
        headers = self._get_headers()

        if requires_auth and not self.api_key:
            raise AuthenticationError("API key required for this operation")

        try:
            response = await self._client.request(
                method, url, headers=headers, **kwargs
            )
            self._handle_response(response)
            return response
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.NetworkError as e:
            raise NetworkError(f"Network error: {e}") from e

    async def register(
        self,
        webhook_url: Optional[str] = None,
    ) -> UserRegistrationResponse:
        """Register a new user and get an API key.

        A unique username is automatically generated for you.

        Args:
            webhook_url: Optional webhook URL for notifications

        Returns:
            User registration response with API key

        Raises:
            ValidationError: If input validation fails
        """
        # Auto-generate a unique username
        username = f"user_{uuid4().hex[:12]}"
        registration = UserRegistration(username=username, webhook_url=webhook_url)
        response = await self._request(
            "POST",
            "/register",
            json=registration.model_dump(exclude_none=True),
        )
        return UserRegistrationResponse.model_validate(response.json())

    async def send_message(
        self,
        content: str,
        to_username: Optional[str] = None,
    ) -> MessageResponse:
        """Send a message to the room or as a direct message.

        Args:
            content: Message content (1-10000 characters)
            to_username: Optional recipient username for direct messages

        Returns:
            Created message response

        Raises:
            AuthenticationError: If not authenticated
            NotFoundError: If recipient doesn't exist
            ValidationError: If input validation fails
        """
        message_request = SendMessageRequest(content=content, to_username=to_username)
        response = await self._request(
            "POST",
            "/messages",
            requires_auth=True,
            json=message_request.model_dump(exclude_none=True),
        )
        return MessageResponse.model_validate(response.json())

    async def get_messages(
        self,
        limit: int = 50,
        offset: int = 0,
        since: Optional[str] = None,
    ) -> PaginatedMessagesResponse:
        """Get recent room messages with pagination.

        Args:
            limit: Maximum number of messages to return (default: 50)
            offset: Number of messages to skip (default: 0)
            since: ISO timestamp to get messages after

        Returns:
            Paginated list of messages with metadata

        Raises:
            AuthenticationError: If not authenticated
            ValidationError: If parameters are invalid
        """
        params = {"limit": limit, "offset": offset}
        if since is not None:
            params["since"] = since

        response = await self._request(
            "GET",
            "/messages",
            requires_auth=True,
            params=params,
        )
        return PaginatedMessagesResponse.model_validate(response.json())

    async def get_direct_messages(
        self,
        limit: int = 50,
        offset: int = 0,
        since: Optional[str] = None,
    ) -> PaginatedMessagesResponse:
        """Get direct messages for the current user with pagination.

        Args:
            limit: Maximum number of messages to return (default: 50)
            offset: Number of messages to skip (default: 0)
            since: ISO timestamp to get messages after

        Returns:
            Paginated list of direct messages with metadata

        Raises:
            AuthenticationError: If not authenticated
            ValidationError: If parameters are invalid
        """
        params = {"limit": limit, "offset": offset}
        if since is not None:
            params["since"] = since

        response = await self._request(
            "GET",
            "/messages/direct",
            requires_auth=True,
            params=params,
        )
        return PaginatedMessagesResponse.model_validate(response.json())

    async def get_users(self) -> list[str]:
        """Get list of all registered usernames.

        Returns:
            List of usernames

        Raises:
            AuthenticationError: If not authenticated
        """
        response = await self._request("GET", "/users", requires_auth=True)
        return response.json()

    async def get_online_users(self) -> list[str]:
        """Get list of users currently connected via WebSocket.

        Returns:
            List of online usernames

        Raises:
            AuthenticationError: If not authenticated
        """
        response = await self._request("GET", "/users/online", requires_auth=True)
        return response.json()

    async def health_check(self) -> dict[str, str]:
        """Check server health status.

        Returns:
            Health status dictionary
        """
        response = await self._request("GET", "/health")
        return response.json()
