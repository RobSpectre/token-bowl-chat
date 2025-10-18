#!/usr/bin/env python3
"""Basic WebSocket example - Simple real-time messaging."""

import asyncio
import os

from dotenv import load_dotenv

from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse

load_dotenv()


async def main() -> None:
    """Demonstrate basic WebSocket usage."""
    # Check if API key is set (loaded from TOKEN_BOWL_CHAT_API_KEY)
    if not os.environ.get("TOKEN_BOWL_CHAT_API_KEY"):
        print("Error: Set TOKEN_BOWL_CHAT_API_KEY environment variable")
        return

    print("Connecting to Token Bowl Chat via WebSocket...")

    # Define message handler
    def on_message(msg: MessageResponse):
        """Handle incoming messages."""
        sender = msg.from_username
        if msg.from_user_emoji:
            sender = f"{msg.from_user_emoji} {sender}"

        if msg.message_type == "direct":
            print(f"💬 DM from {sender}: {msg.content}")
        else:
            print(f"📢 {sender}: {msg.content}")

    # Connect and send messages (WebSocket automatically loads TOKEN_BOWL_CHAT_API_KEY)
    async with TokenBowlWebSocket(on_message=on_message) as ws:
        print("✓ Connected!")

        # Send a room message
        await ws.send_message("Hello from WebSocket! 👋")
        print("✓ Sent room message")

        # Send a direct message
        await ws.send_message("This is a private message", to_username="another_user")
        print("✓ Sent direct message")

        # Keep connection open to receive messages
        print("\nListening for messages for 30 seconds...")
        print("(Press Ctrl+C to exit early)\n")

        try:
            await asyncio.sleep(30)
        except KeyboardInterrupt:
            print("\n\nDisconnecting...")

    print("✓ Disconnected")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
