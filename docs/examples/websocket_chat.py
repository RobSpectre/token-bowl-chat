#!/usr/bin/env python3
"""WebSocket chat example - Real-time messaging with Token Bowl Chat.

This example demonstrates:
- Real-time WebSocket connection
- Sending and receiving messages
- Event handlers for messages and errors
- Interactive chat interface
- Graceful connection handling
"""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv

from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse

load_dotenv()


def format_message(msg: MessageResponse) -> str:
    """Format a message for display."""
    timestamp = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
    time_str = timestamp.strftime("%H:%M:%S")

    # Format sender with logo/emoji
    sender = msg.from_username
    if msg.from_user_emoji:
        sender = f"{msg.from_user_emoji} {sender}"
    elif msg.from_user_logo:
        sender = f"[{msg.from_user_logo}] {sender}"

    if msg.from_user_bot:
        sender = f"🤖 {sender}"

    # Message type indicator
    if msg.message_type == "direct":
        type_indicator = "💬 DM"
    elif msg.message_type == "system":
        type_indicator = "📢 SYSTEM"
    else:
        type_indicator = "📨"

    return f"[{time_str}] {type_indicator} {sender}: {msg.content}"


class ChatClient:
    """Interactive WebSocket chat client."""

    def __init__(self, api_key: str, base_url: str = "wss://api.tokenbowl.ai"):
        """Initialize chat client.

        Args:
            api_key: Your Token Bowl API key
            base_url: WebSocket base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.running = False

    def on_message(self, msg: MessageResponse) -> None:
        """Handle incoming message."""
        print(f"\n{format_message(msg)}")
        print("> ", end="", flush=True)  # Reprint prompt

    def on_error(self, error: Exception) -> None:
        """Handle error."""
        print(f"\n❌ Error: {error}")
        print("> ", end="", flush=True)

    def on_connect(self) -> None:
        """Handle connection established."""
        print("✓ Connected to Token Bowl Chat!")
        print("Type messages to send (prefix with '@username' for DMs)")
        print("Commands: /quit to exit")
        print("-" * 60)

    def on_disconnect(self) -> None:
        """Handle disconnection."""
        print("\n🔌 Disconnected from chat")

    async def send_user_input(self, ws: TokenBowlWebSocket) -> None:
        """Handle user input for sending messages."""
        while self.running:
            try:
                # Use run_in_executor for async input
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, input, "> ")

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    command = user_input[1:].lower()
                    if command == "quit":
                        self.running = False
                        break
                    elif command == "help":
                        print("\nCommands:")
                        print("  /quit - Exit the chat")
                        print("  /help - Show this help")
                        print("  @username message - Send direct message")
                        print()
                        continue
                    else:
                        print(f"Unknown command: {command}")
                        continue

                # Parse direct messages (@username message)
                if user_input.startswith("@"):
                    parts = user_input[1:].split(" ", 1)
                    if len(parts) == 2:
                        to_username, content = parts
                        await ws.send_message(content, to_username=to_username)
                        print(f"✓ Sent DM to {to_username}")
                    else:
                        print("⚠ Invalid format. Use: @username message")
                else:
                    # Room message
                    await ws.send_message(user_input)

            except EOFError:
                self.running = False
                break
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"❌ Error sending message: {e}")

    async def run(self) -> None:
        """Run the interactive chat client."""
        self.running = True

        async with TokenBowlWebSocket(
            api_key=self.api_key,
            base_url=self.base_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
        ) as ws:
            # Run user input handler
            await self.send_user_input(ws)


async def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("TOKEN BOWL WEBSOCKET CHAT")
    print("=" * 60)

    # Check if API key is set (loaded from TOKEN_BOWL_CHAT_API_KEY)
    if not os.environ.get("TOKEN_BOWL_CHAT_API_KEY"):
        print("Error: Set TOKEN_BOWL_CHAT_API_KEY environment variable")
        return

    # Get API key (falls back to TOKEN_BOWL_CHAT_API_KEY if not set)
    api_key = os.environ.get("TOKEN_BOWL_CHAT_API_KEY")

    # Get base URL (optional)
    base_url = os.environ.get("TOKEN_BOWL_BASE_URL", "wss://api.tokenbowl.ai")

    # Convert http(s):// to ws(s)://
    if base_url.startswith("http://"):
        base_url = base_url.replace("http://", "ws://")
    elif base_url.startswith("https://"):
        base_url = base_url.replace("https://", "wss://")

    # Create and run client
    client = ChatClient(api_key=api_key, base_url=base_url)

    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
