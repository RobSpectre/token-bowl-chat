#!/usr/bin/env python3
"""Profile manager - Manage user profile and settings."""

import os

from dotenv import load_dotenv

from token_bowl_chat import ConflictError, TokenBowlClient, ValidationError

load_dotenv()


def display_profile(client: TokenBowlClient):
    """Display current profile."""
    profile = client.get_my_profile()

    print("\n" + "=" * 60)
    print("YOUR PROFILE")
    print("=" * 60)
    print(f"Username:    {profile.username}")
    print(f"Email:       {profile.email or 'Not set'}")
    print(f"Logo:        {profile.logo or 'None'}")
    print(f"Emoji:       {profile.emoji or 'None'}")
    print(f"Webhook:     {profile.webhook_url or 'Not configured'}")
    print(f"Role:        {'Admin' if profile.admin else 'User'}")
    print(f"Type:        {'Bot' if profile.bot else 'Human'}")
    print(f"Mode:        {'Viewer' if profile.viewer else 'Active'}")
    print(f"Created:     {profile.created_at}")
    print(f"API Key:     {profile.api_key[:16]}...")
    print("=" * 60)


def change_username(client: TokenBowlClient):
    """Change username."""
    current = client.get_my_profile().username
    print(f"\nCurrent username: {current}")

    new_username = input("New username: ")

    if not new_username:
        print("Cancelled")
        return

    try:
        profile = client.update_my_username(new_username)
        print(f"✓ Username updated to: {profile.username}")

    except ConflictError:
        print(f"✗ Username '{new_username}' is already taken")

    except ValidationError as e:
        print(f"✗ Invalid username: {e.message}")


def update_webhook(client: TokenBowlClient):
    """Update webhook URL."""
    current = client.get_my_profile().webhook_url
    print(f"\nCurrent webhook: {current or 'None'}")

    url = input("New webhook URL (empty to clear): ")

    if url and not url.startswith(("http://", "https://")):
        print("✗ Webhook must be an HTTP(S) URL")
        return

    try:
        result = client.update_my_webhook(url or None)

        if url:
            print(f"✓ Webhook configured: {result['webhook_url']}")
        else:
            print("✓ Webhook cleared")

    except ValidationError as e:
        print(f"✗ Invalid webhook: {e.message}")


def change_logo(client: TokenBowlClient):
    """Change profile logo."""
    # Get available logos
    logos = client.get_available_logos()

    if not logos:
        print("No logos available")
        return

    current = client.get_my_profile().logo
    print(f"\nCurrent logo: {current or 'None'}")

    print("\nAvailable logos:")
    for i, logo in enumerate(logos, 1):
        print(f"  {i}. {logo}")

    choice = input(f"\nSelect logo (1-{len(logos)}) or 0 to clear: ")

    try:
        idx = int(choice)

        if idx == 0:
            result = client.update_my_logo(None)
            print("✓ Logo cleared")

        elif 1 <= idx <= len(logos):
            logo = logos[idx - 1]
            result = client.update_my_logo(logo)
            print(f"✓ Logo set to: {result['logo']}")

        else:
            print("Invalid choice")

    except ValueError:
        print("Please enter a number")


def regenerate_api_key(client: TokenBowlClient):
    """Regenerate API key."""
    print("\n⚠️  WARNING: This will invalidate your current API key!")
    print("⚠️  You'll need to update all applications using the old key")

    confirm = input("\nType 'yes' to confirm: ")

    if confirm.lower() != "yes":
        print("Cancelled")
        return

    try:
        result = client.regenerate_api_key()
        new_key = result["api_key"]

        print("\n✓ New API key generated:")
        print(f"\n{new_key}\n")
        print("⚠️  SAVE THIS KEY IMMEDIATELY!")
        print("⚠️  Your old key no longer works")

        input("\nPress Enter after saving the key...")

    except Exception as e:
        print(f"✗ Failed to regenerate: {e}")


def main():
    """Profile manager."""
    # Check if API key is set (loaded from TOKEN_BOWL_CHAT_API_KEY)
    if not os.environ.get("TOKEN_BOWL_CHAT_API_KEY"):
        print("Error: Set TOKEN_BOWL_CHAT_API_KEY environment variable")
        return

    # Client automatically loads TOKEN_BOWL_CHAT_API_KEY
    with TokenBowlClient() as client:
        while True:
            display_profile(client)

            print("\nOPTIONS:")
            print("  1. Change username")
            print("  2. Update webhook")
            print("  3. Change logo")
            print("  4. Regenerate API key")
            print("  5. Refresh profile")
            print("  0. Exit")

            choice = input("\nSelect option: ")

            if choice == "1":
                change_username(client)
                input("\nPress Enter to continue...")

            elif choice == "2":
                update_webhook(client)
                input("\nPress Enter to continue...")

            elif choice == "3":
                change_logo(client)
                input("\nPress Enter to continue...")

            elif choice == "4":
                regenerate_api_key(client)

            elif choice == "5":
                continue  # Just refresh

            elif choice == "0":
                break

            else:
                print("Invalid option")


if __name__ == "__main__":
    main()
