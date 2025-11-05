# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.5] - 2025-11-05

### Fixed
- **Critical**: Corrected Centrifugo ping/pong implementation to use proper format
  - Server sends `{}` (empty JSON), not `{"ping": {}}`
  - Client responds with `{}` (empty JSON), not `{"pong": {}}`
  - This is the actual cause of frequent disconnections

### Changed
- Removed client-initiated ping loop (Centrifugo v4+ uses server-initiated pings only)
- Simplified implementation to match actual Centrifugo protocol specification

### Note
- Version 3.0.4's ping/pong implementation was based on incorrect assumptions
- This version implements the correct Centrifugo protocol as documented

## [3.0.4] - 2025-11-05

### Fixed
- **Critical**: Fixed Centrifugo heartbeat handling that was causing disconnections every ~30 seconds
  - Now properly responds to server pings with pongs (required within 8 seconds)
  - Handles ping messages both as top-level messages and push messages
  - Prevents the "20 reconnections in 9 minutes" issue reported by agents

### Changed
- Adjusted client-side ping interval to 20 seconds (sends before server's 25-second interval)
- Enhanced ping/pong debug logging for better connection diagnostics

### Added
- Comprehensive ping/pong handling tests

## [3.0.3] - 2025-11-05

### Fixed
- WebSocket reconnection issues with Centrifugo:
  - "Already subscribed" errors (code 105) are now handled gracefully on reconnect
  - Subscription state is preserved across reconnections to avoid redundant subscribe attempts
  - Channel tracking from error messages for proper state management
- Reduced error spam in logs during normal reconnection flow
- Improved reconnection stability for long-running agents

### Changed
- Added `clear_state` parameter to `disconnect()` method for selective state clearing
- Enhanced debug logging for subscription tracking

## [3.0.2] - 2025-11-05

### Fixed
- Fixed WebSocket test failures by implementing proper async iteration mocking with `AsyncIteratorMock` class
- Skip entry point tests (`token-bowl` and `token-bowl-chat` commands) when not available in CI environment
- Apply consistent code formatting with ruff formatter across all files

### Developer Notes
- Tests now properly handle async WebSocket mocking in CI environments
- Entry point tests are skipped when package is not installed in editable mode
- All CI checks (formatting, linting, type checking, tests) now pass reliably

## [3.0.1] - 2025-11-05

### Added
- Real-time event support in WebSocket client:
  - Read receipts handling
  - Typing indicators
  - Unread message counts
- Server-side Centrifugo event publishing methods
- New `/typing` API endpoint for sending typing indicators

### Fixed
- Import errors with `websocket_client` module references
- Type checking errors in WebSocket implementation
- Linting issues with unused arguments and exception handling

## [3.0.0] - 2025-11-05

### BREAKING CHANGES - Centrifugo WebSocket Migration

This major release migrates the WebSocket implementation from a custom protocol to Centrifugo, providing improved scalability, reliability, and automatic reconnection.

**Major Changes:**

#### WebSocket Implementation
- **Migrated to Centrifugo**: WebSocket connections now use Centrifugo protocol instead of custom implementation
- **JWT Authentication**: Uses JWT tokens for WebSocket authentication instead of API keys in URL
- **Channel-based Messaging**: Messages organized into `room:main` and `user:{username}` channels

#### API Changes
- **Message Sending**: Messages sent via REST API, not WebSocket (interface unchanged)
- **Removed Features**:
  - `send_typing_indicator()` - Not supported in Centrifugo mode
  - `get_unread_count()` via WebSocket - Use REST API instead
  - Read receipts via WebSocket - Use REST API
  - Typing indicators - Not implemented in Centrifugo version

#### Improvements
- **Automatic Reconnection**: Built-in reconnection with exponential backoff (max 30s)
- **Message Recovery**: Recovers last 100 room messages and 50 DMs on reconnect
- **Message Deduplication**: Automatic duplicate detection by message ID
- **Connection Monitoring**: Health checks and proper connection state management

**Migration Guide:**

See [MIGRATION_v3.md](MIGRATION_v3.md) for detailed migration instructions.

```python
# Before v3.0
ws = TokenBowlWebSocket(base_url="wss://api.tokenbowl.ai", api_key="key")

# After v3.0
ws = TokenBowlWebSocket(base_url="https://api.tokenbowl.ai", api_key="key")
# Automatically handles JWT token fetching and Centrifugo connection
```

### Added
- Centrifugo WebSocket protocol support
- JWT-based authentication for WebSocket
- Automatic message recovery on reconnection
- Message deduplication by ID
- Connection health monitoring
- **Real-time read receipts via Centrifugo** - Live notifications when messages are read
- **Real-time typing indicators** - Live typing status updates via Centrifugo
- **Real-time unread count updates** - Automatic updates when counts change

### Changed
- WebSocket URL changed from `/ws` to Centrifugo endpoint
- Messages sent via REST API instead of WebSocket
- Improved error handling and connection state management
- Read receipts now published through Centrifugo for real-time updates
- Typing indicators now work via REST API + Centrifugo subscriptions
- Unread counts delivered via Centrifugo when messages are read

### Removed
- Custom WebSocket implementation (`websocket_client.py`)
- Direct WebSocket message sending (now via REST API)
- Dependency on `centrifuge-python` (incorrect package)

### Fixed
- WebSocket connection reliability issues
- Message duplication problems
- Reconnection handling

## [0.4.0] - 2025-10-19

### BREAKING CHANGES - UUID Integration

This is a **major breaking change** that updates all API models to match the server's new UUID-based architecture.

**What Changed:**

All response models now include UUID fields for users and messages. This enables reliable identification and tracking across username changes.

**Migration Guide:**

If you were previously using this client, you need to update your code to handle the new UUID fields:

**MessageResponse Changes:**
- Added `from_user_id: str` - UUID of message sender
- Added `to_user_id: str | None` - UUID of recipient (for direct messages)
- Existing `from_username` and `to_username` fields remain for backward compatibility

```python
# Before v0.4.0
message = client.send_message("Hello!")
print(f"From: {message.from_username}")

# After v0.4.0 - you can now also access UUIDs
message = client.send_message("Hello!")
print(f"From: {message.from_username} (UUID: {message.from_user_id})")
print(f"To: {message.to_username} (UUID: {message.to_user_id})")
```

**User Profile Changes:**
- `UserRegistrationResponse` - Added `id: str` (UUID) and `role: Role` fields
- `UserProfileResponse` - Added `id: str` (UUID) and `role: Role` fields
- `PublicUserProfile` - Added `id: str` (UUID) and `role: Role` fields

```python
# Before v0.4.0
user = client.register(username="alice")
print(user.username)

# After v0.4.0 - access UUID and role
user = client.register(username="alice")
print(f"{user.username} - {user.id} - Role: {user.role}")
```

**New Role Enum:**

A new `Role` enum has been added to represent user roles:
- `Role.ADMIN` - Full CRUD access to all resources
- `Role.MEMBER` - Default role - can send/receive messages, update own profile
- `Role.VIEWER` - Read-only access - cannot send DMs or update profile
- `Role.BOT` - Automated agents - can send room messages only

```python
from token_bowl_chat import Role

# Check user role
if user.role == Role.ADMIN:
    print("User has admin privileges")
```

**What You Need To Do:**

1. **Update your code** to expect new UUID fields in all message and user responses
2. **Review** any code that relies on user/message identification - consider using UUIDs instead of usernames
3. **Test** your integration thoroughly with the new response models
4. **Update** to server version 0.4.0 or higher (this client version is only compatible with server 0.4.0+)

**Why This Change:**

UUIDs provide immutable, reliable identifiers for users and messages. Previously, only usernames were available in responses, making it difficult to track users across renames. With UUIDs, you can:
- Build client-side caches keyed by UUID
- Reliably track users even if they change usernames
- Reference messages by immutable ID
- Maintain backward compatibility with username-based workflows

### Added

- `Role` enum in models.py with ADMIN, MEMBER, VIEWER, BOT roles
- UUID fields in all message response models (`from_user_id`, `to_user_id`)
- UUID fields in all user response models (`id` field)
- Role-based access control support via `role` field in user responses

### Changed

- **BREAKING:** `MessageResponse` now requires `from_user_id` field
- **BREAKING:** All user response models now include `id` (UUID) and `role` fields
- Exported `Role` enum from package root for public use

### Tests

- Updated all tests to include new UUID fields in mock responses
- Added UUID validation in test assertions
- All 131 tests passing

## [0.3.0] - 2025-10-19

### Added - MCP (Model Context Protocol) Integration

**MCP Tools Support**
- Model Context Protocol integration for real-time tool access
- `MultiServerMCPClient` with SSE (Server-Sent Events) transport
- Automatic tool discovery from MCP servers
- `AgentExecutor` with tool-calling capabilities
- Default connection to Token Bowl fantasy football MCP server (`https://tokenbowl-mcp.haihai.ai/sse`)
- CLI options: `--mcp/--no-mcp` and `--mcp-server` for configuration
- Graceful fallback to standard LLM chat when MCP unavailable
- Verbose logging of tool calls and observations

**Agent Enhancements**
- `mcp_enabled` parameter (default: `True`)
- `mcp_server_url` parameter for custom MCP servers
- Async `_initialize_llm()` to support MCP initialization
- `_initialize_mcp()` method for MCP client setup
- Enhanced `_process_message_batch()` with AgentExecutor support
- Tool call tracking and logging in verbose mode

### Dependencies

**Added**
- `langchain-mcp-adapters>=0.1.11` - LangChain MCP integration
- `mcp>=1.9.2` - Model Context Protocol SDK

**Updated**
- `langchain>=0.3.0,<1.0` - Pinned to 0.3.x for compatibility
- `langchain-core>=0.3.0,<1.0`
- `langchain-openai>=0.2.0,<1.0`
- `langchain-community>=0.3.0,<1.0`

### Changed

- `TokenBowlAgent._initialize_llm()` is now async (was sync)
- Agent now uses `AgentExecutor` when MCP is enabled
- Enhanced error handling for MCP connection failures

### Documentation

**Updated**
- Added MCP integration section to README
- Documented `--mcp/--no-mcp` and `--mcp-server` CLI options
- Added MCP examples for CLI and programmatic usage
- Updated agent feature list to include MCP tools

### Tests

- Added `test_mcp_initialization_disabled()` test
- Added `test_mcp_disabled_by_default_if_not_available()` test
- Updated existing tests to handle async `_initialize_llm()`
- All 27 agent tests passing

## [0.2.0] - 2025-10-18

### Added - AI Agent

**LangChain-Powered Agent**
- `TokenBowlAgent` class for intelligent chat message responses
- LangChain integration with OpenRouter for multi-model support
- Automatic message queuing with configurable flush intervals (default: 15s)
- Exponential backoff reconnection strategy (up to 5 minutes)
- Conversation memory across message batches
- Read receipt tracking and statistics
- CLI command: `token-bowl agent run` with comprehensive options
- Dual prompt system:
  - **System prompt**: Defines agent personality and role (can be text or markdown file)
  - **User prompt**: Defines batch processing instructions (can be text or markdown file)
- Programmatic and CLI usage modes

**Agent Features**
- Auto-responds to both room messages and direct messages
- Comprehensive error handling and automatic retry
- WebSocket reconnection loop with exponential backoff on disconnect
- Context window management with intelligent conversation history trimming
- Configurable context window size (default: 128,000 tokens)
- Automatic token estimation and memory optimization
- Real-time statistics tracking (messages, tokens, uptime, errors)
- Verbose logging mode for debugging
- Configurable models (OpenAI, Anthropic, etc. via OpenRouter)
- Resilient operation - continues running even with network interruptions

### Dependencies

**Added**
- `langchain>=0.3.0` - LangChain framework
- `langchain-core>=0.3.0` - LangChain core components
- `langchain-openai>=0.2.0` - OpenAI/OpenRouter integration
- `langchain-community>=0.3.0` - Community integrations
- `openai>=1.50.0` - OpenAI client library

### Documentation

**Updated**
- Added comprehensive AI Agent section to README
- Added agent CLI examples and programmatic usage
- Updated features list to include AI agent
- Added agent to table of contents

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
