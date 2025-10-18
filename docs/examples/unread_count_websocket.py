#!/usr/bin/env python3
"""Unread count tracking via WebSocket - Real-time unread message monitoring.

This example demonstrates:
- Requesting unread count updates via WebSocket
- Receiving real-time unread count changes
- Marking messages as read and seeing count updates
- Building an interactive unread count dashboard
- Comparing HTTP vs WebSocket approaches for unread tracking

Prerequisites:
    export TOKEN_BOWL_CHAT_API_KEY="your-api-key-here"

Usage:
    python unread_count_websocket.py
"""

import asyncio
import contextlib
import os
from datetime import datetime

from dotenv import load_dotenv

from token_bowl_chat import TokenBowlWebSocket
from token_bowl_chat.models import MessageResponse, UnreadCountResponse

load_dotenv()


class UnreadCountTracker:
    """Track unread counts in real-time via WebSocket."""

    def __init__(self):
        self.ws = None
        self.count = None
        self.count_history = []
        self.recent_messages = []
        self.max_recent = 10

    def on_message(self, msg: MessageResponse):
        """Handle incoming messages."""
        # Add to recent messages
        self.recent_messages.append(msg)
        if len(self.recent_messages) > self.max_recent:
            self.recent_messages.pop(0)

        # Display message
        timestamp = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
        time_str = timestamp.strftime("%H:%M:%S")

        sender = msg.from_username
        if msg.from_user_emoji:
            sender = f"{msg.from_user_emoji} {sender}"

        msg_type = "💬 DM" if msg.message_type == "direct" else "📢"
        print(f"\n[{time_str}] {msg_type} {sender}: {msg.content}")

        # Request updated count
        if self.ws and self.ws.is_connected:
            asyncio.create_task(self.ws.get_unread_count())

    def on_unread_count(self, count: UnreadCountResponse):
        """Handle unread count updates."""
        # Calculate change from previous
        change = None
        if self.count is not None:
            change = count.total_unread - self.count.total_unread

        # Store count
        self.count = count
        self.count_history.append((datetime.now(), count))

        # Keep history limited
        if len(self.count_history) > 100:
            self.count_history.pop(0)

        # Display update
        self._display_count_update(change)

    def _display_count_update(self, change: int | None):
        """Display unread count update."""
        if change is None:
            # Initial count
            print(f"\n📬 Unread: {self.count.total_unread}")
        elif change > 0:
            print(f"\n📬 +{change} unread (total: {self.count.total_unread})")
        elif change < 0:
            print(
                f"\n✓ {abs(change)} marked read (remaining: {self.count.total_unread})"
            )
        else:
            print(f"\n📬 Unread count unchanged: {self.count.total_unread}")

        # Show breakdown
        if self.count.unread_room_messages > 0 or self.count.unread_direct_messages > 0:
            print(
                f"   Room: {self.count.unread_room_messages} | "
                f"DM: {self.count.unread_direct_messages}"
            )

    def get_statistics(self) -> dict:
        """Get tracking statistics."""
        stats = {
            "current_count": self.count,
            "total_updates": len(self.count_history),
            "recent_messages": len(self.recent_messages),
        }

        # Calculate peak unread
        if self.count_history:
            peak = max(c.total_unread for _, c in self.count_history)
            stats["peak_unread"] = peak

        return stats


class UnreadDashboard:
    """Interactive dashboard for unread count management."""

    def __init__(self, tracker: UnreadCountTracker):
        self.tracker = tracker

    def display(self):
        """Display the dashboard."""
        # Clear screen (ANSI escape code)
        print("\033[2J\033[H", end="")

        # Header
        print("=" * 70)
        print("UNREAD MESSAGE DASHBOARD".center(70))
        print("=" * 70)
        print()

        # Current count
        if self.tracker.count:
            print("📬 CURRENT UNREAD COUNT")
            print("-" * 70)
            print(
                f"  Room Messages:   {self.tracker.count.unread_room_messages:>4} unread"
            )
            print(
                f"  Direct Messages: {self.tracker.count.unread_direct_messages:>4} unread"
            )
            print(f"  {'─' * 30}")
            print(f"  Total Unread:    {self.tracker.count.total_unread:>4}")
            print()

        # Recent messages
        if self.tracker.recent_messages:
            print(f"📨 RECENT MESSAGES (last {len(self.tracker.recent_messages)})")
            print("-" * 70)

            for msg in self.tracker.recent_messages[-5:]:
                timestamp = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
                time_str = timestamp.strftime("%H:%M:%S")

                msg_type = "DM  " if msg.message_type == "direct" else "ROOM"
                sender = msg.from_username[:15].ljust(15)
                content = (
                    (msg.content[:35] + "...") if len(msg.content) > 35 else msg.content
                )

                print(f"  [{time_str}] [{msg_type}] {sender} {content}")
            print()

        # Statistics
        stats = self.tracker.get_statistics()
        if stats["total_updates"] > 0:
            print("📊 STATISTICS")
            print("-" * 70)
            print(f"  Count Updates: {stats['total_updates']}")
            if "peak_unread" in stats:
                print(f"  Peak Unread:   {stats['peak_unread']}")
            print()

        # Actions
        print("⚡ ACTIONS")
        print("-" * 70)
        print("  1 - Refresh count")
        print("  2 - Mark all room messages as read")
        print("  3 - Mark all messages as read")
        print("  4 - Send test message")
        print("  S - Show statistics")
        print("  Q - Quit")
        print()
        print("> ", end="", flush=True)


async def interactive_mode(tracker: UnreadCountTracker):
    """Run interactive dashboard mode."""
    dashboard = UnreadDashboard(tracker)

    # Initial display
    dashboard.display()

    # Auto-refresh every 15 seconds
    async def auto_refresh():
        while True:
            await asyncio.sleep(15)
            if tracker.ws and tracker.ws.is_connected:
                await tracker.ws.get_unread_count()
                dashboard.display()

    refresh_task = asyncio.create_task(auto_refresh())

    try:
        while True:
            # Get user input
            loop = asyncio.get_event_loop()
            action = await loop.run_in_executor(None, input)

            action = action.strip().upper()

            if action == "Q":
                break

            elif action == "1":
                print("\n🔄 Refreshing count...")
                await tracker.ws.get_unread_count()
                await asyncio.sleep(0.5)
                dashboard.display()

            elif action == "2":
                print("\n🧹 Marking all room messages as read...")
                await tracker.ws.mark_room_messages_read()
                await asyncio.sleep(0.5)
                await tracker.ws.get_unread_count()
                await asyncio.sleep(0.5)
                dashboard.display()

            elif action == "3":
                print("\n🧹 Marking ALL messages as read...")
                await tracker.ws.mark_all_messages_read()
                await asyncio.sleep(0.5)
                await tracker.ws.get_unread_count()
                await asyncio.sleep(0.5)
                dashboard.display()

            elif action == "4":
                print("\n📤 Sending test message...")
                await tracker.ws.send_message("Test message for unread count tracking")
                await asyncio.sleep(0.5)
                dashboard.display()

            elif action == "S":
                stats = tracker.get_statistics()
                print("\n" + "=" * 70)
                print("DETAILED STATISTICS")
                print("=" * 70)

                if stats["current_count"]:
                    print(f"\nCurrent Count: {stats['current_count'].total_unread}")
                    print(f"  Room: {stats['current_count'].unread_room_messages}")
                    print(f"  DM:   {stats['current_count'].unread_direct_messages}")

                print(f"\nTotal Updates Received: {stats['total_updates']}")
                print(f"Recent Messages Tracked: {stats['recent_messages']}")

                if "peak_unread" in stats:
                    print(f"Peak Unread Count: {stats['peak_unread']}")

                if tracker.count_history:
                    print("\nCount History (last 5):")
                    for timestamp, count in tracker.count_history[-5:]:
                        time_str = timestamp.strftime("%H:%M:%S")
                        print(f"  [{time_str}] Total: {count.total_unread}")

                input("\nPress Enter to continue...")
                dashboard.display()

            else:
                print("\n⚠ Invalid action")
                await asyncio.sleep(1)
                dashboard.display()

    finally:
        refresh_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await refresh_task


async def monitoring_mode(tracker: UnreadCountTracker):
    """Run simple monitoring mode (no dashboard)."""
    print("\n📊 Monitoring unread counts...")
    print("Press Ctrl+C to exit\n")

    # Get initial count
    await tracker.ws.get_unread_count()

    # Poll every 10 seconds
    try:
        while True:
            await asyncio.sleep(10)
            await tracker.ws.get_unread_count()

    except KeyboardInterrupt:
        print("\n\nStopped monitoring")


async def main():
    """Run the unread count tracker."""
    # Check for API key
    if not os.environ.get("TOKEN_BOWL_CHAT_API_KEY"):
        print("Error: Set TOKEN_BOWL_CHAT_API_KEY environment variable")
        return

    print("=" * 70)
    print("UNREAD COUNT TRACKER (WebSocket)")
    print("=" * 70)
    print("\nReal-time unread message count tracking via WebSocket")
    print()
    print("Features:")
    print("  ✓ Real-time count updates")
    print("  ✓ Automatic refresh on new messages")
    print("  ✓ Mark messages as read")
    print("  ✓ Interactive dashboard")
    print()

    # Select mode
    print("Select mode:")
    print("  1. Interactive Dashboard (default)")
    print("  2. Simple Monitoring")
    print()

    mode = input("Mode (1-2): ").strip()

    tracker = UnreadCountTracker()

    try:
        async with TokenBowlWebSocket(
            on_message=tracker.on_message,
            on_unread_count=tracker.on_unread_count,
        ) as ws:
            tracker.ws = ws

            print("\n✓ Connected to Token Bowl Chat\n")

            # Get initial count
            await tracker.ws.get_unread_count()
            await asyncio.sleep(0.5)

            if mode == "2":
                await monitoring_mode(tracker)
            else:
                await interactive_mode(tracker)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback

        traceback.print_exc()

    print("\nGoodbye!")


if __name__ == "__main__":
    asyncio.run(main())
