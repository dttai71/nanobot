# ADR-004: Tool Registry with JSON Schema Validation

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACCEPTED
**Authority**: CTO, Core Team
**Stage**: 02 - DESIGN
**Sprint**: Sprint 01 - Governance & Core Tests

## Context

Nanobot's agent needs extensible tool capabilities (file ops, shell exec, web search, messaging, cron, MCP) with consistent parameter validation and error handling.

## Decision

Implement a **Tool Registry** pattern with:
- Abstract `Tool` base class (`nanobot/agent/tools/base.py`) defining name, description, parameters (JSON Schema), execute()
- `ToolRegistry` (`nanobot/agent/tools/registry.py`) for dynamic registration and lookup
- JSON Schema validation on every tool call before execution
- MCP tool integration for external tool servers

## Rationale

- **Consistency**: All tools (built-in and MCP) share the same interface
- **Safety**: JSON Schema validation catches invalid parameters before execution
- **Extensibility**: New tool = subclass Tool, implement execute(), register
- **LLM compatibility**: JSON Schema parameters map directly to LLM function calling format

## Consequences

- **Positive**: Clean tool abstraction; detailed validation error messages help LLM self-correct
- **Negative**: Tool registration currently happens in AgentLoop._register_default_tools() — could be more declarative
- **Mitigation**: Consider auto-discovery or plugin system in future

## References

- `nanobot/agent/tools/base.py` — Tool abstract base class
- `nanobot/agent/tools/registry.py` — ToolRegistry
- `nanobot/agent/tools/shell.py` — ExecTool with dangerous pattern blocking
