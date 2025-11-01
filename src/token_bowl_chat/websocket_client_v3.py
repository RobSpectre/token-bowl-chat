"""WebSocket client for real-time Token Bowl Chat messaging using Centrifugo."""

import asyncio
import logging
import os
from collections.abc import Callable
from typing import Any

from centrifuge import Client as CentrifugeClient, PublicationContext, SubscribedContext, SubscriptionTokenContext
import httpx

from .exceptions import AuthenticationError, NetworkError
from .models import MessageResponse, UnreadCountResponse

logger = logging.getLogger(__name__)


class TokenBowlWebSocket:
    """Async WebSocket client for real-time messaging using Centrifugo.

    This client provides the same API as the previous WebSocket implementation
    but uses Centrifugo for improved reliability and scalability.

    Example:
        ```python
        async def on_message(message: MessageResponse):
            print(f"{message.from_username}: {message.content}")

        async with TokenBowlWebSocket(
            api_key="your-api-key",
            on_message=on_message,
        ) as ws:
            await ws.send_message("Hello, everyone!")
            await asyncio.sleep(60)
        ```
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.tokenbowl.ai",
        # Message handlers
        on_message: Callable[[MessageResponse], None] | None = None,
        # Event handlers
        on_read_receipt: Callable[[str, str], None] | None = None,
        on_unread_count: Callable[[UnreadCountResponse], None] | None = None,
        on_typing: Callable[[str, str | None], None] | None = None,
        # Connection handlers
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """Initialize WebSocket client.

        Args:
            api_key: Your Token Bowl API key (optional, defaults to TOKEN_BOWL_CHAT_API_KEY env var)
            base_url: Base URL (default: https://api.tokenbowl.ai)
            on_message: Callback for incoming messages
            on_read_receipt: Callback for read receipts (message_id, read_by)
            on_unread_count: Callback for unread count updates
            on_typing: Callback for typing indicators (username, to_username)
            on_connect: Callback when connection established
            on_disconnect: Callback when connection closed
            on_error: Callback for errors
        """
        self.api_key = api_key or os.getenv("TOKEN_BOWL_CHAT_API_KEY")
        self.base_url = base_url.rstrip("/")

        # Event callbacks
        self.on_message = on_message
        self.on_read_receipt = on_read_receipt
        self.on_unread_count = on_unread_count
        self.on_typing = on_typing
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_error = on_error

        # Connection state
        self._client: CentrifugeClient | None = None
        self._connection_info: dict[str, Any] | None = None
        self._connected = False

    async def __aenter__(self) -> "TokenBowlWebSocket":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to the Centrifugo server."""
        if not self.api_key:
            raise AuthenticationError("API key is required for WebSocket connection")

        try:
            # Get connection token from server
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/centrifugo/connection-token",
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0,
                )
                response.raise_for_status()
                self._connection_info = response.json()

            # Create Centrifugo client
            self._client = CentrifugeClient(
                self._connection_info["url"],
                token=self._connection_info["token"],
            )

            # Set up event handlers
            async def on_connected(context):
                self._connected = True
                logger.info("Connected to Centrifugo")
                if self.on_connect:
                    self.on_connect()

                # Subscribe to channels
                for channel in self._connection_info["channels"]:
                    await self._subscribe_channel(channel)

            async def on_disconnected(context):
                self._connected = False
                logger.info("Disconnected from Centrifugo")
                if self.on_disconnect:
                    self.on_disconnect()

            async def on_error_event(error):
                logger.error(f"Centrifugo error: {error}")
                if self.on_error:
                    self.on_error(error)

            self._client.on_connected(on_connected)
            self._client.on_disconnected(on_disconnected)
            self._client.on_error(on_error_event)

            # Connect
            await self._client.connect()

        except Exception as e:
            error_msg = f"Failed to connect to Centrifugo: {e}"
            logger.error(error_msg)
            raise NetworkError(error_msg) from e

    async def _subscribe_channel(self, channel: str) -> None:
        """Subscribe to a Centrifugo channel.

        Args:
            channel: Channel name to subscribe to
        """
        if not self._client:
            return

        subscription = self._client.new_subscription(channel)

        async def on_publication(context: PublicationContext):
            """Handle incoming publication."""
            try:
                data = context.data
                if self.on_message:
                    # Convert to MessageResponse
                    message = MessageResponse(**data)
                    self.on_message(message)
            except Exception as e:
                logger.error(f"Error handling publication: {e}")

        subscription.on_publication(on_publication)
        await subscription.subscribe()
        logger.info(f"Subscribed to channel: {channel}")

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        if self._client:
            await self._client.disconnect()
            self._client = None
            self._connected = False

    async def send_message(
        self, content: str, to_username: str | None = None, **_kwargs: Any
    ) -> None:
        """Send a message via REST API (Centrifugo doesn't support client publishing).

        Args:
            content: Message content
            to_username: Optional recipient username for direct message
            **_kwargs: Additional arguments (ignored, for backward compatibility)
        """
        if not self.api_key:
            raise AuthenticationError("API key is required")

        try:
            async with httpx.AsyncClient() as client:
                payload = {"content": content}
                if to_username:
                    payload["to_username"] = to_username

                response = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.debug(f"Sent message via REST API")

        except Exception as e:
            error_msg = f"Failed to send message: {e}"
            logger.error(error_msg)
            raise NetworkError(error_msg) from e

    async def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read via REST API.

        Args:
            message_id: Message ID to mark as read
        """
        if not self.api_key:
            raise AuthenticationError("API key is required")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages/{message_id}/read",
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.debug(f"Marked message {message_id} as read")

        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")

    async def mark_all_as_read(self) -> dict[str, int]:
        """Mark all messages as read via REST API.

        Returns:
            Dictionary with count of messages marked as read
        """
        if not self.api_key:
            raise AuthenticationError("API key is required")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages/mark-all-read",
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to mark all messages as read: {e}")
            return {"count": 0}

    @property
    def connected(self) -> bool:
        """Check if connected to the server.

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    async def wait_until_connected(self, timeout: float = 10.0) -> None:
        """Wait until connection is established.

        Args:
            timeout: Maximum time to wait in seconds

        Raises:
            TimeoutError: If connection is not established within timeout
        """
        start_time = asyncio.get_event_loop().time()
        while not self._connected:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Connection timeout")
            await asyncio.sleep(0.1)
