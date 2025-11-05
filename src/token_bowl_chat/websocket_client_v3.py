"""WebSocket client for real-time Token Bowl Chat messaging using Centrifugo."""

import asyncio
import contextlib
import json
import logging
import os
import re
from collections.abc import Callable
from typing import Any

import httpx
import websockets
from websockets.asyncio.client import ClientConnection

from .exceptions import AuthenticationError, NetworkError, TimeoutError
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
        self._websocket: ClientConnection | None = None
        self._connection_info: dict[str, Any] | None = None
        self._connected = False
        self._connecting = False
        self._client_id: str | None = None
        self._subscriptions: set[str] = set()

        # Message tracking
        self._message_ids: set[str] = (
            set()
        )  # Track received message IDs to prevent duplicates
        self._command_id = 1  # Command ID counter for Centrifugo protocol

        # Tasks
        self._receive_task: asyncio.Task | None = None

    async def __aenter__(self) -> "TokenBowlWebSocket":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to the Centrifugo server."""
        if self._connecting or self._connected:
            logger.debug("Already connected or connecting")
            return

        if not self.api_key:
            raise AuthenticationError("API key is required for WebSocket connection")

        self._connecting = True
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

            # Connect to Centrifugo WebSocket
            ws_url = self._connection_info["url"]
            self._websocket = await websockets.connect(ws_url)
            # Note: Centrifugo uses standard WebSocket, no specific subprotocol needed

            # Send connection command with token
            connect_cmd = {
                "id": self._get_next_command_id(),
                "connect": {"token": self._connection_info["token"]},
            }
            await self._websocket.send(json.dumps(connect_cmd))

            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Note: In Centrifugo v4+, ping/pong is server-initiated
            # We don't need a client ping loop, just respond to server pings

            logger.info("Connecting to Centrifugo...")

        except Exception as e:
            self._connecting = False
            error_msg = f"Failed to connect to Centrifugo: {e}"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(NetworkError(error_msg))
            raise NetworkError(error_msg) from e

    def _get_next_command_id(self) -> int:
        """Get next command ID for Centrifugo protocol."""
        cmd_id = self._command_id
        self._command_id += 1
        return cmd_id

    async def _receive_loop(self) -> None:
        """Receive and process messages from Centrifugo."""
        if not self._websocket:
            return

        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message)
                    await self._handle_centrifugo_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    if self.on_error:
                        self.on_error(e)

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self._connected = False
            self._connecting = False
            # Don't clear subscriptions - we'll reuse them on reconnect
            if self.on_disconnect:
                self.on_disconnect()
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
            self._connected = False
            self._connecting = False
            # Don't clear subscriptions - we'll reuse them on reconnect
            if self.on_error:
                self.on_error(e)
            if self.on_disconnect:
                self.on_disconnect()

    async def _handle_centrifugo_message(self, data: dict[str, Any]) -> None:
        """Handle Centrifugo protocol messages."""

        # Handle empty message (ping from server) - must respond with pong
        if not data or len(data) == 0:
            # Server sent {} as ping, respond with {} as pong
            pong_response: dict[str, Any] = {}
            if self._websocket:
                await self._websocket.send(json.dumps(pong_response))
                logger.debug("Received ping (empty JSON), sent pong")
            return

        # Handle push messages
        elif "push" in data:
            push_data = data["push"]

            # Check if it's a publication
            if "pub" in push_data:
                pub = push_data["pub"]
                channel = push_data.get("channel", "")
                await self._handle_publication(pub, channel)
                return

        # Handle connect response
        elif "connect" in data:
            result = data["connect"]
            self._client_id = result.get("client")
            self._connected = True
            self._connecting = False

            # Subscribe to channels after successful connection
            await self._subscribe_to_channels()

            if self.on_connect:
                self.on_connect()
            logger.info(f"Connected to Centrifugo with client ID: {self._client_id}")

        # Handle subscribe response
        elif "subscribe" in data:
            channel = data["subscribe"].get("channel")
            if channel:
                self._subscriptions.add(channel)
                logger.info(f"Subscribed to channel: {channel}")

                # Handle any recovered messages
                if "publications" in data["subscribe"]:
                    for pub in data["subscribe"]["publications"]:
                        await self._handle_publication(pub, channel)

        # Handle unsubscribe
        elif "unsubscribe" in data:
            channel = data["unsubscribe"].get("channel")
            if channel and channel in self._subscriptions:
                self._subscriptions.discard(channel)
                logger.info(f"Unsubscribed from channel: {channel}")

        # Handle disconnect
        elif "disconnect" in data:
            disconnect_data = data["disconnect"]
            reason = disconnect_data.get("reason", "unknown")
            reconnect = disconnect_data.get("reconnect", True)
            logger.warning(
                f"Server requested disconnect: {reason}, reconnect: {reconnect}"
            )

            self._connected = False
            self._connecting = False

            if self.on_disconnect:
                self.on_disconnect()

        # Handle error
        elif "error" in data:
            error = data["error"]
            code = error.get("code")
            message = error.get("message", "Unknown error")

            # Error code 105 is "already subscribed" - this is expected on reconnect
            if code == 105:
                # Extract channel from the message if possible
                # Message format is usually "already subscribed on channel room:main"
                match = re.search(r"channel (\S+)", message)
                if match:
                    channel = match.group(1)
                    self._subscriptions.add(channel)
                    logger.debug(
                        f"Already subscribed to {channel} (expected on reconnect)"
                    )
                else:
                    logger.debug(
                        f"Already subscribed (expected on reconnect): {message}"
                    )
            else:
                logger.error(f"Centrifugo error {code}: {message}")
                if self.on_error:
                    self.on_error(Exception(f"Centrifugo error {code}: {message}"))

    async def _handle_publication(self, pub: dict[str, Any], channel: str) -> None:
        """Handle a publication (message or event) from Centrifugo."""
        data = pub.get("data")
        if not data:
            return

        try:
            # Check the type of event
            event_type = data.get("type")

            if event_type == "read_receipt":
                # Handle read receipt event
                if self.on_read_receipt:
                    message_id = data.get("message_id")
                    read_by = data.get("read_by")
                    if message_id and read_by:
                        self.on_read_receipt(message_id, read_by)
                        logger.debug(
                            f"Received read receipt: {message_id} read by {read_by}"
                        )

            elif event_type == "typing":
                # Handle typing indicator event
                if self.on_typing:
                    username = data.get("username")
                    to_username = data.get("to_username")
                    if username:
                        self.on_typing(username, to_username)
                        logger.debug(
                            f"Received typing indicator: {username} typing to {to_username or 'room'}"
                        )

            elif event_type == "unread_count":
                # Handle unread count update
                if self.on_unread_count:
                    count = UnreadCountResponse(
                        unread_room_messages=data.get("unread_room_messages", 0),
                        unread_direct_messages=data.get("unread_direct_messages", 0),
                        total_unread=data.get("total_unread", 0),
                    )
                    self.on_unread_count(count)
                    logger.debug(f"Received unread count: {count.total_unread} total")

            else:
                # Regular message (no type field or unknown type)
                # Check for duplicate messages
                message_id = data.get("id")
                if message_id and message_id in self._message_ids:
                    logger.debug(f"Ignoring duplicate message: {message_id}")
                    return

                if message_id:
                    self._message_ids.add(message_id)
                    # Keep only last 1000 message IDs to prevent memory growth
                    if len(self._message_ids) > 1000:
                        self._message_ids = set(list(self._message_ids)[-1000:])

                # Convert to MessageResponse and call handler
                if self.on_message and "from_username" in data:
                    message = MessageResponse(**data)
                    self.on_message(message)
                    logger.debug(
                        f"Processed message from {message.from_username} on channel {channel}"
                    )

        except Exception as e:
            logger.error(f"Error processing publication: {e}")

    async def _subscribe_to_channels(self) -> None:
        """Subscribe to authorized channels."""
        if not self._websocket or not self._connection_info:
            return

        # Subscribe to each channel from connection info
        for channel in self._connection_info.get("channels", []):
            if channel not in self._subscriptions:
                subscribe_cmd = {
                    "id": self._get_next_command_id(),
                    "subscribe": {
                        "channel": channel,
                        "recover": True,  # Enable message recovery
                    },
                }
                await self._websocket.send(json.dumps(subscribe_cmd))
                logger.debug(f"Attempting to subscribe to channel: {channel}")
            else:
                logger.debug(f"Already tracking subscription to channel: {channel}")

    async def disconnect(self, clear_state: bool = True) -> None:
        """Disconnect from the server.

        Args:
            clear_state: If True, clear all state (for full disconnect).
                        If False, preserve state for reconnection.
        """
        self._connected = False
        self._connecting = False

        # Cancel tasks
        if self._receive_task:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task

        # Close WebSocket
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

        # Only clear state if explicitly requested (full disconnect)
        if clear_state:
            self._subscriptions.clear()
            self._message_ids.clear()
            self._client_id = None
            self._command_id = 1

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
                logger.debug("Sent message via REST API")

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
                result = response.json()
                return (
                    {"count": result.get("marked_as_read", 0)}
                    if isinstance(result, dict)
                    else {"count": 0}
                )

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

    # Backward compatibility methods (these operations are not supported via WebSocket in Centrifugo)
    async def mark_message_read(self, message_id: str) -> None:
        """Mark a message as read (backward compatibility alias)."""
        await self.mark_as_read(message_id)

    async def mark_all_messages_read(self) -> None:
        """Mark all messages as read (backward compatibility alias)."""
        await self.mark_all_as_read()

    async def mark_room_messages_read(self) -> None:
        """Mark all room messages as read (not supported in Centrifugo mode)."""
        logger.debug(
            "mark_room_messages_read not supported via WebSocket in Centrifugo mode"
        )
        # Could implement via REST API if needed

    async def mark_direct_messages_read(self, from_username: str) -> None:
        """Mark all direct messages from a user as read (not supported in Centrifugo mode)."""
        _ = from_username  # Unused but kept for compatibility
        logger.debug(
            "mark_direct_messages_read not supported via WebSocket in Centrifugo mode"
        )
        # Could implement via REST API if needed

    async def send_typing_indicator(self, to_username: str | None = None) -> None:
        """Send typing indicator via REST API.

        Args:
            to_username: Optional recipient for DM typing indicator
        """
        if not self.api_key:
            raise AuthenticationError("API key is required")

        try:
            async with httpx.AsyncClient() as client:
                # Send to_username as query parameter since server expects it there
                url = f"{self.base_url}/typing"
                if to_username:
                    url = f"{url}?to_username={to_username}"

                response = await client.post(
                    url,
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.debug(f"Sent typing indicator to {to_username or 'room'}")

        except Exception as e:
            logger.error(f"Failed to send typing indicator: {e}")

    async def get_unread_count(self) -> None:
        """Request unread count update via REST API.

        The result will be delivered via the on_unread_count callback if the server
        publishes it to Centrifugo. Otherwise, you can use the REST API directly.
        """
        if not self.api_key:
            raise AuthenticationError("API key is required")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/unread",
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                # Call the callback directly with the REST response
                if self.on_unread_count:
                    count = UnreadCountResponse(**data)
                    self.on_unread_count(count)

                logger.debug(
                    f"Fetched unread count: {data.get('total_unread', 0)} total"
                )

        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected (backward compatibility)."""
        return self._connected
