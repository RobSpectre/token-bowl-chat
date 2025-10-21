"""Tests for data models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from token_bowl_chat.models import (
    MessageResponse,
    MessageType,
    SendMessageRequest,
    UserRegistration,
)


def test_message_type_enum() -> None:
    """Test MessageType enum values."""
    assert MessageType.ROOM == "room"
    assert MessageType.DIRECT == "direct"
    assert MessageType.SYSTEM == "system"


def test_user_registration_valid() -> None:
    """Test valid user registration."""
    reg = UserRegistration(username="alice", webhook_url="https://example.com/hook")
    assert reg.username == "alice"
    assert reg.webhook_url == "https://example.com/hook"


def test_user_registration_no_webhook() -> None:
    """Test user registration without webhook."""
    reg = UserRegistration(username="alice")
    assert reg.username == "alice"
    assert reg.webhook_url is None


def test_user_registration_invalid_webhook() -> None:
    """Test user registration with invalid webhook URL."""
    with pytest.raises(ValidationError):
        UserRegistration(username="alice", webhook_url="not-a-url")


def test_user_registration_too_long_username() -> None:
    """Test user registration with too long username."""
    with pytest.raises(ValidationError):
        UserRegistration(username="a" * 51)


def test_send_message_request_valid() -> None:
    """Test valid message request."""
    req = SendMessageRequest(content="Hello!")
    assert req.content == "Hello!"
    assert req.to_username is None


def test_send_message_request_with_recipient() -> None:
    """Test message request with recipient."""
    req = SendMessageRequest(content="Hello!", to_username="bob")
    assert req.to_username == "bob"


def test_send_message_request_too_long() -> None:
    """Test message request with too long content."""
    with pytest.raises(ValidationError):
        SendMessageRequest(content="x" * 10001)


def test_send_message_request_empty() -> None:
    """Test message request with empty content."""
    with pytest.raises(ValidationError):
        SendMessageRequest(content="")


def test_message_response() -> None:
    """Test message response model."""
    msg = MessageResponse(
        id="msg-1",
        from_user_id="550e8400-e29b-41d4-a716-446655440000",
        from_username="alice",
        to_username=None,
        content="Hello!",
        message_type=MessageType.ROOM,
        description="room message from alice",
        timestamp="2025-10-16T12:00:00Z",
    )
    assert msg.id == "msg-1"
    assert msg.from_user_id == "550e8400-e29b-41d4-a716-446655440000"
    assert msg.from_username == "alice"
    assert msg.message_type == MessageType.ROOM


def test_message_response_timestamp_parsing() -> None:
    """Test timestamp parsing in message response."""
    msg = MessageResponse(
        id="msg-1",
        from_user_id="550e8400-e29b-41d4-a716-446655440000",
        from_username="alice",
        to_username=None,
        content="Hello!",
        message_type=MessageType.ROOM,
        description="room message from alice",
        timestamp="2025-10-16T12:00:00Z",
    )
    dt = msg.timestamp_dt
    assert isinstance(dt, datetime)
    assert dt.tzinfo == timezone.utc
    assert dt.year == 2025
    assert dt.month == 10
    assert dt.day == 16
