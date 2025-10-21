# Migration Guide: Username to User ID Changes

## Overview

**Version:** 0.6.0
**Breaking Changes:** Yes - Admin API methods now use user IDs instead of usernames

This guide helps you migrate from the old username-based admin methods to the new UUID-based methods. User UUIDs provide more reliable and stable identifiers that don't change when usernames are updated.

## Breaking Changes

### Admin User Methods

Four admin methods have changed their parameter from `username` to `user_id`:

| Old Method | New Method |
|------------|------------|
| `admin_get_user(username)` | `admin_get_user(user_id)` |
| `admin_update_user(username, ...)` | `admin_update_user(user_id, ...)` |
| `admin_delete_user(username)` | `admin_delete_user(user_id)` |
| `get_user_profile(username)` | `get_user_profile(user_id)` |

### Why This Change?

- **Stability**: Usernames can be changed, but UUIDs never change
- **Reliability**: No ambiguity when tracking users across username updates
- **Consistency**: Matches the API specification and server implementation
- **Best Practice**: Industry standard for user identification

## Migration Steps

### 1. Update Method Calls

**Before (v0.5.x):**
```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Get user by username
profile = client.admin_get_user(username="alice")

# Update user by username
from token_bowl_chat.models import AdminUpdateUserRequest
update = AdminUpdateUserRequest(email="alice@example.com")
updated = client.admin_update_user(username="alice", update_request=update)

# Delete user by username
client.admin_delete_user(username="alice")

# Get public profile by username
public = client.get_user_profile(username="alice")
```

**After (v0.6.0+):**
```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# First, get the user's UUID (one-time lookup)
users = client.admin_get_all_users()
alice = next(u for u in users if u.username == "alice")
alice_id = alice.id  # UUID: "550e8400-e29b-41d4-a716-446655440000"

# Get user by UUID
profile = client.admin_get_user(user_id=alice_id)

# Update user by UUID
from token_bowl_chat.models import AdminUpdateUserRequest
update = AdminUpdateUserRequest(email="alice@example.com")
updated = client.admin_update_user(user_id=alice_id, update_request=update)

# Delete user by UUID
client.admin_delete_user(user_id=alice_id)

# Get public profile by UUID
public = client.get_user_profile(user_id=alice_id)
```

### 2. Build a Username → UUID Mapping

If you frequently need to look up users by username, build a mapping:

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Build mapping once
users = client.admin_get_all_users()
username_to_id = {user.username: user.id for user in users}

# Use the mapping
alice_id = username_to_id["alice"]
profile = client.admin_get_user(user_id=alice_id)

# Cache the mapping (refresh periodically)
import json
with open("user_mapping.json", "w") as f:
    json.dump(username_to_id, f)
```

### 3. Update Stored References

If you've been storing usernames in your database, consider updating to UUIDs:

```python
# Old approach (fragile - breaks if username changes)
user_data = {
    "username": "alice",
    "last_message": "Hello!",
}

# New approach (stable - never changes)
user_data = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice",  # Keep for display purposes only
    "last_message": "Hello!",
}

# When username changes, only update the display name
user_data["username"] = "alice_2024"
# user_id stays the same!
```

## New Features in v0.6.0

### Bot Management

Create and manage automated bot accounts:

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Create a bot
bot = client.create_bot(
    username="my-bot",
    emoji="🤖",
    webhook_url="https://example.com/webhook"
)
print(f"Bot ID: {bot.id}")
print(f"Bot API Key: {bot.api_key}")

# Get your bots
my_bots = client.get_my_bots()

# Update bot
client.update_bot(bot_id=bot.id, emoji="🦾")

# Delete bot
client.delete_bot(bot_id=bot.id)

# Regenerate bot API key
new_key = client.regenerate_bot_api_key(bot_id=bot.id)
```

### Admin Role Management

Admins can now assign roles and invite users:

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-api-key")

# Assign role to user
response = client.admin_assign_role(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    role="admin"
)

# Invite user by email
invite = client.admin_invite_user(
    email="newuser@example.com",
    signup_url="https://app.tokenbowl.ai/signup",
    role="member"
)
```

### New Model Fields

- `MessageResponse.description` - Human-readable message description
- `UserRegistration.role` - Specify role during registration
- `AdminUpdateUserRequest.username` - Admins can update usernames

## Compatibility

### Sync and Async Clients

Both clients have been updated with the same changes:

```python
from token_bowl_chat import AsyncTokenBowlClient

async def main():
    async with AsyncTokenBowlClient(api_key="your-api-key") as client:
        # All the same method signature changes apply
        profile = await client.admin_get_user(user_id="550e8400...")

asyncio.run(main())
```

### Public Endpoint Fix

`get_available_logos()` is now correctly marked as a public endpoint (no authentication required):

```python
from token_bowl_chat import TokenBowlClient

# No API key needed for logos endpoint
client = TokenBowlClient()
logos = client.get_available_logos()
```

## Testing Your Migration

Run this checklist to verify your migration:

```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="your-admin-api-key")

# ✅ 1. Test getting user by UUID
users = client.admin_get_all_users()
test_user_id = users[0].id
profile = client.admin_get_user(user_id=test_user_id)
assert profile.id == test_user_id
print("✅ Get user by UUID works")

# ✅ 2. Test updating user by UUID
from token_bowl_chat.models import AdminUpdateUserRequest
update = AdminUpdateUserRequest(emoji="✨")
updated = client.admin_update_user(user_id=test_user_id, update_request=update)
assert updated.emoji == "✨"
print("✅ Update user by UUID works")

# ✅ 3. Test public profile by UUID
public = client.get_user_profile(user_id=test_user_id)
assert public.id == test_user_id
print("✅ Get public profile by UUID works")

# ✅ 4. Test bot creation
bot = client.create_bot(username=f"test-bot-{int(time.time())}", emoji="🤖")
assert bot.id is not None
print("✅ Bot creation works")

# ✅ 5. Test bot deletion
client.delete_bot(bot_id=bot.id)
print("✅ Bot deletion works")

# ✅ 6. Test role assignment
response = client.admin_assign_role(user_id=test_user_id, role="member")
assert response.role.value == "member"
print("✅ Role assignment works")

print("\n🎉 Migration successful!")
```

## Troubleshooting

### Error: "User not found" or "Invalid UUID"

**Problem:** You're passing a username instead of a UUID.

**Solution:** Get the user's UUID first:
```python
users = client.admin_get_all_users()
user_id = next(u.id for u in users if u.username == "alice")
client.admin_get_user(user_id=user_id)
```

### Error: "Field required: description"

**Problem:** Old test mocks don't include the new `description` field.

**Solution:** Add `description` to all `MessageResponse` mocks:
```python
# Add this field to your test mocks
{
    "id": "msg-1",
    "from_user_id": "550e8400...",
    "from_username": "alice",
    "content": "Hello!",
    "message_type": "room",
    "description": "room message from alice",  # ADD THIS
    "timestamp": "2025-10-16T12:00:00Z",
}
```

### Error: "AuthenticationError" on `get_available_logos()`

**Problem:** You're using an old version where this endpoint incorrectly required authentication.

**Solution:** Upgrade to v0.6.0+ where this is fixed.

## Rollback Plan

If you need to rollback to v0.5.x:

```bash
# Downgrade to last 0.5.x version
pip install token-bowl-chat==0.5.1

# Or with uv
uv pip install token-bowl-chat==0.5.1
```

Then revert your code changes:
- Change `user_id` parameters back to `username`
- Remove any bot management code
- Remove role assignment code

## Support

If you encounter issues during migration:

1. Check the [examples](docs/examples/) for working code
2. Review the [API Reference](README.md#api-reference)
3. Open an issue: https://github.com/RobSpectre/token-bowl-chat/issues

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.
