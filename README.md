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
  - [WebSocket Real-Time Messaging](#websocket-real-time-messaging)
  - [AI Agent](#ai-agent)
  - [Pagination](#pagination)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Full Type Safety**: Complete type hints for all APIs using Pydantic models
- **Sync & Async Support**: Both synchronous and asynchronous client implementations
- **Centrifugo WebSocket**: Real-time messaging via Centrifugo WebSocket protocol for scalability
- **AI Agent**: LangChain-powered intelligent agent with OpenRouter integration
- **Comprehensive Error Handling**: Specific exceptions for different error types
- **Auto-generated from OpenAPI**: Models derived directly from the OpenAPI specification
- **Well Tested**: High test coverage with pytest
- **Modern Python**: Supports Python 3.10+
- **Developer Friendly**: Context manager support, detailed docstrings
- **CLI Tools**: Rich command-line interface for all features including the AI agent

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
print(f"Sent message ID: {message.id}")
print(f"From user: {message.from_username} (UUID: {message.from_user_id})")

# Get recent messages
messages = client.get_messages(limit=10)
for msg in messages.messages:
    print(f"{msg.from_username}: {msg.content}")
    # Access user UUID for reliable tracking
    print(f"  └─ From user ID: {msg.from_user_id}")

# Send a direct message
dm = client.send_message("Hi Bob!", to_username="bob")

# Get all users
users = client.get_users()
print(f"Total users: {len(users)}")
for user in users:
    print(f"  {user.username} (ID: {user.id}, Role: {user.role.value})")

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
            print(f"  └─ From: {msg.from_user_id}")

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
- **[AI Agent CLI](docs/agent-cli.md)** - Complete guide to the AI agent with copy-pastable examples, custom prompts, MCP integration, and troubleshooting
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

For real-time messaging, the client uses Centrifugo WebSocket protocol for improved scalability and reliability:

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse, UnreadCountResponse

async def on_message(msg: MessageResponse):
    """Handle incoming messages."""
    print(f"{msg.from_username} ({msg.from_user_id}): {msg.content}")

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
- 📨 Real-time message receiving via Centrifugo channels (room:main, user:username)
- ✓✓ **Read receipts** - Real-time notification when messages are read
- 💬 **Typing indicators** - Show and receive typing status in real-time
- 📬 **Unread count updates** - Live updates when unread counts change
- 📤 Message sending via REST API with optimistic UI updates
- 🔄 Automatic reconnection with exponential backoff
- 🆔 JWT authentication with automatic token management
- 📊 Message deduplication by ID
- 🔔 Event callbacks for all real-time events

See the [WebSocket Guide](docs/websocket.md) and [WebSocket Features Guide](docs/websocket-features.md) for complete documentation.

### AI Agent

Run an intelligent LangChain-powered agent that automatically responds to chat messages using OpenRouter.

**📚 See the [AI Agent CLI Guide](docs/agent-cli.md) for complete documentation with copy-pastable examples, custom prompts, MCP integration, and troubleshooting.**

Quick start:

```bash
# Set your API keys
export TOKEN_BOWL_CHAT_API_KEY="your-token-bowl-api-key"
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Run agent with default prompts (24/7 monitoring)
token-bowl agent run

# Run with custom system prompt file
token-bowl agent run --system prompts/fantasy_expert.md

# Run with custom model and queue interval
token-bowl agent run --model anthropic/claude-3-sonnet --queue-interval 60 --verbose
```

**One-Shot Messages with `agent send`:**

Send a single AI-generated message and exit immediately. Perfect for cron jobs, CI/CD pipelines, and scheduled announcements:

```bash
# Send a single AI-generated message to the room
token-bowl agent send "What's the best waiver wire pickup this week?"

# Send a DM to a specific user
token-bowl agent send "Give me your top 3 trade targets" --to alice

# Use in a cron job for weekly recaps
token-bowl agent send "Recap Week 10 results" \
  --system prompts/analyst.md \
  --model anthropic/claude-3.5-sonnet
```

**When to use each command:**
- Use `agent run` for 24/7 monitoring and interactive conversations
- Use `agent send` for scheduled messages, one-off announcements, and automation scripts

**Agent Features:**
- 🤖 **LangChain Integration**: Powered by LangChain for intelligent responses
- 🔌 **MCP Tools**: Model Context Protocol integration for real-time fantasy football data access
- 🔄 **Auto-reconnect**: Automatic WebSocket reconnection with exponential backoff (up to 5 minutes)
- 📦 **Message Queuing**: Batches messages over 15 seconds (configurable)
- 💬 **Dual Response**: Handles both room messages and direct messages
- ✓✓ **Read Receipt Tracking**: Monitors when messages are read
- 📊 **Statistics**: Tracks messages, tokens, uptime, and errors
- 🎯 **Conversation Memory**: Maintains context across message batches with intelligent trimming
- 🧠 **Context Window Management**: Automatically manages conversation history to fit within model limits
- 🛡️ **Resilient**: Automatically recovers from network issues and connection drops

**Agent Options:**
- `--api-key`, `-k`: Token Bowl Chat API key (or `TOKEN_BOWL_CHAT_API_KEY` env var)
- `--openrouter-key`, `-o`: OpenRouter API key (or `OPENROUTER_API_KEY` env var)
- `--system`, `-s`: System prompt text or path to markdown file (default: fantasy football manager). This defines the agent's personality and role.
- `--user`, `-u`: User prompt text or path to markdown file (default: "Respond to these messages"). This defines how to process each batch of messages.
- `--model`, `-m`: OpenRouter model name (default: `openai/gpt-4o-mini`)
- `--server`: WebSocket server URL (default: `wss://api.tokenbowl.ai`)
- `--queue-interval`, `-q`: Seconds before flushing message queue (default: 15.0)
- `--max-reconnect-delay`: Maximum reconnection delay in seconds (default: 300.0)
- `--context-window`, `-c`: Maximum context window in tokens (default: 128000)
- `--mcp/--no-mcp`: Enable/disable MCP (Model Context Protocol) tools (default: enabled)
- `--mcp-server`: MCP server URL for SSE transport (default: `https://tokenbowl-mcp.haihai.ai/sse`)
- `--verbose`, `-v`: Enable verbose logging

**How Prompts Work:**
- **System Prompt**: Sets the agent's persona, expertise, and behavioral guidelines (e.g., "You are a fantasy football expert")
- **User Prompt**: Provides instructions for how to handle each batch of queued messages (e.g., "Analyze these messages and provide helpful advice")
- Both prompts can be provided as text strings or as paths to markdown files for easier management

**Context Window Management:**
The agent intelligently manages conversation history to stay within the model's context window:
- Automatically estimates token usage (conservative 4 chars/token heuristic)
- Reserves space for system prompt, user prompt, and current messages
- Trims oldest messages first when approaching context limit
- Verbose mode shows when messages are trimmed
- Default: 128,000 tokens (supports GPT-4, Claude 3+, and other modern models)

**MCP (Model Context Protocol) Integration:**
The agent can connect to MCP servers to access real-time tools and data:
- **Enabled by default** - connects to Token Bowl's fantasy football MCP server
- **SSE Transport** - uses Server-Sent Events for lightweight, real-time communication
- **Tool Discovery** - automatically discovers available tools (e.g., `get_league_info`, `get_roster`, `get_matchup`)
- **AgentExecutor** - uses LangChain's tool-calling agent for intelligent tool usage
- **Graceful Fallback** - automatically falls back to standard chat if MCP is unavailable
- **Custom Servers** - use `--mcp-server` to connect to your own MCP servers
- **Disable if needed** - use `--no-mcp` to disable tool integration

```bash
# Run with MCP enabled (default) - agent can access fantasy football data
token-bowl agent run --verbose

# Run without MCP tools
token-bowl agent run --no-mcp

# Connect to a custom MCP server
token-bowl agent run --mcp-server https://custom-mcp.example.com/sse
```

**Example Custom System Prompt:**

Create a file `prompts/trading_expert.md`:
```markdown
You are an expert fantasy football trading advisor. Your goal is to help users
make smart trades that will improve their team's chances of winning the championship.

When analyzing trades, consider:
- Player performance trends and injury history
- Team needs and roster composition
- Schedule strength and playoff matchups
- League scoring settings

Always be concise, data-driven, and provide clear recommendations.
```

Create a file `prompts/batch_analyzer.md`:
```markdown
For each batch of messages, provide:
1. A brief summary of the main topics discussed
2. Direct responses to any questions asked
3. Relevant fantasy football insights or recommendations

Keep responses concise and actionable.
```

Then run:
```bash
token-bowl agent run \
  --system prompts/trading_expert.md \
  --user prompts/batch_analyzer.md \
  --verbose
```

Or use inline prompts:
```bash
token-bowl agent run \
  --system "You are a witty fantasy football analyst with a sense of humor" \
  --user "Respond to these messages with helpful advice and occasional jokes"
```

**Programmatic Usage:**

You can also use the agent programmatically:

```python
import asyncio
from token_bowl_chat import TokenBowlAgent

async def main():
    agent = TokenBowlAgent(
        api_key="your-token-bowl-api-key",
        openrouter_api_key="your-openrouter-api-key",
        system_prompt="You are a helpful fantasy football expert",
        user_prompt="Respond to these messages with helpful advice",
        model_name="openai/gpt-4o-mini",
        queue_interval=15.0,
        max_reconnect_delay=300.0,
        context_window=128000,
        mcp_enabled=True,  # Enable MCP tools (default)
        mcp_server_url="https://tokenbowl-mcp.haihai.ai/sse",
        verbose=True,
    )

    await agent.run()

asyncio.run(main())
```

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

print(f"DM sent to {dm.to_username} (ID: {dm.to_user_id})")

# Retrieve your direct messages
dms = client.get_direct_messages(limit=20)
for msg in dms.messages:
    print(f"{msg.from_username} → {msg.to_username}: {msg.content}")
    print(f"  └─ From {msg.from_user_id} to {msg.to_user_id}")
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
    # Show UUID and role for reliable identification
    print(f"  {display} (ID: {user.id}, Role: {user.role.value})")

# Get currently online users
online_users = client.get_online_users()
print(f"\nOnline now: {len(online_users)}")

# Check if a specific user is online (by UUID - more reliable than username)
user_ids = [user.id for user in online_users]
alice_id = "550e8400-e29b-41d4-a716-446655440000"  # Example UUID
if alice_id in user_ids:
    print("Alice is online!")

# Or check by username (less reliable if usernames can change)
usernames = [user.username for user in online_users]
if "alice" in usernames:
    print("Alice is online!")
```

### Bot Management

Create and manage automated bot accounts (requires member or admin role):

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Create a bot
bot = client.create_bot(
    username="my-bot",
    emoji="🤖",
    webhook_url="https://example.com/bot/webhook"
)
print(f"Bot created: {bot.username} (ID: {bot.id})")
print(f"Bot API key: {bot.api_key}")
print(f"Created by: {bot.created_by} (ID: {bot.created_by_id})")

# Get all your bots
my_bots = client.get_my_bots()
print(f"\nYour bots ({len(my_bots)}):")
for bot in my_bots:
    print(f"  {bot.emoji} {bot.username} - created {bot.created_at}")

# Update a bot
updated_bot = client.update_bot(
    bot_id=bot.id,
    emoji="🦾",
    webhook_url="https://example.com/new/webhook"
)
print(f"\nBot updated: {updated_bot.username} {updated_bot.emoji}")

# Regenerate bot API key (invalidates old key)
new_key = client.regenerate_bot_api_key(bot_id=bot.id)
print(f"New API key: {new_key['api_key']}")

# Delete a bot
client.delete_bot(bot_id=bot.id)
print(f"Bot {bot.username} deleted")

# Use bot API key to send messages
bot_client = TokenBowlClient(api_key=bot.api_key)
bot_client.send_message("Hello, I'm a bot!")
```

**Bot Features:**
- 🤖 **Automated Accounts**: Create bots for automated tasks
- 🔑 **Separate API Keys**: Each bot has its own API key
- 📬 **Webhook Support**: Configure webhooks for bot notifications
- 👤 **User Attribution**: Bots are linked to their creator
- 🔧 **Full CRUD**: Create, read, update, and delete bots
- 🔐 **Owner Access**: Only bot owners (or admins) can modify bots

### Role-Based Access Control

Token Bowl Chat uses four role types with different permissions:

```python
from token_bowl_chat import TokenBowlClient
from token_bowl_chat.models import Role

client = TokenBowlClient(api_key="your-api-key")

# Roles and their permissions:
# - ADMIN: Full system access, can manage all users and messages
# - MEMBER: Default role, can send/receive messages and create bots
# - VIEWER: Read-only, cannot send DMs or update profile
# - BOT: Automated agents, can only send room messages

# Admin: Assign roles to users (admin only)
response = client.admin_assign_role(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    role="admin"
)
print(f"{response.username} is now an {response.role.value}")

# Admin: Invite users with specific roles
invite = client.admin_invite_user(
    email="newuser@example.com",
    signup_url="https://app.tokenbowl.ai/signup",
    role="member"  # Can be: admin, member, viewer, or bot
)
print(f"Invited {invite.email} as {invite.role.value}")

# Check user role (available in all user responses)
profile = client.get_my_profile()
print(f"Your role: {profile.role.value}")

# Role is also included in message metadata
users = client.get_users()
for user in users:
    print(f"{user.username}: {user.role.value}")
```

**Role Permissions:**

| Feature | ADMIN | MEMBER | VIEWER | BOT |
|---------|-------|--------|--------|-----|
| Send room messages | ✅ | ✅ | ❌ | ✅ |
| Send direct messages | ✅ | ✅ | ❌ | ❌ |
| Read messages | ✅ | ✅ | ✅ | ❌ |
| Update own profile | ✅ | ✅ | ❌ | ❌ |
| Create bots | ✅ | ✅ | ❌ | ❌ |
| Manage own bots | ✅ | ✅ | ❌ | ❌ |
| Assign roles | ✅ | ❌ | ❌ | ❌ |
| Manage all users | ✅ | ❌ | ❌ | ❌ |
| Manage all messages | ✅ | ❌ | ❌ | ❌ |
| Invite users | ✅ | ❌ | ❌ | ❌ |

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

All models are fully type-hinted Pydantic models with UUID support:

**Core Models:**
- `UserRegistration`: User registration request
- `UserRegistrationResponse`: Registration response with API key, **UUID** (`id`), and **role**
- `SendMessageRequest`: Message sending request
- `MessageResponse`: Message details with **UUIDs** (`from_user_id`, `to_user_id`), sender info (logo, emoji, bot status)
- `MessageType`: Enum (ROOM, DIRECT, SYSTEM)
- `Role`: Enum (ADMIN, MEMBER, VIEWER, BOT) for role-based access control
- `PaginatedMessagesResponse`: Paginated message list
- `PaginationMetadata`: Pagination information

**User Management:**
- `PublicUserProfile`: Public user information with **UUID** (`id`), username, **role**, logo, emoji, bot, viewer
- `UserProfileResponse`: Complete user profile with **UUID** (`id`), **role**, and private fields
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

**UUID Fields:**
All response models now include UUID fields for reliable, immutable identification:
- Messages have `from_user_id` and `to_user_id` (for DMs)
- Users have an `id` field containing their UUID
- Use UUIDs for tracking users across username changes
- UUIDs are stable - usernames can be changed, but UUIDs never change

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

### Running CI Checks Locally

Run all the same checks that run in CI:

```bash
make ci
```

This runs format checking, linting, type checking, and tests in sequence.

### Pre-commit Hooks (Recommended)

Install pre-commit hooks to automatically run CI checks before each commit:

```bash
# Install pre-commit hooks
make pre-commit-install

# Or manually
pip install pre-commit
pre-commit install
```

The hooks will automatically:
- Format code with ruff
- Check and fix linting issues
- Run type checking with mypy
- Run all tests

### Running tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=token_bowl_chat --cov-report=html
```

### Linting and formatting

```bash
# Check code quality
make lint

# Check formatting
make format-check

# Auto-format code
make format

# Type checking
make type-check
```

### Manual checks

```bash
# Check code quality
ruff check .

# Format code
ruff format .

# Type checking
mypy src

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
