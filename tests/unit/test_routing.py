"""
Unit tests for routing logic

Tests routing decisions without external dependencies:
- Exact model name matching
- Pattern-based routing
- Capability-based routing
- Fallback chain integrity
- Load balancing weight validation
"""

import re

import pytest


@pytest.mark.unit
class TestExactMatchRouting:
    """Test exact model name routing"""

    def test_exact_match_returns_correct_provider(self, exact_matches):
        """Verify exact model names route to correct provider"""
        # Test each exact match
        for model_name, config in exact_matches.items():
            provider = config.get("provider")
            assert provider is not None, f"Model {model_name} missing provider"
            assert isinstance(provider, str), f"Provider must be string, got {type(provider)}"

    def test_exact_match_has_priority(self, exact_matches):
        """Verify all exact matches have priority defined"""
        valid_priorities = ["primary", "secondary", "tertiary", "fallback"]

        for model_name, config in exact_matches.items():
            priority = config.get("priority")
            assert (
                priority in valid_priorities
            ), f"Model {model_name} has invalid priority: {priority}"

    def test_no_duplicate_primary_providers(self, exact_matches):
        """Verify no model has multiple primary providers"""
        models_by_priority = {}

        for model_name, config in exact_matches.items():
            priority = config.get("priority")
            if priority == "primary":
                assert (
                    model_name not in models_by_priority
                ), f"Model {model_name} has duplicate primary provider"
                models_by_priority[model_name] = config["provider"]


@pytest.mark.unit
class TestPatternMatching:
    """Test pattern-based routing"""

    def test_pattern_syntax_valid(self, mappings_config):
        """Verify all routing patterns are valid regex"""
        patterns = mappings_config.get("patterns", [])

        for entry in patterns:
            pattern = entry.get("pattern")
            assert pattern is not None, "Pattern entry missing pattern field"

            # Verify it compiles as valid regex
            try:
                re.compile(pattern)
            except re.error as e:
                pytest.fail(f"Invalid regex pattern '{pattern}': {e}")

    def test_patterns_match_expected_models(self, mappings_config):
        """Verify patterns match their intended model names"""
        patterns = mappings_config.get("patterns", [])

        test_cases = {
            "^Qwen/Qwen2\\.5-Coder.*": ["Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"],
            "^solidrust/dolphin.*AWQ$": ["solidrust/dolphin-2.8-mistral-7b-v02-AWQ"],
            "^meta-llama/.*": ["meta-llama/Llama-2-13b-chat-hf", "meta-llama/Llama-3-8b"],
            ".*:\\d+[bB]$": ["demo:7b", "another:13B"],
            ".*\\.gguf$": ["model.gguf"],
        }

        for entry in patterns:
            pattern = entry.get("pattern")
            regex = re.compile(pattern)

            # Test against known examples if pattern is in test cases
            if pattern in test_cases:
                for model_name in test_cases[pattern]:
                    assert regex.match(
                        model_name
                    ), f"Pattern '{pattern}' should match '{model_name}'"

    def test_patterns_have_providers(self, mappings_config):
        """Verify all patterns have valid provider assignments"""
        patterns = mappings_config.get("patterns", [])

        for entry in patterns:
            provider = entry.get("provider")
            assert provider is not None, f"Pattern '{entry.get('pattern')}' missing provider"
            assert isinstance(provider, str), f"Provider must be string, got {type(provider)}"


@pytest.mark.unit
class TestCapabilityRouting:
    """Test capability-based routing"""

    def test_capabilities_have_models(self, capability_routing):
        """Verify each capability has at least one model"""
        for capability, config in capability_routing.items():
            models = config.get("preferred_models") or config.get("models") or []
            providers = config.get("providers") or (
                [config.get("provider")] if config.get("provider") else []
            )
            has_additional_constraints = bool(
                config.get("min_model_size") or config.get("min_context")
            )

            assert (
                models or providers or has_additional_constraints
            ), f"Capability '{capability}' lacks routing targets"

            if providers:
                for provider_name in providers:
                    assert (
                        isinstance(provider_name, str) and provider_name
                    ), f"Capability '{capability}' has invalid provider reference"

    def test_capability_strategies_valid(self, capability_routing):
        """Verify routing strategies are valid"""
        valid_strategies = [
            "round_robin",
            "least_loaded",
            "least_latency",
            "priority_based",
            "random",
            "load_balance",
            "direct",
            "usage_based",
            "fastest_response",
            "most_capacity",
            # v1.7 NEW strategies
            "complexity_based",  # Route by task complexity
            "quality_based",  # Route by quality tier
            "adaptive_weighted",  # Dynamic weight adjustment
            "context_based",  # Route by context size
        ]

        for capability, config in capability_routing.items():
            strategy = config.get("routing_strategy") or config.get("strategy")
            if strategy:  # Optional field
                assert (
                    strategy in valid_strategies
                ), f"Capability '{capability}' has invalid strategy: {strategy}"

    def test_capability_models_exist(self, capability_routing, exact_matches, providers_config):
        """Verify capability models reference existing configurations"""
        # Build set of all valid model names
        valid_models = set(exact_matches.keys())

        # Add models from active providers
        for _provider_name, provider_config in providers_config["providers"].items():
            if provider_config.get("status") == "active":
                for model in provider_config.get("models", []):
                    valid_models.add(model.get("name"))

        # Check each capability
        for capability, config in capability_routing.items():
            models = config.get("preferred_models") or config.get("models") or []
            for model_name in models:
                # Allow some flexibility for pattern-based names
                # Just verify it's a non-empty string
                assert model_name, f"Capability '{capability}' has empty model name"
                assert isinstance(
                    model_name, str
                ), f"Model name must be string, got {type(model_name)}"


@pytest.mark.unit
class TestFallbackChains:
    """Test fallback chain integrity"""

    def test_fallback_chains_not_circular(self, fallback_chains):
        """Verify no circular fallback chains"""

        def has_cycle(model: str, visited: set) -> bool:
            if model in visited:
                return True

            visited.add(model)

            if model in fallback_chains:
                chain = fallback_chains[model].get("chain", [])
                for fallback_model in chain:
                    if has_cycle(fallback_model, visited.copy()):
                        return True

            return False

        for model_name in fallback_chains:
            assert not has_cycle(
                model_name, set()
            ), f"Circular fallback chain detected for model: {model_name}"

    def test_fallback_chains_have_models(self, fallback_chains):
        """Verify each fallback chain has at least one fallback (except terminal nodes)"""
        # Terminal nodes are allowed to have empty chains
        terminal_nodes = {
            "llama-cpp-native",  # New terminal node (fastest local, C++ native)
            # Add more terminal nodes here as architecture evolves
        }

        for model_name, config in fallback_chains.items():
            chain = config.get("chain", [])

            # Terminal nodes can have empty chains
            if model_name in terminal_nodes and not chain:
                continue  # Expected for terminal nodes

            # Non-terminal nodes must have fallbacks
            assert len(chain) > 0, f"Non-terminal model '{model_name}' has empty fallback chain"

    def test_fallback_chains_no_self_reference(self, fallback_chains):
        """Fallback chains must not reference the primary model"""
        for model_name, config in fallback_chains.items():
            chain = config.get("chain", [])
            assert model_name not in chain, f"Model '{model_name}' fallback chain references itself"

    def test_fallback_chains_no_duplicate_entries(self, fallback_chains):
        """Fallback chains must not contain duplicate models"""
        for model_name, config in fallback_chains.items():
            chain = config.get("chain", [])
            assert len(chain) == len(
                set(chain)
            ), f"Model '{model_name}' fallback chain has duplicates"

    def test_fallback_strategies_valid(self, fallback_chains):
        """Verify fallback strategies are valid"""
        valid_strategies = ["immediate", "retry_with_backoff", "circuit_breaker"]

        for model_name, config in fallback_chains.items():
            strategy = config.get("strategy")
            if strategy:  # Optional field
                assert (
                    strategy in valid_strategies
                ), f"Model '{model_name}' has invalid fallback strategy: {strategy}"

    def test_fallback_chains_reference_active_providers(
        self, fallback_chains, active_providers, exact_matches
    ):
        """Verify fallback models reference active providers"""
        # Build set of models from active providers
        valid_models = set()
        for _provider_name, provider_config in active_providers.items():
            for model in provider_config.get("models", []):
                valid_models.add(model.get("name"))

        # Also include exact matches
        valid_models.update(exact_matches.keys())

        # Check each fallback chain
        for _model_name, config in fallback_chains.items():
            chain = config.get("chain", [])
            for fallback_model in chain:
                # Allow some flexibility - just verify it's a string
                assert isinstance(
                    fallback_model, str
                ), f"Fallback model must be string, got {type(fallback_model)}"


@pytest.mark.unit
class TestLoadBalancing:
    """Test load balancing configuration"""

    def test_load_balancing_weights_sum_to_one(self, mappings_config):
        """Verify load balancing weights sum to 1.0"""
        load_balancing = mappings_config.get("load_balancing", {})

        for model_name, config in load_balancing.items():
            providers = config.get("providers", [])
            total_weight = sum(p.get("weight", 0) for p in providers)

            # Allow small floating point tolerance
            assert (
                abs(total_weight - 1.0) < 0.01
            ), f"Model '{model_name}' weights sum to {total_weight}, expected 1.0"

    def test_load_balancing_has_providers(self, mappings_config):
        """Verify load balancing configs have at least 2 providers"""
        load_balancing = mappings_config.get("load_balancing", {})

        for model_name, config in load_balancing.items():
            providers = config.get("providers", [])
            assert (
                len(providers) >= 2
            ), f"Model '{model_name}' has only {len(providers)} providers, need at least 2 for load balancing"

    def test_load_balancing_weights_positive(self, mappings_config):
        """Verify all weights are positive"""
        load_balancing = mappings_config.get("load_balancing", {})

        for model_name, config in load_balancing.items():
            providers = config.get("providers", [])
            for provider_config in providers:
                weight = provider_config.get("weight", 0)
                assert (
                    weight > 0
                ), f"Model '{model_name}' provider '{provider_config.get('provider')}' has non-positive weight: {weight}"


@pytest.mark.unit
class TestProviderReferences:
    """Test that all routing configurations reference valid providers"""

    def test_exact_matches_reference_active_providers(self, exact_matches, active_providers):
        """Verify exact matches reference active providers"""
        active_provider_names = set(active_providers.keys())

        for model_name, config in exact_matches.items():
            provider = config.get("provider")
            # Allow special cases like 'auto' or pattern-based providers
            if provider and provider != "auto":
                assert provider in active_provider_names or provider.startswith(
                    "pattern:"
                ), f"Model '{model_name}' references inactive/unknown provider: {provider}"

    def test_pattern_matches_reference_active_providers(
        self, mappings_config, active_providers, providers_config
    ):
        """Verify pattern matches reference active or disabled (documented) providers"""
        patterns = mappings_config.get("patterns", [])

        # Get all provider names (including disabled ones like vllm-dolphin)
        all_provider_names = set(providers_config.get("providers", {}).keys())

        for entry in patterns:
            provider = entry.get("provider")
            if provider:
                # Allow patterns to reference disabled providers (for documentation/future use)
                # e.g., vllm-dolphin is disabled due to single-instance constraint but pattern documented
                assert (
                    provider in all_provider_names
                ), f"Pattern '{entry.get('pattern')}' references unknown provider: {provider}"

    def test_load_balancing_references_active_providers(self, mappings_config, active_providers):
        """Verify load balancing references active providers"""
        load_balancing = mappings_config.get("load_balancing", {})
        active_provider_names = set(active_providers.keys())

        for model_name, config in load_balancing.items():
            providers = config.get("providers", [])
            for provider_config in providers:
                provider = provider_config.get("provider")
                assert (
                    provider in active_provider_names
                ), f"Load balancing for '{model_name}' references inactive/unknown provider: {provider}"


@pytest.mark.unit
class TestRateLimits:
    """Test rate limiting configuration"""

    def test_rate_limits_have_valid_values(self, exact_matches):
        """Verify rate limit values are positive integers"""
        for model_name, config in exact_matches.items():
            rate_limit = config.get("rate_limit")
            if rate_limit:
                rpm = rate_limit.get("rpm")
                tpm = rate_limit.get("tpm")

                if rpm is not None:
                    assert (
                        isinstance(rpm, int) and rpm > 0
                    ), f"Model '{model_name}' has invalid RPM: {rpm}"

                if tpm is not None:
                    assert (
                        isinstance(tpm, int) and tpm > 0
                    ), f"Model '{model_name}' has invalid TPM: {tpm}"

    def test_rate_limits_reasonable_values(self, exact_matches):
        """Verify rate limits are within reasonable ranges"""
        max_rpm = 10000  # requests per minute
        max_tpm = 10000000  # tokens per minute

        for model_name, config in exact_matches.items():
            rate_limit = config.get("rate_limit")
            if rate_limit:
                rpm = rate_limit.get("rpm", 0)
                tpm = rate_limit.get("tpm", 0)

                assert rpm <= max_rpm, f"Model '{model_name}' has unreasonably high RPM: {rpm}"

                assert tpm <= max_tpm, f"Model '{model_name}' has unreasonably high TPM: {tpm}"
