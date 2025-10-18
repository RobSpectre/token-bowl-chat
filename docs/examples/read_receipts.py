#!/usr/bin/env python3
"""Read receipts example - Track message reads and auto-mark messages as read.

This example demonstrates:
- Receiving read receipt events when others read your messages
- Automatically marking incoming messages as read after viewing
- Marking specific messages, all messages, or messages by type as read
- Tracking which messages have been read by whom

Prerequisites:
    export TOKEN_BOWL_CHAT_API_KEY="your-api-key-here"

Usage:
    python read_receipts.py
"""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv

from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse

load_dotenv()


class ReadReceiptTracker:
    """Track read receipts and auto-mark messages as read."""

    def __init__(self):
        self.ws = None
        self.sent_messages = {}  # Track messages we sent
        self.received_messages = {}  # Track messages we received
        self.read_receipts = {}  # Track who read what

    def on_message(self, msg: MessageResponse):
        """Handle incoming messages."""
        timestamp = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
        time_str = timestamp.strftime("%H:%M:%S")

        # Display message with formatting
        sender = msg.from_username
        if msg.from_user_emoji:
            sender = f"{msg.from_user_emoji} {sender}"

        msg_type = "💬 DM" if msg.message_type == "direct" else "📢 Room"

        print(f"\n[{time_str}] {msg_type} from {sender}:")
        print(f"  {msg.content}")

        # Store received message
        self.received_messages[msg.id] = msg

        # Auto-mark as read after 2 seconds (simulating reading time)
        if self.ws and self.ws.is_connected:
            asyncio.create_task(self._auto_mark_read(msg.id))

    async def _auto_mark_read(self, message_id: str):
        """Automatically mark message as read after delay."""
        await asyncio.sleep(2)

        try:
            await self.ws.mark_message_read(message_id)
            print(f"  ✓ Auto-marked {message_id[:8]}... as read")
        except Exception as e:
            print(f"  ✗ Failed to mark as read: {e}")

    def on_read_receipt(self, message_id: str, read_by: str):
        """Handle read receipt events."""
        # Track the receipt
        if message_id not in self.read_receipts:
            self.read_receipts[message_id] = []
        self.read_receipts[message_id].append(read_by)

        # Display receipt
        print(f"\n✓✓ {read_by} read message {message_id[:8]}...")

        # Show message content if we have it
        if message_id in self.sent_messages:
            content = self.sent_messages[message_id]
            print(f'   Message: "{content[:50]}..."')

    async def send_message(self, content: str, to_username: str | None = None):
        """Send a message and track it."""
        await self.ws.send_message(content, to_username=to_username)

        # Note: We don't get the message ID back from send_message directly.
        # In a production app, you'd listen for the message_sent confirmation
        # event which includes the message ID.

        msg_type = f"to @{to_username}" if to_username else "to room"
        print(f"\n📤 Sent {msg_type}: {content}")

    async def mark_all_room_read(self):
        """Mark all room messages as read."""
        print("\n🧹 Marking all room messages as read...")
        await self.ws.mark_room_messages_read()
        print("✓ Done")

    async def mark_all_read(self):
        """Mark all messages as read."""
        print("\n🧹 Marking ALL messages as read...")
        await self.ws.mark_all_messages_read()
        print("✓ Done")

    async def mark_direct_messages_read(self, from_username: str):
        """Mark all DMs from a user as read."""
        print(f"\n🧹 Marking all DMs from {from_username} as read...")
        await self.ws.mark_direct_messages_read(from_username)
        print("✓ Done")

    def show_statistics(self):
        """Display read receipt statistics."""
        print("\n" + "=" * 60)
        print("READ RECEIPT STATISTICS")
        print("=" * 60)

        print(f"\nMessages Sent: {len(self.sent_messages)}")
        print(f"Messages Received: {len(self.received_messages)}")
        print(f"Read Receipts: {len(self.read_receipts)}")

        if self.read_receipts:
            print("\nRead Receipt Details:")
            for msg_id, readers in self.read_receipts.items():
                readers_list = ", ".join(readers)
                print(f"  {msg_id[:8]}... read by: {readers_list}")

        print("=" * 60)


async def interactive_mode(tracker: ReadReceiptTracker):
    """Run interactive command mode."""
    print("\nCOMMANDS:")
    print("  send <message>           - Send room message")
    print("  dm <username> <message>  - Send direct message")
    print("  mark room                - Mark all room messages as read")
    print("  mark all                 - Mark all messages as read")
    print("  mark dm <username>       - Mark DMs from user as read")
    print("  stats                    - Show statistics")
    print("  quit                     - Exit")
    print()

    while True:
        try:
            # Get user input
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, input, "> ")

            if not user_input.strip():
                continue

            # Parse command
            parts = user_input.strip().split(maxsplit=2)
            command = parts[0].lower()

            if command == "quit":
                break

            elif command == "send" and len(parts) >= 2:
                message = " ".join(parts[1:])
                await tracker.send_message(message)

            elif command == "dm" and len(parts) >= 3:
                username = parts[1]
                message = " ".join(parts[2:])
                await tracker.send_message(message, to_username=username)

            elif command == "mark" and len(parts) >= 2:
                action = parts[1].lower()

                if action == "room":
                    await tracker.mark_all_room_read()

                elif action == "all":
                    await tracker.mark_all_read()

                elif action == "dm" and len(parts) >= 3:
                    username = parts[2]
                    await tracker.mark_direct_messages_read(username)

                else:
                    print("Invalid mark command. Use: mark room|all|dm <username>")

            elif command == "stats":
                tracker.show_statistics()

            else:
                print("Unknown command. Type 'quit' to exit.")

        except (EOFError, KeyboardInterrupt):
            break


async def main():
    """Run the read receipt tracker."""
    # Check for API key
    if not os.environ.get("TOKEN_BOWL_CHAT_API_KEY"):
        print("Error: Set TOKEN_BOWL_CHAT_API_KEY environment variable")
        return

    print("=" * 60)
    print("READ RECEIPT TRACKER")
    print("=" * 60)
    print("\nFeatures:")
    print("  ✓ Auto-marks incoming messages as read after 2 seconds")
    print("  ✓ Tracks read receipts for your messages")
    print("  ✓ Manual mark-as-read controls")
    print("  ✓ Statistics and tracking")
    print()

    tracker = ReadReceiptTracker()

    try:
        async with TokenBowlWebSocket(
            on_message=tracker.on_message,
            on_read_receipt=tracker.on_read_receipt,
        ) as ws:
            tracker.ws = ws

            print("✓ Connected to Token Bowl Chat\n")

            # Send a welcome message
            await tracker.send_message("Hello! Testing read receipts...")

            # Run interactive mode
            await interactive_mode(tracker)

            # Show final stats
            tracker.show_statistics()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")

    print("\nGoodbye!")


if __name__ == "__main__":
    asyncio.run(main())
