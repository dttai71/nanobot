# Contributing to Nanobot

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACTIVE
**Authority**: PM/PJM
**Stage**: 08 - COLLABORATE
**Sprint**: Sprint 01 - Governance & Core Tests

---

Thank you for your interest in contributing to nanobot!

## SDLC Governance

This project follows **SDLC 6.0.5 STANDARD tier** governance. Key requirements for contributions:

- **Code review**: All PRs require 1+ reviewer approval
- **Tests**: New code must include tests (target: >= 60% coverage)
- **Lint**: `ruff check nanobot/` must pass with zero errors
- **PR template**: Fill out the MRP checklist in the PR template

## Development Setup

```bash
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
pip install -e ".[dev]"
```

## Development Workflow

1. Create a branch from `main`
2. Make your changes
3. Run tests: `pytest tests/`
4. Run lint: `ruff check nanobot/`
5. Submit a PR using the PR template

## Architecture Reference

Before making significant changes, review the Architecture Decision Records in [docs/02-design/](docs/02-design/):

- [ADR-001](docs/02-design/ADR-001-agent-architecture.md) — Agent-first monolithic architecture
- [ADR-002](docs/02-design/ADR-002-litellm-multi-provider.md) — LiteLLM multi-provider strategy
- [ADR-003](docs/02-design/ADR-003-message-bus-pattern.md) — Message bus decoupling pattern
- [ADR-004](docs/02-design/ADR-004-tool-registry-pattern.md) — Tool registry pattern
- [ADR-005](docs/02-design/ADR-005-memory-two-layer.md) — Two-layer memory system

## Adding a New LLM Provider

Only 2 steps required:
1. Add a `ProviderSpec` entry to `PROVIDERS` in `nanobot/providers/registry.py`
2. Add a config field to `ProvidersConfig` in `nanobot/config/schema.py`

## Adding a New Tool

1. Create a class extending `Tool` in `nanobot/agent/tools/`
2. Implement: `name`, `description`, `parameters`, `execute()`
3. Register in `AgentLoop._register_default_tools()`

## Adding a New Channel

1. Create a class extending `BaseChannel` in `nanobot/channels/`
2. Implement: `start()`, `stop()`, `send()`
3. Add config to `nanobot/config/schema.py`
4. Register in `nanobot/channels/manager.py`
