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
from token_bowl_chat.websocket_client import TokenBowlWebSocket

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


@dataclass
class MessageQueueItem:
    """A message in the processing queue."""

    message_id: str
    content: str
    from_username: str
    to_username: str | None
    timestamp: datetime
    is_direct: bool


@dataclass
class AgentStats:
    """Statistics for the agent."""

    messages_received: int = 0
    messages_sent: int = 0
    errors: int = 0
    reconnections: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def uptime(self) -> str:
        """Get uptime as a formatted string."""
        delta = datetime.now(timezone.utc) - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"


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
        queue_interval: float = 15.0,
        max_reconnect_delay: float = 300.0,
        context_window: int = 128000,
        mcp_enabled: bool = True,
        mcp_server_url: str = "https://tokenbowl-mcp.haihai.ai/sse",
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
            queue_interval: Seconds to wait before flushing message queue
            max_reconnect_delay: Maximum delay between reconnection attempts (seconds)
            context_window: Maximum context window in tokens (default: 128000)
            mcp_enabled: Enable MCP (Model Context Protocol) tools (default: True)
            mcp_server_url: MCP server URL (default: https://tokenbowl-mcp.haihai.ai/sse)
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
        self.context_window = context_window
        self.mcp_enabled = mcp_enabled and MCP_AVAILABLE
        self.mcp_server_url = mcp_server_url
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
        self.message_queue: deque[MessageQueueItem] = deque(maxlen=MAX_MESSAGE_QUEUE_SIZE)
        self.processing_lock = asyncio.Lock()
        self.last_flush_time = datetime.now(timezone.utc)

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
        self.sent_messages: OrderedDict[str, str] = OrderedDict()  # message_id -> content (populated on echo)
        self.sent_message_contents: deque[str] = deque(
            maxlen=100
        )  # Recently sent content

        # Token counting - use tiktoken if available for accuracy
        self.token_encoder: Any = None
        if TIKTOKEN_AVAILABLE:
            try:
                # Try to get encoding for the specific model, fall back to cl100k_base
                # cl100k_base is used by GPT-4, GPT-3.5-turbo, and text-embedding-ada-002
                self.token_encoder = tiktoken.get_encoding("cl100k_base")
            except Exception:
                # If that fails, tiktoken is available but we can't get the encoding
                pass

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
        """Trim conversation history to fit within context window.

        Removes oldest messages first while keeping the conversation coherent.
        Reserves space for system prompt, user prompt, and current messages.
        """
        if not self.conversation_history:
            return

        # Reserve tokens for system/user prompts and current batch
        reserved_tokens = (
            self._estimate_tokens(self.system_prompt)
            + self._estimate_tokens(self.user_prompt)
            + 2000  # Reserve for current message batch
        )

        # Calculate available tokens for history
        available_tokens = self.context_window - reserved_tokens

        # Calculate current history token count
        total_tokens = sum(
            self._estimate_tokens(str(msg.content)) for msg in self.conversation_history
        )

        # Remove oldest messages until we fit in context window
        while total_tokens > available_tokens and self.conversation_history:
            # Remove oldest message (first in list)
            removed_msg = self.conversation_history.pop(0)
            total_tokens -= self._estimate_tokens(str(removed_msg.content))

            if self.verbose:
                msg_type = "User" if isinstance(removed_msg, HumanMessage) else "AI"
                console.print(
                    f"[dim]Trimmed {msg_type} message from history (context window management)[/dim]"
                )

    def _cleanup_sent_messages(self) -> None:
        """Limit sent_messages dict size to prevent unbounded memory growth.

        Removes oldest entries when limit is exceeded.
        This prevents memory leaks in long-running agents.
        """
        while len(self.sent_messages) > MAX_SENT_MESSAGES_TRACKED:
            # Remove oldest entry (first item in OrderedDict)
            self.sent_messages.popitem(last=False)

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
                        # Skip if we've already sent this message
                        if msg.id in self.sent_messages:
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

        try:
            # Combine messages into a single prompt
            message_text = "\n\n".join(
                [
                    f"{'[DM] ' if m.is_direct else ''}{m.from_username}: {m.content}"
                    for m in messages
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

            # Update conversation history
            self.conversation_history.append(HumanMessage(content=prompt))
            self.conversation_history.append(AIMessage(content=response_text))

            # Trim conversation history based on context window
            self._trim_conversation_history()

            if self.verbose:
                console.print(
                    f"[dim]LLM response ({cb.total_tokens} tokens): {response_text[:100]}...[/dim]"
                )

            # Skip sending if response is empty
            if not response_text:
                if self.verbose:
                    console.print(
                        "[yellow]Skipping send - LLM returned empty response[/yellow]"
                    )
                return

            # Send responses
            for msg_item in messages:
                try:
                    # Decide where to send: DMs get DM replies, room messages get room replies
                    to_username = msg_item.from_username if msg_item.is_direct else None

                    if self.ws:
                        # Send typing indicator
                        await self.ws.send_typing_indicator(to_username=to_username)
                        await asyncio.sleep(0.5)

                        # Track sent message content before sending
                        # (so we can identify the echo in _on_message)
                        self.sent_message_contents.append(response_text)

                        # Send message (Note: WebSocket send_message returns None,
                        # message ID tracking happens when server echoes back in _on_message)
                        await self.ws.send_message(
                            response_text, to_username=to_username
                        )

                        self.stats.messages_sent += 1

                        msg_type = f"DM to {to_username}" if to_username else "room"
                        console.print(
                            f"[green]→ Sent {msg_type} response: {response_text[:100]}...[/green]"
                        )

                except Exception as e:
                    self.stats.errors += 1
                    console.print(f"[red]Error sending response: {e}[/red]")

        except Exception as e:
            self.stats.errors += 1
            console.print(f"[red]Error processing messages: {e}[/red]")

    async def _message_processor_loop(self) -> None:
        """Background loop to process queued messages."""
        while self.is_running:
            try:
                await asyncio.sleep(1)  # Check every second

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

            console.print(
                f"\n[bold cyan]📊 Agent Statistics[/bold cyan]\n"
                f"  Uptime: {self.stats.uptime()}\n"
                f"  Messages: {self.stats.messages_received} received, {self.stats.messages_sent} sent\n"
                f"  Tokens: {self.stats.total_input_tokens} in, {self.stats.total_output_tokens} out\n"
                f"  Reconnections: {self.stats.reconnections}\n"
                f"  Errors: {self.stats.errors}\n"
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

            # Fetch unread messages from before connection
            await self._fetch_unread_messages()

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
            console.print(
                f"\n[bold cyan]📊 Final Statistics[/bold cyan]\n"
                f"  Total uptime: {self.stats.uptime()}\n"
                f"  Messages: {self.stats.messages_received} received, {self.stats.messages_sent} sent\n"
                f"  Tokens: {self.stats.total_input_tokens} in, {self.stats.total_output_tokens} out\n"
                f"  Reconnections: {self.stats.reconnections}\n"
                f"  Errors: {self.stats.errors}\n"
            )
