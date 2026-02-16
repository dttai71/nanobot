# ADR-003: Message Bus Decoupling Pattern

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACCEPTED
**Authority**: CTO, Core Team
**Stage**: 02 - DESIGN
**Sprint**: Sprint 01 - Governance & Core Tests

## Context

Nanobot supports 9 chat channels (Telegram, Discord, Slack, WhatsApp, Feishu, DingTalk, Email, QQ, Mochat). Each channel has different APIs, message formats, and authentication. The agent processing logic must be independent of channel specifics.

## Decision

Implement an **event-driven message bus** (`nanobot/bus/`) with:
- `InboundMessage`: Normalized message from any channel (channel, sender_id, chat_id, content, media, metadata)
- `OutboundMessage`: Normalized response to any channel
- `MessageQueue`: Async queue connecting channels to AgentLoop

## Rationale

- **Decoupling**: Channels only know how to convert platform-specific messages to/from InboundMessage/OutboundMessage
- **Single agent loop**: One AgentLoop processes all channels uniformly
- **Extensibility**: New channel = implement BaseChannel.start/stop/send, no agent changes
- **Testability**: Agent can be tested with synthetic messages without real channels

## Consequences

- **Positive**: Clean separation of concerns; adding a channel is ~100-200 LOC
- **Negative**: Metadata field is untyped dict (channel-specific data leaks through)
- **Mitigation**: Future typed metadata per channel if needed

## References

- `nanobot/bus/events.py` — InboundMessage, OutboundMessage definitions
- `nanobot/bus/queue.py` — MessageQueue implementation
- `nanobot/channels/base.py` — BaseChannel abstract interface
