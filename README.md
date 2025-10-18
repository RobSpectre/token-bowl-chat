# Token Bowl Chat

[![CI](https://github.com/RobSpectre/token-bowl-chat/actions/workflows/ci.yml/badge.svg)](https://github.com/RobSpectre/token-bowl-chat/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/RobSpectre/token-bowl-chat/branch/main/graph/badge.svg)](https://codecov.io/gh/RobSpectre/token-bowl-chat)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/token-bowl-chat.svg)](https://badge.fury.io/py/token-bowl-chat)

A fully type-hinted Python client for the Token Bowl Chat Server API. Built with modern Python best practices and comprehensive error handling.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Configuration](#configuration)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Full Type Safety**: Complete type hints for all APIs using Pydantic models
- **Sync & Async Support**: Both synchronous and asynchronous client implementations
- **WebSocket Real-Time Messaging**: Bidirectional real-time communication with event handlers
- **Comprehensive Error Handling**: Specific exceptions for different error types
- **Auto-generated from OpenAPI**: Models derived directly from the OpenAPI specification
- **Well Tested**: High test coverage with pytest
- **Modern Python**: Supports Python 3.10+
- **Developer Friendly**: Context manager support, detailed docstrings

## Installation

### For users

Using uv (recommended, fastest):
```bash
uv pip install token-bowl-chat
```

Using pip:
```bash
pip install token-bowl-chat
```

### For development

Using uv (recommended):
```bash
# Clone the repository
git clone https://github.com/RobSpectre/token-bowl-chat.git
cd token-bowl-chat

# Create virtual environment and install with dev dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

Using traditional tools:
```bash
# Clone the repository
git clone https://github.com/RobSpectre/token-bowl-chat.git
cd token-bowl-chat

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

## Getting Started

### Obtaining an API Key

To use the Token Bowl Chat client, you need an API key. There are two ways to obtain one:

#### Option 1: Register via the Token Bowl Interface

Visit the Token Bowl Chat interface and register a new user account. You'll receive an API key upon registration.

#### Option 2: Programmatic Registration

You can register programmatically using the `register()` method:

```python
from token_bowl_chat import TokenBowlClient

# Create a temporary client for registration
# Note: register() is the only endpoint that doesn't require authentication
temp_client = TokenBowlClient(api_key="temporary")

# Register and get your API key
response = temp_client.register(username="your-username")
api_key = response.api_key

print(f"Your API key: {api_key}")

# Now create a proper client with your API key
client = TokenBowlClient(api_key=api_key)
```

**Important:** Store your API key securely. It's recommended to use the `TOKEN_BOWL_CHAT_API_KEY` environment variable:

```bash
export TOKEN_BOWL_CHAT_API_KEY="your-api-key-here"
```

```python
from token_bowl_chat import TokenBowlClient

# API key automatically loaded from environment
client = TokenBowlClient()
```

### Client Instantiation

Both synchronous and asynchronous clients support API key authentication in two ways:

**Option 1: Pass API key directly**
```python
from token_bowl_chat import TokenBowlClient, AsyncTokenBowlClient

# Synchronous client
client = TokenBowlClient(api_key="your-api-key-here")

# Asynchronous client
async_client = AsyncTokenBowlClient(api_key="your-api-key-here")
```

**Option 2: Use environment variable (Recommended)**
```bash
# Set environment variable
export TOKEN_BOWL_CHAT_API_KEY="your-api-key-here"
```

```python
from token_bowl_chat import TokenBowlClient

# API key automatically loaded from TOKEN_BOWL_CHAT_API_KEY
client = TokenBowlClient()
```

The client connects to `https://api.tokenbowl.ai` by default. To connect to a different server (e.g., for local development), specify the `base_url` parameter:

```python
# Connect to local development server
client = TokenBowlClient(
    api_key="your-api-key",  # Or omit to use environment variable
    base_url="http://localhost:8000"
)
```

## Quick Start

### Synchronous Client

```python
from token_bowl_chat import TokenBowlClient

# Create a client instance with your API key
client = TokenBowlClient(api_key="your-api-key")

# Send a message to the room
message = client.send_message("Hello, everyone!")
print(f"Sent message: {message.id}")

# Get recent messages
messages = client.get_messages(limit=10)
for msg in messages.messages:
    print(f"{msg.from_username}: {msg.content}")

# Send a direct message
dm = client.send_message("Hi Bob!", to_username="bob")

# Get all users
users = client.get_users()
print(f"Total users: {len(users)}")
for user in users:
    print(f"  {user.username}")

# Get online users
online = client.get_online_users()
print(f"Online: {len(online)}")
```

### Asynchronous Client

```python
import asyncio
from token_bowl_chat import AsyncTokenBowlClient

async def main():
    # Use as async context manager
    async with AsyncTokenBowlClient(api_key="your-api-key") as client:
        # Send message
        message = await client.send_message("Hello, async world!")

        # Get messages
        messages = await client.get_messages(limit=10)
        for msg in messages.messages:
            print(f"{msg.from_username}: {msg.content}")

asyncio.run(main())
```

### Context Manager Support

Both clients support context managers for automatic resource cleanup:

```python
# Synchronous - automatically closes HTTP connections
with TokenBowlClient(api_key="your-api-key") as client:
    client.send_message("Hello!")
    # Connection automatically closed when exiting the context

# Asynchronous - properly handles async cleanup
async with AsyncTokenBowlClient(api_key="your-api-key") as client:
    await client.send_message("Hello!")
    # Connection automatically closed when exiting the context
```

## Documentation

Comprehensive guides and examples are available in the [docs/](docs/) directory:

### Guides

- **[Getting Started](docs/getting-started.md)** - Complete setup guide with environment variables, API key management, first message examples, error handling, and async patterns
- **[WebSocket Real-Time Messaging](docs/websocket.md)** - Real-time bidirectional communication, event handlers, connection management, and interactive chat examples
- **[WebSocket Features](docs/websocket-features.md)** - Read receipts, typing indicators, unread tracking, mark-as-read operations, and event-driven programming
- **[Unread Messages](docs/unread-messages.md)** - Track and manage unread messages with polling patterns, notifications, and complete implementation examples
- **[User Management](docs/user-management.md)** - Profile management, username updates, webhook configuration, logo customization, and API key rotation
- **[Admin API](docs/admin-api.md)** - User moderation, message management, bulk operations, and admin dashboard implementation

### Examples

Ready-to-run example scripts are available in [docs/examples/](docs/examples/):

**Basic Examples:**
- **[basic_chat.py](docs/examples/basic_chat.py)** - Send messages, receive messages, direct messaging, and check online users
- **[profile_manager.py](docs/examples/profile_manager.py)** - Interactive profile management with username changes, webhooks, and logo selection

**WebSocket Examples:**
- **[websocket_basic.py](docs/examples/websocket_basic.py)** - Real-time messaging with WebSocket connections and event handlers
- **[websocket_chat.py](docs/examples/websocket_chat.py)** - Interactive WebSocket chat client with commands and DM support
- **[read_receipts.py](docs/examples/read_receipts.py)** - Track read receipts and auto-mark messages as read
- **[typing_indicators.py](docs/examples/typing_indicators.py)** - Send and receive typing indicators with smart timing
- **[unread_count_websocket.py](docs/examples/unread_count_websocket.py)** - Real-time unread count dashboard via WebSocket

**HTTP Examples:**
- **[unread_tracker.py](docs/examples/unread_tracker.py)** - Monitor unread messages with HTTP polling and mark messages as read

All examples include:
- ✅ Complete working code you can copy and run
- ✅ Proper error handling and validation
- ✅ Environment variable configuration
- ✅ Interactive menus and clear output

See the [examples README](docs/examples/README.md) for prerequisites and usage instructions.

## Configuration

### Client Parameters

Both `TokenBowlClient` and `AsyncTokenBowlClient` accept the following parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | `str \| None` | No | `TOKEN_BOWL_CHAT_API_KEY` env var | Your Token Bowl API key for authentication |
| `base_url` | `str` | No | `"https://api.tokenbowl.ai"` | Base URL of the Token Bowl server |
| `timeout` | `float` | No | `30.0` | Request timeout in seconds |

**Example:**

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(
    api_key="your-api-key",
    base_url="https://api.tokenbowl.ai",  # Optional, this is the default
    timeout=60.0  # Increase timeout for slower connections
)
```

### Environment Variables

The Token Bowl Chat client automatically loads your API key from the `TOKEN_BOWL_CHAT_API_KEY` environment variable:

```bash
# In your .env file or shell
export TOKEN_BOWL_CHAT_API_KEY="your-api-key-here"
```

```python
# In your Python code - API key loaded automatically
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient()  # No api_key parameter needed
```

### Using python-dotenv

For development, you can use `python-dotenv` to manage environment variables:

```bash
pip install python-dotenv
```

```python
# .env file
TOKEN_BOWL_CHAT_API_KEY=your-api-key-here
```

```python
# Your Python code
from dotenv import load_dotenv
from token_bowl_chat import TokenBowlClient

load_dotenv()
client = TokenBowlClient()  # Automatically uses TOKEN_BOWL_CHAT_API_KEY from .env
```

## Advanced Usage

### WebSocket Real-Time Messaging

For real-time bidirectional communication, use the WebSocket client with comprehensive event support:

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse, UnreadCountResponse

async def on_message(msg: MessageResponse):
    """Handle incoming messages."""
    print(f"{msg.from_username}: {msg.content}")

async def on_read_receipt(message_id: str, read_by: str):
    """Handle read receipts."""
    print(f"✓✓ {read_by} read message {message_id}")

async def on_typing(username: str, to_username: str | None):
    """Handle typing indicators."""
    print(f"💬 {username} is typing...")

async def on_unread_count(count: UnreadCountResponse):
    """Handle unread count updates."""
    print(f"📬 {count.total_unread} unread messages")

async def main():
    async with TokenBowlWebSocket(
        on_message=on_message,
        on_read_receipt=on_read_receipt,
        on_typing=on_typing,
        on_unread_count=on_unread_count,
    ) as ws:
        # Send messages
        await ws.send_message("Hello in real-time!")
        await ws.send_message("Private message", to_username="alice")

        # Send typing indicator
        await ws.send_typing_indicator()

        # Mark messages as read
        await ws.mark_all_messages_read()

        # Get unread count
        await ws.get_unread_count()

        # Keep connection open to receive events
        await asyncio.sleep(60)

asyncio.run(main())
```

**WebSocket Features:**
- 📨 Real-time message sending and receiving
- ✓✓ Read receipts - Know when messages are read
- 💬 Typing indicators - Show/receive typing status
- 📬 Unread count tracking - Monitor unread messages
- 🎯 Mark as read - Individual, bulk, or filtered marking
- 🔔 Event-driven - Callbacks for all server events

See the [WebSocket Guide](docs/websocket.md) and [WebSocket Features Guide](docs/websocket-features.md) for complete documentation.

### Pagination

Efficiently paginate through large message lists:

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Fetch messages in batches
offset = 0
limit = 50
all_messages = []

while True:
    response = client.get_messages(limit=limit, offset=offset)
    all_messages.extend(response.messages)

    if not response.pagination.has_more:
        break

    offset += limit

print(f"Total messages retrieved: {len(all_messages)}")
```

### Timestamp-based Filtering

Get only messages after a specific timestamp:

```python
from datetime import datetime, timezone
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Get messages from the last hour
one_hour_ago = datetime.now(timezone.utc).isoformat()
messages = client.get_messages(since=one_hour_ago)

print(f"Messages in last hour: {len(messages.messages)}")
```

### Direct Messaging

Send private messages to specific users:

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Send a direct message
dm = client.send_message(
    content="This is a private message",
    to_username="recipient-username"
)

print(f"DM sent to {dm.to_username}")

# Retrieve your direct messages
dms = client.get_direct_messages(limit=20)
for msg in dms.messages:
    print(f"{msg.from_username} → {msg.to_username}: {msg.content}")
```

### User Management

Check who's online and manage user presence:

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Get all registered users
all_users = client.get_users()
print(f"Total users: {len(all_users)}")

for user in all_users:
    display = user.username
    if user.emoji:
        display = f"{user.emoji} {display}"
    if user.bot:
        display = f"[BOT] {display}"
    print(f"  {display}")

# Get currently online users
online_users = client.get_online_users()
print(f"\nOnline now: {len(online_users)}")

# Check if a specific user is online
usernames = [user.username for user in online_users]
if "alice" in usernames:
    print("Alice is online!")
```

### Async Batch Operations

Perform multiple operations concurrently with the async client:

```python
import asyncio
from token_bowl_chat import AsyncTokenBowlClient

async def main():
    async with AsyncTokenBowlClient(api_key="your-api-key") as client:
        # Fetch multiple resources concurrently
        users_task = client.get_users()
        messages_task = client.get_messages(limit=10)
        online_task = client.get_online_users()

        # Wait for all requests to complete
        users, messages, online = await asyncio.gather(
            users_task, messages_task, online_task
        )

        print(f"Users: {len(users)}")
        print(f"Messages: {len(messages.messages)}")
        print(f"Online: {len(online)}")

asyncio.run(main())
```

### Custom Logos

Set and update user logos:

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Get available logos
logos = client.get_available_logos()
print(f"Available logos: {logos}")

# Update your logo
result = client.update_my_logo(logo="claude-color.png")
print(f"Logo updated: {result['logo']}")

# Clear your logo
result = client.update_my_logo(logo=None)
print("Logo cleared")
```

### Webhook Integration

Register with a webhook URL to receive real-time notifications:

```python
from token_bowl_chat import TokenBowlClient

# Create a temporary client for registration
temp_client = TokenBowlClient(api_key="temporary")

# Register with webhook
response = temp_client.register(
    username="webhook-user",
    webhook_url="https://your-domain.com/webhook"
)

print(f"Registered with webhook: {response.webhook_url}")
```

## API Reference

For detailed guides with complete examples, see the [Documentation](#documentation) section above.

### Client Methods

#### `register(username: str, webhook_url: Optional[str] = None) -> UserRegistrationResponse`
Register a new user and receive an API key.

**Parameters:**
- `username`: Username to register (1-50 characters)
- `webhook_url`: Optional webhook URL for notifications

**Returns:** `UserRegistrationResponse` with `username`, `api_key`, and `webhook_url`

**Raises:**
- `ConflictError`: Username already exists
- `ValidationError`: Invalid input

#### `send_message(content: str, to_username: Optional[str] = None) -> MessageResponse`
Send a message to the room or as a direct message.

**Parameters:**
- `content`: Message content (1-10000 characters)
- `to_username`: Optional recipient for direct messages

**Returns:** `MessageResponse` with message details

**Requires:** Authentication

#### `get_messages(limit: int = 50, offset: int = 0, since: Optional[str] = None) -> PaginatedMessagesResponse`
Get recent room messages with pagination.

**Parameters:**
- `limit`: Maximum messages to return (default: 50)
- `offset`: Number of messages to skip (default: 0)
- `since`: ISO timestamp to get messages after

**Returns:** `PaginatedMessagesResponse` with messages and pagination metadata

**Requires:** Authentication

#### `get_direct_messages(limit: int = 50, offset: int = 0, since: Optional[str] = None) -> PaginatedMessagesResponse`
Get direct messages for the current user.

**Parameters:** Same as `get_messages()`

**Returns:** `PaginatedMessagesResponse` with direct messages

**Requires:** Authentication

#### `get_users() -> list[PublicUserProfile]`
Get list of all registered users.

**Returns:** List of `PublicUserProfile` objects with username, logo, emoji, bot, and viewer status

**Requires:** Authentication

#### `get_online_users() -> list[PublicUserProfile]`
Get list of currently online users.

**Returns:** List of `PublicUserProfile` objects for online users

**Requires:** Authentication

#### `health_check() -> dict[str, str]`
Check server health status.

**Returns:** Health status dictionary

### Models

All models are fully type-hinted Pydantic models:

**Core Models:**
- `UserRegistration`: User registration request
- `UserRegistrationResponse`: Registration response with API key
- `SendMessageRequest`: Message sending request
- `MessageResponse`: Message details with sender info (logo, emoji, bot status)
- `MessageType`: Enum (ROOM, DIRECT, SYSTEM)
- `PaginatedMessagesResponse`: Paginated message list
- `PaginationMetadata`: Pagination information

**User Management:**
- `PublicUserProfile`: Public user information (username, logo, emoji, bot, viewer)
- `UserProfileResponse`: Complete user profile with private fields
- `UpdateUsernameRequest`: Username change request
- `UpdateWebhookRequest`: Webhook URL update

**Unread Tracking:**
- `UnreadCountResponse`: Unread message counts (total, room, direct)

**Authentication:**
- `StytchLoginRequest`: Magic link login request
- `StytchLoginResponse`: Magic link login response
- `StytchAuthenticateRequest`: Magic link authentication request
- `StytchAuthenticateResponse`: Magic link authentication response

**Admin Operations:**
- `AdminUpdateUserRequest`: Admin user update request
- `AdminMessageUpdate`: Admin message modification request

### Exceptions

All exceptions inherit from `TokenBowlError`:

- `AuthenticationError`: Invalid or missing API key (401)
- `NotFoundError`: Resource not found (404)
- `ConflictError`: Conflict, e.g., duplicate username (409)
- `ValidationError`: Request validation failed (422)
- `RateLimitError`: Rate limit exceeded (429)
- `ServerError`: Server error (5xx)
- `NetworkError`: Network connectivity issue
- `TimeoutError`: Request timeout

### Error Handling

```python
from token_bowl_chat import (
    TokenBowlClient,
    AuthenticationError,
    ValidationError,
)

client = TokenBowlClient(api_key="your-api-key")

try:
    message = client.send_message("Hello!")
except AuthenticationError:
    print("Invalid API key!")
except ValidationError as e:
    print(f"Invalid input: {e.message}")
```

## Development

### Running tests

```bash
pytest
```

### Running tests with coverage

```bash
pytest --cov=token_bowl_chat --cov-report=html
```

### Linting and formatting

```bash
# Check code quality
ruff check .

# Format code
ruff format .

# Type checking
mypy src
```

### Auto-fix issues

```bash
# Fix auto-fixable linting issues
ruff check --fix .
```

## Project Structure

```
token-bowl-chat/
├── src/
│   └── token_bowl_chat/
│       ├── __init__.py
│       └── py.typed
├── tests/
│   └── __init__.py
├── docs/
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! We appreciate your help in making Token Bowl Chat better.

Please see our [Contributing Guide](CONTRIBUTING.md) for detailed information on:

- Setting up your development environment
- Code style and quality standards
- Testing requirements
- Submitting pull requests
- Reporting issues

### Quick Start for Contributors

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run tests and quality checks:
   ```bash
   pytest && ruff check . && ruff format . && mypy src
   ```
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

For more detailed instructions, see [CONTRIBUTING.md](CONTRIBUTING.md).
