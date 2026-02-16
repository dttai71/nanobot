# ADR-002: LiteLLM Multi-Provider Strategy

**Version**: 1.0.0
**Date**: February 16, 2026
**Status**: ACCEPTED
**Authority**: CTO, Core Team
**Stage**: 02 - DESIGN
**Sprint**: Sprint 01 - Governance & Core Tests

## Context

Nanobot needs to support 13+ LLM providers (OpenRouter, Anthropic, OpenAI, DeepSeek, Groq, Gemini, etc.) without provider-specific code for each.

## Decision

Use **LiteLLM** as the single abstraction layer for all LLM calls, combined with a **Provider Registry** pattern (`nanobot/providers/registry.py`).

Adding a new provider requires only 2 steps:
1. Add a `ProviderSpec` entry to the `PROVIDERS` tuple in `registry.py`
2. Add a config field to `ProvidersConfig` in `config/schema.py`

## Rationale

- **Zero provider-specific code**: LiteLLM handles API differences, auth, streaming
- **2-step extension**: Adding a provider is a data change, not a code change
- **Gateway support**: OpenRouter/AiHubMix can route to multiple models through one key
- **Per-model overrides**: Temperature, max_tokens configurable per model

## Consequences

- **Positive**: 13 providers with ~200 LOC total in registry; easy community contributions
- **Negative**: LiteLLM is a heavy dependency; version compatibility requires monitoring
- **Mitigation**: Thin wrapper in `litellm_provider.py` isolates LiteLLM API surface

## References

- `nanobot/providers/registry.py` — Provider registry with ProviderSpec
- `nanobot/providers/litellm_provider.py` — LiteLLM wrapper
- `nanobot/config/schema.py` — ProvidersConfig
