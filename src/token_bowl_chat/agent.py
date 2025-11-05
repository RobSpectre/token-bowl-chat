"""Token Bowl Chat Agent - LangChain-powered chat agent with WebSocket support.

This module provides an intelligent agent that connects to Token Bowl Chat servers
via WebSocket, processes incoming messages with LangChain, and responds intelligently.
"""

import asyncio
import contextlib
import os
import random
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from rich.console import Console

from token_bowl_chat.async_client import AsyncTokenBowlClient
from token_bowl_chat.models import MessageResponse
from token_bowl_chat.websocket_client_v3 import TokenBowlWebSocket

# MCP imports (optional)
try:
    from langchain_mcp_adapters.client import (  # type: ignore[import-untyped]
        MultiServerMCPClient,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# tiktoken for accurate token counting (optional, comes with openai package)
try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

console = Console()

# Memory management constants
MAX_SENT_MESSAGES_TRACKED = 1000  # Limit sent message tracking to prevent memory leaks
MAX_MESSAGE_QUEUE_SIZE = 1000  # Maximum messages to queue before processing

# Similarity detection constants
SIMILARITY_THRESHOLD = (
    0.85  # Similarity threshold for detecting repetitive responses (0.0-1.0)
)
SIMILARITY_CHECK_COUNT = 3  # Number of previous messages to check for similarity

# Conversation history management
MAX_CONVERSATION_HISTORY = (
    10  # Maximum number of messages to keep in conversation history
)

# Retry mechanism constants
MAX_RETRY_ATTEMPTS = 3  # Maximum number of retry attempts per message
RETRY_BASE_DELAY = 5  # Base delay in seconds for exponential backoff
MAX_RETRY_DELAY = 60  # Maximum retry delay in seconds


@dataclass
class MessageQueueItem:
    """A message in the processing queue."""

    message_id: str
    content: str
    from_username: str
    to_username: str | None
    timestamp: datetime
    is_direct: bool
    retry_count: int = 0
    last_attempt_time: datetime | None = None
    last_error: str | None = None


@dataclass
class AgentStats:
    """Statistics for the agent."""

    messages_received: int = 0
    messages_sent: int = 0
    errors: int = 0
    reconnections: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    retries: int = 0
    messages_failed_permanently: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def uptime(self) -> str:
        """Get uptime as a formatted string."""
        delta = datetime.now(timezone.utc) - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary for JSON serialization."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": int(
                (datetime.now(timezone.utc) - self.start_time).total_seconds()
            ),
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "errors": self.errors,
            "reconnections": self.reconnections,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "retries": self.retries,
            "messages_failed_permanently": self.messages_failed_permanently,
            "start_time": self.start_time.isoformat(),
        }


class TokenBowlAgent:
    """An intelligent agent for Token Bowl Chat using LangChain."""

    def __init__(
        self,
        api_key: str,
        openrouter_api_key: str,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        model_name: str = "openai/gpt-4o-mini",
        server_url: str = "wss://api.tokenbowl.ai",
        queue_interval: float = 30.0,
        max_reconnect_delay: float = 300.0,
        context_window: int = 128000,
        cooldown_messages: int = 3,
        cooldown_minutes: int = 10,
        max_conversation_history: int = 10,
        mcp_enabled: bool = True,
        mcp_server_url: str = "https://tokenbowl-mcp.haihai.ai/sse",
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        max_retry_attempts: int = MAX_RETRY_ATTEMPTS,
        retry_base_delay: float = RETRY_BASE_DELAY,
        max_retry_delay: float = MAX_RETRY_DELAY,
        verbose: bool = False,
    ):
        """Initialize the Token Bowl Agent.

        Args:
            api_key: Token Bowl Chat API key (or TOKEN_BOWL_CHAT_API_KEY env var)
            openrouter_api_key: OpenRouter API key (or OPENROUTER_API_KEY env var)
            system_prompt: System prompt text or path to markdown file
            user_prompt: User prompt for processing messages
            model_name: OpenRouter model name (default: openai/gpt-4o-mini)
            server_url: WebSocket server URL
            queue_interval: Seconds to wait before flushing message queue (default: 30.0)
            max_reconnect_delay: Maximum delay between reconnection attempts (seconds)
            context_window: Maximum context window in tokens (default: 128000)
            cooldown_messages: Number of messages before cooldown starts (default: 3)
            cooldown_minutes: Cooldown duration in minutes (default: 10)
            max_conversation_history: Maximum number of messages to keep in conversation history (default: 10)
            mcp_enabled: Enable MCP (Model Context Protocol) tools (default: True)
            mcp_server_url: MCP server URL (default: https://tokenbowl-mcp.haihai.ai/sse)
            similarity_threshold: Threshold for detecting repetitive responses (0.0-1.0, default: 0.85)
            max_retry_attempts: Maximum number of retry attempts per message (default: 3)
            retry_base_delay: Base delay in seconds for exponential backoff (default: 5)
            max_retry_delay: Maximum retry delay in seconds (default: 60)
            verbose: Enable verbose logging
        """
        self.api_key = api_key or os.getenv("TOKEN_BOWL_CHAT_API_KEY", "")
        self.openrouter_api_key = openrouter_api_key or os.getenv(
            "OPENROUTER_API_KEY", ""
        )
        self.model_name = model_name
        self.server_url = server_url
        self.queue_interval = queue_interval
        self.max_reconnect_delay = max_reconnect_delay

        # Validate and set context window
        if context_window < 1000:
            raise ValueError("context_window must be at least 1000 tokens")
        if context_window > 1000000:
            console.print(
                f"[yellow]Warning: Large context window ({context_window} tokens) may consume significant RAM[/yellow]"
            )
        self.context_window = context_window

        # Validate and set max conversation history
        if max_conversation_history < 1:
            raise ValueError("max_conversation_history must be at least 1")
        if max_conversation_history > 100:
            console.print(
                f"[yellow]Warning: Large conversation history ({max_conversation_history} messages) may consume significant memory[/yellow]"
            )
        self.max_conversation_history = max_conversation_history

        self.mcp_enabled = mcp_enabled and MCP_AVAILABLE
        self.mcp_server_url = mcp_server_url
        self.similarity_threshold = similarity_threshold
        self.verbose = verbose

        # Load prompts
        self.system_prompt = self._load_prompt(
            system_prompt,
            "You are a fantasy football manager trying to win a championship",
        )
        self.user_prompt = self._load_prompt(
            user_prompt,
            "Respond to these messages",
        )

        # Message queue and processing
        # Limit queue size to prevent unbounded growth under heavy load
        self.message_queue: deque[MessageQueueItem] = deque(
            maxlen=MAX_MESSAGE_QUEUE_SIZE
        )
        self.failed_messages: deque[MessageQueueItem] = deque(
            maxlen=MAX_MESSAGE_QUEUE_SIZE
        )
        self.processing_lock = asyncio.Lock()
        self.last_flush_time = datetime.now(timezone.utc)

        # Retry configuration
        self.max_retry_attempts = max_retry_attempts
        self.retry_base_delay = retry_base_delay
        self.max_retry_delay = max_retry_delay

        # WebSocket and reconnection state
        self.ws: TokenBowlWebSocket | None = None
        self.reconnect_attempts = 0
        self.is_running = False

        # Statistics
        self.stats = AgentStats()

        # LangChain components
        self.llm: ChatOpenAI | None = None
        self.conversation_history: list[HumanMessage | AIMessage] = []

        # MCP components
        self.mcp_client: Any = None  # MultiServerMCPClient if enabled
        self.mcp_tools: list[Any] = []
        self.agent_executor: AgentExecutor | None = None

        # Sent message tracking for read receipts
        # Use OrderedDict to maintain insertion order for efficient cleanup
        self.sent_messages: OrderedDict[str, str] = (
            OrderedDict()
        )  # message_id -> content (populated on echo)
        self.sent_message_contents: deque[str] = deque(
            maxlen=100
        )  # Recently sent content

        # Processed message tracking to prevent retry loops
        # Track message IDs we've already attempted to process (successfully or not)
        self.processed_message_ids: deque[str] = deque(
            maxlen=1000
        )  # Limit size to prevent memory leaks

        # Cooldown mechanism
        self.messages_sent_in_window = 0
        self.cooldown_start_time: datetime | None = None
        self.cooldown_duration_seconds = cooldown_minutes * 60
        self.messages_per_window = cooldown_messages

        # Token counting - use tiktoken if available for accuracy
        self.token_encoder: Any = None
        if TIKTOKEN_AVAILABLE:
            # Try to get encoding for the specific model, fall back to cl100k_base
            # cl100k_base is used by GPT-4, GPT-3.5-turbo, and text-embedding-ada-002
            with contextlib.suppress(Exception):
                self.token_encoder = tiktoken.get_encoding("cl100k_base")

    def _load_prompt(self, prompt: str | None, default: str) -> str:
        """Load a prompt from text or file path.

        Args:
            prompt: Prompt text or path to markdown file
            default: Default prompt if none provided

        Returns:
            Loaded prompt text
        """
        if not prompt:
            return default

        # Check if it's a file path
        path = Path(prompt)
        if path.exists() and path.is_file():
            try:
                return path.read_text(encoding="utf-8")
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not read prompt file {prompt}: {e}[/yellow]"
                )
                return default

        # Otherwise, treat as raw text
        return prompt

    async def _initialize_llm(self) -> None:
        """Initialize the LangChain LLM and MCP tools."""
        if not self.openrouter_api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY or pass openrouter_api_key"
            )

        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=SecretStr(self.openrouter_api_key),
            base_url="https://openrouter.ai/api/v1",
            streaming=False,
            default_headers={
                "HTTP-Referer": "https://github.com/RobSpectre/token-bowl-chat",
                "X-Title": "Token Bowl Chat Agent",
            },
        )

        if self.verbose:
            console.print(
                f"[dim]Initialized LLM: {self.model_name} with OpenRouter[/dim]"
            )

        # Initialize MCP client and tools if enabled
        if self.mcp_enabled:
            await self._initialize_mcp()

    async def _initialize_mcp(self) -> None:
        """Initialize MCP client and load tools."""
        if not MCP_AVAILABLE:
            console.print(
                "[yellow]MCP libraries not available. Install with: pip install langchain-mcp-adapters mcp[/yellow]"
            )
            self.mcp_enabled = False
            return

        try:
            # Create MCP client with SSE transport
            self.mcp_client = MultiServerMCPClient(
                {
                    "tokenbowl": {
                        "transport": "sse",
                        "url": self.mcp_server_url,
                    }
                }
            )

            # Get tools from MCP server
            self.mcp_tools = await self.mcp_client.get_tools()

            if self.verbose:
                console.print(f"[dim]MCP: Connected to {self.mcp_server_url}[/dim]")
                console.print(
                    f"[dim]MCP: Loaded {len(self.mcp_tools)} tools: {[t.name for t in self.mcp_tools]}[/dim]"
                )

            # Create agent executor with tools
            if self.mcp_tools and self.llm:
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", self.system_prompt),
                        MessagesPlaceholder("chat_history", optional=True),
                        ("human", "{input}"),
                        MessagesPlaceholder("agent_scratchpad"),
                    ]
                )

                agent = create_tool_calling_agent(self.llm, self.mcp_tools, prompt)
                self.agent_executor = AgentExecutor(
                    agent=agent,
                    tools=self.mcp_tools,
                    verbose=self.verbose,
                    return_intermediate_steps=True,
                    handle_parsing_errors=True,
                    max_iterations=50,
                    max_execution_time=900,
                )

                console.print(
                    f"[bold green]✓ MCP enabled with {len(self.mcp_tools)} tools[/bold green]"
                )

        except Exception as e:
            console.print(f"[yellow]Warning: Failed to initialize MCP: {e}[/yellow]")
            if self.verbose:
                import traceback

                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            self.mcp_enabled = False
            self.mcp_client = None
            self.mcp_tools = []

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses tiktoken for accurate counting if available, otherwise falls back
        to a simple heuristic: ~4 characters per token (conservative estimate).

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        if self.token_encoder:
            try:
                return len(self.token_encoder.encode(text))
            except Exception:
                # Fall back to heuristic if encoding fails
                pass
        return len(text) // 4

    def _trim_conversation_history(self) -> None:
        """Trim conversation history to keep only the last N messages.

        Keeps conversation memory focused and prevents context pollution.
        Removes oldest messages first.
        """
        if not self.conversation_history:
            return

        # Remove oldest messages until we're at the limit
        while len(self.conversation_history) > self.max_conversation_history:
            # Remove oldest message (first in list)
            removed_msg = self.conversation_history.pop(0)

            if self.verbose:
                msg_type = "User" if isinstance(removed_msg, HumanMessage) else "AI"
                console.print(
                    f"[dim]Trimmed {msg_type} message from history (keeping last {self.max_conversation_history} messages)[/dim]"
                )

    def _cleanup_sent_messages(self) -> None:
        """Limit sent_messages dict size to prevent unbounded memory growth.

        Removes oldest entries when limit is exceeded.
        This prevents memory leaks in long-running agents.
        """
        while len(self.sent_messages) > MAX_SENT_MESSAGES_TRACKED:
            # Remove oldest entry (first item in OrderedDict)
            self.sent_messages.popitem(last=False)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using SequenceMatcher.

        Args:
            text1: First text to compare
            text2: Second text to compare

        Returns:
            Similarity ratio (0.0 to 1.0), where 1.0 is identical
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _is_repetitive_response(self, response_text: str) -> bool:
        """Check if response is too similar to recent responses.

        Args:
            response_text: The response text to check

        Returns:
            True if response is repetitive, False otherwise
        """
        if not self.sent_message_contents:
            return False

        # Check similarity against last N sent messages
        recent_messages = list(self.sent_message_contents)[-SIMILARITY_CHECK_COUNT:]

        for previous_message in recent_messages:
            similarity = self._calculate_similarity(response_text, previous_message)
            if similarity >= self.similarity_threshold:
                if self.verbose:
                    console.print(
                        f"[yellow]Detected repetitive response (similarity: {similarity:.2f})[/yellow]"
                    )
                return True

        return False

    def _clear_conversation_memory(self) -> None:
        """Clear all conversation memory to reset the agent.

        This erases conversation history, allowing the agent to start fresh
        and break out of repetitive response loops.
        """
        self.conversation_history.clear()
        if self.verbose:
            console.print("[yellow]Cleared conversation memory to reset agent[/yellow]")

    async def _global_reset(self) -> None:
        """Perform a global reset of all agent state.

        Clears all conversation history, message queues, and waits for next input.
        This provides a clean slate to break out of problematic conversation loops.
        """
        async with self.processing_lock:
            # Clear conversation memory
            self.conversation_history.clear()

            # Clear message queue
            self.message_queue.clear()

            # Clear sent message tracking (except for read receipt tracking)
            self.sent_message_contents.clear()

            # Reset flush time to prevent immediate processing
            self.last_flush_time = datetime.now(timezone.utc)

            console.print(
                "[bold yellow]🔄 Global reset performed - all state cleared, waiting for next input[/bold yellow]"
            )

    async def _calculate_backoff_delay(self) -> float:
        """Calculate exponential backoff delay with jitter.

        Returns:
            Delay in seconds (capped at max_reconnect_delay)
        """
        # Exponential backoff: 2^attempt seconds, with jitter
        base_delay = float(min(2**self.reconnect_attempts, self.max_reconnect_delay))
        jitter = random.uniform(0, 0.1 * base_delay)
        return float(base_delay + jitter)

    async def _connect_websocket(self) -> bool:
        """Connect to the WebSocket server with retry logic.

        Returns:
            True if connected successfully
        """
        while self.is_running:
            try:
                if self.verbose:
                    console.print(
                        f"[dim]Attempting WebSocket connection to {self.server_url} (attempt {self.reconnect_attempts + 1})[/dim]"
                    )

                self.ws = TokenBowlWebSocket(
                    api_key=self.api_key,
                    base_url=self.server_url,
                    on_message=self._on_message,
                    on_read_receipt=self._on_read_receipt,
                    on_disconnect=self._on_disconnect,
                    on_error=self._on_error,
                )

                await self.ws.connect()

                console.print(
                    f"[bold green]✓ Connected to Token Bowl Chat at {self.server_url}[/bold green]"
                )
                self.reconnect_attempts = 0
                return True

            except Exception as e:
                self.stats.errors += 1
                delay = await self._calculate_backoff_delay()

                console.print(
                    f"[yellow]Connection to {self.server_url} failed: {e}. Retrying in {delay:.1f}s...[/yellow]"
                )

                self.reconnect_attempts += 1
                await asyncio.sleep(delay)

        return False

    async def _reconnect_websocket(self) -> None:
        """Reconnect to the WebSocket server after disconnection."""
        self.stats.reconnections += 1
        console.print(
            f"[yellow]Disconnected from {self.server_url}. Attempting to reconnect...[/yellow]"
        )

        await self._connect_websocket()

    def _on_message(self, msg: MessageResponse) -> None:
        """Handle incoming WebSocket messages.

        Args:
            msg: The received message
        """
        self.stats.messages_received += 1

        # Don't respond to our own messages
        # (WebSocket echoes back sent messages)
        if msg.content in self.sent_message_contents:
            # This is an echo of our own message - track it by ID
            self.sent_messages[msg.id] = msg.content
            self._cleanup_sent_messages()  # Prevent unbounded growth
            if self.verbose:
                console.print(f"[dim]Skipping own message: {msg.id[:8]}...[/dim]")
            return

        # Skip messages we've already processed to prevent retry loops
        if msg.id in self.processed_message_ids:
            if self.verbose:
                console.print(
                    f"[dim]Skipping already processed message: {msg.id[:8]}...[/dim]"
                )
            return

        # Queue message for processing
        queue_item = MessageQueueItem(
            message_id=msg.id,
            content=msg.content,
            from_username=msg.from_username,
            to_username=msg.to_username,
            timestamp=datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00")),
            is_direct=msg.message_type == "direct",
        )

        self.message_queue.append(queue_item)

        if self.verbose:
            msg_type = "DM" if queue_item.is_direct else "room"
            console.print(
                f"[dim]Queued {msg_type} message from {msg.from_username}: {msg.content[:50]}...[/dim]"
            )

        # Mark message as read immediately after queuing
        if self.ws:
            asyncio.create_task(self.ws.mark_message_read(msg.id))

    def _on_read_receipt(self, message_id: str, read_by: str) -> None:
        """Handle read receipts.

        Args:
            message_id: ID of the message that was read
            read_by: Username who read the message
        """
        if message_id in self.sent_messages and self.verbose:
            console.print(f"[dim]✓✓ {read_by} read our message[/dim]")

    def _on_error(self, error: Exception) -> None:
        """Handle WebSocket errors.

        Args:
            error: The error that occurred
        """
        error_msg = str(error)

        # Filter out benign server-side validation errors for typing indicators
        # These are non-fatal and don't affect functionality
        if "Missing content field" in error_msg:
            if self.verbose:
                console.print(
                    "[dim yellow]Server validation warning (non-fatal): Missing content field[/dim yellow]"
                )
            return

        # Log other errors normally
        self.stats.errors += 1
        console.print(f"[red]WebSocket error: {error_msg}[/red]")

    def _on_disconnect(self) -> None:
        """Handle WebSocket disconnection.

        Called when the server closes the connection or network issues occur.
        """
        if self.verbose:
            console.print(
                "[yellow]WebSocket disconnected by server (connection may have been replaced)[/yellow]"
            )

    def _is_in_cooldown(self) -> bool:
        """Check if agent is currently in cooldown period.

        Returns:
            True if in cooldown, False otherwise
        """
        if self.cooldown_start_time is None:
            return False

        elapsed = (
            datetime.now(timezone.utc) - self.cooldown_start_time
        ).total_seconds()
        return elapsed < self.cooldown_duration_seconds

    def _get_cooldown_remaining(self) -> int:
        """Get remaining cooldown time in seconds.

        Returns:
            Remaining seconds, or 0 if not in cooldown
        """
        if self.cooldown_start_time is None:
            return 0

        elapsed = (
            datetime.now(timezone.utc) - self.cooldown_start_time
        ).total_seconds()
        remaining = max(0, self.cooldown_duration_seconds - elapsed)
        return int(remaining)

    def _start_cooldown(self) -> None:
        """Start cooldown period and clear conversation history."""
        self.cooldown_start_time = datetime.now(timezone.utc)
        self.messages_sent_in_window = 0

        # Clear conversation history to free memory
        old_history_size = len(self.conversation_history)
        self.conversation_history.clear()

        console.print(
            f"\n[bold yellow]🕐 Cooldown started - {self.cooldown_duration_seconds // 60} minute break[/bold yellow]"
        )
        console.print(
            f"[dim yellow]Cleared {old_history_size} messages from conversation history[/dim yellow]\n"
        )

    def _end_cooldown(self) -> None:
        """End cooldown period and reset counters."""
        self.cooldown_start_time = None
        self.messages_sent_in_window = 0
        console.print(
            "[bold green]✓ Cooldown ended - Ready to respond to messages[/bold green]\n"
        )

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate exponential backoff delay for retries.

        Args:
            retry_count: Number of previous retry attempts

        Returns:
            Delay in seconds before next retry attempt
        """
        import random

        # Exponential backoff: base_delay * 2^retry_count
        delay = self.retry_base_delay * (2**retry_count)

        # Cap at max_retry_delay
        delay = min(delay, self.max_retry_delay)

        # Add jitter to prevent thundering herd (±10%)
        jitter = random.uniform(-0.1 * delay, 0.1 * delay)

        return float(delay + jitter)

    def _should_retry_message(self, message: MessageQueueItem) -> bool:
        """Check if a message should be retried.

        Args:
            message: The message to check

        Returns:
            True if the message should be retried, False otherwise
        """
        # Don't retry if we've exceeded max attempts
        if message.retry_count >= self.max_retry_attempts:
            return False

        # If this is the first attempt, always try
        if message.last_attempt_time is None:
            return True

        # Check if enough time has passed since last attempt
        delay = self._calculate_retry_delay(message.retry_count)
        elapsed = (
            datetime.now(timezone.utc) - message.last_attempt_time
        ).total_seconds()

        return elapsed >= delay

    def _requeue_failed_messages(self) -> None:
        """Check failed messages and requeue those ready for retry."""
        if not self.failed_messages:
            return

        messages_to_retry: list[MessageQueueItem] = []
        messages_to_keep: list[MessageQueueItem] = []

        # Check each failed message
        for msg in self.failed_messages:
            if self._should_retry_message(msg):
                messages_to_retry.append(msg)
            elif msg.retry_count < self.max_retry_attempts:
                # Not ready yet, keep in failed queue
                messages_to_keep.append(msg)
            else:
                # Permanently failed
                self.stats.messages_failed_permanently += 1
                if self.verbose:
                    console.print(
                        f"[red]✗ Message {msg.message_id} failed permanently after {msg.retry_count} attempts: {msg.last_error}[/red]"
                    )

        # Update failed queue
        self.failed_messages.clear()
        self.failed_messages.extend(messages_to_keep)

        # Requeue messages ready for retry
        for msg in messages_to_retry:
            msg.retry_count += 1
            msg.last_attempt_time = datetime.now(timezone.utc)
            self.stats.retries += 1
            if self.verbose:
                console.print(
                    f"[yellow]🔄 Retrying message {msg.message_id} (attempt {msg.retry_count}/{self.max_retry_attempts})[/yellow]"
                )
            self.message_queue.append(msg)

    async def _fetch_unread_messages(self) -> None:
        """Fetch all unread messages and queue them for processing."""
        try:
            # Create HTTP client for fetching unread messages
            # Convert wss:// to https:// for the HTTP API
            http_base_url = self.server_url.replace("wss://", "https://").replace(
                "/ws", ""
            )

            async with AsyncTokenBowlClient(
                api_key=self.api_key, base_url=http_base_url
            ) as client:
                # Fetch unread room messages
                unread_room = await client.get_unread_messages(limit=100)

                # Fetch unread direct messages
                unread_dms = await client.get_unread_direct_messages(limit=100)

                # Combine all unread messages
                all_unread = unread_room + unread_dms

                if all_unread:
                    console.print(
                        f"[cyan]📨 Found {len(unread_room)} unread room messages and {len(unread_dms)} unread DMs[/cyan]"
                    )

                    # Queue each unread message for processing
                    for msg in all_unread:
                        # Skip if we've already processed or sent this message
                        if (
                            msg.id in self.sent_messages
                            or msg.id in self.processed_message_ids
                        ):
                            continue

                        queue_item = MessageQueueItem(
                            message_id=msg.id,
                            content=msg.content,
                            from_username=msg.from_username,
                            to_username=msg.to_username,
                            timestamp=datetime.fromisoformat(
                                msg.timestamp.replace("Z", "+00:00")
                            ),
                            is_direct=msg.message_type == "direct",
                        )

                        self.message_queue.append(queue_item)

                        if self.verbose:
                            msg_type = "DM" if queue_item.is_direct else "room"
                            console.print(
                                f"[dim]Queued unread {msg_type} message from {msg.from_username}: {msg.content[:50]}...[/dim]"
                            )

                        # Mark message as read
                        if self.ws:
                            asyncio.create_task(self.ws.mark_message_read(msg.id))

                    self.stats.messages_received += len(all_unread)

        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to fetch unread messages: {e}[/yellow]"
            )
            if self.verbose:
                import traceback

                console.print(f"[dim]{traceback.format_exc()}[/dim]")

    async def _process_message_batch(self, messages: list[MessageQueueItem]) -> None:
        """Process a batch of queued messages with LangChain.

        Args:
            messages: List of messages to process
        """
        if not messages or not self.llm:
            return

        # Check if we're in cooldown
        if self._is_in_cooldown():
            remaining = self._get_cooldown_remaining()
            minutes = remaining // 60
            seconds = remaining % 60
            if self.verbose:
                console.print(
                    f"[dim yellow]In cooldown - {minutes}m {seconds}s remaining. Skipping message batch.[/dim yellow]"
                )
            return

        # Check if cooldown just ended
        if self.cooldown_start_time is not None and not self._is_in_cooldown():
            self._end_cooldown()

        # Filter out already-processed messages (deduplication)
        new_messages = [
            m for m in messages if m.message_id not in self.processed_message_ids
        ]

        if not new_messages:
            if self.verbose:
                console.print(
                    "[dim]Skipping batch - all messages already processed[/dim]"
                )
            return

        # Update attempt time for all messages in batch
        for message_item in new_messages:
            message_item.last_attempt_time = datetime.now(timezone.utc)

        if self.verbose:
            console.print(f"[dim]Processing {len(new_messages)} message(s)...[/dim]")

        try:
            # Combine messages into a single prompt
            message_text = "\n\n".join(
                [
                    f"{'[DM] ' if m.is_direct else ''}{m.from_username}: {m.content}"
                    for m in new_messages
                ]
            )

            prompt = f"{self.user_prompt}\n\nMessages:\n{message_text}"

            if self.verbose:
                console.print(f"[dim]Processing {len(messages)} message(s)...[/dim]")

            # Call LLM with token tracking
            with get_openai_callback() as cb:
                # Use agent executor if MCP is enabled, otherwise use direct LLM call
                if self.agent_executor:
                    # Use agent with tools
                    result = await self.agent_executor.ainvoke(
                        {
                            "input": prompt,
                            "chat_history": self.conversation_history,
                        }
                    )
                    response_text = result.get("output", "")

                    # Log tool calls if verbose
                    if self.verbose and "intermediate_steps" in result:
                        for step in result["intermediate_steps"]:
                            if len(step) >= 2:
                                action, observation = step
                                console.print(
                                    f"[dim]🔧 Tool: {action.tool} -> {str(observation)[:100]}...[/dim]"
                                )
                else:
                    # Direct LLM call without tools
                    llm_messages: list[dict[str, Any]] = [
                        {"role": "system", "content": self.system_prompt}
                    ]

                    # Add conversation history
                    for msg in self.conversation_history:
                        if isinstance(msg, HumanMessage):
                            llm_messages.append(
                                {"role": "user", "content": msg.content}
                            )
                        elif isinstance(msg, AIMessage):
                            llm_messages.append(
                                {"role": "assistant", "content": msg.content}
                            )

                    llm_messages.append({"role": "user", "content": prompt})

                    response = await self.llm.ainvoke(llm_messages)
                    response_text = str(response.content) if response.content else ""

                # Update token statistics
                self.stats.total_input_tokens += cb.prompt_tokens
                self.stats.total_output_tokens += cb.completion_tokens

            # Strip leading/trailing whitespace from response
            response_text = response_text.strip()

            # Skip sending if response is empty
            if not response_text:
                if self.verbose:
                    console.print(
                        "[yellow]Skipping send - LLM returned empty response[/yellow]"
                    )
                return

            # Check for repetitive responses
            if self._is_repetitive_response(response_text):
                console.print(
                    "[bold yellow]⚠️  Detected repetitive response - performing global reset[/bold yellow]"
                )
                await self._global_reset()
                # Do not send the repetitive message
                return

            # Update conversation history
            self.conversation_history.append(HumanMessage(content=prompt))
            self.conversation_history.append(AIMessage(content=response_text))

            # Trim conversation history based on context window
            self._trim_conversation_history()

            if self.verbose:
                console.print(
                    f"[dim]LLM response ({cb.total_tokens} tokens): {response_text[:100]}...[/dim]"
                )

            # Send response once (not once per message!)
            try:
                # Determine send target:
                # - If any messages are DMs, reply as DM to the most recent sender
                # - Otherwise, send to room
                dm_messages = [m for m in new_messages if m.is_direct]
                to_username = dm_messages[-1].from_username if dm_messages else None

                if self.ws:
                    # Track sent message content before sending
                    # (so we can identify the echo in _on_message)
                    self.sent_message_contents.append(response_text)

                    # Send message (Note: WebSocket send_message returns None,
                    # message ID tracking happens when server echoes back in _on_message)
                    await self.ws.send_message(response_text, to_username=to_username)

                    self.stats.messages_sent += 1

                    msg_type = f"DM to {to_username}" if to_username else "room"
                    console.print(
                        f"[green]→ Sent {msg_type} response: {response_text[:100]}...[/green]"
                    )

                    # Cooldown mechanism: Track messages and start cooldown after 3 messages
                    self.messages_sent_in_window += 1
                    if self.messages_sent_in_window >= self.messages_per_window:
                        self._start_cooldown()

                    # SUCCESS: Mark messages as processed only after successful send
                    for message_item in new_messages:
                        self.processed_message_ids.append(message_item.message_id)

                    if self.verbose:
                        console.print(
                            f"[dim]✓ Successfully processed and sent response for {len(new_messages)} message(s)[/dim]"
                        )

            except Exception as e:
                self.stats.errors += 1
                error_msg = str(e)
                console.print(f"[red]Error sending response: {error_msg}[/red]")

                # Add messages to failed queue for retry
                for message_item in new_messages:
                    message_item.last_error = f"Send error: {error_msg}"
                    self.failed_messages.append(message_item)

                if self.verbose:
                    console.print(
                        f"[yellow]Added {len(new_messages)} message(s) to retry queue[/yellow]"
                    )

        except Exception as e:
            self.stats.errors += 1
            error_msg = str(e)
            console.print(f"[red]Error processing messages: {error_msg}[/red]")

            # Add messages to failed queue for retry
            for message_item in new_messages:
                message_item.last_error = f"Processing error: {error_msg}"
                self.failed_messages.append(message_item)

            if self.verbose:
                console.print(
                    f"[yellow]Added {len(new_messages)} message(s) to retry queue[/yellow]"
                )

    async def _message_processor_loop(self) -> None:
        """Background loop to process queued messages."""
        while self.is_running:
            try:
                await asyncio.sleep(1)  # Check every second

                # Check failed messages and requeue those ready for retry
                self._requeue_failed_messages()

                # Check if it's time to flush
                time_since_last_flush = (
                    datetime.now(timezone.utc) - self.last_flush_time
                ).total_seconds()

                if time_since_last_flush >= self.queue_interval and self.message_queue:
                    async with self.processing_lock:
                        # Collect all queued messages
                        messages_to_process = list(self.message_queue)
                        self.message_queue.clear()

                        if messages_to_process:
                            await self._process_message_batch(messages_to_process)

                        self.last_flush_time = datetime.now(timezone.utc)

            except Exception as e:
                self.stats.errors += 1
                if self.verbose:
                    console.print(f"[red]Error in processor loop: {e}[/red]")

    async def _stats_display_loop(self) -> None:
        """Background loop to display statistics periodically."""
        while self.is_running:
            await asyncio.sleep(60)  # Update every minute

            # Build cooldown status line
            if self._is_in_cooldown():
                remaining = self._get_cooldown_remaining()
                minutes = remaining // 60
                seconds = remaining % 60
                cooldown_status = (
                    f"[yellow]In cooldown ({minutes}m {seconds}s remaining)[/yellow]"
                )
            else:
                cooldown_status = f"{self.messages_sent_in_window}/{self.messages_per_window} messages"

            # Build retry status line
            retry_status = f"{self.stats.retries} retries"
            if self.failed_messages:
                retry_status += f", {len(self.failed_messages)} pending"
            if self.stats.messages_failed_permanently > 0:
                retry_status += (
                    f", {self.stats.messages_failed_permanently} failed permanently"
                )

            console.print(
                f"\n[bold cyan]📊 Agent Statistics[/bold cyan]\n"
                f"  Uptime: {self.stats.uptime()}\n"
                f"  Messages: {self.stats.messages_received} received, {self.stats.messages_sent} sent\n"
                f"  Tokens: {self.stats.total_input_tokens} in, {self.stats.total_output_tokens} out\n"
                f"  Reconnections: {self.stats.reconnections}\n"
                f"  Errors: {self.stats.errors} ({retry_status})\n"
                f"  Cooldown: {cooldown_status}\n"
            )

    async def _websocket_loop_with_reconnect(self) -> None:
        """WebSocket receive loop with automatic reconnection on disconnect."""
        while self.is_running:
            try:
                if not self.ws:
                    console.print(
                        "[yellow]WebSocket not connected, attempting to connect...[/yellow]"
                    )
                    if not await self._connect_websocket():
                        # Failed to connect, wait before retry
                        delay = await self._calculate_backoff_delay()
                        await asyncio.sleep(delay)
                        continue

                # Wait for the receive task to complete (happens when connection closes)
                # The WebSocket client automatically starts _receive_loop() in connect()
                assert self.ws is not None  # Type narrowing for mypy
                if self.ws._receive_task:
                    await self.ws._receive_task

                # If we get here, the connection was closed gracefully
                if self.is_running:
                    console.print(
                        "[yellow]WebSocket connection closed, reconnecting...[/yellow]"
                    )
                    self.ws = None
                    await self._reconnect_websocket()

            except Exception as e:
                if self.is_running:
                    self.stats.errors += 1
                    console.print(f"[red]WebSocket error: {e}. Reconnecting...[/red]")

                    # Clean up current connection
                    if self.ws:
                        with contextlib.suppress(Exception):
                            await self.ws.disconnect()
                        self.ws = None

                    # Wait before reconnecting
                    await self._reconnect_websocket()

    async def run(self) -> None:
        """Run the agent main loop."""
        if not self.api_key:
            raise ValueError(
                "Token Bowl Chat API key required. Set TOKEN_BOWL_CHAT_API_KEY or pass api_key"
            )

        console.print("[bold cyan]🤖 Token Bowl Chat Agent Starting...[/bold cyan]")

        # Initialize LLM and MCP
        await self._initialize_llm()

        # Mark as running
        self.is_running = True

        try:
            # Connect to WebSocket
            if not await self._connect_websocket():
                console.print(
                    f"[bold red]Failed to connect to {self.server_url}[/bold red]"
                )
                return

            console.print(
                f"\n[bold green]✓ Agent running![/bold green]\n"
                f"  Model: {self.model_name}\n"
                f"  Queue interval: {self.queue_interval}s\n"
                f"  Max reconnect delay: {self.max_reconnect_delay}s\n"
            )

            # Note: Skipping unread message fetch to avoid polluting context with old messages
            # Agent will only respond to new messages received after startup

            # Start background tasks
            if not self.ws:
                console.print("[bold red]WebSocket not initialized[/bold red]")
                return

            tasks = [
                asyncio.create_task(self._websocket_loop_with_reconnect()),
                asyncio.create_task(self._message_processor_loop()),
                asyncio.create_task(self._stats_display_loop()),
            ]

            # Wait for tasks (they run indefinitely until cancelled)
            await asyncio.gather(*tasks, return_exceptions=True)

        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down agent...[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Fatal error: {e}[/bold red]")
        finally:
            self.is_running = False

            # Disconnect WebSocket
            if self.ws:
                await self.ws.disconnect()

            # Final stats
            # Build cooldown status line for final output
            if self._is_in_cooldown():
                remaining = self._get_cooldown_remaining()
                minutes = remaining // 60
                seconds = remaining % 60
                cooldown_status = (
                    f"[yellow]In cooldown ({minutes}m {seconds}s remaining)[/yellow]"
                )
            else:
                cooldown_status = f"{self.messages_sent_in_window}/{self.messages_per_window} messages"

            # Build final retry status line
            retry_status = f"{self.stats.retries} retries"
            if self.failed_messages:
                retry_status += f", {len(self.failed_messages)} pending"
            if self.stats.messages_failed_permanently > 0:
                retry_status += (
                    f", {self.stats.messages_failed_permanently} failed permanently"
                )

            console.print(
                f"\n[bold cyan]📊 Final Statistics[/bold cyan]\n"
                f"  Total uptime: {self.stats.uptime()}\n"
                f"  Messages: {self.stats.messages_received} received, {self.stats.messages_sent} sent\n"
                f"  Tokens: {self.stats.total_input_tokens} in, {self.stats.total_output_tokens} out\n"
                f"  Reconnections: {self.stats.reconnections}\n"
                f"  Errors: {self.stats.errors} ({retry_status})\n"
                f"  Cooldown: {cooldown_status}\n"
            )
