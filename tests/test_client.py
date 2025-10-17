"""Tests for the synchronous Token Bowl client."""

import pytest
from pytest_httpx import HTTPXMock

from token_bowl_chat import (
    AuthenticationError,
    ConflictError,
    MessageResponse,
    MessageType,
    NotFoundError,
    PaginatedMessagesResponse,
    TokenBowlClient,
    ValidationError,
)


@pytest.fixture
def client() -> TokenBowlClient:
    """Create a test client."""
    return TokenBowlClient(base_url="http://test.example.com")


def test_register_success(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test successful user registration."""
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/register",
        json={
            "username": "alice",
            "api_key": "test-key-123",
            "webhook_url": None,
        },
        status_code=201,
    )

    response = client.register(username="alice")

    assert response.username == "alice"
    assert response.api_key == "test-key-123"
    assert response.webhook_url is None


def test_register_with_webhook(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test user registration with webhook URL."""
    webhook_url = "https://example.com/webhook"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/register",
        json={
            "username": "bob",
            "api_key": "test-key-456",
            "webhook_url": webhook_url,
        },
        status_code=201,
    )

    response = client.register(username="bob", webhook_url=webhook_url)

    assert response.username == "bob"
    assert response.webhook_url == webhook_url


def test_register_conflict(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test registration with existing username."""
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/register",
        json={"detail": "Username already exists"},
        status_code=409,
    )

    with pytest.raises(ConflictError):
        client.register(username="alice")


def test_send_message_room(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test sending a room message."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/messages",
        json={
            "id": "msg-1",
            "from_username": "alice",
            "to_username": None,
            "content": "Hello, room!",
            "message_type": "room",
            "timestamp": "2025-10-16T12:00:00Z",
        },
        status_code=201,
    )

    response = client.send_message("Hello, room!")

    assert response.id == "msg-1"
    assert response.from_username == "alice"
    assert response.to_username is None
    assert response.content == "Hello, room!"
    assert response.message_type == MessageType.ROOM


def test_send_message_direct(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test sending a direct message."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/messages",
        json={
            "id": "msg-2",
            "from_username": "alice",
            "to_username": "bob",
            "content": "Hello, Bob!",
            "message_type": "direct",
            "timestamp": "2025-10-16T12:00:00Z",
        },
        status_code=201,
    )

    response = client.send_message("Hello, Bob!", to_username="bob")

    assert response.to_username == "bob"
    assert response.message_type == MessageType.DIRECT


def test_send_message_no_auth(client: TokenBowlClient) -> None:
    """Test sending message without authentication."""
    with pytest.raises(AuthenticationError, match="API key required"):
        client.send_message("Hello!")


def test_send_message_recipient_not_found(
    httpx_mock: HTTPXMock, client: TokenBowlClient
) -> None:
    """Test sending message to non-existent user."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/messages",
        json={"detail": "User not found"},
        status_code=404,
    )

    with pytest.raises(NotFoundError):
        client.send_message("Hello!", to_username="nonexistent")


def test_get_messages(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test getting room messages."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/messages?limit=50&offset=0",
        json={
            "messages": [
                {
                    "id": "msg-1",
                    "from_username": "alice",
                    "to_username": None,
                    "content": "Hello!",
                    "message_type": "room",
                    "timestamp": "2025-10-16T12:00:00Z",
                }
            ],
            "pagination": {
                "total": 1,
                "offset": 0,
                "limit": 50,
                "has_more": False,
            },
        },
    )

    response = client.get_messages()

    assert len(response.messages) == 1
    assert response.messages[0].content == "Hello!"
    assert response.pagination.total == 1
    assert response.pagination.has_more is False


def test_get_messages_with_pagination(
    httpx_mock: HTTPXMock, client: TokenBowlClient
) -> None:
    """Test getting messages with custom pagination."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/messages?limit=10&offset=20",
        json={
            "messages": [],
            "pagination": {
                "total": 100,
                "offset": 20,
                "limit": 10,
                "has_more": True,
            },
        },
    )

    response = client.get_messages(limit=10, offset=20)

    assert response.pagination.offset == 20
    assert response.pagination.limit == 10
    assert response.pagination.has_more is True


def test_get_direct_messages(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test getting direct messages."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/messages/direct?limit=50&offset=0",
        json={
            "messages": [
                {
                    "id": "msg-dm-1",
                    "from_username": "bob",
                    "to_username": "alice",
                    "content": "Private message",
                    "message_type": "direct",
                    "timestamp": "2025-10-16T12:00:00Z",
                }
            ],
            "pagination": {
                "total": 1,
                "offset": 0,
                "limit": 50,
                "has_more": False,
            },
        },
    )

    response = client.get_direct_messages()

    assert len(response.messages) == 1
    assert response.messages[0].message_type == MessageType.DIRECT


def test_get_users(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test getting all users."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/users",
        json=["alice", "bob", "charlie"],
    )

    users = client.get_users()

    assert users == ["alice", "bob", "charlie"]
    assert len(users) == 3


def test_get_online_users(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test getting online users."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/users/online",
        json=["alice", "bob"],
    )

    users = client.get_online_users()

    assert users == ["alice", "bob"]
    assert len(users) == 2


def test_health_check(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test health check endpoint."""
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/health",
        json={"status": "healthy"},
    )

    health = client.health_check()

    assert health["status"] == "healthy"


def test_context_manager(httpx_mock: HTTPXMock) -> None:
    """Test using client as context manager."""
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/health",
        json={"status": "healthy"},
    )

    with TokenBowlClient(base_url="http://test.example.com") as client:
        health = client.health_check()
        assert health["status"] == "healthy"


def test_validation_error(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test validation error handling from server."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/messages",
        json={
            "detail": [
                {
                    "loc": ["body", "to_username"],
                    "msg": "recipient does not exist",
                    "type": "value_error",
                }
            ]
        },
        status_code=422,
    )

    with pytest.raises(ValidationError):
        client.send_message("Hello!", to_username="nonexistent")


def test_get_available_logos(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test getting available logos."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/logos",
        json=["claude-color.png", "openai.png", "gemini-color.png"],
    )

    logos = client.get_available_logos()

    assert len(logos) == 3
    assert "claude-color.png" in logos
    assert "openai.png" in logos


def test_register_with_logo(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test registration with logo."""
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/register",
        json={
            "username": "alice",
            "api_key": "test-key-123",
            "webhook_url": None,
            "logo": "claude-color.png",
        },
        status_code=201,
    )

    response = client.register(username="alice", logo="claude-color.png")

    assert response.username == "alice"
    assert response.logo == "claude-color.png"


def test_update_logo(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test updating user logo."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="PATCH",
        url="http://test.example.com/users/me/logo",
        json={"message": "Logo updated successfully", "logo": "openai.png"},
    )

    result = client.update_my_logo(logo="openai.png")

    assert result["message"] == "Logo updated successfully"
    assert result["logo"] == "openai.png"


def test_update_logo_clear(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test clearing user logo."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="PATCH",
        url="http://test.example.com/users/me/logo",
        json={"message": "Logo cleared successfully", "logo": None},
    )

    result = client.update_my_logo(logo=None)

    assert result["message"] == "Logo cleared successfully"
    assert result["logo"] is None


def test_server_error(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test 500 server error handling."""
    from token_bowl_chat import ServerError

    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/health",
        json={"error": "Internal server error"},
        status_code=500,
    )

    with pytest.raises(ServerError):
        client.health_check()


def test_rate_limit_error(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test rate limit error handling."""
    from token_bowl_chat import RateLimitError

    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/messages",
        json={"error": "Rate limit exceeded"},
        status_code=429,
    )

    with pytest.raises(RateLimitError):
        client.send_message("Test message")


def test_get_messages_with_since(
    httpx_mock: HTTPXMock, client: TokenBowlClient
) -> None:
    """Test getting messages with since parameter."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/messages?limit=50&offset=0&since=2025-10-16T12:00:00Z",
        json={
            "messages": [],
            "pagination": {
                "total": 0,
                "offset": 0,
                "limit": 50,
                "has_more": False,
            },
        },
    )

    response = client.get_messages(since="2025-10-16T12:00:00Z")

    assert len(response.messages) == 0
    assert response.pagination.total == 0
