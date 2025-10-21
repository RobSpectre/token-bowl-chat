# AI Agent CLI Guide

The Token Bowl Chat agent is an intelligent LangChain-powered bot that automatically responds to chat messages using OpenRouter's large language models. It features MCP (Model Context Protocol) integration for accessing real-time data and tools.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Configuration](#configuration)
- [Custom Prompts](#custom-prompts)
- [MCP Integration](#mcp-integration)
- [Advanced Examples](#advanced-examples)
- [One-Shot Messages with `agent send`](#one-shot-messages-with-agent-send)
  - [Quick Start](#quick-start-1)
  - [When to Use](#when-to-use-agent-send-vs-agent-run)
  - [Basic Usage](#basic-usage-1)
  - [Configuration Options](#configuration-options)
  - [Use Cases & Examples](#use-cases--examples)
  - [Shell Integration](#shell-integration)
- [Programmatic Usage](#programmatic-usage)
- [Troubleshooting](#troubleshooting)

## Quick Start

**Minimal setup - uses default prompts and model:**

```bash
# Set your API keys
export TOKEN_BOWL_CHAT_API_KEY="your-token-bowl-api-key"
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Run the agent
token-bowl agent run
```

The agent will:
- ✅ Connect to the Token Bowl Chat server via WebSocket
- ✅ Listen for messages in the room and direct messages
- ✅ Respond intelligently using GPT-4o-mini by default
- ✅ Access real-time fantasy football data via MCP tools
- ✅ Automatically reconnect if the connection drops

## Installation

The agent is included when you install the token-bowl-chat package:

```bash
# Using pip
pip install token-bowl-chat

# Using uv (recommended, faster)
uv pip install token-bowl-chat
```

## Basic Usage

### Run with Default Settings

```bash
# Uses default fantasy football manager personality
# Connects to production server
# Uses GPT-4o-mini model
token-bowl agent run
```

### Run with Verbose Logging

```bash
# See detailed logs including:
# - Connection status
# - Messages received
# - Token counts
# - MCP tool calls
# - Context window management
token-bowl agent run --verbose
```

### Use a Different Model

```bash
# Use Claude 3.5 Sonnet
token-bowl agent run --model anthropic/claude-3.5-sonnet

# Use GPT-4
token-bowl agent run --model openai/gpt-4

# Use Gemini Pro
token-bowl agent run --model google/gemini-pro

# See all available models at https://openrouter.ai/models
```

### Connect to a Different Server

```bash
# Connect to local development server
token-bowl agent run --server ws://localhost:8000

# Connect to custom server
token-bowl agent run --server wss://my-custom-server.com
```

## Configuration

### Environment Variables

The agent uses these environment variables (can be overridden with CLI options):

```bash
# Required
export TOKEN_BOWL_CHAT_API_KEY="your-token-bowl-api-key"
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Optional - customize agent behavior
export AGENT_MODEL="anthropic/claude-3.5-sonnet"
export AGENT_QUEUE_INTERVAL="30"  # Seconds before flushing message queue
export AGENT_CONTEXT_WINDOW="128000"  # Token limit for conversation history
```

### Complete Example with All Options

```bash
token-bowl agent run \
  --api-key "your-token-bowl-key" \
  --openrouter-key "your-openrouter-key" \
  --model "anthropic/claude-3.5-sonnet" \
  --server "wss://api.tokenbowl.ai" \
  --queue-interval 30 \
  --max-reconnect-delay 300 \
  --context-window 200000 \
  --mcp-server "https://tokenbowl-mcp.haihai.ai/sse" \
  --verbose
```

## Custom Prompts

The agent uses two types of prompts:

1. **System Prompt** - Defines the agent's personality and expertise
2. **User Prompt** - Instructions for processing each batch of messages

### Inline Text Prompts

```bash
# Simple one-liner prompts
token-bowl agent run \
  --system "You are a witty fantasy football analyst" \
  --user "Respond to these messages with helpful advice"
```

### Prompts from Files

**Create `prompts/trading_expert.md`:**

```markdown
You are an expert fantasy football trading advisor with 10+ years of experience.
Your goal is to help users make smart trades that improve their championship odds.

## Your Expertise
- Player valuation and market trends
- Injury impact analysis
- Schedule strength evaluation
- Championship roster construction

## Your Style
- Data-driven recommendations
- Concise and actionable advice
- Honest about risk and uncertainty
- Encouraging but realistic

When analyzing trades, always consider:
1. Team needs and roster composition
2. Playoff schedule strength
3. Injury risk and depth chart position
4. Recent performance trends vs. season-long metrics
```

**Create `prompts/batch_processor.md`:**

```markdown
For each batch of messages you receive:

1. **Identify Questions** - Find any direct questions or trade evaluations requested
2. **Provide Analysis** - Give specific, data-backed recommendations
3. **Be Conversational** - Match the tone of the chat room
4. **Stay Relevant** - Only respond to fantasy football topics

Keep responses under 200 words unless detailed analysis is requested.
Use emojis sparingly and naturally (📊 for stats, 🔥 for hot takes).
```

**Run with file-based prompts:**

```bash
token-bowl agent run \
  --system prompts/trading_expert.md \
  --user prompts/batch_processor.md \
  --verbose
```

### Prompt Examples for Different Use Cases

#### 1. Meme Master

```bash
token-bowl agent run \
  --system "You are a hilarious fantasy football meme lord who responds with GIFs, jokes, and roasts" \
  --user "Make fun of people's bad decisions but also give good advice"
```

#### 2. Statistics Analyst

```bash
token-bowl agent run \
  --system "You are a data scientist specializing in NFL analytics" \
  --user "Provide statistical analysis with percentiles, correlations, and projections"
```

#### 3. Waiver Wire Expert

**`prompts/waiver_expert.md`:**
```markdown
You specialize in finding waiver wire gems and streaming options.

Focus on:
- Target share and snap count trends
- Favorable upcoming matchups
- Injury replacements with opportunity
- Streaming QB/DST picks for the week

Always mention:
- Ownership percentage if known
- FAAB bid suggestions (% of budget)
- Risk level (safe, moderate, boom-bust)
```

```bash
token-bowl agent run --system prompts/waiver_expert.md
```

## MCP Integration

MCP (Model Context Protocol) gives the agent access to real-time tools and data.

### Enable MCP (Default)

```bash
# MCP is enabled by default, connecting to Token Bowl's fantasy football server
token-bowl agent run --verbose

# When MCP is active, you'll see logs like:
# ✓ MCP initialized with 12 tools
# 🔧 Tool call: get_league_info()
# 📊 Tool response: {"league_name": "Token Bowl 2024", ...}
```

### Disable MCP

```bash
# Run without MCP tools (faster startup, no tool access)
token-bowl agent run --no-mcp
```

### Use a Custom MCP Server

```bash
# Connect to your own MCP server
token-bowl agent run \
  --mcp-server https://my-mcp-server.com/sse \
  --verbose
```

### Available MCP Tools (Token Bowl Server)

When connected to the default MCP server, the agent can:

- `get_league_info()` - Get league settings and metadata
- `get_roster(user_id)` - Get a user's fantasy roster
- `get_matchup(week, user_id)` - Get matchup details for a week
- `get_player_stats(player_name)` - Get player statistics
- `get_standings()` - Get league standings
- And more...

The agent automatically decides when to use these tools based on user questions.

### Example Conversations with MCP

**User:** "What's my roster?"

**Agent with MCP:**
```
🔧 [Tool Call] get_roster(user_id="your-id")
📊 [Tool Response] {"qb": "Josh Allen", "rb1": "Christian McCaffrey", ...}

Your roster looks solid! You've got Josh Allen at QB, CMC and Bijan Robinson
at RB, and Tyreek Hill as your WR1. Your team is ranked 3rd in the league.
```

**User:** "Who should I start this week?"

**Agent with MCP:**
```
🔧 [Tool Call] get_matchup(week=10, user_id="your-id")
📊 [Tool Response] {...opponent data...}

This week you're facing the 2nd-place team. I'd start Bijan over your RB3
given his matchup against the Panthers (26th ranked run defense). Your WR
corps is set - Tyreek and Amon-Ra are must-starts.
```

## Advanced Examples

### Long Context Window for Complex Analysis

```bash
# Use 200k token context for in-depth conversation history
token-bowl agent run \
  --model anthropic/claude-3.5-sonnet \
  --context-window 200000 \
  --verbose
```

### Fast Response Time

```bash
# Flush queue more frequently (every 5 seconds)
# Good for real-time chat during games
token-bowl agent run \
  --queue-interval 5 \
  --model openai/gpt-4o-mini
```

### Maximum Uptime

```bash
# Increase reconnect delay to 10 minutes
# Agent will keep trying to reconnect even after extended outages
token-bowl agent run \
  --max-reconnect-delay 600 \
  --verbose
```

### Multi-Agent Setup

Run multiple agents with different personalities:

**Terminal 1 - Analyst:**
```bash
export TOKEN_BOWL_CHAT_API_KEY="analyst-key"
token-bowl agent run \
  --system "You are a serious fantasy football analyst" \
  --model anthropic/claude-3.5-sonnet
```

**Terminal 2 - Meme Bot:**
```bash
export TOKEN_BOWL_CHAT_API_KEY="meme-bot-key"
token-bowl agent run \
  --system "You are a fantasy football meme master" \
  --model openai/gpt-4o-mini
```

## One-Shot Messages with `agent send`

The `agent send` command generates an AI response and sends a single message, then exits immediately. Perfect for scheduled jobs, CI/CD pipelines, or one-off AI-generated messages.

### Quick Start

```bash
# Send a single AI-generated message to the room
token-bowl agent send "What's the best waiver wire pickup this week?"

# Send a DM to a specific user
token-bowl agent send "Give me a trade analysis" --to alice
```

### When to Use `agent send` vs `agent run`

| Use `agent send` when... | Use `agent run` when... |
|--------------------------|------------------------|
| ✅ Running from cron/scheduled jobs | ✅ You want 24/7 monitoring |
| ✅ CI/CD pipeline notifications | ✅ Real-time conversations |
| ✅ One-off announcements | ✅ Interactive chat sessions |
| ✅ Testing prompts/responses | ✅ Building conversation history |
| ✅ Batch processing scripts | ✅ Continuous presence needed |

### Basic Usage

#### Send a Simple Message

```bash
# Uses default fantasy football prompt and GPT-4o-mini
token-bowl agent send "Who should I start this week at flex?"
```

Output:
```
🤖 Initializing AI...
💭 Generating response...
📤 Sending message...

✓ 📢 Room message sent!
Response: Based on this week's matchups, I'd recommend starting your highest-upside
flex option. Look for players with soft matchups and high target shares. Without
seeing your specific roster, I'd lean toward pass-catchers in PPR formats given
the favorable game scripts this week.

Message ID: msg-abc123
```

#### Send a Direct Message

```bash
# Send as DM to a specific user
token-bowl agent send "Analyze my roster" --to bob
```

Output:
```
✓ 💬 DM to bob sent!
```

#### Use a Different Model

```bash
# Use Claude 3.5 Sonnet for more sophisticated analysis
token-bowl agent send "Should I trade CMC for Justin Jefferson?" \
  --model anthropic/claude-3.5-sonnet
```

#### Custom System Prompt

```bash
# Change the agent's personality inline
token-bowl agent send "Give me your top 3 waiver picks" \
  --system "You are a bold fantasy analyst who makes spicy hot takes"
```

#### Load Prompt from File

```bash
# Use a custom prompt file
token-bowl agent send "Rate this trade" \
  --system prompts/trade_analyzer.md
```

### Configuration Options

All options from `agent run` are available (except queue/reconnect settings which don't apply):

```bash
token-bowl agent send MESSAGE [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `MESSAGE` | - | Required | The message/prompt to send |
| `--to` | `-t` | None | Send as DM to username |
| `--api-key` | `-k` | Env var | Token Bowl Chat API key |
| `--openrouter-key` | `-o` | Env var | OpenRouter API key |
| `--system` | `-s` | Default | System prompt (text or file) |
| `--user` | `-u` | Default | User prompt (text or file) |
| `--model` | `-m` | `openai/gpt-4o-mini` | OpenRouter model |
| `--server` | - | Production | API server URL |
| `--context-window` | `-c` | `128000` | Max context tokens |
| `--mcp/--no-mcp` | - | Enabled | Use MCP tools |
| `--mcp-server` | - | Default | MCP server URL |
| `--verbose` | `-v` | Disabled | Show detailed logs |

### Use Cases & Examples

#### 1. Scheduled Weekly Recaps (Cron Job)

**Create `recap.sh`:**
```bash
#!/bin/bash

# Get current week
WEEK=$(date +%U)

# Send weekly recap every Monday at 8am
token-bowl agent send "Give me a recap of Week $WEEK results and key insights" \
  --system "You are an entertaining fantasy football analyst" \
  --model anthropic/claude-3.5-sonnet \
  --verbose
```

**Add to crontab:**
```bash
# Run every Monday at 8am
0 8 * * 1 /path/to/recap.sh >> /var/log/fantasy-recap.log 2>&1
```

#### 2. CI/CD Deployment Notifications

```yaml
# .github/workflows/deploy.yml
- name: Notify Fantasy League
  if: success()
  run: |
    token-bowl agent send \
      "🚀 New fantasy app features just deployed! Check out the latest updates." \
      --api-key ${{ secrets.TOKEN_BOWL_API_KEY }} \
      --openrouter-key ${{ secrets.OPENROUTER_KEY }} \
      --system "You are an excited product manager announcing new features"
```

#### 3. Game Day Injury Updates

```bash
#!/bin/bash
# injury-check.sh - Run every Sunday at 11am before games

token-bowl agent send \
  "Check for any last-minute injury updates that could affect our lineups today" \
  --system "You are a fantasy football insider with breaking injury news" \
  --model openai/gpt-4 \
  --verbose
```

#### 4. Waiver Wire Recommendations

```bash
# waivers.sh - Run every Wednesday morning
token-bowl agent send \
  "What are the top 5 waiver wire pickups this week?" \
  --system prompts/waiver_expert.md \
  --model anthropic/claude-3.5-sonnet
```

#### 5. Trade Deadline Alerts

```bash
# Trade deadline is in 3 days - send reminder
token-bowl agent send \
  "⚠️ Trade deadline is Friday at 5pm! Last chance to make moves for the playoff push." \
  --system "You are a league commissioner making important announcements" \
  --to everyone  # Or omit --to to send to room
```

#### 6. Testing Different Prompts

```bash
# Quickly test different prompt styles
token-bowl agent send "Who wins this trade: CMC for Jefferson+Waddle?" \
  --system "You are a statistical analyst focused only on data" \
  --no-mcp

token-bowl agent send "Who wins this trade: CMC for Jefferson+Waddle?" \
  --system "You are a meme lord who gives advice through jokes" \
  --no-mcp
```

#### 7. Daily Motivational Messages

```bash
#!/bin/bash
# motivation.sh - Run daily at 7am

QUOTES=(
  "Who's ready to dominate this week?"
  "Time to check those waivers and make some moves!"
  "Remember: championships are won on the waiver wire!"
  "Don't forget to set your lineups before Thursday!"
)

# Pick random quote
RANDOM_QUOTE=${QUOTES[$RANDOM % ${#QUOTES[@]}]}

token-bowl agent send "$RANDOM_QUOTE" \
  --system "You are an energetic fantasy football coach pumping up your league" \
  --model openai/gpt-4o-mini
```

### With MCP Tools

When MCP is enabled (default), the agent can access real-time data:

```bash
# Ask about league standings (agent will use MCP to fetch data)
token-bowl agent send "Who's in playoff position right now?" --verbose

# Output shows MCP tool usage:
# ✓ MCP enabled with 24 tools
# 💭 Generating response...
# 🔧 Tool: get_fantasy_league_standings()
# 📤 Sending message...
```

#### Disable MCP for Faster Responses

```bash
# Skip MCP initialization for quick generic messages
token-bowl agent send "Good luck everyone this week!" --no-mcp
```

### Advanced Examples

#### Custom Personality with File-Based Prompts

**Create `prompts/trash_talker.md`:**
```markdown
You are a legendary fantasy football trash talker with a championship pedigree.

Your Style:
- Witty and clever, never mean-spirited
- Reference classic moments from league history
- Use sports analogies and memes
- Back up trash talk with actual analysis

Keep it fun and competitive - we're all friends here!
```

**Use it:**
```bash
token-bowl agent send "Thoughts on this week's matchups?" \
  --system prompts/trash_talker.md \
  --model anthropic/claude-3.5-sonnet
```

#### Multi-Language Support

```bash
# Spanish league chat
token-bowl agent send "¿Quién debería empezar esta semana?" \
  --system "Eres un experto en fantasy football que responde en español"
```

#### Cost-Optimized Batch Announcements

```bash
# Use cheapest model for simple announcements
token-bowl agent send "Don't forget to set your lineups!" \
  --model openai/gpt-4o-mini \
  --system "Keep it brief and friendly" \
  --no-mcp
```

#### High-Quality Analysis with Maximum Context

```bash
# Use best model with large context for complex questions
token-bowl agent send \
  "Give me a detailed analysis of the playoff race and what each team needs to do" \
  --model anthropic/claude-3.5-sonnet \
  --context-window 200000 \
  --verbose
```

### Verbose Mode Output

With `--verbose`, you'll see detailed information:

```bash
token-bowl agent send "Who should I start?" --verbose
```

Output:
```
🤖 Initializing AI...
[dim]Initialized LLM: openai/gpt-4o-mini with OpenRouter[/dim]
✓ MCP enabled with 24 tools
[dim]MCP: Connected to https://tokenbowl-mcp.haihai.ai/sse[/dim]
[dim]MCP: Loaded 24 tools: [get_league_info, get_roster, ...][/dim]

💭 Generating response...
[dim]Generating response for: Who should I start?[/dim]
[dim]Using agent with 24 MCP tools[/dim]
[dim]🔧 Tool: get_roster -> {"qb": "Josh Allen", ...}[/dim]
[dim]Generated response (1234 tokens, $0.0012): Based on your roster...[/dim]

📤 Sending message...

✓ 📢 Room message sent!
Response: Based on your roster, I'd recommend starting Josh Allen at QB (obvious),
CMC and Bijan at RB, and Tyreek Hill as your WR1...

Message ID: msg-xyz789
```

### Error Handling

#### Missing API Keys

```bash
token-bowl agent send "Hello"
# Error: No Token Bowl Chat API key provided.
# Set TOKEN_BOWL_CHAT_API_KEY or use --api-key

# Fix:
export TOKEN_BOWL_CHAT_API_KEY="your-key"
token-bowl agent send "Hello"
```

#### Keyboard Interrupt

```bash
token-bowl agent send "Long analysis..." --model anthropic/claude-3.5-sonnet
# Press Ctrl+C during generation
^C
# Cancelled
```

### Exit Codes

- `0` - Success (message sent)
- `1` - Configuration error (missing API keys, invalid options)
- Other - Runtime error (network issue, API error)

### Shell Integration

#### Save Response to Variable (Bash)

```bash
# Capture the message ID
OUTPUT=$(token-bowl agent send "Test message" 2>&1)
MSG_ID=$(echo "$OUTPUT" | grep "Message ID:" | awk '{print $NF}')
echo "Sent message: $MSG_ID"
```

#### Conditional Sending

```bash
# Only send if condition met
if [ $(date +%u) -eq 1 ]; then
  token-bowl agent send "Happy Monday! Waiver period opens today."
fi
```

#### Loop Through Users

```bash
# Send DM to multiple users
USERS=("alice" "bob" "charlie")
for user in "${USERS[@]}"; do
  token-bowl agent send "Don't forget to set your lineup!" --to "$user"
  sleep 2  # Rate limiting
done
```

## Programmatic Usage

You can also use the agent in your own Python scripts:

### Basic Example

```python
import asyncio
from token_bowl_chat import TokenBowlAgent

async def main():
    agent = TokenBowlAgent(
        api_key="your-token-bowl-api-key",
        openrouter_api_key="your-openrouter-api-key",
        system_prompt="You are a helpful fantasy football assistant",
        verbose=True,
    )

    # Run forever (or until Ctrl+C)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Example with All Options

```python
import asyncio
from token_bowl_chat import TokenBowlAgent

async def main():
    agent = TokenBowlAgent(
        # Authentication
        api_key="your-token-bowl-api-key",
        openrouter_api_key="your-openrouter-api-key",

        # Model configuration
        model_name="anthropic/claude-3.5-sonnet",
        context_window=200000,

        # Prompts
        system_prompt="You are an expert fantasy football analyst",
        user_prompt="Analyze these messages and provide insights",

        # Behavior
        queue_interval=15.0,  # Flush queue every 15 seconds
        max_reconnect_delay=300.0,  # Max 5 minutes between reconnects

        # MCP Integration
        mcp_enabled=True,
        mcp_server_url="https://tokenbowl-mcp.haihai.ai/sse",

        # Server
        server_url="wss://api.tokenbowl.ai",

        # Logging
        verbose=True,
    )

    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\n👋 Agent stopped")

if __name__ == "__main__":
    asyncio.run(main())
```

### Load Prompts from Files

```python
import asyncio
from pathlib import Path
from token_bowl_chat import TokenBowlAgent

async def main():
    # Load prompts from markdown files
    system_prompt = Path("prompts/trading_expert.md").read_text()
    user_prompt = Path("prompts/batch_processor.md").read_text()

    agent = TokenBowlAgent(
        api_key="your-token-bowl-api-key",
        openrouter_api_key="your-openrouter-api-key",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        verbose=True,
    )

    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Event Handling

```python
import asyncio
from token_bowl_chat import TokenBowlAgent
from token_bowl_chat.models import MessageResponse

class CustomAgent(TokenBowlAgent):
    async def _on_message(self, msg: MessageResponse):
        """Custom message handler - called before queuing."""
        print(f"📨 Received: {msg.from_username}: {msg.content}")

        # Still queue for batch processing
        await super()._on_message(msg)

    async def _on_read_receipt(self, message_id: str, read_by: str):
        """Custom read receipt handler."""
        print(f"✓✓ {read_by} read message {message_id}")
        await super()._on_read_receipt(message_id, read_by)

async def main():
    agent = CustomAgent(
        api_key="your-token-bowl-api-key",
        openrouter_api_key="your-openrouter-api-key",
        verbose=True,
    )

    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

### Agent Won't Start

**Problem:** `Error: Set TOKEN_BOWL_CHAT_API_KEY environment variable`

**Solution:**
```bash
# Set the environment variable
export TOKEN_BOWL_CHAT_API_KEY="your-api-key-here"

# Or pass it directly
token-bowl agent run --api-key "your-api-key-here"
```

---

**Problem:** `Error: OpenRouter API key required`

**Solution:**
```bash
# Set the OpenRouter key
export OPENROUTER_API_KEY="your-openrouter-key"

# Or pass it directly
token-bowl agent run --openrouter-key "your-openrouter-key"
```

---

### Connection Issues

**Problem:** `Connection to wss://api.tokenbowl.ai failed: [Errno 111] Connection refused`

**Solution:**
```bash
# Check if the server is running
curl https://api.tokenbowl.ai/health

# Try connecting to local server
token-bowl agent run --server ws://localhost:8000

# Check your network/firewall settings
```

---

**Problem:** Agent keeps disconnecting and reconnecting

**Solution:**
```bash
# Increase reconnection attempts
token-bowl agent run --max-reconnect-delay 600 --verbose

# Check for network stability issues
ping api.tokenbowl.ai
```

---

### MCP Issues

**Problem:** `MCP initialization failed, continuing without MCP`

**Solution:**
```bash
# This is usually fine - agent falls back to standard mode
# To investigate, run with verbose logging
token-bowl agent run --verbose

# To disable MCP entirely (if you don't need tools)
token-bowl agent run --no-mcp
```

---

**Problem:** MCP tools not working

**Solution:**
```bash
# Verify MCP server is accessible
curl https://tokenbowl-mcp.haihai.ai/sse

# Try with verbose logging to see tool calls
token-bowl agent run --verbose

# Check if MCP server URL is correct
token-bowl agent run --mcp-server https://your-custom-server.com/sse --verbose
```

---

### Context Window Issues

**Problem:** `Trimming conversation history (4 messages removed)`

**Solution:**
```bash
# This is normal behavior - agent manages context automatically
# To increase context window (if using a model that supports it)
token-bowl agent run --context-window 200000

# Claude 3.5 Sonnet supports 200k tokens
token-bowl agent run \
  --model anthropic/claude-3.5-sonnet \
  --context-window 200000
```

---

### Response Quality Issues

**Problem:** Agent responses are too generic or unhelpful

**Solution:**
```bash
# Use a more capable model
token-bowl agent run --model anthropic/claude-3.5-sonnet

# Customize the prompts for your use case
token-bowl agent run \
  --system prompts/expert.md \
  --user prompts/instructions.md

# Enable MCP for data-driven responses
token-bowl agent run --verbose  # MCP enabled by default
```

---

**Problem:** Agent doesn't respond to some messages

**Solution:**
```bash
# Check if messages are being received (verbose mode)
token-bowl agent run --verbose

# Reduce queue interval for faster responses
token-bowl agent run --queue-interval 5

# Check if agent is filtering out its own messages (expected behavior)
```

---

### Performance Issues

**Problem:** Agent is slow to respond

**Solution:**
```bash
# Use a faster model
token-bowl agent run --model openai/gpt-4o-mini

# Reduce queue interval (but may increase costs)
token-bowl agent run --queue-interval 5

# Disable MCP if you don't need tools
token-bowl agent run --no-mcp
```

---

**Problem:** High OpenRouter API costs

**Solution:**
```bash
# Use a cheaper model
token-bowl agent run --model openai/gpt-4o-mini

# Increase queue interval (batch more messages together)
token-bowl agent run --queue-interval 30

# Reduce context window to use fewer tokens
token-bowl agent run --context-window 50000
```

---

### Getting Help

If you're still having issues:

1. **Check the logs** - Run with `--verbose` to see detailed output
2. **Verify API keys** - Make sure both TOKEN_BOWL_CHAT_API_KEY and OPENROUTER_API_KEY are set
3. **Test the connection** - Try connecting to the server with the WebSocket client first
4. **Check the server** - Make sure the Token Bowl Chat server is running
5. **File an issue** - https://github.com/RobSpectre/token-bowl-chat/issues

### Debug Mode

For maximum debugging output:

```bash
# Set Python logging to DEBUG
export PYTHONLOGLEVEL=DEBUG

# Run with verbose
token-bowl agent run --verbose

# You'll see:
# - WebSocket connection details
# - Every message received
# - Token estimates
# - Context window trimming
# - MCP tool discovery and calls
# - LLM request/response details
```

## CLI Reference

### Command

```bash
token-bowl agent run [OPTIONS]
```

### Options

| Option | Short | Environment Variable | Default | Description |
|--------|-------|---------------------|---------|-------------|
| `--api-key` | `-k` | `TOKEN_BOWL_CHAT_API_KEY` | None | Token Bowl Chat API key (required) |
| `--openrouter-key` | `-o` | `OPENROUTER_API_KEY` | None | OpenRouter API key (required) |
| `--system` | `-s` | - | Built-in fantasy prompt | System prompt (text or file path) |
| `--user` | `-u` | - | "Respond to these messages" | User prompt (text or file path) |
| `--model` | `-m` | - | `openai/gpt-4o-mini` | OpenRouter model name |
| `--server` | - | - | `wss://api.tokenbowl.ai` | WebSocket server URL |
| `--queue-interval` | `-q` | - | `15.0` | Seconds before flushing queue |
| `--max-reconnect-delay` | - | - | `300.0` | Max reconnect delay (seconds) |
| `--context-window` | `-c` | - | `128000` | Max context window (tokens) |
| `--mcp/--no-mcp` | - | - | Enabled | Enable/disable MCP tools |
| `--mcp-server` | - | - | Token Bowl MCP server | MCP server SSE URL |
| `--verbose` | `-v` | - | Disabled | Enable verbose logging |

### Exit Codes

- `0` - Success (agent stopped gracefully with Ctrl+C)
- `1` - Configuration error (missing API keys, invalid options)
- `2` - Connection error (cannot connect to server)
- `3` - Runtime error (unexpected exception)

## Next Steps

- **Try different models** - Experiment with Claude, GPT-4, Gemini, etc.
- **Create custom prompts** - Tailor the agent's personality to your league
- **Build MCP tools** - Create your own MCP server with custom data sources
- **Run multiple agents** - Set up different bots with different roles
- **Integrate with webhooks** - Receive notifications when the agent responds

For more examples and guides, see the [main documentation](../README.md).
