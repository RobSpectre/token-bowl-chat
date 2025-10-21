"""Tests for the synchronous Token Bowl client."""

import pytest
from pytest_httpx import HTTPXMock

from token_bowl_chat import (
    AuthenticationError,
    ConflictError,
    MessageType,
    NotFoundError,
    TokenBowlClient,
    ValidationError,
)


@pytest.fixture
def client() -> TokenBowlClient:
    """Create a test client."""
    return TokenBowlClient(api_key="test-key-123", base_url="http://test.example.com")


def test_register_success(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test successful user registration."""
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/register",
        json={
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "alice",
            "api_key": "test-key-123",
            "role": "member",
            "webhook_url": None,
            "viewer": False,
            "admin": False,
            "bot": False,
        },
        status_code=201,
    )

    response = client.register(username="alice")

    assert response.id == "550e8400-e29b-41d4-a716-446655440000"
    assert response.username == "alice"
    assert response.api_key == "test-key-123"
    assert response.role.value == "member"
    assert response.webhook_url is None


def test_register_with_webhook(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test user registration with webhook URL."""
    webhook_url = "https://example.com/webhook"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/register",
        json={
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "username": "bob",
            "api_key": "test-key-456",
            "role": "member",
            "webhook_url": webhook_url,
            "viewer": False,
            "admin": False,
            "bot": False,
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
            "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "from_username": "alice",
            "to_username": None,
            "content": "Hello, room!",
            "message_type": "room",
            "description": "room message from alice",
            "timestamp": "2025-10-16T12:00:00Z",
        },
        status_code=201,
    )

    response = client.send_message("Hello, room!")

    assert response.id == "msg-1"
    assert response.from_user_id == "550e8400-e29b-41d4-a716-446655440000"
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
            "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "from_username": "alice",
            "to_user_id": "550e8400-e29b-41d4-a716-446655440001",
            "to_username": "bob",
            "content": "Hello, Bob!",
            "message_type": "direct",
            "description": "direct message from alice to bob",
            "timestamp": "2025-10-16T12:00:00Z",
        },
        status_code=201,
    )

    response = client.send_message("Hello, Bob!", to_username="bob")

    assert response.to_user_id == "550e8400-e29b-41d4-a716-446655440001"
    assert response.to_username == "bob"
    assert response.message_type == MessageType.DIRECT


def test_send_message_no_auth(client: TokenBowlClient) -> None:
    """Test sending message without authentication."""
    client.api_key = None  # Clear API key to test authentication error
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
                    "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "from_username": "alice",
                    "to_username": None,
                    "content": "Hello!",
                    "message_type": "room",
                    "description": "room message from alice",
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
                    "from_user_id": "550e8400-e29b-41d4-a716-446655440001",
                    "from_username": "bob",
                    "to_user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "to_username": "alice",
                    "content": "Private message",
                    "message_type": "direct",
                    "description": "direct message from bob to alice",
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
        json=[
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "alice",
                "role": "member",
                "logo": "claude.png",
                "bot": False,
                "viewer": False,
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "username": "bob",
                "role": "bot",
                "emoji": "🤖",
                "bot": True,
                "viewer": False,
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "username": "charlie",
                "role": "member",
                "bot": False,
                "viewer": False,
            },
        ],
    )

    users = client.get_users()

    assert len(users) == 3
    assert users[0].id == "550e8400-e29b-41d4-a716-446655440000"
    assert users[0].username == "alice"
    assert users[0].logo == "claude.png"
    assert users[1].id == "550e8400-e29b-41d4-a716-446655440001"
    assert users[1].username == "bob"
    assert users[1].emoji == "🤖"
    assert users[1].bot is True


def test_get_online_users(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test getting online users."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/users/online",
        json=[
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "alice",
                "role": "member",
                "logo": "claude.png",
                "bot": False,
                "viewer": False,
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "username": "bob",
                "role": "member",
                "bot": False,
                "viewer": False,
            },
        ],
    )

    users = client.get_online_users()

    assert len(users) == 2
    assert users[0].username == "alice"
    assert users[1].username == "bob"


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

    with TokenBowlClient(
        api_key="test-key-123", base_url="http://test.example.com"
    ) as client:
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
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "alice",
            "api_key": "test-key-123",
            "role": "member",
            "webhook_url": None,
            "logo": "claude-color.png",
            "viewer": False,
            "admin": False,
            "bot": False,
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


# Bot Management Tests


def test_create_bot(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test creating a bot."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/bots",
        json={
            "id": "550e8400-e29b-41d4-a716-446655440010",
            "username": "test-bot",
            "api_key": "bot-key-123",
            "created_by_id": "550e8400-e29b-41d4-a716-446655440000",
            "created_by": "alice",
            "emoji": "🤖",
            "webhook_url": None,
        },
        status_code=201,
    )

    response = client.create_bot(username="test-bot", emoji="🤖")

    assert response.id == "550e8400-e29b-41d4-a716-446655440010"
    assert response.username == "test-bot"
    assert response.api_key == "bot-key-123"
    assert response.created_by == "alice"
    assert response.emoji == "🤖"


def test_create_bot_with_webhook(
    httpx_mock: HTTPXMock, client: TokenBowlClient
) -> None:
    """Test creating a bot with webhook URL."""
    client.api_key = "test-key-123"
    webhook_url = "https://example.com/bot/webhook"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/bots",
        json={
            "id": "550e8400-e29b-41d4-a716-446655440010",
            "username": "webhook-bot",
            "api_key": "bot-key-456",
            "created_by_id": "550e8400-e29b-41d4-a716-446655440000",
            "created_by": "alice",
            "emoji": None,
            "webhook_url": webhook_url,
        },
        status_code=201,
    )

    response = client.create_bot(username="webhook-bot", webhook_url=webhook_url)

    assert response.username == "webhook-bot"
    assert response.webhook_url == webhook_url


def test_get_my_bots(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test getting user's bots."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/bots/me",
        json=[
            {
                "id": "550e8400-e29b-41d4-a716-446655440010",
                "username": "bot1",
                "api_key": "bot-key-1",
                "created_by_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_by": "alice",
                "emoji": "🤖",
                "webhook_url": None,
                "created_at": "2025-10-16T12:00:00Z",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440011",
                "username": "bot2",
                "api_key": "bot-key-2",
                "created_by_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_by": "alice",
                "emoji": "🦾",
                "webhook_url": None,
                "created_at": "2025-10-16T12:30:00Z",
            },
        ],
    )

    bots = client.get_my_bots()

    assert len(bots) == 2
    assert bots[0].username == "bot1"
    assert bots[1].username == "bot2"
    assert bots[0].emoji == "🤖"


def test_update_bot(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test updating a bot."""
    client.api_key = "test-key-123"
    bot_id = "550e8400-e29b-41d4-a716-446655440010"
    httpx_mock.add_response(
        method="PATCH",
        url=f"http://test.example.com/bots/{bot_id}",
        json={
            "id": bot_id,
            "username": "bot1",
            "api_key": "bot-key-1",
            "created_by_id": "550e8400-e29b-41d4-a716-446655440000",
            "created_by": "alice",
            "emoji": "🦾",
            "webhook_url": "https://example.com/new/webhook",
            "created_at": "2025-10-16T12:00:00Z",
        },
    )

    response = client.update_bot(
        bot_id=bot_id, emoji="🦾", webhook_url="https://example.com/new/webhook"
    )

    assert response.id == bot_id
    assert response.emoji == "🦾"
    assert response.webhook_url == "https://example.com/new/webhook"


def test_delete_bot(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test deleting a bot."""
    client.api_key = "test-key-123"
    bot_id = "550e8400-e29b-41d4-a716-446655440010"
    httpx_mock.add_response(
        method="DELETE",
        url=f"http://test.example.com/bots/{bot_id}",
        status_code=204,
    )

    # Should not raise an exception
    client.delete_bot(bot_id=bot_id)


def test_regenerate_bot_api_key(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test regenerating bot API key."""
    client.api_key = "test-key-123"
    bot_id = "550e8400-e29b-41d4-a716-446655440010"
    httpx_mock.add_response(
        method="POST",
        url=f"http://test.example.com/bots/{bot_id}/regenerate-api-key",
        json={"message": "API key regenerated", "api_key": "new-bot-key-123"},
    )

    response = client.regenerate_bot_api_key(bot_id=bot_id)

    assert response["message"] == "API key regenerated"
    assert response["api_key"] == "new-bot-key-123"


# Admin Role Management Tests


def test_admin_assign_role(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test admin assigning role to user."""
    client.api_key = "test-key-123"
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    httpx_mock.add_response(
        method="PATCH",
        url=f"http://test.example.com/admin/users/{user_id}/role",
        json={
            "username": "alice",
            "role": "admin",
            "message": "Role assigned successfully",
        },
    )

    response = client.admin_assign_role(user_id=user_id, role="admin")

    assert response.username == "alice"
    assert response.role.value == "admin"
    assert response.message == "Role assigned successfully"


def test_admin_invite_user(httpx_mock: HTTPXMock, client: TokenBowlClient) -> None:
    """Test admin inviting user by email."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/admin/invite",
        json={
            "email": "newuser@example.com",
            "role": "member",
            "message": "Invitation sent successfully",
        },
    )

    response = client.admin_invite_user(
        email="newuser@example.com",
        signup_url="https://app.example.com/signup",
        role="member",
    )

    assert response.email == "newuser@example.com"
    assert response.role.value == "member"
    assert response.message == "Invitation sent successfully"


# User ID vs Username Tests (Regression Prevention)


def test_get_user_profile_with_user_id(
    httpx_mock: HTTPXMock, client: TokenBowlClient
) -> None:
    """Test getting user profile by user_id (not username)."""
    client.api_key = "test-key-123"
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    httpx_mock.add_response(
        method="GET",
        url=f"http://test.example.com/users/{user_id}",
        json={
            "id": user_id,
            "username": "alice",
            "role": "member",
            "logo": "claude.png",
            "bot": False,
            "viewer": False,
        },
    )

    profile = client.get_user_profile(user_id=user_id)

    assert profile.id == user_id
    assert profile.username == "alice"


def test_admin_get_user_with_user_id(
    httpx_mock: HTTPXMock, client: TokenBowlClient
) -> None:
    """Test admin getting user by user_id (not username)."""
    client.api_key = "test-key-123"
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    httpx_mock.add_response(
        method="GET",
        url=f"http://test.example.com/admin/users/{user_id}",
        json={
            "id": user_id,
            "username": "alice",
            "role": "member",
            "email": "alice@example.com",
            "api_key": "user-key-123",
            "webhook_url": None,
            "logo": None,
            "viewer": False,
            "admin": False,
            "bot": False,
            "emoji": None,
            "created_at": "2025-10-16T12:00:00Z",
        },
    )

    profile = client.admin_get_user(user_id=user_id)

    assert profile.id == user_id
    assert profile.username == "alice"
    assert profile.email == "alice@example.com"


def test_admin_update_user_with_user_id(
    httpx_mock: HTTPXMock, client: TokenBowlClient
) -> None:
    """Test admin updating user by user_id (not username)."""
    from token_bowl_chat.models import AdminUpdateUserRequest

    client.api_key = "test-key-123"
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    httpx_mock.add_response(
        method="PATCH",
        url=f"http://test.example.com/admin/users/{user_id}",
        json={
            "id": user_id,
            "username": "alice",
            "role": "member",
            "email": "newemail@example.com",
            "api_key": "user-key-123",
            "webhook_url": None,
            "logo": None,
            "viewer": False,
            "admin": False,
            "bot": False,
            "emoji": "🐰",
            "created_at": "2025-10-16T12:00:00Z",
        },
    )

    update_request = AdminUpdateUserRequest(email="newemail@example.com", emoji="🐰")
    profile = client.admin_update_user(user_id=user_id, update_request=update_request)

    assert profile.id == user_id
    assert profile.email == "newemail@example.com"
    assert profile.emoji == "🐰"


def test_admin_delete_user_with_user_id(
    httpx_mock: HTTPXMock, client: TokenBowlClient
) -> None:
    """Test admin deleting user by user_id (not username)."""
    client.api_key = "test-key-123"
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    httpx_mock.add_response(
        method="DELETE",
        url=f"http://test.example.com/admin/users/{user_id}",
        status_code=204,
    )

    # Should not raise an exception
    client.admin_delete_user(user_id=user_id)


# Message description field test


def test_message_response_has_description_field(
    httpx_mock: HTTPXMock, client: TokenBowlClient
) -> None:
    """Test that MessageResponse includes description field."""
    client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/messages",
        json={
            "id": "msg-1",
            "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "from_username": "alice",
            "to_username": None,
            "content": "Hello!",
            "message_type": "room",
            "description": "room message from alice",
            "timestamp": "2025-10-16T12:00:00Z",
        },
        status_code=201,
    )

    response = client.send_message("Hello!")

    assert response.description == "room message from alice"


# Public endpoint test for get_available_logos


def test_get_available_logos_no_auth_required(
    httpx_mock: HTTPXMock,
) -> None:
    """Test that get_available_logos works without authentication."""
    # Create client without API key
    client_no_auth = TokenBowlClient(base_url="http://test.example.com")

    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/logos",
        json=["claude-color.png", "openai.png"],
    )

    logos = client_no_auth.get_available_logos()

    assert len(logos) == 2
    assert "claude-color.png" in logos
