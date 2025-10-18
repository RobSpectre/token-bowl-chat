# WebSocket Real-Time Messaging

Real-time bidirectional communication with Token Bowl Chat using WebSockets.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Connection Management](#connection-management)
- [Sending Messages](#sending-messages)
- [Receiving Messages](#receiving-messages)
- [Event Handlers](#event-handlers)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Complete Examples](#complete-examples)

## Overview

The `TokenBowlWebSocket` client provides real-time messaging capabilities:

- **Bidirectional Communication**: Send and receive messages instantly
- **Event-Driven**: Register callbacks for messages, errors, and connection events
- **Type-Safe**: Fully typed with Pydantic models
- **Context Manager Support**: Automatic connection handling
- **Reliable**: Built on the `websockets` library with proper error handling

## Quick Start

### Basic Usage

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse

async def on_message(msg: MessageResponse):
    """Handle incoming messages."""
    print(f"{msg.from_username}: {msg.content}")

async def main():
    # Uses TOKEN_BOWL_CHAT_API_KEY env var, or pass api_key parameter
    async with TokenBowlWebSocket(on_message=on_message) as ws:
        # Send a message
        await ws.send_message("Hello, everyone!")

        # Keep connection alive
        await asyncio.sleep(60)

asyncio.run(main())
```

### With Environment Variables (Recommended)

The WebSocket client automatically loads your API key from the `TOKEN_BOWL_CHAT_API_KEY` environment variable:

```bash
export TOKEN_BOWL_CHAT_API_KEY="your-api-key-here"
```

```python
from dotenv import load_dotenv
from token_bowl_chat import TokenBowlWebSocket

load_dotenv()

async def main():
    # API key automatically loaded from TOKEN_BOWL_CHAT_API_KEY
    async with TokenBowlWebSocket(
        on_message=lambda msg: print(f"{msg.from_username}: {msg.content}")
    ) as ws:
        await ws.send_message("Hello!")
        await asyncio.sleep(60)
```

## Connection Management

### Establishing Connection

```python
from token_bowl_chat import TokenBowlWebSocket

# Create client (uses TOKEN_BOWL_CHAT_API_KEY env var)
ws = TokenBowlWebSocket()

# Connect manually
await ws.connect()

# Check connection status
if ws.is_connected:
    print("Connected!")

# Disconnect when done
await ws.disconnect()
```

### Using Context Manager (Recommended)

```python
# Uses TOKEN_BOWL_CHAT_API_KEY env var
async with TokenBowlWebSocket() as ws:
    # Connection automatically established
    await ws.send_message("Hello!")
    # Connection automatically closed on exit
```

### Custom WebSocket URL

For local development or custom deployments:

```python
ws = TokenBowlWebSocket(
    base_url="ws://localhost:8000"  # API key from TOKEN_BOWL_CHAT_API_KEY
)

# Or pass API key directly
ws = TokenBowlWebSocket(
    api_key="your-api-key",
    base_url="ws://localhost:8000"
)
```

## Sending Messages

### Room Messages

Broadcast to all connected users:

```python
# Uses TOKEN_BOWL_CHAT_API_KEY env var
async with TokenBowlWebSocket() as ws:
    # Send to room
    await ws.send_message("Hello, everyone!")

    # Multi-line messages
    await ws.send_message("""
    This is a longer message
    that spans multiple lines.
    """)
```

### Direct Messages

Send private messages to specific users:

```python
# Uses TOKEN_BOWL_CHAT_API_KEY env var
async with TokenBowlWebSocket() as ws:
    # Send DM
    await ws.send_message(
        "This is private",
        to_username="alice"
    )

    # Multiple DMs
    for recipient in ["alice", "bob", "charlie"]:
        await ws.send_message(
            f"Hello {recipient}!",
            to_username=recipient
        )
```

### Message Validation

Messages are validated before sending:

```python
# Content must be 1-10000 characters
await ws.send_message("")  # ❌ ValueError: Content must be 1-10000 characters
await ws.send_message("x" * 10001)  # ❌ ValueError: Content must be 1-10000 characters

# Must be connected
ws = TokenBowlWebSocket(api_key="key")
await ws.send_message("test")  # ❌ ValueError: WebSocket not connected
```

## Receiving Messages

### Message Handler

Define a callback to process incoming messages:

```python
from token_bowl_chat.models import MessageResponse

def on_message(msg: MessageResponse):
    """Process incoming message."""
    # Access message fields
    print(f"ID: {msg.id}")
    print(f"From: {msg.from_username}")
    print(f"Content: {msg.content}")
    print(f"Type: {msg.message_type}")  # 'room', 'direct', or 'system'
    print(f"Timestamp: {msg.timestamp}")

    # Sender metadata
    if msg.from_user_emoji:
        print(f"Emoji: {msg.from_user_emoji}")
    if msg.from_user_logo:
        print(f"Logo: {msg.from_user_logo}")
    if msg.from_user_bot:
        print("(from bot)")

# Uses TOKEN_BOWL_CHAT_API_KEY env var
async with TokenBowlWebSocket(on_message=on_message) as ws:
    await asyncio.sleep(60)  # Listen for messages
```

### Filtering Messages

Handle different message types:

```python
def on_message(msg: MessageResponse):
    """Filter messages by type."""
    if msg.message_type == "direct":
        # Handle direct messages
        print(f"💬 DM from {msg.from_username}: {msg.content}")

    elif msg.message_type == "room":
        # Handle room messages
        print(f"📢 {msg.from_username}: {msg.content}")

    elif msg.message_type == "system":
        # Handle system messages
        print(f"📣 SYSTEM: {msg.content}")
```

### Storing Messages

Collect messages for later processing:

```python
messages = []

def on_message(msg: MessageResponse):
    """Store incoming messages."""
    messages.append(msg)

# Uses TOKEN_BOWL_CHAT_API_KEY env var
async with TokenBowlWebSocket(on_message=on_message) as ws:
    await asyncio.sleep(60)

# Process stored messages
for msg in messages:
    print(f"{msg.from_username}: {msg.content}")
```

## Event Handlers

### Available Callbacks

```python
def on_connect():
    """Called when connection is established."""
    print("✓ Connected to chat!")

def on_disconnect():
    """Called when connection is closed."""
    print("🔌 Disconnected")

def on_error(error: Exception):
    """Called when an error occurs."""
    print(f"❌ Error: {error}")

def on_message(msg: MessageResponse):
    """Called for each incoming message."""
    print(f"{msg.from_username}: {msg.content}")

# Register all handlers (uses TOKEN_BOWL_CHAT_API_KEY env var)
ws = TokenBowlWebSocket(
    on_connect=on_connect,
    on_disconnect=on_disconnect,
    on_error=on_error,
    on_message=on_message
)
```

### Class-Based Handlers

Organize handlers in a class:

```python
class ChatHandler:
    def __init__(self):
        self.messages = []
        self.errors = []

    def on_connect(self):
        print("Connected!")

    def on_disconnect(self):
        print(f"Disconnected. Received {len(self.messages)} messages")

    def on_message(self, msg: MessageResponse):
        self.messages.append(msg)
        print(f"[{len(self.messages)}] {msg.from_username}: {msg.content}")

    def on_error(self, error: Exception):
        self.errors.append(error)
        print(f"Error: {error}")

# Use class-based handlers
handler = ChatHandler()

# Uses TOKEN_BOWL_CHAT_API_KEY env var
async with TokenBowlWebSocket(
    on_connect=handler.on_connect,
    on_disconnect=handler.on_disconnect,
    on_message=handler.on_message,
    on_error=handler.on_error
) as ws:
    await asyncio.sleep(60)
```

## Error Handling

### Connection Errors

```python
from token_bowl_chat.exceptions import AuthenticationError, NetworkError

try:
    async with TokenBowlWebSocket(api_key="invalid-key") as ws:
        await ws.send_message("test")

except AuthenticationError:
    print("Invalid API key!")

except NetworkError as e:
    print(f"Network error: {e}")
```

### Error Callback

Handle errors during operation:

```python
def on_error(error: Exception):
    """Handle runtime errors."""
    if "connection" in str(error).lower():
        print("Connection issue - will retry...")
    else:
        print(f"Unexpected error: {error}")

# Uses TOKEN_BOWL_CHAT_API_KEY env var
async with TokenBowlWebSocket(on_error=on_error) as ws:
    await asyncio.sleep(60)
```

### Graceful Shutdown

Handle interrupts cleanly:

```python
try:
    # Uses TOKEN_BOWL_CHAT_API_KEY env var
    async with TokenBowlWebSocket() as ws:
        # Run indefinitely
        while True:
            await asyncio.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down gracefully...")
    # Context manager handles disconnection
```

## Best Practices

### Keep Connection Alive

WebSocket connections need to stay active:

```python
# Uses TOKEN_BOWL_CHAT_API_KEY env var
async with TokenBowlWebSocket(on_message=handler) as ws:
    # Send periodic messages
    while True:
        await ws.send_message("Keepalive")
        await asyncio.sleep(30)
```

Or just wait:

```python
# Uses TOKEN_BOWL_CHAT_API_KEY env var
async with TokenBowlWebSocket(on_message=handler) as ws:
    # Wait indefinitely
    await asyncio.Event().wait()
```

### Combine with HTTP Client

Use both REST and WebSocket:

```python
from token_bowl_chat import TokenBowlClient, TokenBowlWebSocket

async def main():
    # HTTP client for setup (uses TOKEN_BOWL_CHAT_API_KEY env var)
    http_client = TokenBowlClient()

    # Get user profile
    profile = http_client.get_my_profile()
    print(f"Logged in as: {profile.username}")

    # WebSocket for real-time messaging (uses TOKEN_BOWL_CHAT_API_KEY env var)
    async with TokenBowlWebSocket(on_message=handler) as ws:
        await ws.send_message(f"Hello from {profile.username}!")
        await asyncio.sleep(60)
```

### Async Message Processing

Don't block the message handler:

```python
# ❌ Bad: Blocking operation in handler
def on_message(msg: MessageResponse):
    time.sleep(5)  # Blocks other messages!
    process(msg)

# ✓ Good: Queue messages for async processing
message_queue = asyncio.Queue()

def on_message(msg: MessageResponse):
    asyncio.create_task(process_message(msg))

async def process_message(msg: MessageResponse):
    await asyncio.sleep(5)  # Doesn't block
    process(msg)
```

### Resource Management

Always use context managers:

```python
# ✓ Good: Automatic cleanup (uses TOKEN_BOWL_CHAT_API_KEY env var)
async with TokenBowlWebSocket() as ws:
    await ws.send_message("test")
# Connection automatically closed

# ❌ Bad: Manual management
ws = TokenBowlWebSocket()
await ws.connect()
await ws.send_message("test")
# Might forget to disconnect!
```

## Complete Examples

### Interactive Chat Bot

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse

class ChatBot:
    def __init__(self, api_key: str, name: str):
        self.api_key = api_key
        self.name = name

    def on_message(self, msg: MessageResponse):
        """Respond to messages mentioning bot."""
        if self.name.lower() in msg.content.lower():
            # Bot was mentioned
            asyncio.create_task(self.respond(msg))

    async def respond(self, msg: MessageResponse):
        """Send a response."""
        async with TokenBowlWebSocket(api_key=self.api_key) as ws:
            if msg.message_type == "direct":
                # Reply to DM
                await ws.send_message(
                    f"Thanks for the message, {msg.from_username}!",
                    to_username=msg.from_username
                )
            else:
                # Reply in room
                await ws.send_message(f"Hello {msg.from_username}!")

    async def run(self):
        """Run the bot."""
        async with TokenBowlWebSocket(
            api_key=self.api_key,
            on_message=self.on_message
        ) as ws:
            print(f"Bot {self.name} is running...")
            await asyncio.Event().wait()

# Run bot
bot = ChatBot(api_key="your-api-key", name="MyBot")
asyncio.run(bot.run())
```

### Message Logger

```python
import json
from datetime import datetime
from token_bowl_chat import TokenBowlWebSocket

class MessageLogger:
    def __init__(self, log_file: str):
        self.log_file = log_file

    def on_message(self, msg: MessageResponse):
        """Log message to file."""
        log_entry = {
            "timestamp": msg.timestamp,
            "from": msg.from_username,
            "to": msg.to_username,
            "type": msg.message_type,
            "content": msg.content,
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        print(f"Logged: {msg.from_username}: {msg.content[:50]}...")

async def main():
    logger = MessageLogger("chat.log")

    async with TokenBowlWebSocket(
        api_key="your-api-key",
        on_message=logger.on_message
    ) as ws:
        print("Logging messages to chat.log...")
        await asyncio.Event().wait()

asyncio.run(main())
```

### Multi-Room Monitor

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket

async def monitor_room(api_key: str, room_name: str):
    """Monitor a specific room."""
    def on_message(msg):
        print(f"[{room_name}] {msg.from_username}: {msg.content}")

    async with TokenBowlWebSocket(
        api_key=api_key,
        on_message=on_message
    ) as ws:
        await asyncio.Event().wait()

async def main():
    # Monitor multiple rooms concurrently
    api_keys = {
        "room1": "api-key-1",
        "room2": "api-key-2",
        "room3": "api-key-3",
    }

    tasks = [
        monitor_room(key, room)
        for room, key in api_keys.items()
    ]

    await asyncio.gather(*tasks)

asyncio.run(main())
```

## See Also

- [Getting Started Guide](getting-started.md) - Setup and basic usage
- [Examples](examples/) - Ready-to-run example scripts
- [API Reference](../README.md#api-reference) - Complete API documentation
