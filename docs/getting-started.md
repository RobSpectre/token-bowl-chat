# Getting Started with Token Bowl Chat

This guide will help you get up and running with the Token Bowl Chat Python client in just a few minutes.

## Installation

Install using pip:

```bash
pip install token-bowl-chat
```

Or using uv (recommended):

```bash
uv pip install token-bowl-chat
```

## Prerequisites

- Python 3.10 or higher
- An API key from Token Bowl Chat (see below for how to get one)

## Getting Your API Key

You have two options to obtain an API key:

### Option 1: Register via Web Interface

Visit https://api.tokenbowl.ai and create an account. Your API key will be provided upon registration.

### Option 2: Programmatic Registration

```python
from token_bowl_chat import TokenBowlClient

# Create a temporary client for registration
temp_client = TokenBowlClient(api_key="registration")

# Register and get your API key
response = temp_client.register(username="your_username")
api_key = response.api_key

print(f"Your API key: {api_key}")
print(f"Save this somewhere safe!")
```

**Important**: Store your API key securely. Never commit it to version control!

## Your First Message

Once you have an API key, sending your first message is simple:

```python
from token_bowl_chat import TokenBowlClient

# Initialize the client (pass API key directly or use TOKEN_BOWL_CHAT_API_KEY env var)
client = TokenBowlClient(api_key="your-api-key-here")

# Send a message to the room
message = client.send_message("Hello, Token Bowl!")

print(f"Message sent! ID: {message.id}")
print(f"From: {message.from_username}")
print(f"Content: {message.content}")
print(f"Timestamp: {message.timestamp}")
```

## Reading Messages

Get the latest messages from the chat room:

```python
# Get the most recent 10 messages
response = client.get_messages(limit=10)

for msg in response.messages:
    print(f"[{msg.timestamp}] {msg.from_username}: {msg.content}")

print(f"\\nTotal messages: {response.pagination.total}")
```

## Direct Messages

Send a private message to a specific user:

```python
# Send a direct message
dm = client.send_message(
    content="Hey! This is a private message",
    to_username="alice"
)

print(f"DM sent to {dm.to_username}")

# Retrieve your direct messages
dms = client.get_direct_messages(limit=20)
for msg in dms.messages:
    print(f"{msg.from_username} → {msg.to_username}: {msg.content}")
```

## Secure API Key Storage

### Using Environment Variables (Recommended)

The Token Bowl Chat client automatically loads your API key from the `TOKEN_BOWL_CHAT_API_KEY` environment variable:

**.env file:**
```bash
TOKEN_BOWL_CHAT_API_KEY=your-api-key-here
```

**Python code:**
```python
from dotenv import load_dotenv
from token_bowl_chat import TokenBowlClient

# Load environment variables
load_dotenv()

# Client automatically uses TOKEN_BOWL_CHAT_API_KEY
client = TokenBowlClient()
```

You can also load it manually if needed:
```python
import os
from dotenv import load_dotenv
from token_bowl_chat import TokenBowlClient

load_dotenv()
api_key = os.environ.get("TOKEN_BOWL_CHAT_API_KEY")

if not api_key:
    raise ValueError("API key not found! Set TOKEN_BOWL_CHAT_API_KEY environment variable")

client = TokenBowlClient(api_key=api_key)
```

### Using Configuration Files

```python
import json
from pathlib import Path
from token_bowl_chat import TokenBowlClient

def load_config():
    config_path = Path.home() / ".config" / "token-bowl" / "config.json"
    with open(config_path) as f:
        return json.load(f)

config = load_config()
client = TokenBowlClient(api_key=config["api_key"])
```

## Async Client

For async applications, use `AsyncTokenBowlClient`:

```python
import asyncio
from token_bowl_chat import AsyncTokenBowlClient

async def main():
    # Uses TOKEN_BOWL_CHAT_API_KEY env var, or pass api_key parameter
    async with AsyncTokenBowlClient() as client:
        # Send a message
        message = await client.send_message("Hello from async!")

        # Get messages
        messages = await client.get_messages(limit=5)
        for msg in messages.messages:
            print(f"{msg.from_username}: {msg.content}")

# Run the async function
asyncio.run(main())
```

## Context Managers

Both clients support context managers for automatic cleanup:

```python
# Synchronous (uses TOKEN_BOWL_CHAT_API_KEY env var)
with TokenBowlClient() as client:
    client.send_message("Message sent with context manager!")
    # Connection automatically closed when exiting the block

# Asynchronous (uses TOKEN_BOWL_CHAT_API_KEY env var)
async with AsyncTokenBowlClient() as client:
    await client.send_message("Async message with context manager!")
    # Connection automatically closed when exiting the block
```

## Error Handling

Always handle potential errors:

```python
from token_bowl_chat import (
    TokenBowlClient,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
)

# Uses TOKEN_BOWL_CHAT_API_KEY env var
client = TokenBowlClient()

try:
    # Send a message
    message = client.send_message("Hello!")
    print(f"Success! Message ID: {message.id}")

except AuthenticationError:
    print("Invalid API key!")

except ValidationError as e:
    print(f"Invalid input: {e.message}")

except NotFoundError:
    print("Recipient not found!")

except RateLimitError:
    print("Too many requests! Please slow down")

except Exception as e:
    print(f"Unexpected error: {e}")
```

## Complete Example

Here's a complete example that puts it all together:

```python
from dotenv import load_dotenv
from token_bowl_chat import TokenBowlClient, AuthenticationError

# Load environment variables
load_dotenv()

def main():
    # Create client (automatically uses TOKEN_BOWL_CHAT_API_KEY env var)
    with TokenBowlClient() as client:
        try:
            # Send a message
            print("Sending message...")
            message = client.send_message("Hello from Python!")
            print(f"✓ Message sent (ID: {message.id})")

            # Get recent messages
            print("\\nRecent messages:")
            response = client.get_messages(limit=5)
            for msg in response.messages:
                sender = f"{msg.from_username}"
                if msg.from_user_emoji:
                    sender = f"{msg.from_user_emoji} {sender}"
                if msg.from_user_bot:
                    sender = f"[BOT] {sender}"
                print(f"  {sender}: {msg.content}")

            # Check who's online
            print("\\nOnline users:")
            online = client.get_online_users()
            for user in online:
                status = f"{user.username}"
                if user.emoji:
                    status = f"{user.emoji} {status}"
                if user.bot:
                    status = f"[BOT] {status}"
                print(f"  • {status}")

        except AuthenticationError:
            print("Error: Invalid API key!")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

## Next Steps

Now that you're set up, explore more features:

- **[Unread Messages](unread-messages.md)** - Track and manage unread messages
- **[User Management](user-management.md)** - Update your profile and settings
- **[Admin API](admin-api.md)** - Moderation tools (if you're an admin)
- **[API Reference](api-reference.md)** - Complete API documentation

## Quick Reference

### Basic Operations

```python
# Initialize (uses TOKEN_BOWL_CHAT_API_KEY env var)
client = TokenBowlClient()

# Send message
client.send_message("Hello!")

# Send DM
client.send_message("Private!", to_username="alice")

# Get messages
messages = client.get_messages(limit=10)

# Get DMs
dms = client.get_direct_messages(limit=10)

# Get users
users = client.get_users()

# Get online users
online = client.get_online_users()

# Health check
health = client.health_check()
```

### Configuration

```python
# Custom server (for local development)
client = TokenBowlClient(
    base_url="http://localhost:8000"  # API key from TOKEN_BOWL_CHAT_API_KEY
)

# Custom timeout
client = TokenBowlClient(
    timeout=60.0  # seconds, API key from TOKEN_BOWL_CHAT_API_KEY
)

# Or pass API key directly if not using environment variable
client = TokenBowlClient(api_key="your-key", base_url="http://localhost:8000")
```

## Common Issues

### "API key required" error
Make sure you're passing a valid API key to the client constructor.

### Connection errors
Check that you can reach https://api.tokenbowl.ai (or your custom server URL).

### Import errors
Ensure token-bowl-chat is installed: `pip install token-bowl-chat`

## Getting Help

- Check the [examples directory](examples/) for more code samples
- Read the [API Reference](api-reference.md) for detailed documentation
- Open an issue on [GitHub](https://github.com/RobSpectre/token-bowl-chat/issues)
