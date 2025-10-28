"""Tests for the TokenBowlAgent class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from token_bowl_chat.agent import AgentStats, MessageQueueItem, TokenBowlAgent
from token_bowl_chat.models import MessageResponse


class TestAgentStats:
    """Test AgentStats dataclass."""

    def test_stats_initialization(self):
        """Test stats are initialized with correct defaults."""
        stats = AgentStats()
        assert stats.messages_received == 0
        assert stats.messages_sent == 0
        assert stats.errors == 0
        assert stats.reconnections == 0
        assert stats.total_input_tokens == 0
        assert stats.total_output_tokens == 0
        assert stats.start_time is not None

    def test_uptime_calculation(self):
        """Test uptime string formatting."""
        stats = AgentStats()
        uptime = stats.uptime()
        assert isinstance(uptime, str)
        assert "h" in uptime
        assert "m" in uptime
        assert "s" in uptime


class TestMessageQueueItem:
    """Test MessageQueueItem dataclass."""

    def test_queue_item_creation(self):
        """Test creating a message queue item."""
        from datetime import datetime, timezone

        item = MessageQueueItem(
            message_id="test-123",
            content="Hello world",
            from_username="alice",
            to_username="bob",
            timestamp=datetime.now(timezone.utc),
            is_direct=True,
        )
        assert item.message_id == "test-123"
        assert item.content == "Hello world"
        assert item.from_username == "alice"
        assert item.to_username == "bob"
        assert item.is_direct is True


class TestTokenBowlAgent:
    """Test TokenBowlAgent class."""

    def test_agent_initialization_defaults(self):
        """Test agent initializes with correct defaults."""
        agent = TokenBowlAgent(
            api_key="test-api-key", openrouter_api_key="test-openrouter-key"
        )

        assert agent.api_key == "test-api-key"
        assert agent.openrouter_api_key == "test-openrouter-key"
        assert agent.model_name == "openai/gpt-4o-mini"
        assert agent.queue_interval == 30.0
        assert agent.max_reconnect_delay == 300.0
        assert agent.context_window == 128000
        assert agent.mcp_enabled is True  # Default is True (if MCP available)
        assert agent.mcp_server_url == "https://tokenbowl-mcp.haihai.ai/sse"
        assert agent.verbose is False
        assert agent.is_running is False
        assert len(agent.message_queue) == 0
        assert len(agent.conversation_history) == 0

    def test_agent_initialization_custom_values(self):
        """Test agent initializes with custom values."""
        agent = TokenBowlAgent(
            api_key="custom-api-key",
            openrouter_api_key="custom-openrouter-key",
            system_prompt="Custom system prompt",
            user_prompt="Custom user prompt",
            model_name="anthropic/claude-sonnet-4.5",
            queue_interval=30.0,
            max_reconnect_delay=600.0,
            context_window=200000,
            mcp_enabled=False,
            mcp_server_url="https://custom-mcp.example.com/sse",
            verbose=True,
        )

        assert agent.api_key == "custom-api-key"
        assert agent.system_prompt == "Custom system prompt"
        assert agent.user_prompt == "Custom user prompt"
        assert agent.model_name == "anthropic/claude-sonnet-4.5"
        assert agent.queue_interval == 30.0
        assert agent.max_reconnect_delay == 600.0
        assert agent.context_window == 200000
        assert agent.mcp_enabled is False
        assert agent.mcp_server_url == "https://custom-mcp.example.com/sse"
        assert agent.verbose is True

    def test_load_prompt_from_text(self):
        """Test loading prompt from text string."""
        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test", system_prompt="Test prompt"
        )
        assert agent.system_prompt == "Test prompt"

    def test_load_prompt_from_file(self, tmp_path):
        """Test loading prompt from file."""
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("This is a test prompt from file")

        agent = TokenBowlAgent(
            api_key="test",
            openrouter_api_key="test",
            system_prompt=str(prompt_file),
        )
        assert agent.system_prompt == "This is a test prompt from file"

    def test_load_prompt_file_not_found_uses_default(self):
        """Test loading prompt from non-existent file uses default."""
        agent = TokenBowlAgent(
            api_key="test",
            openrouter_api_key="test",
            system_prompt="/nonexistent/file.md",
        )
        # Should use the text as-is if file doesn't exist
        assert agent.system_prompt == "/nonexistent/file.md"

    def test_load_prompt_default(self):
        """Test default prompts are used when none provided."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")
        assert (
            agent.system_prompt
            == "You are a fantasy football manager trying to win a championship"
        )
        assert agent.user_prompt == "Respond to these messages"

    def test_estimate_tokens(self):
        """Test token estimation."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        # Test empty string
        assert agent._estimate_tokens("") == 0

        # Test that token estimation returns reasonable values
        # Note: Results vary based on whether tiktoken is available
        # tiktoken (accurate): "test" = 1 token, "hello world" = 2 tokens, "a"*100 = 13 tokens
        # fallback heuristic: chars // 4
        test_tokens = agent._estimate_tokens("test")
        assert test_tokens >= 1

        hello_tokens = agent._estimate_tokens("hello world")
        assert hello_tokens >= 2

        long_tokens = agent._estimate_tokens("a" * 100)
        assert long_tokens >= 13  # tiktoken gives accurate count of 13

    def test_trim_conversation_history_empty(self):
        """Test trimming empty history does nothing."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")
        agent._trim_conversation_history()
        assert len(agent.conversation_history) == 0

    def test_trim_conversation_history_within_limit(self):
        """Test trimming when history fits in context window."""
        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test", context_window=128000
        )

        # Add messages that fit easily
        agent.conversation_history = [
            HumanMessage(content="Short message 1"),
            AIMessage(content="Short response 1"),
            HumanMessage(content="Short message 2"),
            AIMessage(content="Short response 2"),
        ]

        initial_count = len(agent.conversation_history)
        agent._trim_conversation_history()
        assert len(agent.conversation_history) == initial_count

    def test_trim_conversation_history_exceeds_limit(self):
        """Test trimming when history exceeds context window."""
        agent = TokenBowlAgent(
            api_key="test",
            openrouter_api_key="test",
            context_window=1000,  # Small
        )

        # Add many large messages
        for i in range(20):
            agent.conversation_history.append(
                HumanMessage(content=f"Message {i} " * 100)
            )
            agent.conversation_history.append(AIMessage(content=f"Response {i} " * 100))

        initial_count = len(agent.conversation_history)
        agent._trim_conversation_history()

        # Should have trimmed some messages
        assert len(agent.conversation_history) < initial_count

    def test_trim_conversation_history_removes_oldest_first(self):
        """Test that trimming removes oldest messages first."""
        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test", context_window=5000
        )

        # Add messages with identifiable content
        agent.conversation_history = [
            HumanMessage(content="OLDEST " * 50),  # ~350 chars
            AIMessage(content="OLD " * 50),  # ~200 chars
            HumanMessage(content="NEWER " * 50),  # ~300 chars
            AIMessage(content="NEWEST " * 50),  # ~350 chars
        ]

        agent._trim_conversation_history()

        # Should have some messages remaining
        assert len(agent.conversation_history) > 0

        # The newest messages should be more likely to remain
        remaining_content = "".join(
            str(msg.content) for msg in agent.conversation_history
        )

        # Either NEWEST is present, or the history was completely trimmed
        # due to reserved space for system/user prompts
        if remaining_content:
            # If we have content, newer messages should be favored
            newest_count = remaining_content.count("NEWEST")
            oldest_count = remaining_content.count("OLDEST")
            assert newest_count >= oldest_count

    @pytest.mark.asyncio
    async def test_calculate_backoff_delay_increases(self):
        """Test exponential backoff delay increases."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        agent.reconnect_attempts = 0
        delay1 = await agent._calculate_backoff_delay()

        agent.reconnect_attempts = 1
        delay2 = await agent._calculate_backoff_delay()

        agent.reconnect_attempts = 5
        delay5 = await agent._calculate_backoff_delay()

        # Delays should increase
        assert delay2 > delay1
        assert delay5 > delay2

    @pytest.mark.asyncio
    async def test_calculate_backoff_delay_caps_at_max(self):
        """Test backoff delay is capped at max_reconnect_delay."""
        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test", max_reconnect_delay=60.0
        )

        agent.reconnect_attempts = 100  # Very high number
        delay = await agent._calculate_backoff_delay()

        # Should not exceed max (plus jitter is 10%)
        assert delay <= 60.0 * 1.1

    def test_on_message_queues_message(self):
        """Test _on_message adds message to queue."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        msg = MessageResponse(
            id="msg-123",
            content="Test message",
            from_user_id="user-1",
            from_username="alice",
            to_user_id=None,
            to_username=None,
            message_type="room",
            timestamp="2025-10-19T12:00:00Z",
            description="test message",
        )

        agent._on_message(msg)

        assert len(agent.message_queue) == 1
        queued_item = agent.message_queue[0]
        assert queued_item.message_id == "msg-123"
        assert queued_item.content == "Test message"
        assert queued_item.from_username == "alice"
        assert queued_item.is_direct is False

    def test_on_message_ignores_own_messages(self):
        """Test _on_message ignores messages sent by the agent."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        # Track a sent message content (this happens before sending)
        agent.sent_message_contents.append("My message")

        msg = MessageResponse(
            id="msg-123",
            content="My message",
            from_user_id="user-1",
            from_username="me",
            to_user_id=None,
            to_username=None,
            message_type="room",
            timestamp="2025-10-19T12:00:00Z",
            description="test message",
        )

        agent._on_message(msg)

        # Should not queue own message
        assert len(agent.message_queue) == 0
        # Should track the message ID after receiving the echo
        assert agent.sent_messages["msg-123"] == "My message"

    def test_on_message_marks_as_read(self):
        """Test _on_message marks messages as read."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        # Mock WebSocket client with mark_message_read
        agent.ws = AsyncMock()
        agent.ws.mark_message_read = AsyncMock()

        msg = MessageResponse(
            id="msg-456",
            content="Test message",
            from_user_id="user-1",
            from_username="alice",
            to_user_id=None,
            to_username=None,
            message_type="room",
            timestamp="2025-10-19T12:00:00Z",
            description="test message",
        )

        # Create a side effect that closes the coroutine to avoid warnings
        def close_coro(coro):
            coro.close()
            return MagicMock()

        with patch("asyncio.create_task", side_effect=close_coro) as mock_create_task:
            agent._on_message(msg)

            # Verify message was queued
            assert len(agent.message_queue) == 1

            # Verify mark_message_read was scheduled to be called
            mock_create_task.assert_called_once()
            # The task should be calling mark_message_read
            call_args = mock_create_task.call_args
            assert call_args is not None

    def test_on_message_marks_direct_message_as_read(self):
        """Test _on_message marks direct messages as read."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        # Mock WebSocket client
        agent.ws = AsyncMock()
        agent.ws.mark_message_read = AsyncMock()

        msg = MessageResponse(
            id="dm-789",
            content="Direct message",
            from_user_id="user-2",
            from_username="bob",
            to_user_id="user-me",
            to_username="me",
            message_type="direct",
            timestamp="2025-10-19T12:00:00Z",
            description="test message",
        )

        # Create a side effect that closes the coroutine to avoid warnings
        def close_coro(coro):
            coro.close()
            return MagicMock()

        with patch("asyncio.create_task", side_effect=close_coro) as mock_create_task:
            agent._on_message(msg)

            # Verify DM was queued
            assert len(agent.message_queue) == 1
            assert agent.message_queue[0].is_direct is True

            # Verify mark_message_read was scheduled
            mock_create_task.assert_called_once()

    def test_on_read_receipt(self):
        """Test _on_read_receipt tracks receipts."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test", verbose=True)

        agent.sent_messages["msg-123"] = "Test message"

        # Should not raise error
        agent._on_read_receipt("msg-123", "alice")
        agent._on_read_receipt("unknown-msg", "bob")

    def test_environment_variable_api_keys(self, monkeypatch):
        """Test API keys can be loaded from environment variables."""
        monkeypatch.setenv("TOKEN_BOWL_CHAT_API_KEY", "env-chat-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "env-openrouter-key")

        agent = TokenBowlAgent(api_key="", openrouter_api_key="")

        assert agent.api_key == "env-chat-key"
        assert agent.openrouter_api_key == "env-openrouter-key"

    @pytest.mark.asyncio
    async def test_initialize_llm(self):
        """Test LLM initialization."""
        agent = TokenBowlAgent(
            api_key="test",
            openrouter_api_key="test-key",
            model_name="test-model",
            mcp_enabled=False,  # Disable MCP for this test
        )

        await agent._initialize_llm()

        assert agent.llm is not None
        assert agent.conversation_history == []

    @pytest.mark.asyncio
    async def test_initialize_llm_requires_api_key(self, monkeypatch):
        """Test LLM initialization fails without API key."""
        # Clear environment variable
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        agent = TokenBowlAgent(api_key="test", openrouter_api_key="")

        with pytest.raises(ValueError, match="OpenRouter API key required"):
            await agent._initialize_llm()

    @pytest.mark.asyncio
    async def test_process_message_batch_empty(self):
        """Test processing empty message batch does nothing."""
        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test", mcp_enabled=False
        )
        await agent._initialize_llm()

        # Should not raise error
        await agent._process_message_batch([])

        # Conversation history should be empty
        assert len(agent.conversation_history) == 0

    @pytest.mark.asyncio
    async def test_process_message_batch_updates_history(self):
        """Test processing messages updates conversation history."""
        from datetime import datetime, timezone

        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test-key", mcp_enabled=False
        )
        await agent._initialize_llm()

        # Mock the LLM
        mock_response = MagicMock()
        mock_response.content = "Test response"
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        # Mock WebSocket
        agent.ws = AsyncMock()
        agent.ws.send_typing_indicator = AsyncMock()
        agent.ws.send_message = AsyncMock(return_value=MagicMock(id="sent-123"))

        messages = [
            MessageQueueItem(
                message_id="msg-1",
                content="Hello",
                from_username="alice",
                to_username=None,
                timestamp=datetime.now(timezone.utc),
                is_direct=False,
            )
        ]

        with patch(
            "token_bowl_chat.agent.get_openai_callback"
        ) as mock_callback_context:
            mock_callback = MagicMock()
            mock_callback.prompt_tokens = 10
            mock_callback.completion_tokens = 20
            mock_callback.total_tokens = 30
            mock_callback_context.return_value.__enter__.return_value = mock_callback

            await agent._process_message_batch(messages)

        # Should have added to conversation history
        assert len(agent.conversation_history) == 2  # User message + AI response
        assert isinstance(agent.conversation_history[0], HumanMessage)
        assert isinstance(agent.conversation_history[1], AIMessage)

    @pytest.mark.asyncio
    async def test_process_message_batch_strips_whitespace(self):
        """Test that LLM responses have leading/trailing whitespace stripped."""
        from datetime import datetime, timezone

        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test-key", mcp_enabled=False
        )
        await agent._initialize_llm()

        # Mock the LLM with response that has extra whitespace
        mock_response = MagicMock()
        mock_response.content = "\n\nTest response with whitespace\n\n"
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        # Mock WebSocket
        agent.ws = AsyncMock()
        agent.ws.send_typing_indicator = AsyncMock()
        agent.ws.send_message = AsyncMock(return_value=MagicMock(id="sent-123"))

        messages = [
            MessageQueueItem(
                message_id="msg-1",
                content="Hello",
                from_username="alice",
                to_username=None,
                timestamp=datetime.now(timezone.utc),
                is_direct=False,
            )
        ]

        with patch(
            "token_bowl_chat.agent.get_openai_callback"
        ) as mock_callback_context:
            mock_callback = MagicMock()
            mock_callback.prompt_tokens = 10
            mock_callback.completion_tokens = 20
            mock_callback.total_tokens = 30
            mock_callback_context.return_value.__enter__.return_value = mock_callback

            await agent._process_message_batch(messages)

        # Verify the sent message was stripped
        agent.ws.send_message.assert_called_once()
        sent_content = agent.ws.send_message.call_args[0][0]
        assert sent_content == "Test response with whitespace"
        assert not sent_content.startswith("\n")
        assert not sent_content.endswith("\n")

        # Verify conversation history also has stripped version
        assert agent.conversation_history[1].content == "Test response with whitespace"

    def test_stats_tracking(self):
        """Test that stats are tracked correctly."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        assert agent.stats.messages_received == 0

        # Simulate receiving a message
        msg = MessageResponse(
            id="msg-1",
            content="Test",
            from_user_id="user-1",
            from_username="alice",
            to_user_id=None,
            to_username=None,
            message_type="room",
            timestamp="2025-10-19T12:00:00Z",
            description="test message",
        )
        agent._on_message(msg)

        assert agent.stats.messages_received == 1

    @pytest.mark.asyncio
    async def test_mcp_initialization_disabled(self):
        """Test MCP initialization when disabled."""
        agent = TokenBowlAgent(
            api_key="test",
            openrouter_api_key="test-key",
            mcp_enabled=False,
        )

        await agent._initialize_llm()

        assert agent.llm is not None
        assert agent.mcp_client is None
        assert len(agent.mcp_tools) == 0
        assert agent.agent_executor is None

    def test_mcp_disabled_by_default_if_not_available(self, monkeypatch):
        """Test MCP is disabled if libraries not available."""
        # Mock MCP as unavailable
        import token_bowl_chat.agent as agent_module

        original_mcp_available = agent_module.MCP_AVAILABLE
        agent_module.MCP_AVAILABLE = False

        try:
            agent = TokenBowlAgent(
                api_key="test",
                openrouter_api_key="test-key",
                mcp_enabled=True,  # Try to enable
            )

            # Should be disabled because MCP_AVAILABLE is False
            assert agent.mcp_enabled is False
        finally:
            agent_module.MCP_AVAILABLE = original_mcp_available

    @pytest.mark.asyncio
    async def test_fetch_unread_messages(self):
        """Test fetching unread messages on startup."""

        agent = TokenBowlAgent(
            api_key="test",
            openrouter_api_key="test-key",
            server_url="wss://test.example.com",
        )

        # Mock WebSocket
        agent.ws = AsyncMock()
        agent.ws.mark_message_read = AsyncMock()

        # Mock unread messages
        mock_room_msg = MessageResponse(
            id="room-msg-1",
            content="Unread room message",
            from_user_id="user-1",
            from_username="alice",
            to_user_id=None,
            to_username=None,
            message_type="room",
            timestamp="2025-10-19T12:00:00Z",
            description="test message",
        )

        mock_dm = MessageResponse(
            id="dm-1",
            content="Unread DM",
            from_user_id="user-2",
            from_username="bob",
            to_user_id="user-me",
            to_username="me",
            message_type="direct",
            timestamp="2025-10-19T12:01:00Z",
            description="test message",
        )

        # Mock AsyncTokenBowlClient
        with patch("token_bowl_chat.agent.AsyncTokenBowlClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_unread_messages = AsyncMock(return_value=[mock_room_msg])
            mock_client.get_unread_direct_messages = AsyncMock(return_value=[mock_dm])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await agent._fetch_unread_messages()

            # Verify client was created with correct parameters
            mock_client_class.assert_called_once_with(
                api_key="test", base_url="https://test.example.com"
            )

            # Verify unread messages were fetched
            mock_client.get_unread_messages.assert_called_once_with(limit=100)
            mock_client.get_unread_direct_messages.assert_called_once_with(limit=100)

            # Verify messages were queued
            assert len(agent.message_queue) == 2

            # Verify stats were updated
            assert agent.stats.messages_received == 2

            # Verify messages were marked as read
            assert agent.ws.mark_message_read.call_count == 2

    def test_calculate_similarity_identical(self):
        """Test similarity calculation for identical texts."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        similarity = agent._calculate_similarity("Hello world", "Hello world")
        assert similarity == 1.0

    def test_calculate_similarity_different(self):
        """Test similarity calculation for completely different texts."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        similarity = agent._calculate_similarity(
            "Hello world", "Completely different text"
        )
        assert similarity < 0.5

    def test_calculate_similarity_case_insensitive(self):
        """Test similarity calculation is case insensitive."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        similarity = agent._calculate_similarity("Hello World", "hello world")
        assert similarity == 1.0

    def test_is_repetitive_response_no_previous_messages(self):
        """Test that no messages returns False for repetition check."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        # No previous messages
        assert not agent._is_repetitive_response("Any message")

    def test_is_repetitive_response_detects_similar(self):
        """Test that similar messages are detected as repetitive."""
        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test", similarity_threshold=0.85
        )

        # Add some previous messages
        agent.sent_message_contents.append("I understand your concern.")
        agent.sent_message_contents.append("Let me help you with that.")
        agent.sent_message_contents.append("I understand your concern about this.")

        # This should be detected as similar to the third message
        assert agent._is_repetitive_response("I understand your concern about that.")

    def test_is_repetitive_response_allows_different(self):
        """Test that different messages are not flagged as repetitive."""
        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test", similarity_threshold=0.85
        )

        # Add some previous messages
        agent.sent_message_contents.append("I understand your concern.")
        agent.sent_message_contents.append("Let me help you with that.")
        agent.sent_message_contents.append("Here's some information.")

        # This should not be detected as similar
        assert not agent._is_repetitive_response(
            "Completely different response about something else entirely."
        )

    def test_clear_conversation_memory(self):
        """Test that conversation memory is cleared."""
        agent = TokenBowlAgent(api_key="test", openrouter_api_key="test")

        # Add some conversation history
        agent.conversation_history.append(HumanMessage(content="Hello"))
        agent.conversation_history.append(AIMessage(content="Hi there"))
        agent.conversation_history.append(HumanMessage(content="How are you?"))

        assert len(agent.conversation_history) == 3

        # Clear memory
        agent._clear_conversation_memory()

        # Should be empty now
        assert len(agent.conversation_history) == 0

    @pytest.mark.asyncio
    async def test_process_message_batch_detects_repetition(self):
        """Test that repetitive responses are not sent and memory is cleared."""
        from datetime import datetime, timezone

        agent = TokenBowlAgent(
            api_key="test",
            openrouter_api_key="test-key",
            mcp_enabled=False,
            similarity_threshold=0.85,
        )
        await agent._initialize_llm()

        # Mock the LLM to return a repetitive response
        mock_response = MagicMock()
        mock_response.content = "I understand your concern."
        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        # Mock WebSocket
        agent.ws = AsyncMock()
        agent.ws.send_typing_indicator = AsyncMock()
        agent.ws.send_message = AsyncMock()

        # Add previous similar messages
        agent.sent_message_contents.append("I understand your concern.")
        agent.sent_message_contents.append("I understand your concern about that.")
        agent.sent_message_contents.append("I understand your concerns.")

        # Add some conversation history
        agent.conversation_history.append(HumanMessage(content="Previous message"))

        messages = [
            MessageQueueItem(
                message_id="msg-1",
                content="Hello",
                from_username="alice",
                to_username=None,
                timestamp=datetime.now(timezone.utc),
                is_direct=False,
            )
        ]

        with patch(
            "token_bowl_chat.agent.get_openai_callback"
        ) as mock_callback_context:
            mock_callback = MagicMock()
            mock_callback.prompt_tokens = 10
            mock_callback.completion_tokens = 20
            mock_callback.total_tokens = 30
            mock_callback_context.return_value.__enter__.return_value = mock_callback

            await agent._process_message_batch(messages)

        # Message should NOT have been sent due to repetition
        agent.ws.send_message.assert_not_called()

        # Conversation history should have been cleared
        assert len(agent.conversation_history) == 0

    def test_similarity_threshold_configurable(self):
        """Test that similarity threshold can be configured."""
        agent = TokenBowlAgent(
            api_key="test", openrouter_api_key="test", similarity_threshold=0.9
        )

        assert agent.similarity_threshold == 0.9
