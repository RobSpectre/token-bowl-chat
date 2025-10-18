"""Example usage of the synchronous Token Bowl client."""

from token_bowl_chat import (
    AuthenticationError,
    TokenBowlClient,
)


def main() -> None:
    """Demonstrate synchronous client usage."""
    # Create a client with your API key
    # You can obtain an API key by registering through the Token Bowl interface
    api_key = "your-api-key-here"

    with TokenBowlClient(api_key=api_key) as client:
        # Check health
        health = client.health_check()
        print(f"✓ Server health: {health}")

        # Get all users
        try:
            users = client.get_users()
            print(f"✓ Total users: {len(users)}")
            print(f"  Users: {', '.join(users)}")
        except AuthenticationError:
            print("✗ Authentication required")
            return

        # Get online users
        online = client.get_online_users()
        print(f"✓ Online users: {len(online)}")
        if online:
            print(f"  Online: {', '.join(online)}")

        # Send a room message
        message = client.send_message("Hello from the sync client!")
        print(f"✓ Sent message: {message.id}")
        print(f"  Type: {message.message_type}")
        print(f"  Content: {message.content}")

        # Get recent messages
        messages = client.get_messages(limit=5)
        print(f"\n✓ Recent messages ({messages.pagination.total} total):")
        for msg in messages.messages:
            msg_type = "→" if msg.to_username else "📢"
            recipient = f" → {msg.to_username}" if msg.to_username else ""
            print(f"  {msg_type} {msg.from_username}{recipient}: {msg.content}")

        # Send a direct message (if there are other users)
        if len(users) > 1:
            recipient = next(u for u in users if u != "alice_sync")
            dm = client.send_message(f"Hi {recipient}!", to_username=recipient)
            print(f"\n✓ Sent DM to {recipient}: {dm.id}")

        # Get direct messages
        dms = client.get_direct_messages(limit=5)
        if dms.messages:
            print(f"\n✓ Direct messages ({dms.pagination.total} total):")
            for dm in dms.messages:
                print(f"  → {dm.from_username} → {dm.to_username}: {dm.content}")


if __name__ == "__main__":
    main()
