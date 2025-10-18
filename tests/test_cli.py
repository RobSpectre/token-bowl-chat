"""Tests for the CLI module.

These tests verify:
1. CLI dependencies are available (typer, rich)
2. CLI commands can be imported and invoked
3. Basic CLI functionality works
4. Entry points are properly configured
"""

import subprocess

import pytest
from typer.testing import CliRunner

from token_bowl_chat.cli import app, main


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_cli_dependencies_available():
    """Test that CLI dependencies (typer, rich) are available."""
    try:
        import rich  # noqa: F401
        import typer  # noqa: F401
    except ImportError as e:
        pytest.fail(f"CLI dependencies not available: {e}")


def test_cli_module_imports():
    """Test that CLI module can be imported without errors."""
    from token_bowl_chat import cli  # noqa: F401


def test_main_function_exists():
    """Test that main() function exists and is callable."""
    assert callable(main)


def test_app_is_typer_instance():
    """Test that app is a Typer instance."""
    import typer

    assert isinstance(app, typer.Typer)


def test_cli_help_command(runner):
    """Test that --help flag works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Token Bowl Chat CLI" in result.stdout
    assert "register" in result.stdout
    assert "info" in result.stdout
    assert "messages" in result.stdout
    assert "users" in result.stdout
    assert "unread" in result.stdout
    assert "live" in result.stdout


def test_register_command_exists(runner):
    """Test that register command exists."""
    result = runner.invoke(app, ["register", "--help"])
    assert result.exit_code == 0
    assert "Register a new user" in result.stdout


def test_info_command_exists(runner):
    """Test that info command exists."""
    result = runner.invoke(app, ["info", "--help"])
    assert result.exit_code == 0
    assert "profile information" in result.stdout


def test_messages_group_exists(runner):
    """Test that messages command group exists."""
    result = runner.invoke(app, ["messages", "--help"])
    assert result.exit_code == 0
    assert "Send and manage messages" in result.stdout
    assert "send" in result.stdout
    assert "list" in result.stdout


def test_messages_send_command_exists(runner):
    """Test that messages send command exists."""
    result = runner.invoke(app, ["messages", "send", "--help"])
    assert result.exit_code == 0
    assert "Send a message" in result.stdout


def test_messages_list_command_exists(runner):
    """Test that messages list command exists."""
    result = runner.invoke(app, ["messages", "list", "--help"])
    assert result.exit_code == 0
    assert "List recent messages" in result.stdout


def test_users_group_exists(runner):
    """Test that users command group exists."""
    result = runner.invoke(app, ["users", "--help"])
    assert result.exit_code == 0
    assert "Manage users and profiles" in result.stdout
    assert "list" in result.stdout
    assert "update" in result.stdout


def test_users_list_command_exists(runner):
    """Test that users list command exists."""
    result = runner.invoke(app, ["users", "list", "--help"])
    assert result.exit_code == 0
    assert "List all users" in result.stdout


def test_users_update_command_exists(runner):
    """Test that users update command exists."""
    result = runner.invoke(app, ["users", "update", "--help"])
    assert result.exit_code == 0
    assert "Update your profile" in result.stdout


def test_unread_group_exists(runner):
    """Test that unread command group exists."""
    result = runner.invoke(app, ["unread", "--help"])
    assert result.exit_code == 0
    assert "Track and manage unread messages" in result.stdout
    assert "count" in result.stdout
    assert "mark-read" in result.stdout


def test_unread_count_command_exists(runner):
    """Test that unread count command exists."""
    result = runner.invoke(app, ["unread", "count", "--help"])
    assert result.exit_code == 0
    assert "Show unread message count" in result.stdout


def test_unread_mark_read_command_exists(runner):
    """Test that unread mark-read command exists."""
    result = runner.invoke(app, ["unread", "mark-read", "--help"])
    assert result.exit_code == 0
    assert "Mark all messages as read" in result.stdout


def test_live_group_exists(runner):
    """Test that live command group exists."""
    result = runner.invoke(app, ["live", "--help"])
    assert result.exit_code == 0
    assert "Real-time WebSocket features" in result.stdout
    assert "chat" in result.stdout
    assert "monitor" in result.stdout


def test_live_chat_command_exists(runner):
    """Test that live chat command exists."""
    result = runner.invoke(app, ["live", "chat", "--help"])
    assert result.exit_code == 0
    assert "Interactive real-time chat" in result.stdout


def test_live_monitor_command_exists(runner):
    """Test that live monitor command exists."""
    result = runner.invoke(app, ["live", "monitor", "--help"])
    assert result.exit_code == 0
    assert "Monitor messages in real-time" in result.stdout


def test_token_bowl_entry_point():
    """Test that token-bowl entry point is installed."""
    result = subprocess.run(
        ["token-bowl", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert "Token Bowl Chat CLI" in result.stdout


def test_token_bowl_chat_entry_point():
    """Test that token-bowl-chat entry point is installed."""
    result = subprocess.run(
        ["token-bowl-chat", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert "Token Bowl Chat CLI" in result.stdout


def test_cli_requires_api_key_for_info(runner):
    """Test that info command requires API key."""
    result = runner.invoke(app, ["info"])
    # Should fail without API key
    assert result.exit_code != 0
    assert "No API key provided" in result.stdout


def test_cli_accepts_api_key_option(runner):
    """Test that commands accept --api-key option."""
    # This will still fail (invalid key) but should parse the option
    result = runner.invoke(app, ["info", "--api-key", "test-key"])
    # Should fail with auth error or network error, not "No API key provided"
    assert "No API key provided" not in result.stdout


def test_register_command_requires_username(runner):
    """Test that register command requires username."""
    result = runner.invoke(app, ["register"])
    assert result.exit_code != 0
    # Typer may use stdout or stderr for error messages
    output = result.stdout + result.stderr if hasattr(result, "stderr") else result.output
    assert "Missing argument" in output or result.exit_code == 2


def test_messages_send_requires_message(runner):
    """Test that messages send requires message text."""
    result = runner.invoke(app, ["messages", "send"])
    assert result.exit_code != 0
    # Typer may use stdout or stderr for error messages
    output = result.stdout + result.stderr if hasattr(result, "stderr") else result.output
    assert "Missing argument" in output or result.exit_code == 2


def test_cli_commands_have_emojis(runner):
    """Test that CLI uses emojis for visual appeal."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Check for various emojis in the output
    emojis = ["🎯", "ℹ️", "📨", "👥", "📬", "⚡"]
    emoji_found = any(emoji in result.stdout for emoji in emojis)
    assert emoji_found, "CLI should include emojis for visual appeal"


def test_cli_module_has_console():
    """Test that CLI module has Rich console configured."""
    from rich.console import Console

    from token_bowl_chat.cli import console

    assert isinstance(console, Console)


def test_cli_module_has_command_groups():
    """Test that CLI module has all expected command groups."""
    import typer

    from token_bowl_chat.cli import live_app, messages_app, unread_app, users_app

    assert isinstance(messages_app, typer.Typer)
    assert isinstance(users_app, typer.Typer)
    assert isinstance(unread_app, typer.Typer)
    assert isinstance(live_app, typer.Typer)


def test_cli_entry_points_in_pyproject():
    """Test that entry points are defined in pyproject.toml."""
    import tomli

    with open("pyproject.toml", "rb") as f:
        pyproject = tomli.load(f)

    scripts = pyproject.get("project", {}).get("scripts", {})
    assert "token-bowl" in scripts
    assert "token-bowl-chat" in scripts
    assert scripts["token-bowl"] == "token_bowl_chat.cli:main"
    assert scripts["token-bowl-chat"] == "token_bowl_chat.cli:main"


def test_cli_optional_dependencies_in_pyproject():
    """Test that CLI optional dependencies are defined in pyproject.toml."""
    import tomli

    with open("pyproject.toml", "rb") as f:
        pyproject = tomli.load(f)

    optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})
    assert "cli" in optional_deps
    cli_deps = optional_deps["cli"]
    assert any("typer" in dep for dep in cli_deps)
    assert any("rich" in dep for dep in cli_deps)
