# Tier Classification — Nanobot

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACTIVE
**Authority**: CTO
**Stage**: 09 - GOVERN
**Framework**: SDLC 6.0.5
**Sprint**: Sprint 01 - Governance & Core Tests

---

## Classification

**Tier**: STANDARD

## Rationale

| Factor | Value | Implication |
|--------|-------|-------------|
| Team size | 22+ contributors (3 core) | STANDARD (3-10 active) |
| Project type | AI/ML framework with shell execution | Requires Stage 09 (GOVERN) per AI/ML exception |
| User data handling | Manages conversations, memory files, API keys | Elevated governance needed |
| Distribution | PyPI (public), Docker | Production-grade release process |
| Risk profile | Shell command execution, file system access | Security governance required |

## Required Stages

| Stage | Name | Required | Rationale |
|-------|------|----------|-----------|
| 00 | FOUNDATION | Yes | Business case, vision |
| 01 | PLANNING | Yes | Requirements, roadmap |
| 02 | DESIGN | Yes | Architecture decisions (ADRs) |
| 03 | INTEGRATE | Yes | 13 LLM providers, 9 channels, MCP |
| 04 | BUILD | Yes | Core development |
| 05 | TEST | Yes | Quality assurance |
| 06 | DEPLOY | Yes | Docker, PyPI releases |
| 09 | GOVERN | Yes | AI/ML exception — compliance, audit |

## Quality Targets

| Metric | Target | Current |
|--------|--------|---------|
| Unit test coverage | >= 60% | ~15% |
| Code review | 1+ reviewer per PR | Informal |
| Linting | PASS (Ruff) | Configured, not enforced |
| Deployment frequency | Weekly-Monthly | Post-release pattern |
| Lead time | 1-4 weeks | Variable |
| MTTR | < 1 week | Unknown |

## Sprint Governance

| Aspect | STANDARD Requirement |
|--------|---------------------|
| G-Sprint approval | Tech Lead |
| G-Sprint-Close | Tech Lead |
| Weekly review | Bi-weekly (recommended) |
| Documentation | SPRINT-XX.md + CURRENT-SPRINT.md |
