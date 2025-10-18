#!/usr/bin/env python3
"""Unread message tracker - Monitor and manage unread messages."""

import os
import time

from dotenv import load_dotenv

from token_bowl_chat import TokenBowlClient

load_dotenv()


def display_unread_summary(client: TokenBowlClient):
    """Display unread message summary."""
    counts = client.get_unread_count()

    if counts.total_unread == 0:
        print("✓ No unread messages")
        return

    print(f"\n🔔 {counts.total_unread} Unread Messages")
    print("=" * 50)
    print(f"Room messages: {counts.unread_room_messages}")
    print(f"Direct messages: {counts.unread_direct_messages}")
    print("=" * 50)


def show_unread_messages(client: TokenBowlClient):
    """Show unread messages."""
    counts = client.get_unread_count()

    if counts.total_unread == 0:
        print("\n✓ All caught up!")
        return

    # Show unread room messages
    if counts.unread_room_messages > 0:
        print(f"\n📢 Unread Room Messages ({counts.unread_room_messages}):")
        unread_room = client.get_unread_messages(limit=10)

        for msg in unread_room:
            print(f"  [{msg.timestamp}] {msg.from_username}: {msg.content}")

    # Show unread DMs
    if counts.unread_direct_messages > 0:
        print(f"\n💬 Unread Direct Messages ({counts.unread_direct_messages}):")
        unread_dms = client.get_unread_direct_messages(limit=10)

        for msg in unread_dms:
            print(f"  {msg.from_username}: {msg.content}")


def mark_all_read(client: TokenBowlClient):
    """Mark all messages as read."""
    result = client.mark_all_messages_read()
    count = result.get("messages_marked_read", 0)
    print(f"✓ Marked {count} messages as read")


def poll_for_messages(client: TokenBowlClient, interval: int = 30):
    """Poll for new messages."""
    print(f"Polling for messages every {interval} seconds...")
    print("Press Ctrl+C to stop\n")

    last_count = 0

    try:
        while True:
            counts = client.get_unread_count()
            current_count = counts.total_unread

            if current_count > last_count:
                new_count = current_count - last_count
                print(f"\n🔔 {new_count} new message(s)! Total unread: {current_count}")

                # Get new messages
                unread = client.get_unread_messages(limit=new_count)
                for msg in unread:
                    print(f"   {msg.from_username}: {msg.content}")

            last_count = current_count
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nStopped polling")


def main():
    """Unread message tracker."""
    # Check if API key is set (loaded from TOKEN_BOWL_CHAT_API_KEY)
    if not os.environ.get("TOKEN_BOWL_CHAT_API_KEY"):
        print("Error: Set TOKEN_BOWL_CHAT_API_KEY environment variable")
        return

    # Client automatically loads TOKEN_BOWL_CHAT_API_KEY
    with TokenBowlClient() as client:
        while True:
            print("\n" + "=" * 50)
            print("UNREAD MESSAGE TRACKER")
            print("=" * 50)

            display_unread_summary(client)

            print("\nOPTIONS:")
            print("  1. Show unread messages")
            print("  2. Mark all as read")
            print("  3. Start polling (30s)")
            print("  0. Exit")

            choice = input("\nSelect option: ")

            if choice == "1":
                show_unread_messages(client)
                input("\nPress Enter to continue...")

            elif choice == "2":
                confirm = input("Mark all as read? (y/n): ")
                if confirm.lower() == "y":
                    mark_all_read(client)
                input("\nPress Enter to continue...")

            elif choice == "3":
                poll_for_messages(client)

            elif choice == "0":
                break

            else:
                print("Invalid option")


if __name__ == "__main__":
    main()
