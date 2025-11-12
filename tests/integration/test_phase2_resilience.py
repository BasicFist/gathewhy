"""
Phase 2 Resilience Tests - Production Hardening Validation

Tests for Phase 2 production hardening improvements:
1. Cloud model authentication
2. Circuit breaker behavior
3. Fallback chain triggering
4. Request timeout enforcement
5. Rate limiting
6. Redis persistence

Requires:
- LiteLLM gateway running on http://localhost:4000
- Ollama Cloud API key set in environment
- Redis running on localhost:6379
"""

import os
import time

import pytest
import redis
import requests


@pytest.mark.integration
@pytest.mark.requires_cloud
class TestCloudModelAuthentication:
    """Test authentication for cloud model providers"""

    def test_ollama_cloud_api_key_present(self):
        """Verify OLLAMA_API_KEY environment variable is set"""
        api_key = os.getenv("OLLAMA_API_KEY")
        assert api_key is not None, "OLLAMA_API_KEY environment variable not set"
        assert len(api_key) > 0, "OLLAMA_API_KEY is empty"
        assert len(api_key) > 20, "OLLAMA_API_KEY appears too short (likely invalid)"

    def test_cloud_model_request_with_auth(self, litellm_url, providers_config):
        """Test request to Ollama Cloud model with authentication"""
        # Check if ollama_cloud provider is active
        ollama_cloud = providers_config.get("providers", {}).get("ollama_cloud", {})
        if ollama_cloud.get("status") != "active":
            pytest.skip("Ollama Cloud provider not active")

        # Get first cloud model
        models = ollama_cloud.get("models", [])
        if not models:
            pytest.skip("No Ollama Cloud models configured")

        model_name = models[0].get("name") if isinstance(models[0], dict) else models[0]

        # Make request
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Say 'auth test passed' only"}],
            "max_tokens": 20,
            "temperature": 0,
        }

        response = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=60)

        # Verify successful authentication
        assert response.status_code == 200, f"Cloud model request failed: {response.text}"
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0

    def test_cloud_model_invalid_auth_handling(self, litellm_url):
        """Test graceful handling of invalid authentication"""
        # This would require temporarily breaking auth, which is destructive
        # Instead, test that error response is properly formatted
        pytest.skip("Destructive test - would require breaking auth temporarily")

    def test_cloud_model_in_model_list(self, litellm_url, providers_config):
        """Verify cloud models appear in /v1/models endpoint"""
        ollama_cloud = providers_config.get("providers", {}).get("ollama_cloud", {})
        if ollama_cloud.get("status") != "active":
            pytest.skip("Ollama Cloud provider not active")

        response = requests.get(f"{litellm_url}/v1/models", timeout=5)
        assert response.status_code == 200

        data = response.json()
        model_ids = [model["id"] for model in data["data"]]

        # Check at least one cloud model is listed
        cloud_models = ollama_cloud.get("models", [])
        if cloud_models:
            first_cloud_model = (
                cloud_models[0].get("name")
                if isinstance(cloud_models[0], dict)
                else cloud_models[0]
            )
            assert (
                first_cloud_model in model_ids
            ), f"Cloud model {first_cloud_model} not in model list"


@pytest.mark.integration
@pytest.mark.requires_ollama
class TestCircuitBreakerBehavior:
    """Test circuit breaker configuration and behavior"""

    def test_circuit_breaker_config_present(self, litellm_config):
        """Verify circuit breaker configuration is present"""
        router_settings = litellm_config.get("router_settings", {})

        # Circuit breaker settings
        assert "allowed_fails" in router_settings
        assert router_settings["allowed_fails"] == 5, "Expected 5 failures for circuit breaker"

        assert "cooldown_time" in router_settings
        assert router_settings["cooldown_time"] == 60, "Expected 60s cooldown time"

        assert "enable_pre_call_checks" in router_settings
        assert router_settings["enable_pre_call_checks"] is True

    def test_circuit_breaker_activation(self, litellm_url):
        """Test circuit breaker activates after threshold failures"""
        # This would require intentionally failing requests repeatedly
        # Skip for now as it would pollute logs and affect other tests
        pytest.skip("Requires isolated test environment to trigger failures")


@pytest.mark.integration
@pytest.mark.requires_ollama
class TestFallbackChainTriggering:
    """Test fallback chain activation and execution"""

    def test_fallback_chains_configured(self, litellm_config):
        """Verify fallback chains are present in configuration"""
        router_settings = litellm_config.get("router_settings", {})
        fallbacks = router_settings.get("fallbacks", [])

        assert len(fallbacks) > 0, "No fallback chains configured"

        # Verify fallback structure
        for fallback_entry in fallbacks:
            assert isinstance(fallback_entry, dict)
            assert len(fallback_entry) == 1  # Single key per entry

            primary_model = list(fallback_entry.keys())[0]
            fallback_models = fallback_entry[primary_model]

            assert isinstance(fallback_models, list)
            assert len(fallback_models) > 0, f"No fallbacks for {primary_model}"

    def test_fallback_chain_no_cycles(self, fallback_chains):
        """Verify no circular fallback chains"""

        def has_cycle(model: str, visited: set[str]) -> bool:
            if model in visited:
                return True
            if model not in fallback_chains:
                return False

            visited.add(model)
            chain = fallback_chains[model].get("chain", [])
            for fallback_model in chain:
                if has_cycle(fallback_model, visited.copy()):
                    return True
            visited.remove(model)
            return False

        for model_name in fallback_chains:
            assert not has_cycle(
                model_name, set()
            ), f"Circular fallback chain detected: {model_name}"

    def test_fallback_chain_execution(self, litellm_url):
        """Test fallback chain actually executes when primary fails"""
        # This requires intentionally making primary fail
        # Skip for now - would need controlled test environment
        pytest.skip("Requires ability to simulate provider failure")

    def test_fallback_models_exist(self, litellm_config, fallback_chains):
        """Verify all fallback chain models exist in configuration"""
        model_list = litellm_config.get("model_list", [])
        available_models = {model["model_name"] for model in model_list}

        for primary_model, config in fallback_chains.items():
            fallback_models = config.get("chain", [])
            for fallback_model in fallback_models:
                assert (
                    fallback_model in available_models
                ), f"Fallback model '{fallback_model}' for '{primary_model}' not in model_list"


@pytest.mark.integration
class TestRequestTimeoutPolicies:
    """Test request timeout configuration and enforcement"""

    def test_timeout_settings_configured(self, litellm_config):
        """Verify timeout policies are configured"""
        litellm_settings = litellm_config.get("litellm_settings", {})
        router_settings = litellm_config.get("router_settings", {})

        # LiteLLM settings timeouts
        assert "request_timeout" in litellm_settings
        assert litellm_settings["request_timeout"] == 60

        assert "stream_timeout" in litellm_settings
        assert litellm_settings["stream_timeout"] == 120

        assert "timeout" in litellm_settings
        assert litellm_settings["timeout"] == 300

        # Router settings timeout
        assert "timeout" in router_settings
        assert router_settings["timeout"] == 30

    def test_retry_policy_configured(self, litellm_config):
        """Verify retry policies are configured"""
        litellm_settings = litellm_config.get("litellm_settings", {})
        router_settings = litellm_config.get("router_settings", {})

        # LiteLLM retry count
        assert "num_retries" in litellm_settings
        assert litellm_settings["num_retries"] == 3

        # Router retry count
        assert "num_retries" in router_settings
        assert router_settings["num_retries"] == 2

    def test_timeout_enforcement(self, litellm_url):
        """Test that timeouts are actually enforced"""
        # Would require a slow provider to test timeout
        pytest.skip("Requires controlled slow provider for timeout testing")


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting for cloud providers"""

    def test_rate_limits_configured(self, litellm_config):
        """Verify rate limiting is configured for all models"""
        rate_limit_settings = litellm_config.get("rate_limit_settings", {})

        assert rate_limit_settings.get("enabled") is True
        limits = rate_limit_settings.get("limits", {})
        assert len(limits) > 0, "No rate limits configured"

        # Check cloud models have rate limits
        model_list = litellm_config.get("model_list", [])
        cloud_models = [
            model["model_name"] for model in model_list if "cloud" in model["model_name"].lower()
        ]

        for cloud_model in cloud_models:
            assert cloud_model in limits, f"Cloud model {cloud_model} missing rate limit"
            assert "rpm" in limits[cloud_model]
            assert "tpm" in limits[cloud_model]
            assert limits[cloud_model]["rpm"] > 0
            assert limits[cloud_model]["tpm"] > 0

    def test_rate_limit_enforcement(self, litellm_url):
        """Test rate limit is actually enforced"""
        # Would require rapid requests exceeding limit
        pytest.skip("Requires rapid request generation to test rate limiting")


@pytest.mark.integration
class TestRedisPersistence:
    """Test Redis persistence configuration"""

    def test_redis_connection(self):
        """Verify Redis is accessible"""
        try:
            r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
            r.ping()
        except Exception as e:
            pytest.fail(f"Redis connection failed: {e}")

    def test_redis_rdb_enabled(self):
        """Verify RDB persistence is enabled"""
        r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
        info = r.info("persistence")

        # Check RDB is configured
        assert "rdb_last_save_time" in info
        assert "rdb_last_bgsave_status" in info
        assert info["rdb_last_bgsave_status"] == "ok"

    def test_redis_aof_enabled(self):
        """Verify AOF persistence is enabled"""
        r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
        info = r.info("persistence")

        # Check AOF is enabled
        assert "aof_enabled" in info
        assert info["aof_enabled"] == 1, "AOF persistence not enabled"

    def test_redis_aof_fsync_policy(self):
        """Verify AOF fsync policy is set to everysec"""
        r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
        config = r.config_get("appendfsync")

        assert "appendfsync" in config
        assert (
            config["appendfsync"] == "everysec"
        ), f"Expected everysec, got {config['appendfsync']}"

    def test_redis_cache_working(self):
        """Verify Redis caching is functional"""
        r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

        # Write test key
        test_key = f"test:persistence:{int(time.time())}"
        test_value = "phase2_resilience_test"

        r.set(test_key, test_value)
        retrieved = r.get(test_key)

        assert retrieved == test_value, "Redis write/read failed"

        # Cleanup
        r.delete(test_key)


@pytest.mark.integration
class TestPhase2IntegrationSummary:
    """Overall Phase 2 integration verification"""

    def test_all_phase2_features_configured(self, litellm_config):
        """Verify all Phase 2 features are present in configuration"""
        features = {
            "circuit_breaker": False,
            "timeout_policies": False,
            "retry_logic": False,
            "rate_limiting": False,
            "fallback_chains": False,
        }

        # Check circuit breaker
        router_settings = litellm_config.get("router_settings", {})
        if router_settings.get("allowed_fails") == 5 and router_settings.get("cooldown_time") == 60:
            features["circuit_breaker"] = True

        # Check timeout policies
        litellm_settings = litellm_config.get("litellm_settings", {})
        if (
            litellm_settings.get("request_timeout")
            and litellm_settings.get("stream_timeout")
            and litellm_settings.get("timeout")
        ):
            features["timeout_policies"] = True

        # Check retry logic
        if litellm_settings.get("num_retries") and router_settings.get("num_retries"):
            features["retry_logic"] = True

        # Check rate limiting
        rate_limit_settings = litellm_config.get("rate_limit_settings", {})
        if rate_limit_settings.get("enabled") and len(rate_limit_settings.get("limits", {})) > 0:
            features["rate_limiting"] = True

        # Check fallback chains
        if len(router_settings.get("fallbacks", [])) > 0:
            features["fallback_chains"] = True

        # Verify all features enabled
        missing_features = [name for name, enabled in features.items() if not enabled]
        assert (
            len(missing_features) == 0
        ), f"Phase 2 features missing: {', '.join(missing_features)}"

    def test_phase2_system_health(self, litellm_url):
        """Overall system health check with Phase 2 improvements"""
        # Check gateway health
        response = requests.get(f"{litellm_url}/health", timeout=5)
        assert response.status_code == 200

        # Check models available
        response = requests.get(f"{litellm_url}/v1/models", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("data", [])) > 0

        # Check Redis connectivity
        try:
            r = redis.Redis(host="127.0.0.1", port=6379)
            r.ping()
        except Exception as e:
            pytest.fail(f"Redis not accessible: {e}")
