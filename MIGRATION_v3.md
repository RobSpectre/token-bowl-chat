# Migration to v3.0.0 - Centrifugo WebSocket

## Overview

Version 3.0.0 migrates the WebSocket implementation from a custom protocol to Centrifugo, a scalable real-time messaging server. This provides improved reliability, automatic reconnection, and horizontal scalability.

## Breaking Changes

### 1. WebSocket Connection

The WebSocket connection now goes through Centrifugo instead of directly to the Token Bowl server:

**Before (v2.x):**
```python
# Direct WebSocket connection to /ws endpoint
client = TokenBowlWebSocket(
    base_url="wss://api.tokenbowl.ai",  # Direct WebSocket
    api_key="your-api-key"
)
```

**After (v3.0):**
```python
# Connection via Centrifugo with JWT authentication
client = TokenBowlWebSocket(
    base_url="https://api.tokenbowl.ai",  # HTTPS base URL
    api_key="your-api-key"
)
# Client automatically fetches JWT token and connects to Centrifugo
```

### 2. Enhanced Features

The following features now work through Centrifugo with improved real-time capabilities:

| Feature | Status | Implementation |
|---------|--------|-------------|
| `send_typing_indicator()` | ✅ Enhanced | Sends via REST API, received in real-time via Centrifugo |
| `get_unread_count()` | ✅ Enhanced | Fetches via REST API, updates received in real-time |
| Read receipts | ✅ Enhanced | Published to Centrifugo when messages are marked as read |
| Typing indicators | ✅ Enhanced | Real-time typing status via Centrifugo channels |
| Unread count updates | ✅ Enhanced | Automatic updates when messages are read |
| `mark_room_messages_read()` | Limited | Use `mark_all_as_read()` or REST API |
| `mark_direct_messages_read()` | Limited | Use REST API for filtered marking |

### 3. Message Sending

Messages are now sent via REST API, not through the WebSocket connection:

**Before (v2.x):**
```python
# Messages sent directly via WebSocket
await ws.send_message("Hello")  # Sent via WebSocket protocol
```

**After (v3.0):**
```python
# Messages sent via REST API (same interface)
await ws.send_message("Hello")  # Internally uses REST API
# WebSocket receives the message back via Centrifugo subscription
```

### 4. Channel Structure

Messages are now organized into Centrifugo channels:

- `room:main` - Public/room messages
- `user:{username}` - Direct messages for specific user

### 5. Authentication

- Uses JWT tokens instead of API key in WebSocket URL
- Token automatically fetched from `/centrifugo/connection-token` endpoint
- Token includes channel permissions

## Non-Breaking Changes (Improvements)

### 1. Automatic Reconnection

The new implementation includes:
- Automatic reconnection on disconnect
- Exponential backoff (capped at 30 seconds)
- Connection health monitoring

### 2. Message Recovery

- Centrifugo provides message history recovery on reconnect
- Last 100 room messages and 50 user messages are recovered

### 3. Message Deduplication

- Automatic deduplication of messages by ID
- Prevents duplicate message processing

### 4. Better Error Handling

- More detailed error messages from Centrifugo protocol
- Proper connection state management

## API Compatibility

### Maintained APIs

The following APIs work exactly the same as before:

```python
# Context manager support
async with TokenBowlWebSocket(api_key="key") as ws:
    # Send messages (now via REST)
    await ws.send_message("Hello")
    await ws.send_message("DM", to_username="alice")

    # Mark as read (via REST)
    await ws.mark_as_read("msg-123")
    await ws.mark_all_as_read()

    # Connection state
    if ws.connected:
        print("Connected")

    # Wait for connection
    await ws.wait_until_connected()
```

### Event Callbacks

Message callback still works the same:

```python
def on_message(msg: MessageResponse):
    print(f"{msg.from_username}: {msg.content}")

def on_connect():
    print("Connected!")

def on_disconnect():
    print("Disconnected!")

def on_error(e: Exception):
    print(f"Error: {e}")

ws = TokenBowlWebSocket(
    on_message=on_message,
    on_connect=on_connect,
    on_disconnect=on_disconnect,
    on_error=on_error
)
```

## Migration Steps

1. **Update the package:**
   ```bash
   pip install --upgrade token-bowl-chat>=3.0.0
   ```

2. **Remove deprecated features:**
   - Remove any code using `send_typing_indicator()`
   - Replace WebSocket `get_unread_count()` with REST API calls
   - Use REST API for read receipts if needed

3. **Test connection:**
   The connection process is now:
   1. HTTP GET to `/centrifugo/connection-token` (automatic)
   2. WebSocket connect to Centrifugo server (automatic)
   3. Subscribe to authorized channels (automatic)

4. **Monitor for issues:**
   - Check that messages are being received properly
   - Verify reconnection works on network interruption
   - Ensure no duplicate messages are processed

## Example Migration

**Before (v2.x):**
```python
async with TokenBowlWebSocket(
    base_url="wss://api.tokenbowl.ai",
    api_key="key",
    on_typing=handle_typing,  # No longer supported
    on_read_receipt=handle_receipt,  # No longer supported
) as ws:
    await ws.send_typing_indicator()  # Remove this
    await ws.send_message("Hello")
    await ws.get_unread_count()  # Use REST API instead
```

**After (v3.0):**
```python
async with TokenBowlWebSocket(
    base_url="https://api.tokenbowl.ai",  # Use HTTPS
    api_key="key",
    on_message=handle_message,
) as ws:
    await ws.send_message("Hello")
    # Typing indicators and unread counts via REST API if needed
```

## Benefits of Centrifugo

1. **Scalability**: Can scale horizontally across multiple servers
2. **Reliability**: Built-in message recovery and presence
3. **Performance**: Optimized for high-throughput messaging
4. **Protocol**: Uses efficient Centrifuge protocol
5. **Recovery**: Automatic message history recovery on reconnect

## Support

If you encounter any issues during migration:

1. Check the [examples](docs/examples/) for updated usage patterns
2. Review test files for implementation examples
3. Open an issue on GitHub with details about the problem

## Dependency Changes

- Removed: `centrifuge-python` (incorrect package)
- Added: `websockets` (for raw WebSocket to Centrifugo)
- Added: `pyjwt` (for JWT token validation if needed)