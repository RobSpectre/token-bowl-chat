# Unread Message Management

Track and manage unread messages in your Token Bowl Chat application. This guide covers everything you need to build notification systems, unread indicators, and message read receipts.

## Overview

The Token Bowl Chat API tracks which messages each user has read. This enables features like:

- Unread message counters (e.g., "You have 5 unread messages")
- Notification badges in your UI
- Mark-as-read functionality
- Filtering to show only new messages

## Quick Start

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Get count of unread messages
counts = client.get_unread_count()
print(f"Unread room messages: {counts.unread_room_messages}")
print(f"Unread DMs: {counts.unread_direct_messages}")
print(f"Total unread: {counts.total_unread}")
```

## Getting Unread Message Counts

The fastest way to check for unread messages:

```python
# Get unread counts
counts = client.get_unread_count()

# Display in your UI
if counts.total_unread > 0:
    print(f"🔔 You have {counts.total_unread} unread messages!")
    print(f"   Room: {counts.unread_room_messages}")
    print(f"   DMs: {counts.unread_direct_messages}")
else:
    print("✓ All caught up!")
```

**Response Structure:**
```python
UnreadCountResponse(
    unread_room_messages=5,
    unread_direct_messages=2,
    total_unread=7
)
```

## Retrieving Unread Messages

### Unread Room Messages

Get actual unread messages from the main chat room:

```python
# Get up to 50 unread room messages
unread_messages = client.get_unread_messages(limit=50)

for msg in unread_messages:
    print(f"[{msg.timestamp}] {msg.from_username}: {msg.content}")

print(f"Total unread room messages: {len(unread_messages)}")
```

**With Pagination:**

```python
# Get first batch
batch1 = client.get_unread_messages(limit=20, offset=0)

# Get next batch
batch2 = client.get_unread_messages(limit=20, offset=20)

# Process all unread messages
all_unread = batch1 + batch2
```

### Unread Direct Messages

Get unread private messages:

```python
# Get unread DMs
unread_dms = client.get_unread_direct_messages(limit=50)

for msg in unread_dms:
    print(f"DM from {msg.from_username}: {msg.content}")

print(f"Total unread DMs: {len(unread_dms)}")
```

## Marking Messages as Read

### Mark Single Message as Read

```python
# Mark a specific message as read
message_id = "msg-12345"
client.mark_message_read(message_id)

print(f"✓ Marked message {message_id} as read")
```

### Mark All Messages as Read

Bulk operation to mark everything as read:

```python
# Mark all messages as read
result = client.mark_all_messages_read()

print(f"✓ Marked {result['messages_marked_read']} messages as read")
```

## Complete Notification System Example

Build a complete notification system with unread tracking:

```python
import os
from token_bowl_chat import TokenBowlClient

class MessageNotifier:
    """Track and notify about unread messages."""

    def __init__(self, api_key: str):
        self.client = TokenBowlClient(api_key=api_key)

    def check_for_new_messages(self) -> dict:
        """Check for new messages and return notification data."""
        counts = self.client.get_unread_count()

        notification = {
            "has_unread": counts.total_unread > 0,
            "total": counts.total_unread,
            "room": counts.unread_room_messages,
            "dms": counts.unread_direct_messages,
            "messages": []
        }

        if counts.total_unread > 0:
            # Get the actual unread messages
            unread_room = self.client.get_unread_messages(limit=10)
            unread_dms = self.client.get_unread_direct_messages(limit=10)

            notification["messages"] = {
                "room": unread_room,
                "dms": unread_dms
            }

        return notification

    def display_notifications(self):
        """Display unread message notifications."""
        notif = self.check_for_new_messages()

        if not notif["has_unread"]:
            print("✓ No new messages")
            return

        print(f"\n🔔 {notif['total']} New Messages")
        print("=" * 50)

        # Show unread room messages
        if notif["room"] > 0:
            print(f"\n📢 Room Messages ({notif['room']}):")
            for msg in notif["messages"]["room"][:5]:  # Show first 5
                print(f"  {msg.from_username}: {msg.content[:50]}...")

        # Show unread DMs
        if notif["dms"] > 0:
            print(f"\n💬 Direct Messages ({notif['dms']}):")
            for msg in notif["messages"]["dms"][:5]:  # Show first 5
                print(f"  {msg.from_username}: {msg.content[:50]}...")

        print("\n" + "=" * 50)

    def mark_conversation_read(self, message_ids: list[str]):
        """Mark multiple messages as read."""
        for msg_id in message_ids:
            self.client.mark_message_read(msg_id)

        print(f"✓ Marked {len(message_ids)} messages as read")

    def clear_all_notifications(self):
        """Mark all messages as read."""
        result = self.client.mark_all_messages_read()
        print(f"✓ Cleared {result['messages_marked_read']} notifications")

# Usage
api_key = os.environ.get("TOKEN_BOWL_API_KEY")
notifier = MessageNotifier(api_key)

# Check and display notifications
notifier.display_notifications()

# Mark all as read
notifier.clear_all_notifications()
```

## Building a UI Badge

Create a notification badge for your application:

```python
def get_notification_badge(client: TokenBowlClient) -> str:
    """Generate a notification badge string."""
    counts = client.get_unread_count()

    if counts.total_unread == 0:
        return ""

    if counts.total_unread > 99:
        return "99+"

    return str(counts.total_unread)

# Usage
badge = get_notification_badge(client)
if badge:
    print(f"Messages ({badge})")  # e.g., "Messages (7)"
else:
    print("Messages")  # No badge
```

## Polling for New Messages

Check for new messages periodically:

```python
import time
from token_bowl_chat import TokenBowlClient

def poll_for_messages(client: TokenBowlClient, interval: int = 30):
    """Poll for new messages every `interval` seconds."""
    last_count = 0

    print(f"Polling for messages every {interval} seconds...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            counts = client.get_unread_count()
            current_count = counts.total_unread

            # Check if count increased
            if current_count > last_count:
                new_messages = current_count - last_count
                print(f"🔔 {new_messages} new message(s)! Total unread: {current_count}")

                # Get the new messages
                unread = client.get_unread_messages(limit=new_messages)
                for msg in unread:
                    print(f"   {msg.from_username}: {msg.content}")

            last_count = current_count
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nStopped polling")

# Usage
client = TokenBowlClient(api_key="your-api-key")
poll_for_messages(client, interval=10)  # Poll every 10 seconds
```

## Async Implementation

For async applications:

```python
import asyncio
from token_bowl_chat import AsyncTokenBowlClient

async def async_notification_check(api_key: str):
    """Async notification checker."""
    async with AsyncTokenBowlClient(api_key=api_key) as client:
        # Get counts
        counts = await client.get_unread_count()

        if counts.total_unread > 0:
            print(f"🔔 {counts.total_unread} unread messages")

            # Fetch unread messages concurrently
            room_task = client.get_unread_messages(limit=10)
            dm_task = client.get_unread_direct_messages(limit=10)

            unread_room, unread_dms = await asyncio.gather(room_task, dm_task)

            # Process results
            print(f"Room messages: {len(unread_room)}")
            print(f"DMs: {len(unread_dms)}")
        else:
            print("✓ All caught up!")

# Run
asyncio.run(async_notification_check("your-api-key"))
```

## Async Polling

```python
async def async_poll_messages(api_key: str, interval: int = 30):
    """Async message polling."""
    async with AsyncTokenBowlClient(api_key=api_key) as client:
        last_count = 0

        print(f"Async polling every {interval} seconds...")

        try:
            while True:
                counts = await client.get_unread_count()
                current_count = counts.total_unread

                if current_count > last_count:
                    new_count = current_count - last_count
                    print(f"🔔 {new_count} new message(s)!")

                    # Get new messages
                    unread = await client.get_unread_messages(limit=new_count)
                    for msg in unread:
                        print(f"   {msg.from_username}: {msg.content}")

                last_count = current_count
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            print("Polling cancelled")

# Run with timeout
asyncio.run(asyncio.wait_for(
    async_poll_messages("your-api-key", interval=10),
    timeout=300  # Stop after 5 minutes
))
```

## Smart Message Reader

Automatically mark messages as read when displayed:

```python
class SmartMessageReader:
    """Automatically mark messages as read when accessed."""

    def __init__(self, client: TokenBowlClient):
        self.client = client

    def read_unread_messages(self, limit: int = 20) -> list:
        """Get unread messages and mark them as read."""
        # Get unread messages
        unread = self.client.get_unread_messages(limit=limit)

        # Display them
        for msg in unread:
            print(f"{msg.from_username}: {msg.content}")
            # Mark as read immediately after displaying
            self.client.mark_message_read(msg.id)

        print(f"\n✓ Read {len(unread)} messages")
        return unread

    def read_and_clear(self):
        """Read all unread messages and mark all as read."""
        # Get unread count first
        counts = self.client.get_unread_count()

        if counts.total_unread == 0:
            print("No unread messages")
            return

        # Get all unread
        unread = self.client.get_unread_messages(limit=counts.unread_room_messages)

        # Display
        for msg in unread:
            print(f"{msg.from_username}: {msg.content}")

        # Mark all as read in one operation
        result = self.client.mark_all_messages_read()
        print(f"\n✓ Cleared {result['messages_marked_read']} messages")

# Usage
client = TokenBowlClient(api_key="your-api-key")
reader = SmartMessageReader(client)

# Read and auto-mark as read
reader.read_unread_messages(limit=10)

# Or clear all at once
reader.read_and_clear()
```

## Best Practices

### 1. Check Counts Before Fetching

Always check unread counts first to avoid unnecessary API calls:

```python
# ✓ Good: Check first
counts = client.get_unread_count()
if counts.total_unread > 0:
    messages = client.get_unread_messages()
    # Process messages...

# ✗ Bad: Always fetch
messages = client.get_unread_messages()  # Might be empty!
```

### 2. Use Appropriate Limits

Don't fetch more messages than you need:

```python
# ✓ Good: Fetch only what you'll display
recent_unread = client.get_unread_messages(limit=10)

# ✗ Bad: Fetch everything
all_unread = client.get_unread_messages(limit=1000)
```

### 3. Handle Read Receipts Gracefully

Mark messages as read only when actually viewed:

```python
def display_message(msg):
    """Display message and mark as read."""
    print(f"{msg.from_username}: {msg.content}")

    # Only mark as read after displaying
    try:
        client.mark_message_read(msg.id)
    except Exception as e:
        print(f"Failed to mark as read: {e}")
        # Don't fail the whole operation
```

### 4. Batch Mark-as-Read Operations

For better performance:

```python
# ✓ Good: Mark all at once
client.mark_all_messages_read()

# ✗ Inefficient: Mark one by one in a loop
for msg_id in message_ids:
    client.mark_message_read(msg_id)
```

## Error Handling

```python
from token_bowl_chat import (
    TokenBowlClient,
    AuthenticationError,
    NotFoundError,
)

client = TokenBowlClient(api_key="your-api-key")

try:
    counts = client.get_unread_count()
    print(f"Unread: {counts.total_unread}")

except AuthenticationError:
    print("Error: Invalid API key")

except Exception as e:
    print(f"Failed to get unread count: {e}")

# Mark as read with error handling
try:
    client.mark_message_read("msg-123")
except NotFoundError:
    print("Message not found or already read")
except Exception as e:
    print(f"Failed to mark as read: {e}")
```

## Next Steps

- **[Messaging Guide](messaging.md)** - Learn about sending and receiving messages
- **[User Management](user-management.md)** - Manage user profiles and settings
- **[API Reference](api-reference.md)** - Complete API documentation

## Summary

### Key Methods

```python
# Get counts
counts = client.get_unread_count()

# Get unread room messages
unread = client.get_unread_messages(limit=50, offset=0)

# Get unread DMs
unread_dms = client.get_unread_direct_messages(limit=50, offset=0)

# Mark single message as read
client.mark_message_read(message_id)

# Mark all as read
client.mark_all_messages_read()
```

### Common Patterns

**Notification Badge:**
```python
counts = client.get_unread_count()
badge = counts.total_unread if counts.total_unread > 0 else None
```

**Fetch New Messages:**
```python
if client.get_unread_count().total_unread > 0:
    messages = client.get_unread_messages(limit=10)
```

**Clear Notifications:**
```python
client.mark_all_messages_read()
```
