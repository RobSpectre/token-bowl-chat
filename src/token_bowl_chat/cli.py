#!/usr/bin/env python3
"""Token Bowl Chat CLI - Interactive command-line interface for Token Bowl Chat.

A beautiful, feature-rich CLI for interacting with Token Bowl Chat from your terminal.
Built with Typer and Rich for an amazing user experience.
"""

import asyncio
import contextlib
import os
from datetime import datetime

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from token_bowl_chat import TokenBowlClient, TokenBowlWebSocket, __version__
from token_bowl_chat.exceptions import (
    AuthenticationError,
    ConflictError,
    NetworkError,
    NotFoundError,
    ValidationError,
)
from token_bowl_chat.models import MessageResponse

# Create the main app and console
app = typer.Typer(
    name="token-bowl-chat",
    help="🎳 Token Bowl Chat CLI - Chat from your terminal!",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"token-bowl-chat version {__version__}")
        raise typer.Exit()


# Create command groups
messages_app = typer.Typer(help="📨 Send and manage messages")
users_app = typer.Typer(help="👥 Manage users and profiles")
unread_app = typer.Typer(help="📬 Track and manage unread messages")
live_app = typer.Typer(help="⚡ Real-time WebSocket features")

app.add_typer(messages_app, name="messages")
app.add_typer(users_app, name="users")
app.add_typer(unread_app, name="unread")
app.add_typer(live_app, name="live")


# Global options
@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version",
    ),
) -> None:
    """Token Bowl Chat CLI."""
    pass


def get_client(api_key: str | None = None) -> TokenBowlClient:
    """Get a configured Token Bowl client."""
    key = api_key or os.getenv("TOKEN_BOWL_CHAT_API_KEY")
    if not key:
        console.print(
            "[bold red]Error:[/bold red] No API key provided. "
            "Set TOKEN_BOWL_CHAT_API_KEY or use --api-key"
        )
        raise typer.Exit(1)

    return TokenBowlClient(api_key=key)


def handle_error(e: Exception) -> None:
    """Handle and display errors beautifully."""
    if isinstance(e, AuthenticationError):
        console.print("[bold red]Authentication Error:[/bold red] Invalid API key")
    elif isinstance(e, ValidationError):
        console.print(f"[bold red]Validation Error:[/bold red] {e.message}")
    elif isinstance(e, NotFoundError):
        console.print("[bold red]Not Found:[/bold red] Resource not found")
    elif isinstance(e, ConflictError):
        console.print("[bold red]Conflict:[/bold red] Resource already exists")
    elif isinstance(e, NetworkError):
        console.print(f"[bold red]Network Error:[/bold red] {str(e)}")
    else:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    raise typer.Exit(1)


def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to readable string."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp


# ============================================================================
# MAIN COMMANDS
# ============================================================================


@app.command()
def register(
    username: str = typer.Argument(..., help="Username to register"),
    webhook_url: str | None = typer.Option(None, "--webhook", help="Webhook URL"),
) -> None:
    """🎯 Register a new user and get an API key."""
    try:
        # Use temporary client for registration
        temp_client = TokenBowlClient(api_key="temporary")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Registering user...", total=None)
            response = temp_client.register(username=username, webhook_url=webhook_url)

        # Display success
        panel = Panel.fit(
            f"[bold green]✓[/bold green] Registration successful!\n\n"
            f"[bold]Username:[/bold] {response.username}\n"
            f"[bold]API Key:[/bold] {response.api_key}\n"
            + (
                f"[bold]Webhook:[/bold] {response.webhook_url}\n" if webhook_url else ""
            ),
            title="🎉 Welcome to Token Bowl Chat",
            border_style="green",
        )
        console.print(panel)

        console.print(
            "\n[yellow]💡 Tip:[/yellow] Save your API key to TOKEN_BOWL_CHAT_API_KEY environment variable"
        )

    except ConflictError:
        console.print(
            f"[bold red]Error:[/bold red] Username '{username}' is already taken"
        )
        raise typer.Exit(1) from None
    except Exception as e:
        handle_error(e)


@app.command()
def info(
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key"),
) -> None:
    """ℹ️  Show your profile information."""
    try:
        client = get_client(api_key)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Fetching profile...", total=None)
            profile = client.get_my_profile()

        # Create profile table
        table = Table(title="👤 Your Profile", show_header=False, border_style="cyan")
        table.add_column("Field", style="bold cyan")
        table.add_column("Value")

        table.add_row("Username", profile.username)
        table.add_row("Email", profile.email or "[dim]Not set[/dim]")
        table.add_row("Logo", profile.logo or "[dim]None[/dim]")
        table.add_row("Emoji", profile.emoji or "[dim]None[/dim]")
        table.add_row("Webhook", profile.webhook_url or "[dim]Not configured[/dim]")
        table.add_row("Role", "[bold]Admin[/bold]" if profile.admin else "User")
        table.add_row("Type", "🤖 Bot" if profile.bot else "👤 Human")
        table.add_row("Created", format_timestamp(profile.created_at))

        console.print(table)

    except Exception as e:
        handle_error(e)


# ============================================================================
# MESSAGES COMMANDS
# ============================================================================


@messages_app.command("send")
def send_message(
    message: str = typer.Argument(..., help="Message to send"),
    to: str | None = typer.Option(None, "--to", "-t", help="Send as DM to user"),
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key"),
) -> None:
    """📤 Send a message to the room or as a DM."""
    try:
        client = get_client(api_key)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Sending message...", total=None)
            response = client.send_message(message, to_username=to)

        # Display success
        msg_type = f"💬 DM to {to}" if to else "📢 Room message"
        console.print(
            f"\n[bold green]✓[/bold green] {msg_type} sent!\n"
            f"[dim]ID: {response.id}[/dim]"
        )

    except Exception as e:
        handle_error(e)


@messages_app.command("list")
def list_messages(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of messages"),
    offset: int = typer.Option(0, "--offset", help="Offset for pagination"),
    direct: bool = typer.Option(False, "--direct", "-d", help="Show DMs instead"),
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key"),
) -> None:
    """📋 List recent messages."""
    try:
        client = get_client(api_key)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Fetching messages...", total=None)

            if direct:
                response = client.get_direct_messages(limit=limit, offset=offset)
                title = "💬 Direct Messages"
            else:
                response = client.get_messages(limit=limit, offset=offset)
                title = "📢 Room Messages"

        if not response.messages:
            console.print("[dim]No messages found[/dim]")
            return

        # Create messages table
        table = Table(title=title, border_style="blue")
        table.add_column("Time", style="dim")
        table.add_column("From", style="cyan")
        if direct:
            table.add_column("To", style="cyan")
        table.add_column("Message")

        for msg in response.messages:
            timestamp = format_timestamp(msg.timestamp)
            time_str = timestamp.split()[1]  # Just the time part

            from_user = msg.from_username
            if msg.from_user_emoji:
                from_user = f"{msg.from_user_emoji} {from_user}"
            if msg.from_user_bot:
                from_user = f"🤖 {from_user}"

            if direct:
                to_user = msg.to_username or "[dim]room[/dim]"
                table.add_row(time_str, from_user, to_user, msg.content)
            else:
                table.add_row(time_str, from_user, msg.content)

        console.print(table)

        # Show pagination info
        if response.pagination.has_more:
            console.print(
                f"\n[dim]Showing {len(response.messages)} of {response.pagination.total} "
                f"(use --offset {offset + limit} for next page)[/dim]"
            )

    except Exception as e:
        handle_error(e)


# ============================================================================
# USERS COMMANDS
# ============================================================================


@users_app.command("list")
def list_users(
    online_only: bool = typer.Option(
        False, "--online", "-o", help="Show only online users"
    ),
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key"),
) -> None:
    """👥 List all users or online users."""
    try:
        client = get_client(api_key)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Fetching users...", total=None)

            if online_only:
                users = client.get_online_users()
                title = "🟢 Online Users"
            else:
                users = client.get_users()
                title = "👥 All Users"

        if not users:
            console.print("[dim]No users found[/dim]")
            return

        # Create users table
        table = Table(title=title, border_style="green")
        table.add_column("Username", style="cyan")
        table.add_column("Type")
        table.add_column("Logo")

        for user in users:
            username = user.username
            if user.emoji:
                username = f"{user.emoji} {username}"

            user_type = []
            if user.bot:
                user_type.append("🤖 Bot")
            if user.viewer:
                user_type.append("👁️  Viewer")
            if not user_type:
                user_type.append("👤 User")

            logo = user.logo if user.logo else "[dim]none[/dim]"

            table.add_row(username, ", ".join(user_type), logo)

        console.print(table)
        console.print(f"\n[bold]Total:[/bold] {len(users)} users")

    except Exception as e:
        handle_error(e)


@users_app.command("update")
def update_profile(
    username: str | None = typer.Option(None, "--username", "-u", help="New username"),
    webhook: str | None = typer.Option(None, "--webhook", "-w", help="Webhook URL"),
    clear_webhook: bool = typer.Option(False, "--clear-webhook", help="Clear webhook"),
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key"),
) -> None:
    """✏️  Update your profile."""
    try:
        client = get_client(api_key)

        if not username and not webhook and not clear_webhook:
            console.print(
                "[yellow]No changes specified. Use --username, --webhook, or --clear-webhook[/yellow]"
            )
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Updating profile...", total=None)

            if username:
                client.update_my_username(username)
                console.print(f"[green]✓[/green] Username updated to: {username}")

            if webhook or clear_webhook:
                webhook_url = None if clear_webhook else webhook
                client.update_my_webhook(webhook_url)
                if clear_webhook:
                    console.print("[green]✓[/green] Webhook cleared")
                else:
                    console.print(f"[green]✓[/green] Webhook updated to: {webhook}")

    except ConflictError:
        console.print(
            f"[bold red]Error:[/bold red] Username '{username}' is already taken"
        )
        raise typer.Exit(1) from None
    except Exception as e:
        handle_error(e)


# ============================================================================
# UNREAD COMMANDS
# ============================================================================


@unread_app.command("count")
def unread_count(
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key"),
) -> None:
    """📬 Show unread message count."""
    try:
        client = get_client(api_key)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Fetching unread count...", total=None)
            count = client.get_unread_count()

        # Create count panel
        content = (
            f"[bold]Room Messages:[/bold] {count.unread_room_messages}\n"
            f"[bold]Direct Messages:[/bold] {count.unread_direct_messages}\n"
            f"[bold]Total:[/bold] {count.total_unread}"
        )

        panel_style = "yellow" if count.total_unread > 0 else "green"
        title = "📬 Unread Messages" if count.total_unread > 0 else "✓ All Caught Up!"

        panel = Panel(content, title=title, border_style=panel_style)
        console.print(panel)

    except Exception as e:
        handle_error(e)


@unread_app.command("mark-read")
def mark_read(
    all_messages: bool = typer.Option(
        False, "--all", "-a", help="Mark all messages as read"
    ),
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key"),
) -> None:
    """✓ Mark all messages as read."""
    try:
        client = get_client(api_key)

        if not all_messages:
            console.print("[yellow]Use --all to mark all messages as read[/yellow]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Marking messages as read...", total=None)
            result = client.mark_all_messages_read()
            count = result.get("messages_marked_read", 0)
            console.print(f"[green]✓[/green] Marked {count} messages as read")

    except Exception as e:
        handle_error(e)


# ============================================================================
# LIVE/WEBSOCKET COMMANDS
# ============================================================================


@live_app.command("chat")
def live_chat(
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key"),
) -> None:
    """💬 Interactive real-time chat (WebSocket)."""
    key = api_key or os.getenv("TOKEN_BOWL_CHAT_API_KEY")
    if not key:
        console.print(
            "[bold red]Error:[/bold red] No API key provided. "
            "Set TOKEN_BOWL_CHAT_API_KEY or use --api-key"
        )
        raise typer.Exit(1)

    # Run async chat
    try:
        asyncio.run(_run_live_chat(key))
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Chat ended[/yellow]")


async def _run_live_chat(api_key: str) -> None:
    """Run the live chat session."""

    messages_buffer: list[str] = []
    typing_users: set[str] = set()

    def on_message(msg: MessageResponse) -> None:
        """Handle incoming messages."""
        timestamp = format_timestamp(msg.timestamp)
        time_str = timestamp.split()[1]

        sender = msg.from_username
        if msg.from_user_emoji:
            sender = f"{msg.from_user_emoji} {sender}"

        msg_type = "💬" if msg.message_type == "direct" else "📢"

        # Remove from typing
        typing_users.discard(msg.from_username)

        message_line = (
            f"[dim]{time_str}[/dim] {msg_type} [cyan]{sender}[/cyan]: {msg.content}"
        )
        messages_buffer.append(message_line)

        # Keep only last 20 messages
        if len(messages_buffer) > 20:
            messages_buffer.pop(0)

    def on_typing(username: str, _to_username: str | None) -> None:
        """Handle typing indicators."""
        typing_users.add(username)

    def on_read_receipt(message_id: str, read_by: str) -> None:
        """Handle read receipts."""
        messages_buffer.append(
            f"[dim]✓✓ {read_by} read message {message_id[:8]}...[/dim]"
        )

    # Connect to WebSocket
    console.print("[bold green]🔌 Connecting to Token Bowl Chat...[/bold green]")

    async with TokenBowlWebSocket(
        api_key=api_key,
        on_message=on_message,
        on_typing=on_typing,
        on_read_receipt=on_read_receipt,
    ) as ws:
        console.print("[bold green]✓ Connected![/bold green]\n")
        console.print("[yellow]Commands:[/yellow]")
        console.print("  /quit - Exit chat")
        console.print("  @username message - Send DM")
        console.print("  message - Send to room")
        console.print()

        # Create task to read user input
        async def input_loop() -> None:
            loop = asyncio.get_event_loop()

            while True:
                try:
                    # Display current state
                    console.print("\n".join(messages_buffer[-10:]))

                    if typing_users:
                        users = ", ".join(sorted(typing_users))
                        console.print(f"[dim]💬 {users} typing...[/dim]")

                    # Get input
                    user_input = await loop.run_in_executor(None, input, "\n> ")

                    if not user_input.strip():
                        continue

                    if user_input.strip() == "/quit":
                        return

                    # Parse DM
                    if user_input.startswith("@"):
                        parts = user_input[1:].split(None, 1)
                        if len(parts) == 2:
                            to_user, message = parts
                            await ws.send_typing_indicator(to_username=to_user)
                            await asyncio.sleep(0.5)
                            await ws.send_message(message, to_username=to_user)
                        else:
                            console.print("[red]Format: @username message[/red]")
                    else:
                        # Room message
                        await ws.send_typing_indicator()
                        await asyncio.sleep(0.5)
                        await ws.send_message(user_input)

                except EOFError:
                    return
                except KeyboardInterrupt:
                    return

        await input_loop()


@live_app.command("monitor")
def live_monitor(
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key"),
) -> None:
    """👁️  Monitor messages in real-time (read-only)."""
    key = api_key or os.getenv("TOKEN_BOWL_CHAT_API_KEY")
    if not key:
        console.print(
            "[bold red]Error:[/bold red] No API key provided. "
            "Set TOKEN_BOWL_CHAT_API_KEY or use --api-key"
        )
        raise typer.Exit(1)

    try:
        asyncio.run(_run_monitor(key))
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Monitoring stopped[/yellow]")


async def _run_monitor(api_key: str) -> None:
    """Run the message monitor."""

    table = Table(title="📡 Live Message Monitor", border_style="cyan")
    table.add_column("Time", style="dim")
    table.add_column("From", style="cyan")
    table.add_column("Message")

    message_count = 0

    def on_message(msg: MessageResponse) -> None:
        nonlocal message_count
        message_count += 1

        timestamp = format_timestamp(msg.timestamp)
        time_str = timestamp.split()[1]

        sender = msg.from_username
        if msg.from_user_emoji:
            sender = f"{msg.from_user_emoji} {sender}"

        table.add_row(time_str, sender, msg.content)

    console.print("[bold green]🔌 Connecting...[/bold green]")

    async with TokenBowlWebSocket(api_key=api_key, on_message=on_message):
        console.print("[bold green]✓ Connected! Monitoring messages...[/bold green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        with (
            Live(table, refresh_per_second=4, console=console),
            contextlib.suppress(asyncio.CancelledError),
        ):
            await asyncio.Event().wait()

        console.print(f"\n[bold]Total messages received:[/bold] {message_count}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
