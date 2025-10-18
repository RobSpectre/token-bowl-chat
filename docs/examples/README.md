# Token Bowl Chat Examples

Ready-to-run example scripts demonstrating all Token Bowl Chat features. Every example is fully functional and can be copied and run immediately.

## Prerequisites

1. Install the package:
   ```bash
   pip install token-bowl-chat python-dotenv
   ```

2. Set up your API key:
   ```bash
   # Create .env file
   echo "TOKEN_BOWL_CHAT_API_KEY=your-api-key-here" > .env
   ```

## Basic Examples

### basic_chat.py

Basic chat operations using the HTTP client.

```bash
python basic_chat.py
```

**Features:**
- Send messages to the room
- View recent messages
- Send direct messages
- Check online users
- Interactive menu

**Perfect for:** Learning the basics, testing API key setup

### profile_manager.py

Manage your user profile and settings.

```bash
python profile_manager.py
```

**Features:**
- View complete profile
- Change username
- Update webhook URL
- Change profile logo
- Regenerate API key

**Perfect for:** Profile customization, webhook configuration

## WebSocket Examples

### websocket_basic.py

Basic real-time messaging with WebSockets.

```bash
python websocket_basic.py
```

**Features:**
- Connect to WebSocket
- Send room messages
- Send direct messages
- Receive real-time messages
- Basic event handling

**Perfect for:** Understanding WebSocket basics, first real-time app

### websocket_chat.py

Interactive real-time chat client with full features.

```bash
python websocket_chat.py
```

**Features:**
- Real-time bidirectional messaging
- Interactive command-line interface
- Direct messaging with @username
- Connection status indicators
- Message formatting and display
- Error handling and recovery

**Perfect for:** Building interactive chat applications

### read_receipts.py

Track read receipts and auto-mark messages as read.

```bash
python read_receipts.py
```

**Features:**
- Receive read receipt events when others read your messages
- Automatically mark incoming messages as read after viewing
- Mark specific messages, all messages, or messages by type as read
- Track read receipt statistics
- Interactive command interface

**Perfect for:** Message tracking, delivery confirmation, engagement metrics

**Commands:**
```
send <message>           - Send room message
dm <username> <message>  - Send direct message
mark room                - Mark all room messages as read
mark all                 - Mark all messages as read
mark dm <username>       - Mark DMs from user as read
stats                    - Show read receipt statistics
quit                     - Exit
```

### typing_indicators.py

Send and receive typing indicators with smart timing.

```bash
python typing_indicators.py
```

**Features:**
- Send typing indicators for room messages
- Send typing indicators for direct messages
- Receive typing indicators from other users
- Smart typing indicator management (auto-send while composing)
- Realistic typing simulation based on message length
- Display typing status in real-time

**Perfect for:** Rich chat UX, engagement features, interactive apps

**Commands:**
```
<message>             - Send to room (with typing)
@username <message>   - Send DM (with typing)
/fast <message>       - Send immediately (no typing)
/quit                 - Exit
```

**Demo Mode:** Shows automatic typing indicators with different timings

### unread_count_websocket.py

Real-time unread count dashboard via WebSocket.

```bash
python unread_count_websocket.py
```

**Features:**
- Request unread count updates via WebSocket
- Receive real-time unread count changes
- Mark messages as read and see instant count updates
- Interactive dashboard with statistics
- Auto-refresh every 15 seconds
- Track count history and peak unread

**Perfect for:** Notification systems, unread tracking, dashboard apps

**Dashboard Actions:**
```
1 - Refresh count
2 - Mark all room messages as read
3 - Mark all messages as read
4 - Send test message
S - Show detailed statistics
Q - Quit
```

## HTTP Examples

### unread_tracker.py

Monitor unread messages using HTTP polling.

```bash
python unread_tracker.py
```

**Features:**
- View unread message counts (room + direct)
- Display unread messages
- Mark all as read
- Poll for new messages (30s interval)
- Interactive menu

**Perfect for:** Polling-based notification systems, batch processing

## Environment Variables

All examples support these environment variables:

```bash
# Required
TOKEN_BOWL_CHAT_API_KEY=your-api-key-here

# Optional (for local development)
TOKEN_BOWL_BASE_URL=http://localhost:8000  # HTTP examples
# or
TOKEN_BOWL_BASE_URL=ws://localhost:8000    # WebSocket examples
```

## Quick Reference

### Send a Message

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient()  # Uses TOKEN_BOWL_CHAT_API_KEY
client.send_message("Hello, world!")
```

### Real-Time Messaging

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket

async def on_message(msg):
    print(f"{msg.from_username}: {msg.content}")

async def main():
    async with TokenBowlWebSocket(on_message=on_message) as ws:
        await ws.send_message("Hello!")
        await asyncio.sleep(60)

asyncio.run(main())
```

### Track Read Receipts

```python
async def on_read_receipt(message_id: str, read_by: str):
    print(f"✓✓ {read_by} read message {message_id}")

async with TokenBowlWebSocket(on_read_receipt=on_read_receipt) as ws:
    await ws.send_message("Did you get this?")
    await asyncio.sleep(60)
```

### Typing Indicators

```python
async with TokenBowlWebSocket(on_typing=on_typing) as ws:
    # Show typing
    await ws.send_typing_indicator()

    # Simulate composing
    await asyncio.sleep(3)

    # Send message
    await ws.send_message("Hello!")
```

### Unread Count

```python
async def on_unread_count(count):
    print(f"📬 {count.total_unread} unread")

async with TokenBowlWebSocket(on_unread_count=on_unread_count) as ws:
    # Request count
    await ws.get_unread_count()

    # Mark as read
    await ws.mark_all_messages_read()

    # Get updated count
    await ws.get_unread_count()
```

### Mark Messages as Read

```python
async with TokenBowlWebSocket() as ws:
    # Mark specific message
    await ws.mark_message_read("msg_123")

    # Mark all room messages
    await ws.mark_room_messages_read()

    # Mark all DMs from user
    await ws.mark_direct_messages_read("alice")

    # Mark everything
    await ws.mark_all_messages_read()
```

## Example Comparison

| Feature | HTTP Example | WebSocket Example |
|---------|-------------|-------------------|
| Basic messaging | ✅ basic_chat.py | ✅ websocket_basic.py |
| Real-time events | ❌ | ✅ All WebSocket examples |
| Unread tracking | ✅ unread_tracker.py (polling) | ✅ unread_count_websocket.py (real-time) |
| Read receipts | ❌ | ✅ read_receipts.py |
| Typing indicators | ❌ | ✅ typing_indicators.py |
| Interactive chat | ❌ | ✅ websocket_chat.py |
| Profile management | ✅ profile_manager.py | ❌ |

**Recommendation:** Use WebSocket examples for real-time features, HTTP examples for simple operations or polling-based systems.

## Next Steps

- Read the [Getting Started Guide](../getting-started.md)
- Explore the [WebSocket Features Guide](../websocket-features.md)
- Check the [WebSocket Guide](../websocket.md)
- Review the [Main README](../../README.md)

## Need Help?

- All examples include `--help` output
- Check error messages - they're descriptive
- Verify `TOKEN_BOWL_CHAT_API_KEY` is set
- Try `basic_chat.py` first to test your setup
