# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nanobot is an ultra-lightweight personal AI assistant framework (~3,600 core agent lines). Python 3.11+, MIT licensed.

## Common Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run tests
pytest tests/
pytest tests/test_tool_validation.py        # single file
pytest tests/test_tool_validation.py -k "test_name"  # single test

# Lint
ruff check nanobot/
ruff check --fix nanobot/

# Run the assistant
nanobot onboard                  # first-time setup
nanobot agent -m "Hello"         # single message
nanobot gateway                  # start multi-channel gateway
```

## Architecture

### Core Flow
Messages flow through: **Channel → Message Bus → Agent Loop → LLM → Tool Execution → Response → Channel**

- **Agent Loop** (`nanobot/agent/loop.py`): Main processing loop — receives messages from the bus, builds context (history + memory + skills), calls LLM via LiteLLM, executes tool calls, sends responses back. Max 20 iterations per turn.
- **Message Bus** (`nanobot/bus/`): Event-driven routing with `InboundMessage`/`OutboundMessage` that decouples channels from agent processing.
- **Context Builder** (`nanobot/agent/context.py`): Assembles the system prompt from memory, skills, and conversation history.

### Key Subsystems

- **Tools** (`nanobot/agent/tools/`): Abstract `Tool` base class with JSON Schema validation. Built-in: file ops (read/write/edit/list-dir), shell exec, web search/fetch, messaging, spawn (subagents), cron, MCP integration. Register new tools in `AgentLoop._register_default_tools()`.
- **Providers** (`nanobot/providers/registry.py`): LLM provider registry using LiteLLM. To add a provider: (1) add `ProviderSpec` to `PROVIDERS` tuple in registry.py, (2) add field to `ProvidersConfig` in `config/schema.py`.
- **Channels** (`nanobot/channels/`): Abstract `BaseChannel` with implementations for Telegram, Discord, Slack, WhatsApp, Feishu, DingTalk, Email, QQ, Mochat. Each implements `start()`, `stop()`, `send()`.
- **Config** (`nanobot/config/schema.py`): Pydantic-based, stored at `~/.nanobot/config.json`. Snake_case Python ↔ camelCase JSON automatic conversion.
- **Memory** (`nanobot/agent/memory.py`): Two-layer — `MEMORY.md` (long-term facts) and `HISTORY.md` (grep-searchable log). Append-only for LLM cache efficiency.
- **Skills** (`nanobot/agent/skills.py`): Markdown files (`SKILL.md`) that teach the agent capabilities. Sources: workspace-local + built-in (`nanobot/skills/`). Progressive loading: always-loaded in full, available skills as summary only.
- **Sessions** (`nanobot/session/manager.py`): Conversation history as JSONL files, keyed by `{channel}:{chat_id}`.
- **Subagents** (`nanobot/agent/subagent.py`): Background task execution with isolated context and result announcement.
- **CLI** (`nanobot/cli/commands.py`): Typer-based. Commands: `onboard`, `agent`, `gateway`, `status`, `channels login`, `cron add/list/remove`.

### Conventions

- Fully async (`async`/`await`) throughout the codebase.
- Ruff for linting: line-length 100, target Python 3.11, rules E/F/I/N/W, E501 ignored.
- `pytest-asyncio` with `asyncio_mode = "auto"` — async test functions are auto-detected.
- Config uses Pydantic models with `alias_generator` for snake_case ↔ camelCase mapping.
