# ADR-001: Agent-First Monolithic Architecture

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACCEPTED
**Authority**: CTO, Core Team
**Stage**: 02 - DESIGN
**Sprint**: Sprint 01 - Governance & Core Tests

## Context

Nanobot needed an architecture that delivers full agent capabilities (tool use, memory, multi-channel, multi-provider) while maintaining an ultra-lightweight footprint (~4,000 LOC target).

## Decision

Adopt a **message-bus-centric monolithic architecture** where:

1. **AgentLoop** (`nanobot/agent/loop.py`) is the central processing engine
2. **MessageBus** (`nanobot/bus/`) decouples channels from agent processing via InboundMessage/OutboundMessage events
3. All components run in a single async Python process
4. Core flow: Channel -> MessageBus -> AgentLoop -> LLM -> Tool Execution -> Response -> Channel

## Rationale

- **Simplicity**: Single process, no microservice overhead, no message broker dependency
- **Research-friendly**: Entire codebase readable in one session (~3,663 core LOC)
- **Performance**: No network hop between components, shared memory
- **Deployment**: Single pip install, single Docker container

## Consequences

- **Positive**: Ultra-fast startup, minimal resource usage, easy to understand and extend
- **Negative**: AgentLoop accumulates responsibilities (477 LOC, approaching god-class threshold); vertical scaling only
- **Mitigation**: Extract sub-components (MemoryConsolidator, MCPManager) when complexity grows

## References

- `nanobot/agent/loop.py` — AgentLoop implementation
- `nanobot/bus/queue.py` — MessageBus implementation
- `nanobot/bus/events.py` — Message types
