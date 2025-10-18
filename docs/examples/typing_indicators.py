#!/usr/bin/env python3
"""Typing indicators example - Show and receive typing status in real-time.

This example demonstrates:
- Sending typing indicators for room messages
- Sending typing indicators for direct messages
- Receiving typing indicators from other users
- Smart typing indicator management (auto-send while composing)
- Displaying typing status in real-time

Prerequisites:
    export TOKEN_BOWL_CHAT_API_KEY="your-api-key-here"

Usage:
    python typing_indicators.py
"""

import asyncio
import contextlib
import os
import time
from datetime import datetime

from dotenv import load_dotenv

from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse

load_dotenv()


class TypingIndicatorManager:
    """Manage typing indicators with smart auto-sending."""

    def __init__(self, ws: TokenBowlWebSocket):
        self.ws = ws
        self.typing_task = None
        self.is_typing = False
        self.typing_to = None

    async def start_typing(self, to_username: str | None = None):
        """Start showing typing indicator."""
        if self.is_typing and self.typing_to == to_username:
            return  # Already typing to this recipient

        # Stop any existing typing
        if self.is_typing:
            await self.stop_typing()

        self.is_typing = True
        self.typing_to = to_username

        # Start the typing indicator loop
        self.typing_task = asyncio.create_task(self._typing_loop())

    async def stop_typing(self):
        """Stop showing typing indicator."""
        self.is_typing = False
        self.typing_to = None

        if self.typing_task:
            self.typing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.typing_task

    async def _typing_loop(self):
        """Send typing indicator every 3 seconds while typing."""
        try:
            while self.is_typing:
                await self.ws.send_typing_indicator(to_username=self.typing_to)
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n⚠ Error sending typing indicator: {e}")


class TypingChat:
    """Chat client with typing indicators."""

    def __init__(self):
        self.ws = None
        self.typing_manager = None
        self.typing_users = {}  # username -> (to_username, timestamp)
        self.display_task = None

    def on_message(self, msg: MessageResponse):
        """Handle incoming messages."""
        # Remove from typing when message arrives
        if msg.from_username in self.typing_users:
            del self.typing_users[msg.from_username]

        timestamp = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
        time_str = timestamp.strftime("%H:%M:%S")

        # Format sender
        sender = msg.from_username
        if msg.from_user_emoji:
            sender = f"{msg.from_user_emoji} {sender}"
        if msg.from_user_bot:
            sender = f"🤖 {sender}"

        # Format message type
        if msg.message_type == "direct":
            msg_type = "💬 DM"
            if msg.to_username:
                msg_type = f"💬 DM to {msg.to_username}"
        elif msg.message_type == "system":
            msg_type = "📢 SYSTEM"
        else:
            msg_type = "📨 Room"

        print(f"\n[{time_str}] {msg_type} {sender}")
        print(f"  {msg.content}")

        self._show_typing_status()
        print("\n> ", end="", flush=True)

    def on_typing(self, username: str, to_username: str | None):
        """Handle typing indicator events."""
        # Record typing with timestamp
        self.typing_users[username] = (to_username, time.time())

        self._show_typing_status()

    def _show_typing_status(self):
        """Display who's currently typing."""
        # Clean up old typing indicators (older than 5 seconds)
        current_time = time.time()
        self.typing_users = {
            user: (to_user, ts)
            for user, (to_user, ts) in self.typing_users.items()
            if current_time - ts < 5
        }

        if not self.typing_users:
            return

        # Group by type
        room_typing = []
        dm_typing = []

        for username, (to_username, _) in self.typing_users.items():
            if to_username is None:
                room_typing.append(username)
            else:
                dm_typing.append((username, to_username))

        # Display typing status
        status_lines = []

        if room_typing:
            users = ", ".join(sorted(room_typing))
            verb = "is" if len(room_typing) == 1 else "are"
            status_lines.append(f"💬 {users} {verb} typing in room")

        if dm_typing:
            for username, to_username in dm_typing:
                status_lines.append(f"💬 {username} is typing to {to_username}")

        if status_lines:
            print(f"\r{' | '.join(status_lines)}{' ' * 20}", end="", flush=True)

    async def send_with_typing(self, content: str, to_username: str | None = None):
        """Send message with realistic typing indicator."""
        # Calculate typing duration based on message length
        # Simulate ~60 WPM typing speed (5 characters per second)
        typing_duration = min(len(content) / 5.0, 10.0)  # Cap at 10 seconds

        # Start typing indicator
        await self.typing_manager.start_typing(to_username=to_username)

        recipient = f"to @{to_username}" if to_username else "to room"
        print(f"\n✍️  Typing {recipient}... ", end="", flush=True)

        # Simulate typing
        await asyncio.sleep(typing_duration)

        # Stop typing and send
        await self.typing_manager.stop_typing()
        await self.ws.send_message(content, to_username=to_username)

        print("✓ Sent")

    async def interactive_loop(self):
        """Run interactive chat loop."""
        print("\nCOMMANDS:")
        print("  <message>             - Send to room (with typing)")
        print("  @username <message>   - Send DM (with typing)")
        print("  /fast <message>       - Send immediately (no typing)")
        print("  /quit                 - Exit")
        print()

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

                elif user_input.startswith("/fast "):
                    # Send immediately without typing
                    message = user_input[6:]
                    await self.ws.send_message(message)
                    print("✓ Sent (no typing indicator)")

                elif user_input.startswith("@"):
                    # Direct message with typing
                    parts = user_input[1:].split(None, 1)
                    if len(parts) == 2:
                        to_username, content = parts
                        await self.send_with_typing(content, to_username=to_username)
                    else:
                        print("⚠ Format: @username message")

                else:
                    # Room message with typing
                    await self.send_with_typing(user_input)

            except (EOFError, KeyboardInterrupt):
                break

    async def run(self):
        """Run the typing indicator chat."""
        # Initialize typing manager
        self.typing_manager = TypingIndicatorManager(self.ws)

        # Send welcome message
        await self.ws.send_message("👋 Joined chat with typing indicators enabled!")

        # Run interactive loop
        await self.interactive_loop()

        # Cleanup
        if self.typing_manager:
            await self.typing_manager.stop_typing()


async def demo_mode():
    """Run a demonstration of typing indicators."""
    print("\n" + "=" * 60)
    print("TYPING INDICATORS DEMO")
    print("=" * 60)
    print("\nThis demo shows automatic typing indicators:")
    print()

    async with TokenBowlWebSocket() as ws:
        manager = TypingIndicatorManager(ws)

        # Demo 1: Room typing
        print("1. Typing in room...")
        await manager.start_typing()
        await asyncio.sleep(5)
        await manager.stop_typing()
        await ws.send_message("Demo message to room")
        print("   ✓ Sent message")
        await asyncio.sleep(1)

        # Demo 2: DM typing
        print("\n2. Typing DM to another user...")
        await manager.start_typing(to_username="test_user")
        await asyncio.sleep(5)
        await manager.stop_typing()
        await ws.send_message("Demo DM", to_username="test_user")
        print("   ✓ Sent DM")
        await asyncio.sleep(1)

        # Demo 3: Quick typing
        print("\n3. Quick typing (short duration)...")
        await manager.start_typing()
        await asyncio.sleep(2)
        await manager.stop_typing()
        await ws.send_message("Quick message!")
        print("   ✓ Sent quick message")

        print("\nDemo complete!")


async def main():
    """Run the typing indicator chat."""
    # Check for API key
    if not os.environ.get("TOKEN_BOWL_CHAT_API_KEY"):
        print("Error: Set TOKEN_BOWL_CHAT_API_KEY environment variable")
        return

    print("=" * 60)
    print("TYPING INDICATORS CHAT")
    print("=" * 60)
    print("\nFeatures:")
    print("  ✓ Automatic typing indicators while composing")
    print("  ✓ See when others are typing")
    print("  ✓ Smart timing based on message length")
    print("  ✓ Support for room and DM typing")
    print()

    # Ask for mode
    print("Select mode:")
    print("  1. Interactive chat (default)")
    print("  2. Demo mode")
    print()

    mode = input("Mode (1-2): ").strip()

    try:
        if mode == "2":
            await demo_mode()
        else:
            # Interactive mode
            chat = TypingChat()

            async with TokenBowlWebSocket(
                on_message=chat.on_message,
                on_typing=chat.on_typing,
            ) as ws:
                chat.ws = ws

                print("\n✓ Connected to Token Bowl Chat")

                await chat.run()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback

        traceback.print_exc()

    print("\nGoodbye!")


if __name__ == "__main__":
    asyncio.run(main())
