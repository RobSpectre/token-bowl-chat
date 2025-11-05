"""Tests for Centrifugo WebSocket client."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.exceptions import AuthenticationError, NetworkError
from token_bowl_chat.models import MessageResponse


class AsyncIteratorMock:
    """Mock for async iteration over WebSocket messages."""

    def __init__(self, messages):
        self.messages = messages
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index < len(self.messages):
            msg = self.messages[self.index]
            self.index += 1
            return msg
        raise StopAsyncIteration


@pytest.fixture
def mock_websocket():
    """Create a mock websocket connection."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    ws.__aiter__ = MagicMock(return_value=AsyncIteratorMock([]))
    return ws


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response for connection token."""
    response = MagicMock()
    response.json.return_value = {
        "url": "ws://localhost:8001/connection/websocket",
        "token": "test-jwt-token",
        "channels": ["room:main", "user:testuser"],
        "user": "testuser",
    }
    response.raise_for_status = MagicMock()
    return response


@pytest.mark.asyncio
async def test_connect_success(mock_websocket, mock_httpx_response):
    """Test successful WebSocket connection to Centrifugo."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Mock the receive loop to simulate connect response
        connect_response = json.dumps({"connect": {"client": "test-client-id"}})
        mock_websocket.__aiter__ = MagicMock(
            return_value=AsyncIteratorMock([connect_response])
        )

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(api_key="test-key")

            await client.connect()

            # Give time for async tasks to process
            await asyncio.sleep(0.1)

            assert client.connected
            assert client._websocket == mock_websocket

            # Verify connection command was sent
            mock_websocket.send.assert_called()
            # First call should be the connect command
            first_call = mock_websocket.send.call_args_list[0]
            sent_data = json.loads(first_call[0][0])
            assert "connect" in sent_data
            assert sent_data["connect"]["token"] == "test-jwt-token"


@pytest.mark.asyncio
async def test_connect_no_api_key():
    """Test WebSocket connection without API key."""
    client = TokenBowlWebSocket()
    with pytest.raises(AuthenticationError, match="API key is required"):
        await client.connect()


@pytest.mark.asyncio
async def test_connect_token_endpoint_error():
    """Test WebSocket connection when token endpoint fails."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client

        client = TokenBowlWebSocket(api_key="test-key")
        with pytest.raises(NetworkError, match="Failed to connect to Centrifugo"):
            await client.connect()


@pytest.mark.asyncio
async def test_send_message_via_rest(mock_httpx_response):
    """Test sending message via REST API."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        # Mock response for send message
        send_response = MagicMock()
        send_response.raise_for_status = MagicMock()
        mock_client.post.return_value = send_response

        mock_client_class.return_value = mock_client

        client = TokenBowlWebSocket(api_key="test-key")
        await client.send_message("Hello, world!")

        # Verify REST API call was made
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0].endswith("/messages")
        assert call_args[1]["json"]["content"] == "Hello, world!"
        assert "X-API-Key" in call_args[1]["headers"]


@pytest.mark.asyncio
async def test_send_direct_message_via_rest(mock_httpx_response):
    """Test sending direct message via REST API."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        # Mock response for send message
        send_response = MagicMock()
        send_response.raise_for_status = MagicMock()
        mock_client.post.return_value = send_response

        mock_client_class.return_value = mock_client

        client = TokenBowlWebSocket(api_key="test-key")
        await client.send_message("Hello!", to_username="alice")

        # Verify REST API call was made
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["content"] == "Hello!"
        assert call_args[1]["json"]["to_username"] == "alice"


@pytest.mark.asyncio
async def test_handle_incoming_message(mock_websocket, mock_httpx_response):
    """Test handling incoming message from Centrifugo."""
    messages_received = []

    def on_message(msg: MessageResponse):
        messages_received.append(msg)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Simulate connect and then message
        messages = [
            json.dumps({"connect": {"client": "test-client-id"}}),
            json.dumps(
                {
                    "push": {
                        "channel": "room:main",
                        "pub": {
                            "data": {
                                "id": "msg-123",
                                "content": "Test message",
                                "from_username": "alice",
                                "from_user_id": "user-123",
                                "timestamp": "2024-01-01T00:00:00Z",
                                "message_type": "room",
                            }
                        },
                    }
                }
            ),
        ]
        mock_websocket.__aiter__ = MagicMock(return_value=AsyncIteratorMock(messages))

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(api_key="test-key", on_message=on_message)

            await client.connect()
            await asyncio.sleep(0.1)

            assert len(messages_received) == 1
            assert messages_received[0].content == "Test message"
            assert messages_received[0].from_username == "alice"


@pytest.mark.asyncio
async def test_duplicate_message_ignored(mock_websocket, mock_httpx_response):
    """Test that duplicate messages are ignored."""
    messages_received = []

    def on_message(msg: MessageResponse):
        messages_received.append(msg)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Send the same message twice
        messages = [
            json.dumps({"connect": {"client": "test-client-id"}}),
            json.dumps(
                {
                    "push": {
                        "channel": "room:main",
                        "pub": {
                            "data": {
                                "id": "msg-123",
                                "content": "Test message",
                                "from_username": "alice",
                                "from_user_id": "user-123",
                                "timestamp": "2024-01-01T00:00:00Z",
                                "message_type": "room",
                            }
                        },
                    }
                }
            ),
            json.dumps(
                {
                    "push": {
                        "channel": "room:main",
                        "pub": {
                            "data": {
                                "id": "msg-123",  # Same ID
                                "content": "Test message",
                                "from_username": "alice",
                                "from_user_id": "user-123",
                                "timestamp": "2024-01-01T00:00:00Z",
                                "message_type": "room",
                            }
                        },
                    }
                }
            ),
        ]
        mock_websocket.__aiter__ = MagicMock(return_value=AsyncIteratorMock(messages))

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(api_key="test-key", on_message=on_message)

            await client.connect()
            await asyncio.sleep(0.1)

            # Only one message should be received (duplicate ignored)
            assert len(messages_received) == 1


@pytest.mark.asyncio
async def test_disconnect(mock_websocket, mock_httpx_response):
    """Test disconnecting from Centrifugo."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Connect
        mock_websocket.__aiter__ = MagicMock(
            return_value=AsyncIteratorMock(
                [json.dumps({"connect": {"client": "test-client-id"}})]
            )
        )

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(api_key="test-key")

            await client.connect()
            await asyncio.sleep(0.1)

            assert client.connected

            # Disconnect
            await client.disconnect()

            assert not client.connected
            mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_context_manager(mock_websocket, mock_httpx_response):
    """Test using WebSocket client as context manager."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        mock_websocket.__aiter__ = MagicMock(
            return_value=AsyncIteratorMock(
                [json.dumps({"connect": {"client": "test-client-id"}})]
            )
        )

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            async with TokenBowlWebSocket(api_key="test-key") as client:
                await asyncio.sleep(0.1)
                assert client.connected

            # Should be disconnected after exiting context
            assert not client.connected
            mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_mark_message_read(mock_httpx_response):
    """Test marking a message as read via REST API."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        # Mock response for mark read
        read_response = MagicMock()
        read_response.raise_for_status = MagicMock()
        mock_client.post.return_value = read_response

        mock_client_class.return_value = mock_client

        client = TokenBowlWebSocket(api_key="test-key")
        await client.mark_as_read("msg-123")

        # Verify REST API call was made
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0].endswith("/messages/msg-123/read")


@pytest.mark.asyncio
async def test_mark_all_as_read(mock_httpx_response):
    """Test marking all messages as read via REST API."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        # Mock response for mark all read
        read_response = MagicMock()
        read_response.raise_for_status = MagicMock()
        read_response.json.return_value = {"marked_as_read": 5}
        mock_client.post.return_value = read_response

        mock_client_class.return_value = mock_client

        client = TokenBowlWebSocket(api_key="test-key")
        result = await client.mark_all_as_read()

        assert result["count"] == 5

        # Verify REST API call was made
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0].endswith("/messages/mark-all-read")


@pytest.mark.asyncio
async def test_wait_until_connected(mock_websocket, mock_httpx_response):
    """Test waiting for connection to be established."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Create a delayed connection simulation
        connect_msg = json.dumps({"connect": {"client": "test-client-id"}})
        mock_websocket.__aiter__ = MagicMock(
            return_value=AsyncIteratorMock([connect_msg])
        )

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(api_key="test-key")

            # Start connection in background
            connect_task = asyncio.create_task(client.connect())

            # Wait for connection
            await client.wait_until_connected(timeout=5.0)
            assert client.connected

            await connect_task


@pytest.mark.asyncio
async def test_handle_read_receipt(mock_websocket, mock_httpx_response):
    """Test handling read receipt events from Centrifugo."""
    receipts_received = []

    def on_read_receipt(message_id: str, read_by: str):
        receipts_received.append((message_id, read_by))

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Simulate connect and then read receipt
        messages = [
            json.dumps({"connect": {"client": "test-client-id"}}),
            json.dumps(
                {
                    "push": {
                        "channel": "room:main",
                        "pub": {
                            "data": {
                                "type": "read_receipt",
                                "message_id": "msg-123",
                                "read_by": "alice",
                                "read_at": "2024-01-01T00:00:00Z",
                            }
                        },
                    }
                }
            ),
        ]
        mock_websocket.__aiter__ = MagicMock(return_value=AsyncIteratorMock(messages))

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(
                api_key="test-key", on_read_receipt=on_read_receipt
            )

            await client.connect()
            await asyncio.sleep(0.1)

            assert len(receipts_received) == 1
            assert receipts_received[0] == ("msg-123", "alice")


@pytest.mark.asyncio
async def test_handle_typing_indicator(mock_websocket, mock_httpx_response):
    """Test handling typing indicator events from Centrifugo."""
    typing_events = []

    def on_typing(username: str, to_username: str | None):
        typing_events.append((username, to_username))

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Simulate connect and then typing indicator
        messages = [
            json.dumps({"connect": {"client": "test-client-id"}}),
            json.dumps(
                {
                    "push": {
                        "channel": "room:main",
                        "pub": {
                            "data": {
                                "type": "typing",
                                "username": "bob",
                                "to_username": None,
                                "timestamp": "2024-01-01T00:00:00Z",
                            }
                        },
                    }
                }
            ),
        ]
        mock_websocket.__aiter__ = MagicMock(return_value=AsyncIteratorMock(messages))

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(api_key="test-key", on_typing=on_typing)

            await client.connect()
            await asyncio.sleep(0.1)

            assert len(typing_events) == 1
            assert typing_events[0] == ("bob", None)


@pytest.mark.asyncio
async def test_handle_unread_count(mock_websocket, mock_httpx_response):
    """Test handling unread count updates from Centrifugo."""
    unread_counts = []

    def on_unread_count(count):
        unread_counts.append(count)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Simulate connect and then unread count update
        messages = [
            json.dumps({"connect": {"client": "test-client-id"}}),
            json.dumps(
                {
                    "push": {
                        "channel": "user:testuser",
                        "pub": {
                            "data": {
                                "type": "unread_count",
                                "unread_room_messages": 5,
                                "unread_direct_messages": 3,
                                "total_unread": 8,
                                "timestamp": "2024-01-01T00:00:00Z",
                            }
                        },
                    }
                }
            ),
        ]
        mock_websocket.__aiter__ = MagicMock(return_value=AsyncIteratorMock(messages))

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(
                api_key="test-key", on_unread_count=on_unread_count
            )

            await client.connect()
            await asyncio.sleep(0.1)

            assert len(unread_counts) == 1
            assert unread_counts[0].unread_room_messages == 5
            assert unread_counts[0].unread_direct_messages == 3
            assert unread_counts[0].total_unread == 8


@pytest.mark.asyncio
async def test_send_typing_indicator_via_rest():
    """Test sending typing indicator via REST API."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        # Mock response for typing indicator
        typing_response = MagicMock()
        typing_response.raise_for_status = MagicMock()
        mock_client.post.return_value = typing_response

        mock_client_class.return_value = mock_client

        client = TokenBowlWebSocket(api_key="test-key")
        await client.send_typing_indicator()

        # Verify REST API call was made
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0].endswith("/typing")


@pytest.mark.asyncio
async def test_server_disconnect(mock_websocket, mock_httpx_response):
    """Test handling server-initiated disconnect."""
    disconnect_called = []

    def on_disconnect():
        disconnect_called.append(True)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Simulate connect and then disconnect
        messages = [
            json.dumps({"connect": {"client": "test-client-id"}}),
            json.dumps({"disconnect": {"reason": "shutdown", "reconnect": False}}),
        ]
        mock_websocket.__aiter__ = MagicMock(return_value=AsyncIteratorMock(messages))

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(api_key="test-key", on_disconnect=on_disconnect)

            await client.connect()
            await asyncio.sleep(0.1)

            assert not client.connected
            assert len(disconnect_called) == 1


@pytest.mark.asyncio
async def test_ping_pong_handling(mock_websocket, mock_httpx_response):
    """Test handling ping from server and responding with pong."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        # Track messages sent by client
        sent_messages = []

        async def track_send(msg):
            sent_messages.append(json.loads(msg))

        mock_websocket.send = track_send

        # Simulate connect and then server ping (empty JSON)
        messages = [
            json.dumps({"connect": {"client": "test-client-id"}}),
            json.dumps({}),  # Server sends empty {} as ping
        ]
        mock_websocket.__aiter__ = MagicMock(return_value=AsyncIteratorMock(messages))

        with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
            client = TokenBowlWebSocket(api_key="test-key")
            await client.connect()
            await asyncio.sleep(0.1)

            # Check that we responded with empty {} as pong
            pong_sent = any(msg == {} for msg in sent_messages)
            assert pong_sent, (
                f"Expected empty {{}} pong response to server ping, sent: {sent_messages}"
            )
