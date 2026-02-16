"""
Unit tests for Provider Registry (registry.py).

Stage: 05 - TEST
Sprint: Sprint 02 - TT-012
"""

import pytest

from nanobot.providers.registry import (
    PROVIDERS,
    ProviderSpec,
    find_by_model,
    find_by_name,
    find_gateway,
)


class TestProviderSpec:
    """Tests for the ProviderSpec dataclass."""

    def test_label_with_display_name(self):
        spec = ProviderSpec(
            name="test", keywords=("test",), env_key="TEST_KEY",
            display_name="My Provider"
        )
        assert spec.label == "My Provider"

    def test_label_without_display_name(self):
        spec = ProviderSpec(
            name="testprov", keywords=("test",), env_key="TEST_KEY"
        )
        assert spec.label == "Testprov"

    def test_frozen(self):
        spec = ProviderSpec(name="test", keywords=("test",), env_key="TEST_KEY")
        with pytest.raises(AttributeError):
            spec.name = "changed"

    def test_defaults(self):
        spec = ProviderSpec(name="x", keywords=(), env_key="X_KEY")
        assert spec.litellm_prefix == ""
        assert spec.skip_prefixes == ()
        assert spec.env_extras == ()
        assert spec.is_gateway is False
        assert spec.is_local is False
        assert spec.detect_by_key_prefix == ""
        assert spec.detect_by_base_keyword == ""
        assert spec.default_api_base == ""
        assert spec.strip_model_prefix is False
        assert spec.model_overrides == ()


class TestProvidersRegistry:
    """Tests for the PROVIDERS tuple itself."""

    def test_providers_is_tuple(self):
        assert isinstance(PROVIDERS, tuple)

    def test_providers_not_empty(self):
        assert len(PROVIDERS) > 0

    def test_all_entries_are_provider_specs(self):
        for spec in PROVIDERS:
            assert isinstance(spec, ProviderSpec)

    def test_known_providers_exist(self):
        names = {s.name for s in PROVIDERS}
        for expected in ("anthropic", "openai", "deepseek", "gemini", "openrouter"):
            assert expected in names, f"Expected provider '{expected}' in registry"

    def test_unique_names(self):
        names = [s.name for s in PROVIDERS]
        assert len(names) == len(set(names)), "Provider names must be unique"

    def test_gateways_first(self):
        """Gateways should appear before standard providers (order = priority)."""
        gateway_indices = [i for i, s in enumerate(PROVIDERS) if s.is_gateway]
        standard_indices = [i for i, s in enumerate(PROVIDERS)
                           if not s.is_gateway and not s.is_local]
        if gateway_indices and standard_indices:
            assert max(gateway_indices) < min(standard_indices), \
                "Gateways should be ordered before standard providers"


class TestFindByModel:
    """Tests for find_by_model()."""

    def test_anthropic_by_claude(self):
        spec = find_by_model("claude-sonnet-4-5")
        assert spec is not None
        assert spec.name == "anthropic"

    def test_openai_by_gpt(self):
        spec = find_by_model("gpt-4o")
        assert spec is not None
        assert spec.name == "openai"

    def test_deepseek_model(self):
        spec = find_by_model("deepseek-chat")
        assert spec is not None
        assert spec.name == "deepseek"

    def test_gemini_model(self):
        spec = find_by_model("gemini-pro")
        assert spec is not None
        assert spec.name == "gemini"

    def test_dashscope_qwen(self):
        spec = find_by_model("qwen-max")
        assert spec is not None
        assert spec.name == "dashscope"

    def test_moonshot_kimi(self):
        spec = find_by_model("kimi-k2.5")
        assert spec is not None
        assert spec.name == "moonshot"

    def test_unknown_model_returns_none(self):
        assert find_by_model("unknown-model-xyz") is None

    def test_case_insensitive(self):
        spec = find_by_model("CLAUDE-3-OPUS")
        assert spec is not None
        assert spec.name == "anthropic"

    def test_skips_gateways(self):
        """find_by_model should not match gateway providers."""
        spec = find_by_model("openrouter")
        # openrouter has keyword "openrouter" but is_gateway=True → skipped
        assert spec is None or not spec.is_gateway

    def test_skips_local(self):
        """find_by_model should not match local providers."""
        spec = find_by_model("vllm")
        assert spec is None or not spec.is_local


class TestFindByName:
    """Tests for find_by_name()."""

    def test_find_anthropic(self):
        spec = find_by_name("anthropic")
        assert spec is not None
        assert spec.name == "anthropic"

    def test_find_openrouter(self):
        spec = find_by_name("openrouter")
        assert spec is not None
        assert spec.is_gateway is True

    def test_find_vllm(self):
        spec = find_by_name("vllm")
        assert spec is not None
        assert spec.is_local is True

    def test_not_found(self):
        assert find_by_name("nonexistent") is None

    def test_all_providers_findable(self):
        for spec in PROVIDERS:
            found = find_by_name(spec.name)
            assert found is not None
            assert found.name == spec.name


class TestFindGateway:
    """Tests for find_gateway()."""

    def test_by_provider_name_openrouter(self):
        spec = find_gateway(provider_name="openrouter")
        assert spec is not None
        assert spec.name == "openrouter"

    def test_by_provider_name_vllm(self):
        spec = find_gateway(provider_name="vllm")
        assert spec is not None
        assert spec.name == "vllm"

    def test_by_api_key_prefix_openrouter(self):
        spec = find_gateway(api_key="sk-or-abc123")
        assert spec is not None
        assert spec.name == "openrouter"

    def test_by_api_base_keyword_aihubmix(self):
        spec = find_gateway(api_base="https://aihubmix.com/v1")
        assert spec is not None
        assert spec.name == "aihubmix"

    def test_by_api_base_keyword_openrouter(self):
        spec = find_gateway(api_base="https://openrouter.ai/api/v1")
        assert spec is not None
        assert spec.name == "openrouter"

    def test_standard_provider_not_gateway(self):
        """Standard providers should not be returned by find_gateway."""
        spec = find_gateway(provider_name="anthropic")
        assert spec is None

    def test_no_match_returns_none(self):
        spec = find_gateway(provider_name="nonexistent", api_key="random-key")
        assert spec is None

    def test_provider_name_takes_priority(self):
        """provider_name should take priority over api_key auto-detection."""
        spec = find_gateway(provider_name="openrouter", api_key="sk-or-abc")
        assert spec is not None
        assert spec.name == "openrouter"

    def test_custom_gateway(self):
        spec = find_gateway(provider_name="custom")
        assert spec is not None
        assert spec.name == "custom"
        assert spec.is_gateway is True
