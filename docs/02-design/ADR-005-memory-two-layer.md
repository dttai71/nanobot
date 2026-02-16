# ADR-005: Two-Layer Memory System

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACCEPTED
**Authority**: CTO, Core Team
**Stage**: 02 - DESIGN
**Sprint**: Sprint 01 - Governance & Core Tests

## Context

An AI assistant needs persistent memory across conversations. The memory system must be lightweight, human-readable, and LLM-cache-friendly.

## Decision

Implement a **two-layer memory system** (`nanobot/agent/memory.py`):

1. **MEMORY.md**: Long-term facts (user preferences, relationships, context). Structured markdown, overwritten on consolidation.
2. **HISTORY.md**: Append-only event log. Grep-searchable for recalling past events. Never modified, only appended.

Both stored as plain markdown files in the workspace.

## Rationale

- **Simplicity**: Plain files, no database dependency
- **Human-readable**: Users can read/edit their own memory files
- **LLM cache efficiency**: Append-only HISTORY.md maximizes cache hits (prior tokens unchanged)
- **Separation of concerns**: Facts (MEMORY.md) vs timeline (HISTORY.md)

## Consequences

- **Positive**: Zero infrastructure, portable, transparent to users
- **Negative**: HISTORY.md grows unbounded; grep search is O(n); no concurrent access safety
- **Mitigation**: Consolidation process summarizes HISTORY.md periodically; consider SQLite for high-volume use (backlog item)

## References

- `nanobot/agent/memory.py` — Memory system implementation
- `workspace/memory/MEMORY.md` — Default memory file
- `nanobot/agent/context.py` — Memory integration into LLM context
