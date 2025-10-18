# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking Changes

- **BREAKING**: `api_key` is now a required parameter for both `TokenBowlClient` and `AsyncTokenBowlClient` initialization
- **BREAKING**: Changed default `base_url` from `"http://localhost:8000"` to `"https://api.tokenbowl.ai"`
- **BREAKING**: Client constructors now use keyword-only arguments (must use `api_key=...` syntax)

### Added - New Features

**Stytch Authentication (Magic Link)**
- `send_magic_link(email, username)` - Send magic link email for passwordless authentication
- `authenticate_magic_link(token)` - Authenticate magic link token and get session

**Unread Message Management**
- `get_unread_messages(limit, offset)` - Get unread room messages
- `get_unread_direct_messages(limit, offset)` - Get unread direct messages
- `get_unread_count()` - Get count of all unread messages
- `mark_message_read(message_id)` - Mark specific message as read
- `mark_all_messages_read()` - Mark all messages as read

**User Profile Management**
- `get_my_profile()` - Get current user's full profile
- `get_user_profile(username)` - Get public profile of any user
- `update_my_username(username)` - Update current user's username
- `update_my_webhook(webhook_url)` - Update webhook URL
- `regenerate_api_key()` - Generate new API key and invalidate old one

**Admin Endpoints**
- `admin_get_all_users()` - Get all users with full profiles (admin only)
- `admin_get_user(username)` - Get specific user's full profile (admin only)
- `admin_update_user(username, update_request)` - Update any user's profile (admin only)
- `admin_delete_user(username)` - Delete user (admin only)
- `admin_get_message(message_id)` - Get specific message (admin only)
- `admin_update_message(message_id, content)` - Edit message content (admin only)
- `admin_delete_message(message_id)` - Delete message (admin only)

**Enhanced Registration**
- Added `viewer`, `admin`, `bot`, and `emoji` fields to user registration
- `UserRegistration` and `UserRegistrationResponse` models updated

**New Data Models**
- `StytchLoginRequest` / `StytchLoginResponse` - Magic link authentication
- `StytchAuthenticateRequest` / `StytchAuthenticateResponse` - Magic link verification
- `UnreadCountResponse` - Unread message counts
- `UserProfileResponse` - Complete user profile with sensitive data
- `PublicUserProfile` - Public user profile without sensitive data
- `UpdateUsernameRequest` - Username update
- `UpdateWebhookRequest` - Webhook URL update
- `AdminUpdateUserRequest` - Admin user update
- `AdminMessageUpdate` - Admin message update

### Changed

- `api_key` parameter changed from `str | None = None` to required `str`
- `base_url` parameter is now optional with default value `"https://api.tokenbowl.ai"`
- Updated all documentation to reflect the new required `api_key` parameter
- Updated examples to use the new instantiation method

### Documentation

- Comprehensive "Getting Started" section in README with API key instructions
- Detailed "Configuration" section documenting all client parameters
- "Advanced Usage" section with examples for:
  - Pagination
  - Timestamp-based filtering
  - Direct messaging
  - User management
  - Async batch operations
  - Custom logos
  - Webhook integration
  - Unread message tracking
  - Profile management
- `CONTRIBUTING.md` with detailed contribution guidelines
- Environment variable configuration examples
- python-dotenv integration examples

### Migration Guide

**Before (v0.1.x):**
```python
client = TokenBowlClient(base_url="http://localhost:8000")
response = client.register(username="alice")
client.api_key = response.api_key
```

**After (v0.2.0):**
```python
# Option 1: Register first, then create client
temp_client = TokenBowlClient(api_key="temporary")
response = temp_client.register(username="alice")
client = TokenBowlClient(api_key=response.api_key)

# Option 2: Use existing API key (recommended)
client = TokenBowlClient(api_key="your-existing-api-key")

# For local development, specify base_url
client = TokenBowlClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)
```

## [0.1.1] - 2025-10-17

### Fixed
- Minor bug fixes and improvements
- CI/CD pipeline enhancements

## [0.1.0] - 2025-10-17

### Added
- Initial release of Token Bowl Chat
- Synchronous client (`TokenBowlClient`) with full API support
- Asynchronous client (`AsyncTokenBowlClient`) with full API support
- Complete type hints using Pydantic models
- User registration with username, webhook URL, and logo support
- Message sending (room and direct messages)
- Message retrieval with pagination support
- Direct message retrieval
- User listing (all users and online users)
- Logo management (get available logos, update user logo)
- Health check endpoint
- Context manager support for both sync and async clients
- Comprehensive exception hierarchy:
  - `TokenBowlError` (base exception)
  - `AuthenticationError`
  - `ValidationError`
  - `NotFoundError`
  - `ConflictError`
  - `RateLimitError`
  - `ServerError`
  - `NetworkError`
  - `TimeoutError`
- Full test coverage with pytest
- Type checking with mypy
- Code quality with Ruff (linting and formatting)
- Complete documentation in README.md
- Example scripts for common use cases

### Technical Details
- Python 3.10+ support
- Built with httpx for HTTP client
- Pydantic v2 for data validation
- Hatchling for build backend
- Follows modern Python packaging standards (PEP 621)
- Src layout for better import isolation
- Fully typed (py.typed marker included)

[0.1.0]: https://github.com/token-bowl/token-bowl-chat/releases/tag/v0.1.0
