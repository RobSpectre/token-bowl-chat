"""Tests for the asynchronous Token Bowl client."""

import pytest
from pytest_httpx import HTTPXMock

from token_bowl_chat import (
    AsyncTokenBowlClient,
    AuthenticationError,
    MessageType,
)


@pytest.fixture
def async_client() -> AsyncTokenBowlClient:
    """Create a test async client."""
    return AsyncTokenBowlClient(
        api_key="test-key-123", base_url="http://test.example.com"
    )


@pytest.mark.asyncio
async def test_register_success(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test successful async user registration."""
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

    response = await async_client.register(username="alice")

    assert response.id == "550e8400-e29b-41d4-a716-446655440000"
    assert response.username == "alice"
    assert response.api_key == "test-key-123"


@pytest.mark.asyncio
async def test_send_message(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test sending an async message."""
    async_client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/messages",
        json={
            "id": "msg-1",
            "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "from_username": "alice",
            "to_username": None,
            "content": "Hello, async!",
            "message_type": "room",
            "description": "test message",
            "timestamp": "2025-10-16T12:00:00Z",
        },
        status_code=201,
    )

    response = await async_client.send_message("Hello, async!")

    assert response.content == "Hello, async!"
    assert response.message_type == MessageType.ROOM


@pytest.mark.asyncio
async def test_get_messages(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test getting messages asynchronously."""
    async_client.api_key = "test-key-123"
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
                    "description": "test message",
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

    response = await async_client.get_messages()

    assert len(response.messages) == 1
    assert response.messages[0].content == "Hello!"


@pytest.mark.asyncio
async def test_get_users(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test getting users asynchronously."""
    async_client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/users",
        json=[
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "alice",
                "role": "member",
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
        ],
    )

    users = await async_client.get_users()

    assert len(users) == 2
    assert users[0].username == "alice"
    assert users[1].bot is True


@pytest.mark.asyncio
async def test_health_check(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test async health check."""
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/health",
        json={"status": "healthy"},
    )

    health = await async_client.health_check()

    assert health["status"] == "healthy"


@pytest.mark.asyncio
async def test_context_manager(httpx_mock: HTTPXMock) -> None:
    """Test using async client as context manager."""
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/health",
        json={"status": "healthy"},
    )

    async with AsyncTokenBowlClient(
        api_key="test-key-123", base_url="http://test.example.com"
    ) as client:
        health = await client.health_check()
        assert health["status"] == "healthy"


@pytest.mark.asyncio
async def test_no_auth_error(async_client: AsyncTokenBowlClient) -> None:
    """Test error when authentication required but not provided."""
    async_client.api_key = None  # Clear API key to test authentication error
    with pytest.raises(AuthenticationError, match="API key required"):
        await async_client.send_message("Hello!")


@pytest.mark.asyncio
async def test_register_with_logo(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test async registration with logo."""
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

    response = await async_client.register(username="alice", logo="claude-color.png")

    assert response.username == "alice"
    assert response.logo == "claude-color.png"


@pytest.mark.asyncio
async def test_get_available_logos(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test getting available logos asynchronously."""
    async_client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/logos",
        json=["claude-color.png", "openai.png"],
    )

    logos = await async_client.get_available_logos()

    assert len(logos) == 2
    assert "claude-color.png" in logos


@pytest.mark.asyncio
async def test_update_logo(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test updating user logo asynchronously."""
    async_client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="PATCH",
        url="http://test.example.com/users/me/logo",
        json={"message": "Logo updated", "logo": "openai.png"},
    )

    result = await async_client.update_my_logo(logo="openai.png")

    assert result["logo"] == "openai.png"


@pytest.mark.asyncio
async def test_get_direct_messages(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test getting direct messages asynchronously."""
    async_client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/messages/direct?limit=50&offset=0",
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

    response = await async_client.get_direct_messages()

    assert len(response.messages) == 0


@pytest.mark.asyncio
async def test_get_online_users(
    httpx_mock: HTTPXMock, async_client: AsyncTokenBowlClient
) -> None:
    """Test getting online users asynchronously."""
    async_client.api_key = "test-key-123"
    httpx_mock.add_response(
        method="GET",
        url="http://test.example.com/users/online",
        json=[
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "alice",
                "role": "member",
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

    users = await async_client.get_online_users()

    assert len(users) == 2
    assert users[0].username == "alice"
    assert users[1].username == "bob"
