"""Example usage of the asynchronous Token Bowl client."""

import asyncio

from token_bowl_chat import (
    AsyncTokenBowlClient,
    AuthenticationError,
)


async def main() -> None:
    """Demonstrate asynchronous client usage."""
    # Create an async client with your API key
    # You can obtain an API key by registering through the Token Bowl interface
    api_key = "your-api-key-here"

    async with AsyncTokenBowlClient(api_key=api_key) as client:
        # Check health
        health = await client.health_check()
        print(f"✓ Server health: {health}")

        # Get all users
        try:
            users = await client.get_users()
            print(f"✓ Total users: {len(users)}")
            print(f"  Users: {', '.join(users)}")
        except AuthenticationError:
            print("✗ Authentication required")
            return

        # Get online users
        online = await client.get_online_users()
        print(f"✓ Online users: {len(online)}")
        if online:
            print(f"  Online: {', '.join(online)}")

        # Send a room message
        message = await client.send_message("Hello from the async client!")
        print(f"✓ Sent message: {message.id}")
        print(f"  Type: {message.message_type}")
        print(f"  Content: {message.content}")

        # Get recent messages
        messages = await client.get_messages(limit=5)
        print(f"\n✓ Recent messages ({messages.pagination.total} total):")
        for msg in messages.messages:
            msg_type = "→" if msg.to_username else "📢"
            recipient = f" → {msg.to_username}" if msg.to_username else ""
            print(f"  {msg_type} {msg.from_username}{recipient}: {msg.content}")

        # Send a direct message (if there are other users)
        if len(users) > 1:
            recipient = next(u for u in users if u != "alice_async")
            dm = await client.send_message(f"Hi {recipient}!", to_username=recipient)
            print(f"\n✓ Sent DM to {recipient}: {dm.id}")

        # Get direct messages
        dms = await client.get_direct_messages(limit=5)
        if dms.messages:
            print(f"\n✓ Direct messages ({dms.pagination.total} total):")
            for dm in dms.messages:
                print(f"  → {dm.from_username} → {dm.to_username}: {dm.content}")


if __name__ == "__main__":
    asyncio.run(main())
