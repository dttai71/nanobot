# Design Decisions Index

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACTIVE
**Authority**: PM/PJM
**Stage**: 09 - GOVERN
**Framework**: SDLC 6.0.5
**Sprint**: Sprint 01 - Governance & Core Tests

---

## Architecture Decision Records

| ADR | Title | Status | Date | Location |
|-----|-------|--------|------|----------|
| ADR-001 | Agent-First Monolithic Architecture | Accepted | 2026-02-16 | [docs/02-design/](../02-design/ADR-001-agent-architecture.md) |
| ADR-002 | LiteLLM Multi-Provider Strategy | Accepted | 2026-02-16 | [docs/02-design/](../02-design/ADR-002-litellm-multi-provider.md) |
| ADR-003 | Message Bus Decoupling Pattern | Accepted | 2026-02-16 | [docs/02-design/](../02-design/ADR-003-message-bus-pattern.md) |
| ADR-004 | Tool Registry with JSON Schema Validation | Accepted | 2026-02-16 | [docs/02-design/](../02-design/ADR-004-tool-registry-pattern.md) |
| ADR-005 | Two-Layer Memory System | Accepted | 2026-02-16 | [docs/02-design/](../02-design/ADR-005-memory-two-layer.md) |

---

## Sprint-Scoped Decisions

Lightweight decisions made within sprints (not requiring full ADR):

| Sprint | Decision | Rationale | Author |
|--------|----------|-----------|--------|
| Sprint 01 | Adopt SDLC 6.0.5 STANDARD tier | AI/ML exception requires Stage 09, team size fits STANDARD | PM/PJM + CTO |
| Sprint 01 | Use Ruff for linting (not pylint) | Already configured in pyproject.toml, faster execution | CTO |
| Sprint 01 | AGENTS.md at project root (not workspace/) | SDLC 6.0.5 SASE standard: project-root for development context | PM/PJM |
