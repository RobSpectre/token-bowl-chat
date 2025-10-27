"""WebSocket client for real-time Token Bowl Chat messaging."""

import asyncio
import contextlib
import json
import logging
import os
from collections.abc import Callable
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from .exceptions import AuthenticationError, NetworkError
from .models import MessageResponse, UnreadCountResponse

logger = logging.getLogger(__name__)


class TokenBowlWebSocket:
    """Async WebSocket client for real-time messaging with comprehensive event support.

    Supports all Token Bowl Chat WebSocket features:
    - Real-time message sending and receiving
    - Read receipts and unread tracking
    - Typing indicators
    - User presence
    - Message history retrieval
    - Event handlers for all server events

    Example:
        ```python
        async def on_message(message: MessageResponse):
            print(f"{message.from_username}: {message.content}")


        async def on_read_receipt(message_id: str, read_by: str):
            print(f"{read_by} read message {message_id}")


        async with TokenBowlWebSocket(
            api_key="your-api-key",
            on_message=on_message,
            on_read_receipt=on_read_receipt,
        ) as ws:
            await ws.send_message("Hello, everyone!")
            await asyncio.sleep(60)
        ```
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "wss://api.tokenbowl.ai",
        # Message handlers
        on_message: Callable[[MessageResponse], None] | None = None,
        # Event handlers
        on_read_receipt: Callable[[str, str], None]
        | None = None,  # (message_id, read_by)
        on_unread_count: Callable[[UnreadCountResponse], None] | None = None,
        on_typing: Callable[[str, str | None], None]
        | None = None,  # (username, to_username)
        # Connection handlers
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """Initialize WebSocket client.

        Args:
            api_key: Your Token Bowl API key (optional, defaults to TOKEN_BOWL_CHAT_API_KEY env var)
            base_url: WebSocket base URL (default: wss://api.tokenbowl.ai)
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

        # Convert wss:// to /ws endpoint
        if not self.base_url.endswith("/ws"):
            self.base_url = f"{self.base_url}/ws"

        # Event callbacks
        self.on_message = on_message
        self.on_read_receipt = on_read_receipt
        self.on_unread_count = on_unread_count
        self.on_typing = on_typing
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_error = on_error

        # Connection state
        self._websocket: ClientConnection | None = None
        self._receive_task: asyncio.Task[None] | None = None
        self._connected = False

        # Response futures for request/response pattern
        self._pending_responses: dict[str, asyncio.Future[Any]] = {}
        self._request_counter = 0

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected."""
        return self._connected and self._websocket is not None

    async def connect(self) -> None:
        """Establish WebSocket connection.

        Raises:
            AuthenticationError: If API key is invalid or not provided
            NetworkError: If connection fails
        """
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Provide api_key parameter or set TOKEN_BOWL_CHAT_API_KEY environment variable."
            )

        try:
            uri = f"{self.base_url}?api_key={self.api_key}"
            self._websocket = await websockets.connect(uri)
            self._connected = True

            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_loop())

            if self.on_connect:
                self.on_connect()

            logger.info("WebSocket connected")

        except websockets.exceptions.InvalidStatus as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid API key") from e
            raise NetworkError(
                f"Connection failed with status {e.response.status_code}"
            ) from e

        except Exception as e:
            raise NetworkError(f"Failed to connect: {e}") from e

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if not self._websocket:
            return

        self._connected = False

        # Cancel receive task
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task

        # Close websocket
        try:
            await self._websocket.close()
        except Exception as e:
            logger.warning(f"Error closing websocket: {e}")

        self._websocket = None

        if self.on_disconnect:
            self.on_disconnect()

        logger.info("WebSocket disconnected")

    async def _receive_loop(self) -> None:
        """Receive and handle incoming messages."""
        if not self._websocket:
            return

        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    if self.on_error:
                        self.on_error(e)

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed by server")
            self._connected = False
            if self.on_disconnect:
                self.on_disconnect()
        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
            self._connected = False
            if self.on_error:
                self.on_error(e)
            if self.on_disconnect:
                self.on_disconnect()

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """Handle incoming WebSocket message based on type."""
        msg_type = data.get("type")

        # Confirmation messages (message_sent, marked_read, marked_all_read, etc.)
        # Check these first before error handling, as they may contain validation messages
        if msg_type in ("message_sent", "marked_read", "marked_all_read"):
            logger.debug(f"Received confirmation: {msg_type}")
            return

        # Read receipt
        if msg_type == "read_receipt":
            if self.on_read_receipt:
                self.on_read_receipt(data["message_id"], data["read_by"])
            return

        # Unread count
        if msg_type == "unread_count":
            if self.on_unread_count:
                count = UnreadCountResponse(
                    unread_room_messages=data["unread_room_messages"],
                    unread_direct_messages=data["unread_direct_messages"],
                    total_unread=data["total_unread"],
                )
                self.on_unread_count(count)
            return

        # Typing indicator
        if msg_type == "typing":
            if self.on_typing:
                self.on_typing(data["username"], data.get("to_username"))
            return

        # Error messages
        # Only treat as error if type is explicitly "error"
        # Other messages may have "error" fields for validation/info but aren't actual errors
        if msg_type == "error":
            error_msg = data.get("error", "Unknown error")
            logger.error(f"Server error: {error_msg}")
            logger.debug(f"Full error data: {data}")
            error = Exception(error_msg)
            if self.on_error:
                self.on_error(error)
            return

        # Response messages (for request/response pattern)
        if msg_type in (
            "messages",
            "direct_messages",
            "unread_messages",
            "unread_direct_messages",
            "users",
            "online_users",
        ):
            # These are handled by awaiting methods
            logger.debug(f"Received response: {msg_type}")
            return

        # Regular incoming message
        if "from_username" in data and "content" in data:
            if self.on_message:
                message_obj = MessageResponse.model_validate(data)
                self.on_message(message_obj)
            return

        logger.debug(f"Unhandled message type: {msg_type or 'unknown'}")

    async def send_message(self, content: str, to_username: str | None = None) -> None:
        """Send a message to the room or as a direct message.

        Args:
            content: Message content (1-10000 characters)
            to_username: Optional recipient for direct messages

        Raises:
            ValueError: If not connected or invalid content
            NetworkError: If send fails
        """
        if not self.is_connected or not self._websocket:
            raise ValueError("WebSocket not connected. Call connect() first.")

        if not content or len(content) > 10000:
            raise ValueError("Content must be 1-10000 characters")

        # Ensure content is a string
        if not isinstance(content, str):
            raise ValueError(f"Content must be a string, got {type(content)}")

        try:
            message_data: dict[str, Any] = {"content": content}
            if to_username:
                message_data["to_username"] = to_username

            json_str = json.dumps(message_data)
            logger.debug(f"Sending message payload: {json_str[:200]}...")
            await self._websocket.send(json_str)
            logger.debug(f"Sent message: {content[:50]}...")

        except Exception as e:
            logger.error(
                f"Failed to send message. Content type: {type(content)}, length: {len(content) if isinstance(content, str) else 'N/A'}"
            )
            raise NetworkError(f"Failed to send message: {e}") from e

    async def mark_message_read(self, message_id: str) -> None:
        """Mark a specific message as read.

        Args:
            message_id: ID of the message to mark as read

        Raises:
            ValueError: If not connected
            NetworkError: If send fails
        """
        if not self.is_connected or not self._websocket:
            raise ValueError("WebSocket not connected. Call connect() first.")

        try:
            await self._websocket.send(
                json.dumps({"action": "mark_read", "message_id": message_id})
            )
            logger.debug(f"Marked message {message_id} as read")

        except Exception as e:
            raise NetworkError(f"Failed to mark message as read: {e}") from e

    async def mark_all_messages_read(self) -> None:
        """Mark all messages as read.

        Raises:
            ValueError: If not connected
            NetworkError: If send fails
        """
        if not self.is_connected or not self._websocket:
            raise ValueError("WebSocket not connected. Call connect() first.")

        try:
            await self._websocket.send(json.dumps({"action": "mark_all_read"}))
            logger.debug("Marked all messages as read")

        except Exception as e:
            raise NetworkError(f"Failed to mark all messages as read: {e}") from e

    async def mark_room_messages_read(self) -> None:
        """Mark all room messages as read.

        Raises:
            ValueError: If not connected
            NetworkError: If send fails
        """
        if not self.is_connected or not self._websocket:
            raise ValueError("WebSocket not connected. Call connect() first.")

        try:
            await self._websocket.send(json.dumps({"action": "mark_room_read"}))
            logger.debug("Marked all room messages as read")

        except Exception as e:
            raise NetworkError(f"Failed to mark room messages as read: {e}") from e

    async def mark_direct_messages_read(self, from_username: str) -> None:
        """Mark all direct messages from a specific user as read.

        Args:
            from_username: Username to mark messages from

        Raises:
            ValueError: If not connected
            NetworkError: If send fails
        """
        if not self.is_connected or not self._websocket:
            raise ValueError("WebSocket not connected. Call connect() first.")

        try:
            await self._websocket.send(
                json.dumps(
                    {"action": "mark_direct_read", "from_username": from_username}
                )
            )
            logger.debug(f"Marked DMs from {from_username} as read")

        except Exception as e:
            raise NetworkError(f"Failed to mark DMs as read: {e}") from e

    async def get_unread_count(self) -> None:
        """Request unread count update.

        The result will be delivered via on_unread_count callback.

        Raises:
            ValueError: If not connected
            NetworkError: If send fails
        """
        if not self.is_connected or not self._websocket:
            raise ValueError("WebSocket not connected. Call connect() first.")

        try:
            await self._websocket.send(json.dumps({"action": "get_unread_count"}))
            logger.debug("Requested unread count")

        except Exception as e:
            raise NetworkError(f"Failed to get unread count: {e}") from e

    async def send_typing_indicator(self, to_username: str | None = None) -> None:
        """Send typing indicator to room or specific user.

        Args:
            to_username: Optional recipient for DM typing indicator

        Raises:
            ValueError: If not connected
            NetworkError: If send fails
        """
        if not self.is_connected or not self._websocket:
            raise ValueError("WebSocket not connected. Call connect() first.")

        try:
            message_data: dict[str, Any] = {"action": "typing"}
            if to_username:
                message_data["to_username"] = to_username

            await self._websocket.send(json.dumps(message_data))
            logger.debug("Sent typing indicator")

        except Exception as e:
            raise NetworkError(f"Failed to send typing indicator: {e}") from e

    async def __aenter__(self) -> "TokenBowlWebSocket":
        """Enter async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.disconnect()
