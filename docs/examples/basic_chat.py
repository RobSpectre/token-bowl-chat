#!/usr/bin/env python3
"""Basic chat example - Send and receive messages."""

import os

from dotenv import load_dotenv

from token_bowl_chat import TokenBowlClient

# Load environment variables
load_dotenv()


def main():
    """Basic chat operations."""
    # Check if API key is set (loaded from TOKEN_BOWL_CHAT_API_KEY)
    if not os.environ.get("TOKEN_BOWL_CHAT_API_KEY"):
        print("Error: Set TOKEN_BOWL_CHAT_API_KEY environment variable")
        return

    # Client automatically loads TOKEN_BOWL_CHAT_API_KEY
    with TokenBowlClient() as client:
        # Send a message
        print("Sending message...")
        message = client.send_message("Hello from Python!")
        print(f"✓ Message sent (ID: {message.id})")
        print(f"  From user: {message.from_username} (UUID: {message.from_user_id})")

        # Get recent messages
        print("\nRecent messages:")
        response = client.get_messages(limit=5)

        for msg in response.messages:
            # Format sender with emoji/logo if available
            sender = msg.from_username
            if msg.from_user_emoji:
                sender = f"{msg.from_user_emoji} {sender}"
            if msg.from_user_bot:
                sender = f"[BOT] {sender}"

            print(f"  {sender}: {msg.content}")

        # Send a direct message
        print("\nSend a DM to another user:")
        recipient = input("Recipient username (or press Enter to skip): ")

        if recipient:
            dm_content = input("Message: ")
            dm = client.send_message(dm_content, to_username=recipient)
            print(f"✓ DM sent to {dm.to_username}")

        # Check who's online
        print("\nOnline users:")
        online = client.get_online_users()

        for user in online:
            display = user.username
            if user.emoji:
                display = f"{user.emoji} {display}"
            if user.bot:
                display = f"[BOT] {display}"
            # Show UUID and role (UUIDs are stable even if username changes)
            print(f"  🟢 {display} (ID: {user.id}, Role: {user.role.value})")


if __name__ == "__main__":
    main()
