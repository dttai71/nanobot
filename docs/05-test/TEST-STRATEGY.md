# Test Strategy — Nanobot

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACTIVE
**Authority**: PM/PJM
**Stage**: 05 - TEST
**Tier**: STANDARD
**Sprint**: Sprint 01 - Governance & Core Tests

---

## Test Framework

- **Unit tests**: pytest + pytest-asyncio (asyncio_mode=auto)
- **Linting**: Ruff (line-length 100, Python 3.11, rules E/F/I/N/W)
- **Coverage**: pytest-cov (target: >= 60% for STANDARD tier)

## Coverage Targets

| Module | Priority | Target | Current |
|--------|----------|--------|---------|
| agent/loop.py | P0 | 60% | ~0% |
| bus/ | P0 | 80% | ~0% |
| agent/context.py | P1 | 60% | ~0% |
| agent/memory.py | P1 | 60% | ~0% |
| agent/tools/ | P1 | 50% | ~30% |
| providers/ | P1 | 50% | ~0% |
| config/ | P2 | 50% | ~20% |
| channels/ | P2 | 40% | ~10% |
| session/ | P2 | 50% | ~30% |

**Overall target**: >= 60% (STANDARD tier requirement)

## Test Categories

### Unit Tests (tests/)
- Tool parameter validation
- Config loading and schema validation
- Session consolidation logic
- CLI input handling
- Channel message parsing

### Integration Tests (planned)
- Agent loop with mock LLM responses
- Channel → MessageBus → AgentLoop flow
- Memory read/write/consolidation cycle
- Tool execution with workspace isolation

## Testing Principles

1. **Real implementations preferred**: Use Docker Compose for real services when feasible
2. **Mock only external services**: LLM API calls, third-party channel APIs
3. **Async-native**: All tests use pytest-asyncio auto mode
4. **Fast feedback**: Pre-commit runs fast unit tests only; CI runs full suite

## Running Tests

```bash
pytest tests/                           # All tests
pytest tests/test_tool_validation.py    # Single file
pytest -k "test_name"                   # Single test
pytest --cov=nanobot tests/             # With coverage
```
