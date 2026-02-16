# Phase 1: Quality Foundation

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACTIVE
**Authority**: PM/PJM
**Stage**: 04 - BUILD
**Duration**: 2026-02-17 - 2026-03-14 (4 weeks)
**Sprint**: Sprint 01 - Governance & Core Tests

---

## Phase Overview

### Theme
Build the safety net before we run — establish governance, testing, and quality infrastructure.

### Objectives
1. Reach 60%+ test coverage on core modules
2. Establish CI/CD pipeline with quality gates
3. Set up SDLC 6.0.5 governance artifacts and documentation structure

### Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Test coverage | >= 60% | pytest --cov report |
| Lint compliance | 0 errors | ruff check nanobot/ |
| SDLC docs complete | All Stage-mapped /docs | ls -R docs/ |
| Sprint governance | G-Sprint + G-Sprint-Close operational | Checklist completion |

---

## Roadmap Alignment

| Roadmap Item | Phase Contribution |
|--------------|-------------------|
| G1: Production Readiness | Core test coverage + CI/CD pipeline |
| G3: Developer Experience | AGENTS.md, CONTRIBUTING.md, ADRs |
| G2 gate: Design Ready | 5 ADRs approved by end of Phase 1 |

---

## Sprint Breakdown

| Sprint | Name | Duration | Focus | Status |
|--------|------|----------|-------|--------|
| Sprint 01 | Governance & Core Tests | 10 days (Feb 17-28) | SDLC setup + AgentLoop/Bus tests | Active |
| Sprint 02 | Provider & Channel Tests | 10 days (Mar 3-14) | Provider/Channel tests + CI/CD | Planned |

### Sprint 01: Governance & Core Tests
**Duration**: Feb 17 - Feb 28, 2026
**Focus**: Establish SDLC governance foundation and achieve 40% test coverage on core modules

Key Deliverables:
- [x] /docs folder structure with stage mapping
- [x] 5 foundation ADRs
- [x] AGENTS.md (< 60 lines, SDLC compliant)
- [x] Unit tests for AgentLoop, MessageBus, ContextBuilder, MemoryStore
- [x] .github/ governance files (PR template, issue templates, CODEOWNERS)
- [x] Pre-commit hooks configuration
- [x] CONTRIBUTING.md with SDLC tier reference

### Sprint 02: Provider & Channel Tests
**Duration**: Mar 3 - Mar 14, 2026
**Focus**: Expand test coverage to providers and channels, establish CI/CD

Key Deliverables:
- [ ] Unit tests for Provider Registry, LiteLLM wrapper
- [ ] Unit tests for Channel Manager, BaseChannel implementations
- [ ] GitHub Actions CI/CD pipeline
- [ ] Coverage reporting and enforcement

---

## Dependencies

### External Dependencies

| Dependency | Owner | Due Date | Status |
|------------|-------|----------|--------|
| GitHub Actions quota | GitHub | Ongoing | Available |
| PyPI publishing access | Core Team | Available | Resolved |

---

## Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Core modules hard to test in isolation | High | High | Dependency injection, mock external services only | Dev team |
| LiteLLM makes unit testing complex | Medium | Medium | Thin wrapper for testability | Dev team |
| Documentation overhead slows development | Low | Medium | Templates + AI assistance for doc generation | PM/PJM |

---

## Quality Gates

| Gate | Date | Criteria | Status |
|------|------|----------|--------|
| Phase Start | Feb 17 | SDLC tier classified, roadmap approved | Passed |
| Mid-Phase Review | Mar 1 | Sprint 01 complete, 40%+ coverage | In Progress (33%) |
| Phase Complete (G3) | Mar 14 | 60%+ coverage, CI/CD green, docs complete | Pending |

---

## Metrics

| Metric | Target | Actual | Trend |
|--------|--------|--------|-------|
| Test coverage | 60% | 33% | Up |
| Lint errors | 0 | 759 (pre-existing upstream) | -- |
| ADRs documented | 5 | 5 | -- |

---

**Document Status**: Active
**Last Updated**: 2026-02-16
**Next Review**: 2026-03-01
