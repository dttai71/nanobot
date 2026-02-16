# Nanobot Product Roadmap

**Version**: 1.0.0
**Status**: Active
**Owner**: PM/PJM (under CTO direction)
**Last Updated**: 2026-02-16

---

## Vision Statement

Nanobot is an ultra-lightweight personal AI assistant framework that delivers full agent capabilities in ~4,000 lines of code. We aim to make it production-ready, secure, and research-friendly — the simplest path from "pip install" to a working AI assistant.

---

## Strategic Goals (6 months)

| Goal | Description | Success Metric | Target |
|------|-------------|----------------|--------|
| G1 | Production Readiness | Test coverage, CI/CD, zero P0 bugs | >= 60% coverage, CI green |
| G2 | Security Hardening | SAST clean, sandbox options | Zero critical findings |
| G3 | Developer Experience | Onboard time, docs quality | < 5 min onboard, AGENTS.md compliant |

---

## Phase Breakdown

| Phase | Name | Duration | Quarter | Status |
|-------|------|----------|---------|--------|
| Phase 1 | Quality Foundation | 4 weeks (Feb 17 - Mar 14) | Q1 | Active |
| Phase 2 | Security & Stability | 4 weeks (Mar 17 - Apr 11) | Q1-Q2 | Planned |
| Phase 3 | Growth & Polish | 6 weeks (Apr 14 - May 23) | Q2 | Planned |

> See [Phase Plans](../04-build/) for details

---

## Quality Gates

| Gate | Name | Target Date | Criteria |
|------|------|-------------|----------|
| G0.2 | Solution Diversity | Passed | Architecture validated (3,663 LOC vs 430K+ alternatives) |
| G2 | Design Ready | 2026-02-28 | 5 ADRs approved, AGENTS.md compliant |
| G3 | Ship Ready | 2026-03-14 | 60%+ coverage, CI/CD green, lint clean |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Core modules tightly coupled | Medium | High | Dependency injection, incremental refactoring |
| LiteLLM breaking changes | Low | High | Pin version, thin wrapper isolation |
| Low test coverage causing regressions | High | High | Phase 1 priority: test coverage sprint |

---

## Change Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-02-16 | 1.0.0 | Initial roadmap creation | PM/PJM |

---

**Document Status**: Active
**Review Cadence**: Monthly
**Next Review**: 2026-03-16
