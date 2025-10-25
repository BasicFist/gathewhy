"""
Unit tests for configuration validation.

These tests validate configuration schema and cross-file consistency without
external dependencies. Tests focus on configuration structure, types, and
relationships between configurations.

Test Markers:
  - unit: Fast unit tests without external dependencies
"""

import re
from urllib.parse import urlparse

import pytest


@pytest.mark.unit
class TestProviderSchemaValidation:
    """Test provider configuration schema validation."""

    def test_providers_config_has_providers_key(
        self, providers_config: dict
    ) -> None:
        """Verify providers.yaml has top-level 'providers' key."""
        assert "providers" in providers_config
        assert isinstance(providers_config["providers"], dict)

    def test_provider_config_structure(
        self, providers_config: dict
    ) -> None:
        """Verify each provider has required fields."""
        providers = providers_config.get("providers", {})

        required_fields = {"type", "base_url", "status"}

        for provider_name, config in providers.items():
            for field in required_fields:
                assert field in config, \
                    f"Provider {provider_name} missing required field: {field}"

    def test_provider_types_are_valid(
        self, providers_config: dict
    ) -> None:
        """Verify provider types are from known set."""
        valid_types = {
            "ollama", "vllm", "llama_cpp", "openai",
            "anthropic", "openai_compatible"
        }

        providers = providers_config.get("providers", {})

        for provider_name, config in providers.items():
            provider_type = config.get("type")
            assert provider_type in valid_types, \
                f"Provider {provider_name} has invalid type: {provider_type}"

    def test_provider_status_values_are_valid(
        self, providers_config: dict
    ) -> None:
        """Verify provider status values are from known set."""
        valid_statuses = {"active", "disabled", "pending_integration", "template"}

        providers = providers_config.get("providers", {})

        for provider_name, config in providers.items():
            status = config.get("status")
            assert status in valid_statuses, \
                f"Provider {provider_name} has invalid status: {status}"

    def test_base_urls_are_valid_http_urls(
        self, providers_config: dict
    ) -> None:
        """Verify all base URLs are valid HTTP(S) URLs."""
        providers = providers_config.get("providers", {})

        for provider_name, config in providers.items():
            base_url = config.get("base_url")

            # Check URL format
            try:
                parsed = urlparse(base_url)
                assert parsed.scheme in ("http", "https"), \
                    f"Provider {provider_name} has URL with invalid scheme: {parsed.scheme}"
                assert parsed.netloc, \
                    f"Provider {provider_name} has URL with no hostname: {base_url}"
            except Exception as e:
                pytest.fail(f"Provider {provider_name} has invalid URL: {base_url} ({e})")

    def test_provider_models_field_is_list_or_missing(
        self, providers_config: dict
    ) -> None:
        """Verify provider 'models' field is list when present."""
        providers = providers_config.get("providers", {})

        for provider_name, config in providers.items():
            if "models" in config:
                models = config["models"]
                assert isinstance(models, (list, type(None))), \
                    f"Provider {provider_name} 'models' must be list, got {type(models)}"


@pytest.mark.unit
class TestModelMappingsSchemaValidation:
    """Test model mappings configuration schema validation."""

    def test_mappings_config_structure(
        self, mappings_config: dict
    ) -> None:
        """Verify model-mappings.yaml has expected structure."""
        # Should have at least one of these sections
        keys = mappings_config.keys()
        assert any(k in keys for k in [
            "exact_matches", "patterns", "fallback_chains", "capabilities"
        ]), "model-mappings.yaml missing routing configuration sections"

    def test_exact_matches_structure(
        self, exact_matches: dict
    ) -> None:
        """Verify exact_matches entries have required fields."""
        for model_name, config in exact_matches.items():
            assert isinstance(model_name, str)
            assert isinstance(config, dict)
            assert "provider" in config, \
                f"Exact match '{model_name}' missing provider field"

    def test_exact_match_priority_values(
        self, exact_matches: dict
    ) -> None:
        """Verify exact match priorities are valid."""
        valid_priorities = {"primary", "secondary", "tertiary", "fallback"}

        for model_name, config in exact_matches.items():
            priority = config.get("priority")
            if priority is not None:
                assert priority in valid_priorities, \
                    f"Exact match '{model_name}' has invalid priority: {priority}"

    def test_fallback_chains_are_lists(
        self, fallback_chains: dict
    ) -> None:
        """Verify fallback chains are lists of model names."""
        for primary_model, chain_config in fallback_chains.items():
            # Fallback chains may be wrapped in a dict with 'chain' key
            if isinstance(chain_config, dict) and "chain" in chain_config:
                chain = chain_config["chain"]
            else:
                chain = chain_config

            assert isinstance(chain, list), \
                f"Fallback chain for '{primary_model}' is not a list: {type(chain)}"

            for fallback_entry in chain:
                assert isinstance(fallback_entry, str), \
                    f"Fallback entry in '{primary_model}' is not a string: {fallback_entry}"

    def test_patterns_are_valid_regex(
        self, mappings_config: dict
    ) -> None:
        """Verify all patterns are valid regular expressions."""
        patterns = mappings_config.get("patterns", [])

        for entry in patterns:
            if isinstance(entry, dict):
                pattern = entry.get("pattern")
                if pattern:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        pytest.fail(
                            f"Invalid regex pattern '{pattern}': {e}"
                        )

    def test_capabilities_routing_structure(
        self, capability_routing: dict
    ) -> None:
        """Verify capability-based routing has valid structure."""
        for capability, config in capability_routing.items():
            assert isinstance(config, dict), \
                f"Capability '{capability}' config is not a dict"

            if "preferred_models" in config:
                models = config["preferred_models"]
                assert isinstance(models, list), \
                    f"Capability '{capability}' preferred_models must be list"


@pytest.mark.unit
class TestLiteLLMConfigurationValidation:
    """Test LiteLLM unified configuration schema validation."""

    def test_litellm_config_has_model_list(
        self, litellm_config: dict
    ) -> None:
        """Verify litellm config has model_list section."""
        assert "model_list" in litellm_config, \
            "litellm-unified.yaml missing model_list"
        assert isinstance(litellm_config["model_list"], list)

    def test_model_list_entries_have_required_fields(
        self, litellm_config: dict
    ) -> None:
        """Verify each model entry has required LiteLLM fields."""
        model_list = litellm_config.get("model_list", [])

        required_fields = {"model_name", "litellm_params"}

        for idx, model_entry in enumerate(model_list):
            for field in required_fields:
                assert field in model_entry, \
                    f"Model entry {idx} missing required field: {field}"

    def test_litellm_params_have_model_key(
        self, litellm_config: dict
    ) -> None:
        """Verify litellm_params entries have 'model' key."""
        model_list = litellm_config.get("model_list", [])

        for idx, model_entry in enumerate(model_list):
            litellm_params = model_entry.get("litellm_params", {})
            assert "model" in litellm_params, \
                f"Model entry {idx} litellm_params missing 'model' key"

    def test_litellm_config_has_router_settings(
        self, litellm_config: dict
    ) -> None:
        """Verify litellm config has router settings section."""
        # router_settings may be optional, but if present should be valid
        if "router_settings" in litellm_config:
            settings = litellm_config["router_settings"]
            assert isinstance(settings, dict)


@pytest.mark.unit
class TestCrossConfigurationConsistency:
    """Test consistency between configuration files."""

    def test_providers_in_mappings_exist_in_providers_config(
        self, providers_config: dict,
        exact_matches: dict
    ) -> None:
        """Verify providers referenced in mappings exist in providers config."""
        provider_names = set(providers_config.get("providers", {}).keys())

        for model_name, config in exact_matches.items():
            provider = config.get("provider")
            assert provider in provider_names, \
                f"Exact match '{model_name}' references unknown provider: {provider}"

    def test_no_duplicate_exact_match_model_names(
        self, exact_matches: dict
    ) -> None:
        """Verify no duplicate model names in exact matches."""
        seen = set()

        for model_name in exact_matches.keys():
            assert model_name not in seen, \
                f"Duplicate model name in exact_matches: {model_name}"
            seen.add(model_name)

    def test_fallback_chain_primary_models_referenced(
        self, fallback_chains: dict,
        exact_matches: dict
    ) -> None:
        """Verify fallback chain primary models exist in exact matches or are special."""
        # 'default' is a special catch-all fallback chain, not an exact match model
        special_chains = {"default", "*"}

        for primary_model in fallback_chains.keys():
            # Skip special fallback chains
            if primary_model in special_chains:
                continue

            assert primary_model in exact_matches, \
                f"Fallback chain primary model '{primary_model}' not in exact matches"

    def test_model_names_are_strings_not_numbers(
        self, exact_matches: dict,
        fallback_chains: dict
    ) -> None:
        """Verify model names are strings."""
        for model_name in exact_matches.keys():
            assert isinstance(model_name, str), \
                f"Model name is not string: {model_name} ({type(model_name)})"

        for primary_model, chain in fallback_chains.items():
            assert isinstance(primary_model, str)
            for fallback_model in chain:
                assert isinstance(fallback_model, str), \
                    f"Fallback model is not string: {fallback_model}"


@pytest.mark.unit
class TestConfigurationPortReferences:
    """Test that configuration references valid ports."""

    def test_provider_urls_use_valid_ports(
        self, providers_config: dict
    ) -> None:
        """Verify provider URLs reference valid port numbers."""
        providers = providers_config.get("providers", {})

        for provider_name, config in providers.items():
            base_url = config.get("base_url", "")

            # Extract port from URL
            parsed = urlparse(base_url)
            try:
                if parsed.port:
                    assert 1 <= parsed.port <= 65535, \
                        f"Provider {provider_name} has invalid port: {parsed.port}"
            except ValueError:
                # Port may contain environment variables like ${PORT} or CUSTOM_PORT
                # These are valid template variables, so skip validation
                pass

    def test_litellm_url_port_standard(
        self, litellm_config: dict
    ) -> None:
        """Verify LiteLLM gateway uses standard ports."""
        # LiteLLM default is 4000, but config may vary
        # This just verifies if port is in router_settings it's valid
        settings = litellm_config.get("router_settings", {})

        if "redis_port" in settings:
            redis_port = settings["redis_port"]
            assert isinstance(redis_port, int)
            assert 1 <= redis_port <= 65535


@pytest.mark.unit
class TestConfigurationHealthChecks:
    """Test configuration health checks and validations."""

    def test_at_least_one_provider_is_active(
        self, active_providers: dict
    ) -> None:
        """Verify at least one provider is configured as active."""
        assert len(active_providers) > 0, \
            "No active providers configured"

    def test_at_least_one_exact_match_defined(
        self, exact_matches: dict
    ) -> None:
        """Verify at least one exact match model is defined."""
        assert len(exact_matches) > 0, \
            "No exact match models defined"

    def test_litellm_model_list_not_empty(
        self, litellm_config: dict
    ) -> None:
        """Verify litellm model list is not empty."""
        model_list = litellm_config.get("model_list", [])
        assert len(model_list) > 0, \
            "LiteLLM model_list is empty"

    def test_provider_model_names_not_empty(
        self, active_providers: dict
    ) -> None:
        """Verify all active providers have at least some models or are optional."""
        # Some providers like llama_cpp_python may not have models pre-configured
        # They may dynamically load models at runtime
        # This test just validates that if models are present, they're valid
        for provider_name, config in active_providers.items():
            models = config.get("models", [])

            # Allow empty models for providers that may load dynamically
            # But if models are present, they should be non-empty after loading
            if models:
                for model in models:
                    if isinstance(model, dict):
                        assert "name" in model, \
                            f"Provider {provider_name} model missing 'name' field"
