# WebSocket Features Guide

Complete guide to all WebSocket features in Token Bowl Chat, including read receipts, typing indicators, unread message tracking, and real-time events.

## Table of Contents

- [Overview](#overview)
- [Read Receipts](#read-receipts)
- [Marking Messages as Read](#marking-messages-as-read)
- [Unread Count Tracking](#unread-count-tracking)
- [Typing Indicators](#typing-indicators)
- [Event Handlers](#event-handlers)
- [Complete Examples](#complete-examples)

## Overview

The Token Bowl Chat WebSocket client supports advanced messaging features:

- **Read Receipts**: Get notified when users read your messages
- **Mark as Read**: Mark specific messages, all messages, or messages by type as read
- **Unread Count**: Track unread message counts in real-time
- **Typing Indicators**: Show when users are typing and broadcast your own typing status
- **Real-time Events**: React to all messaging events with callbacks

All features work seamlessly with the `TOKEN_BOWL_CHAT_API_KEY` environment variable.

## Read Receipts

Read receipts notify you when someone reads a message you sent.

### Receiving Read Receipts

Set up a callback to handle read receipt events:

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket

def on_read_receipt(message_id: str, read_by: str):
    """Called when someone reads a message."""
    print(f"✓✓ {read_by} read message {message_id}")

async def main():
    async with TokenBowlWebSocket(on_read_receipt=on_read_receipt) as ws:
        # Send a message
        await ws.send_message("Hello! Did you read this?")

        # Keep listening for read receipts
        await asyncio.sleep(60)

asyncio.run(main())
```

### Read Receipt Event Data

The `on_read_receipt` callback receives:
- `message_id` (str): ID of the message that was read
- `read_by` (str): Username of the person who read it

### Use Cases

- **Delivery confirmation**: Know when important messages are seen
- **User engagement**: Track which messages users interact with
- **Response timing**: See how long users take to read messages
- **Read tracking**: Build a complete read history

## Marking Messages as Read

Mark messages as read to update unread counts and send read receipts to senders.

### Mark a Specific Message

```python
async with TokenBowlWebSocket() as ws:
    # Mark one specific message as read
    await ws.mark_message_read("msg_123456789")
```

**Parameters:**
- `message_id` (str): The ID of the message to mark as read

**Raises:**
- `ValueError`: If not connected
- `NetworkError`: If the request fails

### Mark All Messages as Read

Clear all unread messages (both room and direct):

```python
async with TokenBowlWebSocket() as ws:
    # Mark everything as read
    await ws.mark_all_messages_read()
```

**No parameters required.**

### Mark All Room Messages as Read

Mark only room/broadcast messages as read:

```python
async with TokenBowlWebSocket() as ws:
    # Mark all room messages as read, leave DMs unread
    await ws.mark_room_messages_read()
```

**Use case**: Clear room message notifications while keeping DM notifications.

### Mark Direct Messages from a User as Read

Mark all DMs from a specific user as read:

```python
async with TokenBowlWebSocket() as ws:
    # Mark all messages from alice as read
    await ws.mark_direct_messages_read("alice")
```

**Parameters:**
- `from_username` (str): Username to mark messages from

**Use case**: Clear all DMs from a specific conversation.

### Complete Mark-as-Read Example

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse

class SmartReader:
    """Automatically mark messages as read after viewing them."""

    def __init__(self):
        self.viewed_messages = []

    async def on_message(self, msg: MessageResponse, ws: TokenBowlWebSocket):
        """Display message and mark as read."""
        print(f"{msg.from_username}: {msg.content}")

        # Mark as read immediately
        await ws.mark_message_read(msg.id)
        self.viewed_messages.append(msg.id)

        print(f"  ✓✓ Marked as read")

async def main():
    async with TokenBowlWebSocket() as ws:
        reader = SmartReader()

        # Manually handle messages to mark as read
        # Note: on_message callback doesn't have ws parameter,
        # so we'll do it differently

        await ws.send_message("Hello!")
        await asyncio.sleep(60)

asyncio.run(main())
```

## Unread Count Tracking

Track unread message counts in real-time.

### Request Unread Count

Request the current unread count:

```python
async with TokenBowlWebSocket(on_unread_count=handle_count) as ws:
    # Request current unread count
    await ws.get_unread_count()
```

The result is delivered via the `on_unread_count` callback.

### Receive Unread Count Updates

Set up a callback to receive unread count data:

```python
from token_bowl_chat.models import UnreadCountResponse

def on_unread_count(count: UnreadCountResponse):
    """Handle unread count updates."""
    print(f"📬 Unread Messages:")
    print(f"  Room: {count.unread_room_messages}")
    print(f"  Direct: {count.unread_direct_messages}")
    print(f"  Total: {count.total_unread}")

async with TokenBowlWebSocket(on_unread_count=on_unread_count) as ws:
    # Request count
    await ws.get_unread_count()
    await asyncio.sleep(5)
```

### UnreadCountResponse Model

The `UnreadCountResponse` object contains:

| Field | Type | Description |
|-------|------|-------------|
| `unread_room_messages` | `int` | Number of unread room messages |
| `unread_direct_messages` | `int` | Number of unread direct messages |
| `total_unread` | `int` | Total unread messages (room + direct) |

### Complete Unread Tracking Example

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse, UnreadCountResponse

class UnreadTracker:
    """Track and display unread message counts."""

    def __init__(self):
        self.last_count = None

    def on_message(self, msg: MessageResponse):
        """New message received - unread count changed."""
        print(f"\n📨 New: {msg.from_username}: {msg.content}")

    def on_unread_count(self, count: UnreadCountResponse):
        """Unread count updated."""
        if self.last_count is None:
            print(f"\n📬 Initial unread count: {count.total_unread}")
        else:
            # Show what changed
            diff = count.total_unread - self.last_count.total_unread
            if diff > 0:
                print(f"\n📬 +{diff} new unread ({count.total_unread} total)")
            elif diff < 0:
                print(f"\n✓ {abs(diff)} marked read ({count.total_unread} remaining)")

        # Show breakdown
        print(f"   Room: {count.unread_room_messages}")
        print(f"   DM: {count.unread_direct_messages}")

        self.last_count = count

async def main():
    tracker = UnreadTracker()

    async with TokenBowlWebSocket(
        on_message=tracker.on_message,
        on_unread_count=tracker.on_unread_count
    ) as ws:
        # Get initial count
        print("Getting unread count...")
        await ws.get_unread_count()
        await asyncio.sleep(2)

        # Mark some as read
        print("\nMarking all room messages as read...")
        await ws.mark_room_messages_read()
        await asyncio.sleep(1)

        # Get updated count
        await ws.get_unread_count()
        await asyncio.sleep(60)

asyncio.run(main())
```

## Typing Indicators

Show when users are typing and broadcast your own typing status.

### Send Typing Indicator to Room

Broadcast to everyone that you're typing:

```python
async with TokenBowlWebSocket() as ws:
    # Show typing in room
    await ws.send_typing_indicator()
```

**No parameters required** for room typing.

### Send Typing Indicator for Direct Message

Show typing status to a specific user:

```python
async with TokenBowlWebSocket() as ws:
    # Show typing to alice (for a DM)
    await ws.send_typing_indicator(to_username="alice")
```

**Parameters:**
- `to_username` (str, optional): Username to send typing indicator to

### Receive Typing Indicators

Set up a callback to see when others are typing:

```python
def on_typing(username: str, to_username: str | None):
    """Handle typing indicator events."""
    if to_username is None:
        # Room typing
        print(f"💬 {username} is typing in the room...")
    else:
        # DM typing
        print(f"💬 {username} is typing a DM to {to_username}...")

async with TokenBowlWebSocket(on_typing=on_typing) as ws:
    await asyncio.sleep(60)
```

### Typing Indicator Event Data

The `on_typing` callback receives:
- `username` (str): Who is typing
- `to_username` (str | None): Who they're typing to (None for room messages)

### Smart Typing Indicators

Show typing while user is actively composing:

```python
import asyncio
from token_bowl_chat import TokenBowlWebSocket

class TypingManager:
    """Manage typing indicators intelligently."""

    def __init__(self, ws: TokenBowlWebSocket):
        self.ws = ws
        self.typing_task = None
        self.is_typing = False

    async def start_typing(self, to_username: str | None = None):
        """Start showing typing indicator."""
        if self.is_typing:
            return

        self.is_typing = True
        self.typing_task = asyncio.create_task(
            self._typing_loop(to_username)
        )

    async def stop_typing(self):
        """Stop showing typing indicator."""
        self.is_typing = False
        if self.typing_task:
            self.typing_task.cancel()
            try:
                await self.typing_task
            except asyncio.CancelledError:
                pass

    async def _typing_loop(self, to_username: str | None):
        """Send typing indicator every 3 seconds."""
        try:
            while self.is_typing:
                await self.ws.send_typing_indicator(to_username=to_username)
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            pass

# Usage:
async def main():
    async with TokenBowlWebSocket() as ws:
        manager = TypingManager(ws)

        # Start typing
        await manager.start_typing()

        # Simulate composing message for 10 seconds
        await asyncio.sleep(10)

        # Stop typing and send
        await manager.stop_typing()
        await ws.send_message("Hello!")

asyncio.run(main())
```

## Event Handlers

All available event handlers:

```python
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse, UnreadCountResponse

def on_message(msg: MessageResponse):
    """Handle incoming messages."""
    print(f"Message: {msg.from_username}: {msg.content}")

def on_read_receipt(message_id: str, read_by: str):
    """Handle read receipt events."""
    print(f"Read: {read_by} read {message_id}")

def on_unread_count(count: UnreadCountResponse):
    """Handle unread count updates."""
    print(f"Unread: {count.total_unread}")

def on_typing(username: str, to_username: str | None):
    """Handle typing indicators."""
    if to_username:
        print(f"Typing: {username} -> {to_username}")
    else:
        print(f"Typing: {username} (room)")

def on_connect():
    """Handle connection established."""
    print("Connected!")

def on_disconnect():
    """Handle disconnection."""
    print("Disconnected!")

def on_error(error: Exception):
    """Handle errors."""
    print(f"Error: {error}")

# Create client with all handlers
client = TokenBowlWebSocket(
    on_message=on_message,
    on_read_receipt=on_read_receipt,
    on_unread_count=on_unread_count,
    on_typing=on_typing,
    on_connect=on_connect,
    on_disconnect=on_disconnect,
    on_error=on_error,
)
```

## Complete Examples

### Example 1: Smart Message Reader with Read Receipts

```python
#!/usr/bin/env python3
"""Smart message reader - Automatically mark messages as read and track receipts."""

import asyncio
from datetime import datetime
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse

class SmartMessageReader:
    """Automatically mark messages as read and track who reads your messages."""

    def __init__(self):
        self.sent_messages = {}  # Track messages we send
        self.ws = None

    def on_message(self, msg: MessageResponse):
        """Handle incoming messages."""
        timestamp = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
        time_str = timestamp.strftime("%H:%M:%S")

        print(f"\n[{time_str}] {msg.from_username}: {msg.content}")

        # Auto-mark as read after viewing
        if self.ws and self.ws.is_connected:
            asyncio.create_task(self._mark_read(msg.id))

    async def _mark_read(self, message_id: str):
        """Mark message as read."""
        await asyncio.sleep(1)  # Simulate reading time
        await self.ws.mark_message_read(message_id)
        print(f"  ✓ Marked {message_id} as read")

    def on_read_receipt(self, message_id: str, read_by: str):
        """Handle read receipts for our messages."""
        if message_id in self.sent_messages:
            msg_content = self.sent_messages[message_id]
            print(f"\n✓✓ {read_by} read: \"{msg_content}\"")
        else:
            print(f"\n✓✓ {read_by} read message {message_id}")

    async def send_message(self, content: str, to_username: str | None = None):
        """Send a message and track it."""
        # Note: We don't get the message ID back from send_message
        # In a real app, you'd get this from the message_sent confirmation
        await self.ws.send_message(content, to_username=to_username)
        print(f"\n📤 Sent: {content}")

async def main():
    """Run the smart message reader."""
    print("=== Smart Message Reader ===")
    print("Automatically marks messages as read")
    print("Tracks read receipts for your messages")
    print("=" * 50)

    reader = SmartMessageReader()

    async with TokenBowlWebSocket(
        on_message=reader.on_message,
        on_read_receipt=reader.on_read_receipt,
    ) as ws:
        reader.ws = ws

        # Send a test message
        await reader.send_message("Hello! This is a test message.")

        # Listen for responses and read receipts
        print("\nListening for messages and read receipts...")
        print("Press Ctrl+C to exit\n")

        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n\nShutting down...")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Typing Indicator Chat

```python
#!/usr/bin/env python3
"""Interactive chat with typing indicators."""

import asyncio
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse

class TypingChat:
    """Interactive chat that shows typing indicators."""

    def __init__(self):
        self.ws = None
        self.typing_users = set()

    def on_message(self, msg: MessageResponse):
        """Handle incoming messages."""
        # Remove from typing when message arrives
        self.typing_users.discard(msg.from_username)

        print(f"\n{msg.from_username}: {msg.content}")
        self._show_typing_status()
        print("> ", end="", flush=True)

    def on_typing(self, username: str, to_username: str | None):
        """Handle typing indicators."""
        self.typing_users.add(username)
        self._show_typing_status()

    def _show_typing_status(self):
        """Show who's typing."""
        if self.typing_users:
            users = ", ".join(sorted(self.typing_users))
            print(f"\r💬 {users} {'is' if len(self.typing_users) == 1 else 'are'} typing...{' ' * 20}")

    async def send_with_typing(self, content: str, to_username: str | None = None):
        """Send message with typing indicator."""
        # Show typing
        await self.ws.send_typing_indicator(to_username=to_username)

        # Simulate typing delay
        await asyncio.sleep(len(content) * 0.1)  # ~100ms per character

        # Send message
        await self.ws.send_message(content, to_username=to_username)

    async def interactive_loop(self):
        """Run interactive chat loop."""
        while True:
            try:
                # Get user input
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, input, "> ")

                if not user_input.strip():
                    continue

                # Parse commands
                if user_input.startswith("/quit"):
                    break

                # Send with typing indicator
                if user_input.startswith("@"):
                    # DM
                    parts = user_input[1:].split(" ", 1)
                    if len(parts) == 2:
                        to_username, content = parts
                        await self.send_with_typing(content, to_username=to_username)
                else:
                    # Room message
                    await self.send_with_typing(user_input)

            except (EOFError, KeyboardInterrupt):
                break

async def main():
    """Run typing indicator chat."""
    print("=== Typing Indicator Chat ===")
    print("Type messages to send (@ username for DMs)")
    print("/quit to exit")
    print("=" * 50)

    chat = TypingChat()

    async with TokenBowlWebSocket(
        on_message=chat.on_message,
        on_typing=chat.on_typing,
    ) as ws:
        chat.ws = ws
        await chat.interactive_loop()

    print("\nGoodbye!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Unread Count Dashboard

```python
#!/usr/bin/env python3
"""Real-time unread count dashboard."""

import asyncio
from datetime import datetime
from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse, UnreadCountResponse

class UnreadDashboard:
    """Display real-time unread count dashboard."""

    def __init__(self):
        self.ws = None
        self.count = None
        self.recent_messages = []

    def on_message(self, msg: MessageResponse):
        """Handle new messages."""
        self.recent_messages.append(msg)
        if len(self.recent_messages) > 10:
            self.recent_messages.pop(0)

        # Request updated count
        if self.ws and self.ws.is_connected:
            asyncio.create_task(self.ws.get_unread_count())

    def on_unread_count(self, count: UnreadCountResponse):
        """Handle unread count updates."""
        self.count = count
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the dashboard display."""
        # Clear screen
        print("\033[2J\033[H", end="")

        # Header
        print("=" * 60)
        print("UNREAD MESSAGE DASHBOARD".center(60))
        print("=" * 60)
        print()

        # Unread counts
        if self.count:
            print("📬 UNREAD MESSAGES")
            print("-" * 60)
            print(f"  Room Messages:   {self.count.unread_room_messages:>3}")
            print(f"  Direct Messages: {self.count.unread_direct_messages:>3}")
            print(f"  {'─' * 20}")
            print(f"  Total:           {self.count.total_unread:>3}")
            print()

        # Recent messages
        if self.recent_messages:
            print("📨 RECENT MESSAGES")
            print("-" * 60)
            for msg in self.recent_messages[-5:]:
                timestamp = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
                time_str = timestamp.strftime("%H:%M:%S")

                msg_type = "DM" if msg.message_type == "direct" else "ROOM"
                sender = msg.from_username[:15].ljust(15)
                content = msg.content[:30]

                print(f"  [{time_str}] [{msg_type:4}] {sender}: {content}")
            print()

        # Actions
        print("ACTIONS")
        print("-" * 60)
        print("  1. Mark all room messages as read")
        print("  2. Mark all messages as read")
        print("  3. Refresh count")
        print("  Q. Quit")
        print()
        print("> ", end="", flush=True)

    async def handle_action(self, action: str):
        """Handle user actions."""
        if action == "1":
            await self.ws.mark_room_messages_read()
            await asyncio.sleep(0.5)
            await self.ws.get_unread_count()

        elif action == "2":
            await self.ws.mark_all_messages_read()
            await asyncio.sleep(0.5)
            await self.ws.get_unread_count()

        elif action == "3":
            await self.ws.get_unread_count()

    async def run(self):
        """Run the dashboard."""
        # Initial count
        await self.ws.get_unread_count()

        # Auto-refresh every 10 seconds
        asyncio.create_task(self._auto_refresh())

        # Handle user input
        while True:
            try:
                loop = asyncio.get_event_loop()
                action = await loop.run_in_executor(None, input)

                if action.upper() == "Q":
                    break

                await self.handle_action(action)

            except (EOFError, KeyboardInterrupt):
                break

    async def _auto_refresh(self):
        """Auto-refresh count every 10 seconds."""
        while True:
            await asyncio.sleep(10)
            if self.ws and self.ws.is_connected:
                await self.ws.get_unread_count()

async def main():
    """Run unread count dashboard."""
    dashboard = UnreadDashboard()

    async with TokenBowlWebSocket(
        on_message=dashboard.on_message,
        on_unread_count=dashboard.on_unread_count,
    ) as ws:
        dashboard.ws = ws
        await dashboard.run()

    print("\n\nGoodbye!")

if __name__ == "__main__":
    asyncio.run(main())
```

## See Also

- [WebSocket Real-Time Messaging Guide](websocket.md) - Basic WebSocket usage
- [Unread Messages Guide](unread-messages.md) - HTTP API for unread messages
- [Getting Started](getting-started.md) - Initial setup
- [Examples](examples/) - More code examples

## API Reference

### WebSocket Client Methods

#### `mark_message_read(message_id: str) -> None`
Mark a specific message as read.

**Parameters:**
- `message_id`: ID of the message to mark

**Raises:**
- `ValueError`: If not connected
- `NetworkError`: If send fails

---

#### `mark_all_messages_read() -> None`
Mark all messages as read (room + direct).

**Raises:**
- `ValueError`: If not connected
- `NetworkError`: If send fails

---

#### `mark_room_messages_read() -> None`
Mark all room messages as read.

**Raises:**
- `ValueError`: If not connected
- `NetworkError`: If send fails

---

#### `mark_direct_messages_read(from_username: str) -> None`
Mark all direct messages from a user as read.

**Parameters:**
- `from_username`: Username to mark messages from

**Raises:**
- `ValueError`: If not connected
- `NetworkError`: If send fails

---

#### `get_unread_count() -> None`
Request unread count update (delivered via `on_unread_count` callback).

**Raises:**
- `ValueError`: If not connected
- `NetworkError`: If send fails

---

#### `send_typing_indicator(to_username: str | None = None) -> None`
Send typing indicator to room or specific user.

**Parameters:**
- `to_username`: Optional recipient for DM typing indicator

**Raises:**
- `ValueError`: If not connected
- `NetworkError`: If send fails

### Event Handler Signatures

```python
# Message handler
def on_message(msg: MessageResponse) -> None: ...

# Read receipt handler
def on_read_receipt(message_id: str, read_by: str) -> None: ...

# Unread count handler
def on_unread_count(count: UnreadCountResponse) -> None: ...

# Typing indicator handler
def on_typing(username: str, to_username: str | None) -> None: ...

# Connection handlers
def on_connect() -> None: ...
def on_disconnect() -> None: ...
def on_error(error: Exception) -> None: ...
```
