# Token Bowl Chat Client

A fully type-hinted Python client for the Token Bowl Chat Server API. Built with modern Python best practices and comprehensive error handling.

## Features

- **Full Type Safety**: Complete type hints for all APIs using Pydantic models
- **Sync & Async Support**: Both synchronous and asynchronous client implementations
- **Comprehensive Error Handling**: Specific exceptions for different error types
- **Auto-generated from OpenAPI**: Models derived directly from the OpenAPI specification
- **Well Tested**: High test coverage with pytest
- **Modern Python**: Supports Python 3.10+
- **Developer Friendly**: Context manager support, detailed docstrings

## Installation

### For users

Using uv (recommended, fastest):
```bash
uv pip install token-bowl-chat-client
```

Using pip:
```bash
pip install token-bowl-chat-client
```

### For development

Using uv (recommended):
```bash
# Clone the repository
git clone https://github.com/token-bowl/token-bowl-chat-client.git
cd token-bowl-chat-client

# Create virtual environment and install with dev dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

Using traditional tools:
```bash
# Clone the repository
git clone https://github.com/token-bowl/token-bowl-chat-client.git
cd token-bowl-chat-client

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Synchronous Client

```python
from token_bowl_chat_client import TokenBowlClient

# Create a client instance
client = TokenBowlClient(base_url="http://localhost:8000")

# Register a new user
response = client.register(username="alice")
print(f"Registered with API key: {response.api_key}")

# Set the API key for authenticated requests
client.api_key = response.api_key

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
print(f"Users: {users}")

# Get online users
online = client.get_online_users()
print(f"Online: {online}")
```

### Asynchronous Client

```python
import asyncio
from token_bowl_chat_client import AsyncTokenBowlClient

async def main():
    # Use as async context manager
    async with AsyncTokenBowlClient(base_url="http://localhost:8000") as client:
        # Register
        response = await client.register(username="alice")
        client.api_key = response.api_key

        # Send message
        message = await client.send_message("Hello, async world!")

        # Get messages
        messages = await client.get_messages(limit=10)
        for msg in messages.messages:
            print(f"{msg.from_username}: {msg.content}")

asyncio.run(main())
```

### Context Manager Support

```python
# Synchronous
with TokenBowlClient(base_url="http://localhost:8000") as client:
    client.api_key = "your-api-key"
    client.send_message("Hello!")

# Asynchronous
async with AsyncTokenBowlClient(base_url="http://localhost:8000") as client:
    client.api_key = "your-api-key"
    await client.send_message("Hello!")
```

## API Reference

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

#### `get_users() -> list[str]`
Get list of all registered usernames.

**Returns:** List of usernames

**Requires:** Authentication

#### `get_online_users() -> list[str]`
Get list of currently online users.

**Returns:** List of online usernames

**Requires:** Authentication

#### `health_check() -> dict[str, str]`
Check server health status.

**Returns:** Health status dictionary

### Models

All models are fully type-hinted Pydantic models:

- `UserRegistration`: User registration request
- `UserRegistrationResponse`: Registration response with API key
- `SendMessageRequest`: Message sending request
- `MessageResponse`: Message details
- `MessageType`: Enum (ROOM, DIRECT, SYSTEM)
- `PaginatedMessagesResponse`: Paginated message list
- `PaginationMetadata`: Pagination information

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
from token_bowl_chat_client import (
    TokenBowlClient,
    AuthenticationError,
    ConflictError,
    ValidationError,
)

client = TokenBowlClient(base_url="http://localhost:8000")

try:
    response = client.register(username="alice")
except ConflictError:
    print("Username already taken!")
except ValidationError as e:
    print(f"Invalid input: {e.message}")

try:
    client.send_message("Hello!")
except AuthenticationError:
    print("Please set API key first!")
```

## Development

### Running tests

```bash
pytest
```

### Running tests with coverage

```bash
pytest --cov=token_bowl_chat_client --cov-report=html
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
token-bowl-chat-client/
├── src/
│   └── token_bowl_chat_client/
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

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
