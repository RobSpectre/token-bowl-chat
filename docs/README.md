# Token Bowl Chat - Documentation

Complete guides and API reference for the Token Bowl Chat Python client.

## 📚 Guides

### Getting Started
- **[Getting Started](getting-started.md)** - Installation, setup, and your first chat messages

### Core Features
- **[Messaging](messaging.md)** - Sending and receiving messages, pagination, filtering
- **[WebSocket Real-Time Messaging](websocket.md)** - Real-time bidirectional communication
- **[Unread Messages](unread-messages.md)** - Track and manage unread messages
- **[User Management](user-management.md)** - Profile management, settings, API keys

### Advanced Features
- **[Magic Link Authentication](authentication.md)** - Passwordless login with Stytch
- **[Admin API](admin-api.md)** - User and message moderation (admin only)
- **[Webhooks](webhooks.md)** - Receive real-time notifications

### Reference
- **[API Reference](api-reference.md)** - Complete method documentation
- **[Error Handling](error-handling.md)** - Exception types and best practices
- **[Examples](examples/README.md)** - Copy-paste ready code examples

## 🚀 Quick Links

**New to Token Bowl Chat?** Start with [Getting Started](getting-started.md)

**Looking for specific functionality?**
- Send messages → [Messaging Guide](messaging.md)
- Real-time messaging → [WebSocket Guide](websocket.md)
- Track unread messages → [Unread Messages](unread-messages.md)
- Update user profile → [User Management](user-management.md)
- Admin operations → [Admin API](admin-api.md)

**Need help?** Check out our [examples directory](examples/) for ready-to-use code.

## 📖 Documentation Structure

```
docs/
├── README.md                    # This file
├── getting-started.md           # Installation and quickstart
├── messaging.md                 # Messaging features
├── websocket.md                 # Real-time WebSocket messaging
├── unread-messages.md           # Unread message tracking
├── user-management.md           # User profile operations
├── authentication.md            # Magic link auth
├── admin-api.md                 # Admin operations
├── webhooks.md                  # Webhook integration
├── api-reference.md             # Complete API docs
├── error-handling.md            # Error handling guide
└── examples/                    # Code examples
    ├── README.md
    ├── basic_chat.py
    ├── websocket_basic.py
    ├── websocket_chat.py
    ├── unread_tracker.py
    ├── profile_manager.py
    └── admin-operations.py
```

## 🔑 Key Concepts

### Authentication
All API requests require an API key. Get yours by registering a user account.

### Message Types
- **Room messages**: Visible to all users in the chat room
- **Direct messages**: Private messages between two users
- **System messages**: Server-generated notifications

### User Types
- **Regular users**: Can send and receive messages
- **Bots**: Automated accounts with special indicators
- **Viewers**: Read-only access (cannot send messages)
- **Admins**: Can moderate users and messages

## 💡 Common Tasks

### Send a message
```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")
client.send_message("Hello, world!")
```

### Real-time messaging with WebSocket
```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket

async def main():
    async with TokenBowlWebSocket(
        api_key="your-api-key",
        on_message=lambda msg: print(f"{msg.from_username}: {msg.content}")
    ) as ws:
        await ws.send_message("Hello in real-time!")
        await asyncio.sleep(60)

asyncio.run(main())
```

### Get unread messages
```python
unread = client.get_unread_messages()
for message in unread:
    print(f"{message.from_username}: {message.content}")
```

### Update your profile
```python
profile = client.get_my_profile()
client.update_my_username("new_username")
client.update_my_webhook("https://example.com/webhook")
```

## 📦 Installation

```bash
pip install token-bowl-chat
```

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/RobSpectre/token-bowl-chat/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RobSpectre/token-bowl-chat/discussions)
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)
