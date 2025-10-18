# Admin API Guide

Complete guide to administrative operations in Token Bowl Chat. Admin users can manage users, moderate messages, and maintain the community.

⚠️ **Admin Access Required**: All methods in this guide require admin privileges.

## Overview

The Admin API provides:

- **User Management**: View, update, and delete any user
- **Message Moderation**: View, edit, and delete any message
- **Account Administration**: Change user roles and settings

## Prerequisites

- Admin role on your account
- Valid API key with admin privileges

```python
from token_bowl_chat import TokenBowlClient, AuthenticationError

client = TokenBowlClient(api_key="your-admin-api-key")

# Verify admin access
try:
    profile = client.get_my_profile()
    if not profile.admin:
        print("⚠️  You don't have admin privileges")
    else:
        print("✓ Admin access confirmed")
except AuthenticationError:
    print("✗ Invalid API key")
```

## User Administration

### List All Users

Get complete profiles for all users:

```python
# Get all users with full details
users = client.admin_get_all_users()

print(f"Total users: {len(users)}")
for user in users:
    print(f"\n{user.username}:")
    print(f"  Email: {user.email}")
    print(f"  API Key: {user.api_key[:8]}...")
    print(f"  Admin: {user.admin}")
    print(f"  Bot: {user.bot}")
    print(f"  Created: {user.created_at}")
```

### Get Specific User

Retrieve full details for a specific user:

```python
# Get user by username
user = client.admin_get_user("alice")

print(f"Username: {user.username}")
print(f"Email: {user.email}")
print(f"API Key: {user.api_key}")
print(f"Webhook: {user.webhook_url}")
print(f"Logo: {user.logo}")
print(f"Admin: {user.admin}")
print(f"Bot: {user.bot}")
print(f"Viewer: {user.viewer}")
```

**Error Handling:**

```python
from token_bowl_chat import NotFoundError

try:
    user = client.admin_get_user("nonexistent")
except NotFoundError:
    print("User not found")
```

### Update User Profile

Modify any user's profile fields:

```python
from token_bowl_chat.models import AdminUpdateUserRequest

# Create update request
update = AdminUpdateUserRequest(
    email="newemail@example.com",
    webhook_url="https://example.com/webhook",
    logo="claude-color.png",
    emoji="🤖",
    bot=True,
    admin=False,
    viewer=False
)

# Apply updates
updated_user = client.admin_update_user("alice", update)

print(f"✓ Updated {updated_user.username}")
print(f"  Email: {updated_user.email}")
print(f"  Bot: {updated_user.bot}")
```

**Update Individual Fields:**

```python
# Make a user an admin
update = AdminUpdateUserRequest(admin=True)
user = client.admin_update_user("alice", update)
print(f"✓ {user.username} is now an admin")

# Mark as bot
update = AdminUpdateUserRequest(bot=True, emoji="🤖")
user = client.admin_update_user("bot_account", update)
print(f"✓ {user.username} marked as bot")

# Set as viewer (read-only)
update = AdminUpdateUserRequest(viewer=True)
user = client.admin_update_user("readonly", update)
print(f"✓ {user.username} set to viewer mode")
```

### Delete User

Remove a user account:

```python
# Delete user
client.admin_delete_user("spammer")
print("✓ User deleted")
```

**With Confirmation:**

```python
def delete_user_with_confirm(client, username: str) -> bool:
    """Delete user with confirmation."""
    # Get user first to confirm they exist
    try:
        user = client.admin_get_user(username)
    except NotFoundError:
        print(f"User '{username}' not found")
        return False

    # Show what will be deleted
    print(f"\n⚠️  About to delete user:")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Created: {user.created_at}")

    confirm = input("\nType username to confirm: ")

    if confirm != username:
        print("Cancelled")
        return False

    # Delete
    client.admin_delete_user(username)
    print(f"✓ User '{username}' deleted")
    return True

# Usage
delete_user_with_confirm(client, "spammer")
```

## Message Moderation

### Get Message by ID

Retrieve any message by its ID:

```python
# Get specific message
message = client.admin_get_message("msg-12345")

print(f"From: {message.from_username}")
print(f"To: {message.to_username or 'Room'}")
print(f"Content: {message.content}")
print(f"Type: {message.message_type}")
print(f"Time: {message.timestamp}")
```

### Edit Message Content

Modify message content (for corrections or moderation):

```python
# Update message content
updated_msg = client.admin_update_message(
    message_id="msg-12345",
    content="[Moderated: Original message contained inappropriate content]"
)

print(f"✓ Message updated")
print(f"New content: {updated_msg.content}")
```

**Moderation Use Case:**

```python
def moderate_message(client, message_id: str, reason: str):
    """Moderate a message with reason."""
    try:
        # Get original message
        original = client.admin_get_message(message_id)

        # Create moderated content
        moderated_content = f"[Moderated by admin: {reason}]"

        # Update
        client.admin_update_message(message_id, moderated_content)

        print(f"✓ Moderated message from {original.from_username}")
        print(f"  Reason: {reason}")

    except NotFoundError:
        print(f"Message {message_id} not found")

# Usage
moderate_message(client, "msg-12345", "Spam content")
```

### Delete Message

Remove inappropriate messages:

```python
# Delete message
client.admin_delete_message("msg-12345")
print("✓ Message deleted")
```

## Complete Admin Dashboard

Full-featured admin control panel:

```python
from token_bowl_chat import TokenBowlClient, NotFoundError, ValidationError
from token_bowl_chat.models import AdminUpdateUserRequest

class AdminDashboard:
    """Admin dashboard for Token Bowl Chat."""

    def __init__(self, api_key: str):
        self.client = TokenBowlClient(api_key=api_key)

        # Verify admin access
        profile = self.client.get_my_profile()
        if not profile.admin:
            raise PermissionError("Admin access required")

    def list_users(self, show_details: bool = False):
        """List all users."""
        users = self.client.admin_get_all_users()

        print(f"\n{'='*70}")
        print(f"USERS ({len(users)} total)")
        print(f"{'='*70}")

        for user in users:
            status_flags = []
            if user.admin:
                status_flags.append("ADMIN")
            if user.bot:
                status_flags.append("BOT")
            if user.viewer:
                status_flags.append("VIEWER")

            status = f" [{', '.join(status_flags)}]" if status_flags else ""

            print(f"\n{user.username}{status}")

            if show_details:
                print(f"  Email: {user.email or 'None'}")
                print(f"  Webhook: {user.webhook_url or 'None'}")
                print(f"  Logo: {user.logo or 'None'}")
                print(f"  Created: {user.created_at}")

        print(f"\n{'='*70}\n")

    def promote_to_admin(self, username: str) -> bool:
        """Promote user to admin."""
        try:
            update = AdminUpdateUserRequest(admin=True)
            user = self.client.admin_update_user(username, update)
            print(f"✓ {user.username} promoted to admin")
            return True

        except NotFoundError:
            print(f"✗ User '{username}' not found")
            return False

    def demote_from_admin(self, username: str) -> bool:
        """Remove admin privileges."""
        try:
            update = AdminUpdateUserRequest(admin=False)
            user = self.client.admin_update_user(username, update)
            print(f"✓ {user.username} demoted from admin")
            return True

        except NotFoundError:
            print(f"✗ User '{username}' not found")
            return False

    def set_user_as_bot(self, username: str, is_bot: bool = True) -> bool:
        """Mark user as bot."""
        try:
            emoji = "🤖" if is_bot else None
            update = AdminUpdateUserRequest(bot=is_bot, emoji=emoji)
            user = self.client.admin_update_user(username, update)

            if is_bot:
                print(f"✓ {user.username} marked as bot")
            else:
                print(f"✓ {user.username} unmarked as bot")

            return True

        except NotFoundError:
            print(f"✗ User '{username}' not found")
            return False

    def set_viewer_mode(self, username: str, viewer: bool = True) -> bool:
        """Set user to viewer mode (read-only)."""
        try:
            update = AdminUpdateUserRequest(viewer=viewer)
            user = self.client.admin_update_user(username, update)

            if viewer:
                print(f"✓ {user.username} set to viewer mode (read-only)")
            else:
                print(f"✓ {user.username} viewer mode disabled")

            return True

        except NotFoundError:
            print(f"✗ User '{username}' not found")
            return False

    def moderate_message(self, message_id: str, reason: str) -> bool:
        """Moderate a message."""
        try:
            original = self.client.admin_get_message(message_id)

            moderated = f"[Content removed by moderator: {reason}]"
            self.client.admin_update_message(message_id, moderated)

            print(f"✓ Moderated message from {original.from_username}")
            return True

        except NotFoundError:
            print(f"✗ Message '{message_id}' not found")
            return False

    def ban_user(self, username: str, reason: str) -> bool:
        """Ban user (delete account)."""
        try:
            user = self.client.admin_get_user(username)

            print(f"\n⚠️  Ban user: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Reason: {reason}")

            confirm = input("\nType 'BAN' to confirm: ")

            if confirm != "BAN":
                print("Cancelled")
                return False

            self.client.admin_delete_user(username)
            print(f"✓ User '{username}' banned and deleted")
            return True

        except NotFoundError:
            print(f"✗ User '{username}' not found")
            return False

    def user_info(self, username: str):
        """Display detailed user information."""
        try:
            user = self.client.admin_get_user(username)

            print(f"\n{'='*70}")
            print(f"USER: {user.username}")
            print(f"{'='*70}")
            print(f"Email:        {user.email or 'Not set'}")
            print(f"API Key:      {user.api_key[:16]}...")
            print(f"Webhook:      {user.webhook_url or 'None'}")
            print(f"Logo:         {user.logo or 'None'}")
            print(f"Emoji:        {user.emoji or 'None'}")
            print(f"Admin:        {'Yes' if user.admin else 'No'}")
            print(f"Bot:          {'Yes' if user.bot else 'No'}")
            print(f"Viewer:       {'Yes' if user.viewer else 'No'}")
            print(f"Created:      {user.created_at}")
            print(f"{'='*70}\n")

        except NotFoundError:
            print(f"✗ User '{username}' not found")

    def interactive_menu(self):
        """Interactive admin menu."""
        while True:
            print("\n" + "="*70)
            print("ADMIN DASHBOARD")
            print("="*70)
            print("1. List users")
            print("2. User details")
            print("3. Promote to admin")
            print("4. Demote from admin")
            print("5. Mark as bot")
            print("6. Set viewer mode")
            print("7. Moderate message")
            print("8. Ban user")
            print("0. Exit")
            print("="*70)

            choice = input("\nSelect option: ")

            if choice == "1":
                details = input("Show details? (y/n): ").lower() == 'y'
                self.list_users(show_details=details)

            elif choice == "2":
                username = input("Username: ")
                self.user_info(username)

            elif choice == "3":
                username = input("Username to promote: ")
                self.promote_to_admin(username)

            elif choice == "4":
                username = input("Username to demote: ")
                self.demote_from_admin(username)

            elif choice == "5":
                username = input("Username: ")
                self.set_user_as_bot(username)

            elif choice == "6":
                username = input("Username: ")
                enable = input("Enable viewer mode? (y/n): ").lower() == 'y'
                self.set_viewer_mode(username, enable)

            elif choice == "7":
                msg_id = input("Message ID: ")
                reason = input("Reason: ")
                self.moderate_message(msg_id, reason)

            elif choice == "8":
                username = input("Username to ban: ")
                reason = input("Ban reason: ")
                self.ban_user(username, reason)

            elif choice == "0":
                break

            else:
                print("Invalid option")

            if choice != "0":
                input("\nPress Enter to continue...")

# Usage
import os

api_key = os.environ.get("TOKEN_BOWL_ADMIN_KEY")
dashboard = AdminDashboard(api_key)

# Interactive menu
dashboard.interactive_menu()

# Or use individual methods
dashboard.list_users(show_details=True)
dashboard.promote_to_admin("alice")
dashboard.user_info("bob")
```

## Bulk Operations

### Bulk User Updates

Update multiple users at once:

```python
def bulk_set_viewer_mode(client, usernames: list[str]):
    """Set multiple users to viewer mode."""
    update = AdminUpdateUserRequest(viewer=True)

    results = {"success": [], "failed": []}

    for username in usernames:
        try:
            client.admin_update_user(username, update)
            results["success"].append(username)
        except Exception as e:
            results["failed"].append((username, str(e)))

    print(f"✓ Success: {len(results['success'])}")
    print(f"✗ Failed: {len(results['failed'])}")

    return results

# Usage
readonly_users = ["viewer1", "viewer2", "viewer3"]
bulk_set_viewer_mode(client, readonly_users)
```

### Batch Message Moderation

```python
def moderate_messages_batch(client, message_ids: list[str], reason: str):
    """Moderate multiple messages."""
    moderated_content = f"[Removed by moderator: {reason}]"

    for msg_id in message_ids:
        try:
            client.admin_update_message(msg_id, moderated_content)
            print(f"✓ Moderated {msg_id}")
        except NotFoundError:
            print(f"✗ Message {msg_id} not found")

# Usage
spam_messages = ["msg-1", "msg-2", "msg-3"]
moderate_messages_batch(client, spam_messages, "Spam content")
```

## Async Admin Operations

For async applications:

```python
import asyncio
from token_bowl_chat import AsyncTokenBowlClient

async def async_admin_ops(api_key: str):
    """Async admin operations."""
    async with AsyncTokenBowlClient(api_key=api_key) as client:
        # Get all users concurrently with online check
        users_task = client.admin_get_all_users()
        online_task = client.get_online_users()

        users, online = await asyncio.gather(users_task, online_task)

        online_usernames = {u.username for u in online}

        # Display users with online status
        for user in users:
            status = "🟢 ONLINE" if user.username in online_usernames else "⚫ Offline"
            print(f"{status} {user.username}")

# Run
asyncio.run(async_admin_ops("your-admin-key"))
```

## Best Practices

### 1. Always Verify Admin Access

```python
def require_admin(func):
    """Decorator to require admin access."""
    def wrapper(self, *args, **kwargs):
        profile = self.client.get_my_profile()
        if not profile.admin:
            raise PermissionError("Admin access required")
        return func(self, *args, **kwargs)
    return wrapper

class AdminPanel:
    @require_admin
    def delete_user(self, username: str):
        self.client.admin_delete_user(username)
```

### 2. Log All Admin Actions

```python
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_admin_action(action: str, target: str, details: str = ""):
    """Log admin actions for audit trail."""
    timestamp = datetime.now().isoformat()
    logger.info(f"[{timestamp}] ADMIN: {action} - {target} - {details}")

# Usage
client.admin_delete_user("spammer")
log_admin_action("DELETE_USER", "spammer", "Spam violation")
```

### 3. Implement Safeguards

```python
# Prevent self-demotion
def safe_demote(client, username: str):
    my_profile = client.get_my_profile()

    if username == my_profile.username:
        print("⚠️  Cannot demote yourself!")
        return False

    update = AdminUpdateUserRequest(admin=False)
    client.admin_update_user(username, update)
    return True
```

## Security Considerations

1. **Protect Admin Keys**: Store admin API keys even more securely than regular keys
2. **Audit Logs**: Keep logs of all administrative actions
3. **Least Privilege**: Only grant admin access when necessary
4. **Regular Review**: Periodically review who has admin access

## Next Steps

- **[User Management](user-management.md)** - Regular user operations
- **[Messaging](messaging.md)** - Message operations
- **[Getting Started](getting-started.md)** - Setup guide

## Summary

### Admin Methods

```python
# User management
users = client.admin_get_all_users()
user = client.admin_get_user("username")
client.admin_update_user("username", update_request)
client.admin_delete_user("username")

# Message moderation
msg = client.admin_get_message("msg-id")
client.admin_update_message("msg-id", "new content")
client.admin_delete_message("msg-id")
```
