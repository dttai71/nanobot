# AGENTS.md

## Quick Start
- `pip install -e ".[dev]"` — Install for development
- `pytest tests/` — Run tests
- `ruff check nanobot/` — Lint
- `nanobot onboard` — First-time setup
- `nanobot agent -m "Hello"` — Single message

## Architecture
Monolithic async Python agent framework. Core flow:
Channel → MessageBus → AgentLoop → LLM (via LiteLLM) → Tools → Response → Channel

Key modules: `agent/loop.py` (core), `bus/` (events), `providers/` (LLM registry),
`channels/` (9 platforms), `agent/tools/` (tool registry), `agent/memory.py` (2-layer),
`config/schema.py` (Pydantic, snake_case↔camelCase), `session/` (JSONL history)

## Conventions
- Python 3.11+, fully async (async/await throughout)
- snake_case everywhere, type hints with Pydantic models
- Ruff: line-length 100, rules E/F/I/N/W, E501 ignored
- Config: `~/.nanobot/config.json` (camelCase JSON)
- New LLM provider: add ProviderSpec to `providers/registry.py` + field in `config/schema.py`
- New tool: subclass `Tool` in `agent/tools/`, implement execute(), register in AgentLoop
- New channel: subclass `BaseChannel`, implement start/stop/send

## Security
- NEVER commit API keys or secrets
- Shell exec blocks dangerous patterns (rm -rf /, fork bombs)
- File ops have path traversal protection
- restrict_to_workspace option for production isolation

## DO NOT
- Add TODO/placeholder code — implement fully or skip
- Skip error handling on tool execution
- Hardcode provider-specific logic outside registry
- Push to main without review
