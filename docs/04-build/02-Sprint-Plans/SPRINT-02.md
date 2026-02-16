# Sprint 02: Provider & Channel Tests

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: PLANNED
**Authority**: PM/PJM
**Stage**: 04 - BUILD
**Duration**: 2026-03-03 - 2026-03-14 (10 days)
**Phase**: Phase 1 - Quality Foundation
**Team**: Core Team

---

## Sprint Goal

Expand test coverage to provider and channel subsystems and establish CI/CD pipeline to reach 60%+ overall coverage.

---

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| Sprint Number | 02 |
| Duration | 10 days |
| Start Date | 2026-03-03 |
| End Date | 2026-03-14 |
| Capacity | M (medium) — test writing + CI/CD setup |
| Team Size | Core team |

---

## G-Sprint Gate Checklist (Pre-Execution)

- [ ] Sprint goal aligns with Phase 1 objective (Quality Foundation)
- [ ] Priorities explicit: P0 = provider/channel tests, P1 = CI/CD, P2 = coverage enforcement
- [ ] Team capacity assessed: test-heavy sprint, feasible
- [ ] External dependencies identified: GitHub Actions quota (available)
- [ ] Top 3 risks identified (see Risks section below)
- [ ] This SPRINT-02.md created and reviewed

**G-Sprint Status**: PENDING | **Approved by**: TBD

---

## Sprint Context (from Sprint 01)

| Metric | Sprint 01 Close | Sprint 02 Target |
|--------|----------------|-----------------|
| Test Coverage | 33% (124 tests) | >= 60% |
| Core Module Coverage | loop 75%, context 87%, memory 100%, bus 98% | Maintain |
| Provider/Channel Coverage | ~0% (only email channel tested) | >= 50% on key files |
| Lint Errors | 759 (pre-existing upstream) | 759 or fewer |

---

## Committed Work

### Provider Tests (P0)

| ID | Task | Size | Assignee | Status |
|----|------|------|----------|--------|
| TT-012 | Write unit tests for Provider Registry (registry.py, 375 LOC) | L | Dev | To Do |
| TT-013 | Write unit tests for LiteLLM Provider (litellm_provider.py, 209 LOC) | M | Dev | To Do |
| TT-014 | Write unit tests for Provider base classes (base.py, 74 LOC) | S | Dev | To Do |

### Channel Tests (P0)

| ID | Task | Size | Assignee | Status |
|----|------|------|----------|--------|
| TT-015 | Write unit tests for ChannelManager (manager.py, 231 LOC) | L | Dev | To Do |
| TT-016 | Write unit tests for BaseChannel interface (base.py, 131 LOC) | M | Dev | To Do |
| TT-017 | Write unit tests for Telegram channel (telegram.py, 379 LOC) | M | Dev | To Do |
| TT-018 | Write unit tests for Discord channel (discord.py, 265 LOC) | M | Dev | To Do |
| TT-019 | Write unit tests for Slack channel (slack.py, 209 LOC) | M | Dev | To Do |

### CI/CD Pipeline (P1)

| ID | Task | Size | Assignee | Status |
|----|------|------|----------|--------|
| TT-020 | Create GitHub Actions CI workflow (lint + test + coverage) | M | Dev | To Do |
| TT-021 | Configure coverage reporting and enforcement (60% gate) | S | Dev | To Do |

### Stretch Goals (P2)

| ID | Task | Size | Assignee | Status |
|----|------|------|----------|--------|
| TT-022 | Write unit tests for Transcription provider (transcription.py, 69 LOC) | S | Dev | To Do |
| TT-023 | Write unit tests for remaining channels (WhatsApp, Feishu, DingTalk) | L | Dev | To Do |

---

## Dependencies

| Dependency | Type | Source | Status |
|------------|------|--------|--------|
| Sprint 01 test infrastructure (pytest + pytest-asyncio) | Internal | Sprint 01 | Resolved |
| GitHub Actions quota | External | GitHub | Available |
| LiteLLM library (for mocking) | Internal | pyproject.toml | Resolved |
| python-telegram-bot, discord.py, slack_sdk (for mocking) | Internal | pyproject.toml | Resolved |

---

## Risks & Blockers

| Risk/Blocker | Impact | Mitigation | Owner | Status |
|--------------|--------|------------|-------|--------|
| LiteLLM makes unit testing complex (carried from Sprint 01) | M | Create thin wrapper, mock at LiteLLM boundary | Dev | Open |
| Channel implementations depend on external APIs/webhooks | H | Mock all external HTTP calls, test message parsing logic only | Dev | Open |
| CI/CD pipeline may need iteration to stabilize | M | Start simple (lint + test), add gates incrementally | Dev | Open |

---

## Definition of Done

Sprint items are considered DONE when:

- [ ] Code reviewed (1+ reviewer for STANDARD tier)
- [ ] Tests passing (pytest green)
- [ ] Ruff lint clean (no new errors)
- [ ] Documentation updated
- [ ] Coverage does not regress

---

## Sprint Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Completion Rate | 90%+ | TBD |
| Test Coverage | 60% | TBD |
| Lint Errors | 759 or fewer | TBD |
| CI/CD Pipeline | Green | TBD |

---

## G-Sprint-Close Checklist (Post-Completion)

- [ ] All committed work done OR explicitly carried over
- [ ] Definition of Done met for completed items
- [ ] Sprint retro completed
- [ ] Velocity/metrics calculated
- [ ] Documentation updated within 24h
- [ ] SPRINT-INDEX.md updated
- [ ] CURRENT-SPRINT.md updated

**G-Sprint-Close Status**: PENDING

---

## Carry Over (if any)

| ID | Task | Reason | Target Sprint |
|----|------|--------|---------------|
| — | — | — | — |

---

**Document Status**: Planned
**Last Updated**: 2026-02-16
