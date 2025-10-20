"""Tests for WebSocket client."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.exceptions import AuthenticationError, NetworkError
from token_bowl_chat.models import MessageResponse


@pytest.fixture
def mock_websocket():
    """Create a mock websocket connection."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    ws.__aiter__ = MagicMock(return_value=iter([]))
    return ws


@pytest.mark.asyncio
async def test_connect_success(mock_websocket):
    """Test successful WebSocket connection."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        assert client.is_connected
        assert client._websocket == mock_websocket


@pytest.mark.asyncio
async def test_connect_authentication_error():
    """Test WebSocket connection with invalid API key."""
    mock_error = Exception("401 Unauthorized")
    mock_error.response = MagicMock(status_code=401)

    with patch(
        "websockets.connect",
        side_effect=lambda *args, **kwargs: (_ for _ in ()).throw(
            type(
                "InvalidStatus",
                (Exception,),
                {"response": MagicMock(status_code=401)},
            )()
        ),
    ):
        client = TokenBowlWebSocket(api_key="invalid-key")

        # Import the exception type we need to catch
        from websockets.exceptions import InvalidStatus

        with (
            patch(
                "websockets.connect",
                side_effect=InvalidStatus(MagicMock(status_code=401)),
            ),
            pytest.raises(AuthenticationError, match="Invalid API key"),
        ):
            await client.connect()


@pytest.mark.asyncio
async def test_connect_with_callbacks(mock_websocket):
    """Test connection with on_connect callback."""
    on_connect_called = False

    def on_connect():
        nonlocal on_connect_called
        on_connect_called = True

    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key", on_connect=on_connect)
        await client.connect()

        assert on_connect_called


@pytest.mark.asyncio
async def test_send_message_room(mock_websocket):
    """Test sending a room message."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        await client.send_message("Hello, world!")

        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["content"] == "Hello, world!"
        assert "to_username" not in sent_data


@pytest.mark.asyncio
async def test_send_message_direct(mock_websocket):
    """Test sending a direct message."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        await client.send_message("Hi Bob!", to_username="bob")

        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["content"] == "Hi Bob!"
        assert sent_data["to_username"] == "bob"


@pytest.mark.asyncio
async def test_send_message_not_connected():
    """Test sending message when not connected."""
    client = TokenBowlWebSocket(api_key="test-key")

    with pytest.raises(ValueError, match="not connected"):
        await client.send_message("test")


@pytest.mark.asyncio
async def test_send_message_invalid_content(mock_websocket):
    """Test sending message with invalid content."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        # Empty content
        with pytest.raises(ValueError, match="1-10000 characters"):
            await client.send_message("")

        # Too long content
        with pytest.raises(ValueError, match="1-10000 characters"):
            await client.send_message("x" * 10001)


@pytest.mark.asyncio
async def test_receive_message():
    """Test receiving a message."""
    message_data = {
        "id": "msg123",
        "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
        "from_username": "alice",
        "to_username": None,
        "content": "Hello!",
        "message_type": "room",
        "timestamp": "2024-01-01T00:00:00Z",
    }

    messages_received = []

    def on_message(msg: MessageResponse):
        messages_received.append(msg)

    # Create mock websocket that yields one message
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.close = AsyncMock()

    # Make the websocket async iterator yield our message
    async def message_generator():
        yield json.dumps(message_data)

    mock_ws.__aiter__ = lambda self: message_generator()

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = TokenBowlWebSocket(api_key="test-key", on_message=on_message)
        await client.connect()

        # Wait a bit for message to be received
        await asyncio.sleep(0.1)

        assert len(messages_received) == 1
        assert (
            messages_received[0].from_user_id == "550e8400-e29b-41d4-a716-446655440000"
        )
        assert messages_received[0].from_username == "alice"
        assert messages_received[0].content == "Hello!"

        await client.disconnect()


@pytest.mark.asyncio
async def test_receive_error_message():
    """Test receiving an error message from server."""
    error_data = {"type": "error", "error": "Something went wrong"}

    errors_received = []

    def on_error(error: Exception):
        errors_received.append(error)

    # Create mock websocket that yields an error
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.close = AsyncMock()

    async def message_generator():
        yield json.dumps(error_data)

    mock_ws.__aiter__ = lambda self: message_generator()

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = TokenBowlWebSocket(api_key="test-key", on_error=on_error)
        await client.connect()

        # Wait for error to be processed
        await asyncio.sleep(0.1)

        assert len(errors_received) == 1
        assert "Something went wrong" in str(errors_received[0])

        await client.disconnect()


@pytest.mark.asyncio
async def test_disconnect(mock_websocket):
    """Test disconnecting from WebSocket."""
    on_disconnect_called = False

    def on_disconnect():
        nonlocal on_disconnect_called
        on_disconnect_called = True

    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key", on_disconnect=on_disconnect)
        await client.connect()

        assert client.is_connected

        await client.disconnect()

        assert not client.is_connected
        assert on_disconnect_called
        mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_context_manager(mock_websocket):
    """Test using WebSocket as async context manager."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        async with TokenBowlWebSocket(api_key="test-key") as client:
            assert client.is_connected
            await client.send_message("test")

        # Should be disconnected after exiting context
        assert not client.is_connected
        mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_base_url_normalization():
    """Test that base URL is properly normalized."""
    # WSS URL without /ws
    client1 = TokenBowlWebSocket(api_key="key", base_url="wss://example.com")
    assert client1.base_url == "wss://example.com/ws"

    # WSS URL with trailing slash
    client2 = TokenBowlWebSocket(api_key="key", base_url="wss://example.com/")
    assert client2.base_url == "wss://example.com/ws"

    # WSS URL with /ws already
    client3 = TokenBowlWebSocket(api_key="key", base_url="wss://example.com/ws")
    assert client3.base_url == "wss://example.com/ws"


@pytest.mark.asyncio
async def test_receive_confirmation_message():
    """Test that confirmation messages are properly handled and not passed to on_message."""
    confirmation_data = {
        "status": "sent",
        "message": {"id": "123", "content": "test"},
    }

    messages_received = []

    def on_message(msg: MessageResponse):
        messages_received.append(msg)

    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.close = AsyncMock()

    async def message_generator():
        yield json.dumps(confirmation_data)

    mock_ws.__aiter__ = lambda self: message_generator()

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = TokenBowlWebSocket(api_key="test-key", on_message=on_message)
        await client.connect()

        await asyncio.sleep(0.1)

        # Confirmation messages should not trigger on_message callback
        assert len(messages_received) == 0

        await client.disconnect()


@pytest.mark.asyncio
async def test_send_network_error(mock_websocket):
    """Test handling network error when sending."""
    mock_websocket.send.side_effect = Exception("Network error")

    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        with pytest.raises(NetworkError, match="Failed to send"):
            await client.send_message("test")


@pytest.mark.asyncio
async def test_mark_message_read(mock_websocket):
    """Test marking a specific message as read."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        await client.mark_message_read("msg123")

        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["action"] == "mark_read"
        assert sent_data["message_id"] == "msg123"


@pytest.mark.asyncio
async def test_mark_all_messages_read(mock_websocket):
    """Test marking all messages as read."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        await client.mark_all_messages_read()

        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["action"] == "mark_all_read"


@pytest.mark.asyncio
async def test_mark_room_messages_read(mock_websocket):
    """Test marking all room messages as read."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        await client.mark_room_messages_read()

        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["action"] == "mark_room_read"


@pytest.mark.asyncio
async def test_mark_direct_messages_read(mock_websocket):
    """Test marking direct messages from a user as read."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        await client.mark_direct_messages_read("alice")

        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["action"] == "mark_direct_read"
        assert sent_data["from_username"] == "alice"


@pytest.mark.asyncio
async def test_get_unread_count(mock_websocket):
    """Test requesting unread count."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        await client.get_unread_count()

        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["action"] == "get_unread_count"


@pytest.mark.asyncio
async def test_send_typing_indicator_room(mock_websocket):
    """Test sending typing indicator to room."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        await client.send_typing_indicator()

        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["action"] == "typing"
        assert "to_username" not in sent_data


@pytest.mark.asyncio
async def test_send_typing_indicator_direct(mock_websocket):
    """Test sending typing indicator to specific user."""
    with patch("websockets.connect", new=AsyncMock(return_value=mock_websocket)):
        client = TokenBowlWebSocket(api_key="test-key")
        await client.connect()

        await client.send_typing_indicator(to_username="bob")

        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["action"] == "typing"
        assert sent_data["to_username"] == "bob"


@pytest.mark.asyncio
async def test_receive_read_receipt():
    """Test receiving a read receipt event."""
    read_receipt_data = {
        "type": "read_receipt",
        "message_id": "msg123",
        "read_by": "alice",
    }

    receipts_received = []

    def on_read_receipt(message_id: str, read_by: str):
        receipts_received.append((message_id, read_by))

    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.close = AsyncMock()

    async def message_generator():
        yield json.dumps(read_receipt_data)

    mock_ws.__aiter__ = lambda self: message_generator()

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = TokenBowlWebSocket(api_key="test-key", on_read_receipt=on_read_receipt)
        await client.connect()

        await asyncio.sleep(0.1)

        assert len(receipts_received) == 1
        assert receipts_received[0] == ("msg123", "alice")

        await client.disconnect()


@pytest.mark.asyncio
async def test_receive_unread_count():
    """Test receiving unread count update."""
    unread_count_data = {
        "type": "unread_count",
        "unread_room_messages": 5,
        "unread_direct_messages": 3,
        "total_unread": 8,
    }

    counts_received = []

    def on_unread_count(count):
        counts_received.append(count)

    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.close = AsyncMock()

    async def message_generator():
        yield json.dumps(unread_count_data)

    mock_ws.__aiter__ = lambda self: message_generator()

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = TokenBowlWebSocket(api_key="test-key", on_unread_count=on_unread_count)
        await client.connect()

        await asyncio.sleep(0.1)

        assert len(counts_received) == 1
        assert counts_received[0].unread_room_messages == 5
        assert counts_received[0].unread_direct_messages == 3
        assert counts_received[0].total_unread == 8

        await client.disconnect()


@pytest.mark.asyncio
async def test_receive_typing_indicator():
    """Test receiving typing indicator."""
    typing_data = {"type": "typing", "username": "alice", "to_username": None}

    typing_events = []

    def on_typing(username: str, to_username: str | None):
        typing_events.append((username, to_username))

    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.close = AsyncMock()

    async def message_generator():
        yield json.dumps(typing_data)

    mock_ws.__aiter__ = lambda self: message_generator()

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = TokenBowlWebSocket(api_key="test-key", on_typing=on_typing)
        await client.connect()

        await asyncio.sleep(0.1)

        assert len(typing_events) == 1
        assert typing_events[0] == ("alice", None)

        await client.disconnect()


@pytest.mark.asyncio
async def test_receive_typing_indicator_direct():
    """Test receiving typing indicator for direct message."""
    typing_data = {"type": "typing", "username": "alice", "to_username": "bob"}

    typing_events = []

    def on_typing(username: str, to_username: str | None):
        typing_events.append((username, to_username))

    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.close = AsyncMock()

    async def message_generator():
        yield json.dumps(typing_data)

    mock_ws.__aiter__ = lambda self: message_generator()

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = TokenBowlWebSocket(api_key="test-key", on_typing=on_typing)
        await client.connect()

        await asyncio.sleep(0.1)

        assert len(typing_events) == 1
        assert typing_events[0] == ("alice", "bob")

        await client.disconnect()


@pytest.mark.asyncio
async def test_mark_read_not_connected():
    """Test marking message read when not connected."""
    client = TokenBowlWebSocket(api_key="test-key")

    with pytest.raises(ValueError, match="not connected"):
        await client.mark_message_read("msg123")


@pytest.mark.asyncio
async def test_typing_indicator_not_connected():
    """Test sending typing indicator when not connected."""
    client = TokenBowlWebSocket(api_key="test-key")

    with pytest.raises(ValueError, match="not connected"):
        await client.send_typing_indicator()


@pytest.mark.asyncio
async def test_connect_without_api_key():
    """Test connecting without API key."""
    client = TokenBowlWebSocket()

    with pytest.raises(AuthenticationError, match="API key required"):
        await client.connect()
