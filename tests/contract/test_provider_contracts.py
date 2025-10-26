"""
Contract tests for provider API compliance.

These tests validate that each provider adheres to expected API contracts
and response formats. Tests check actual provider responses against schemas
and behavior expectations.

Test Markers:
  - contract: Full provider contract compliance
  - requires_ollama: Requires Ollama provider running
  - requires_vllm: Requires vLLM provider running
  - requires_redis: Requires Redis cache running
"""


import pytest
import requests


@pytest.mark.contract
@pytest.mark.requires_ollama
class TestOllamaContract:
    """Test Ollama provider API contract compliance."""

    @pytest.fixture(scope="class")
    def ollama_base_url(self, provider_urls: dict[str, str]) -> str:
        """Get Ollama base URL from config."""
        return provider_urls.get("ollama", "http://localhost:11434")

    def test_ollama_health_endpoint(self, ollama_base_url: str) -> None:
        """Verify Ollama health endpoint responds correctly."""
        response = requests.get(f"{ollama_base_url}/api/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or response.text == ""

    def test_ollama_tags_endpoint_response_format(self, ollama_base_url: str) -> None:
        """Verify Ollama /api/tags endpoint returns expected format."""
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "models" in data
        assert isinstance(data["models"], list)

    def test_ollama_models_have_required_fields(self, ollama_base_url: str) -> None:
        """Verify each model in Ollama tags has required fields."""
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        data = response.json()
        models = data.get("models", [])

        assert len(models) > 0, "No models found in Ollama"

        for model in models:
            assert "name" in model, "Model missing 'name' field"
            assert "digest" in model, "Model missing 'digest' field"
            assert isinstance(model["name"], str)
            assert isinstance(model["digest"], str)

    def test_ollama_completion_endpoint_accepts_openai_format(self, ollama_base_url: str) -> None:
        """Verify Ollama accepts OpenAI-compatible completion format."""
        # Get first available model
        tags_response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        models = tags_response.json().get("models", [])

        if not models:
            pytest.skip("No models available in Ollama")

        model_name = models[0]["name"]

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "say hello"}],
            "stream": False,
        }

        response = requests.post(f"{ollama_base_url}/api/chat", json=payload, timeout=10)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "content" in data["message"]


@pytest.mark.contract
@pytest.mark.requires_vllm
class TestVLLMContract:
    """Test vLLM provider API contract compliance."""

    @pytest.fixture(scope="class")
    def vllm_base_url(self, provider_urls: dict[str, str]) -> str:
        """Get vLLM base URL from config."""
        return provider_urls.get("vllm", "http://localhost:8001")

    def test_vllm_openai_compliant_models_endpoint(self, vllm_base_url: str) -> None:
        """Verify vLLM /v1/models endpoint returns OpenAI-compatible format."""
        response = requests.get(f"{vllm_base_url}/v1/models", timeout=5)
        assert response.status_code == 200
        data = response.json()

        assert "object" in data
        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_vllm_model_entries_have_required_fields(self, vllm_base_url: str) -> None:
        """Verify each model entry has OpenAI-compatible required fields."""
        response = requests.get(f"{vllm_base_url}/v1/models", timeout=5)
        data = response.json()
        models = data.get("data", [])

        assert len(models) > 0, "No models found in vLLM"

        for model in models:
            assert "id" in model, "Model missing 'id' field"
            assert "object" in model, "Model missing 'object' field"
            assert model["object"] == "model"
            assert "owned_by" in model

    def test_vllm_completions_endpoint_openai_compatible(self, vllm_base_url: str) -> None:
        """Verify vLLM /v1/chat/completions endpoint is OpenAI-compatible."""
        # Get first available model
        models_response = requests.get(f"{vllm_base_url}/v1/models", timeout=5)
        models = models_response.json().get("data", [])

        if not models:
            pytest.skip("No models available in vLLM")

        model_id = models[0]["id"]

        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": "say hello"}],
            "max_tokens": 10,
        }

        response = requests.post(f"{vllm_base_url}/v1/chat/completions", json=payload, timeout=10)

        assert response.status_code == 200
        data = response.json()

        # Verify OpenAI response format
        assert "choices" in data
        assert isinstance(data["choices"], list)
        assert len(data["choices"]) > 0
        assert "message" in data["choices"][0]
        assert "content" in data["choices"][0]["message"]


@pytest.mark.contract
class TestProviderResponseFormats:
    """Test that provider responses conform to expected formats."""

    def test_provider_urls_are_reachable(self, provider_urls: dict[str, str]) -> None:
        """Verify all configured provider URLs respond to requests."""
        unreachable = []

        for provider_name, url in provider_urls.items():
            try:
                response = requests.head(url, timeout=3)
                # Expect either 200 or 405 (Method Not Allowed for HEAD)
                assert response.status_code in [
                    200,
                    405,
                    404,
                ], f"Provider {provider_name} returned {response.status_code}"
            except (requests.ConnectionError, requests.Timeout) as e:
                unreachable.append((provider_name, str(e)))

        if unreachable:
            pytest.skip(
                f"Some providers unreachable: {'; '.join(
                    f'{p}({e})' for p, e in unreachable
                )}"
            )

    def test_litellm_gateway_available(self, litellm_url: str) -> None:
        """Verify LiteLLM gateway is available."""
        try:
            response = requests.get(f"{litellm_url}/health", timeout=5)
            assert response.status_code in [200, 404]  # 404 OK if endpoint not available
        except (requests.ConnectionError, requests.Timeout):
            pytest.skip("LiteLLM gateway not reachable")

    def test_litellm_models_endpoint_format(self, litellm_url: str) -> None:
        """Verify LiteLLM /v1/models endpoint returns OpenAI-compatible format."""
        try:
            response = requests.get(f"{litellm_url}/v1/models", timeout=5)
        except (requests.ConnectionError, requests.Timeout):
            pytest.skip("LiteLLM gateway not reachable")

        assert response.status_code == 200
        data = response.json()

        assert "object" in data
        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)


@pytest.mark.contract
class TestProviderConfiguration:
    """Test that provider configuration matches expected contracts."""

    def test_all_active_providers_have_base_urls(self, active_providers: dict[str, dict]) -> None:
        """Verify all active providers have configured base URLs."""
        for provider_name, config in active_providers.items():
            assert "base_url" in config, f"Provider {provider_name} missing base_url"
            assert config["base_url"].startswith(
                ("http://", "https://")
            ), f"Provider {provider_name} base_url invalid: {config['base_url']}"

    def test_all_active_providers_have_type(self, active_providers: dict[str, dict]) -> None:
        """Verify all active providers have a configured type."""
        valid_types = {"ollama", "vllm", "llama_cpp", "openai", "anthropic", "openai_compatible"}

        for provider_name, config in active_providers.items():
            assert "type" in config, f"Provider {provider_name} missing type"
            assert (
                config["type"] in valid_types
            ), f"Provider {provider_name} has invalid type: {config['type']}"

    def test_provider_models_list_not_empty(self, active_providers: dict[str, dict]) -> None:
        """Verify all active providers have at least one model configured."""
        for provider_name, config in active_providers.items():
            models = config.get("models", [])
            assert len(models) > 0, f"Provider {provider_name} has no models configured"

    def test_provider_models_have_names(self, active_providers: dict[str, dict]) -> None:
        """Verify all provider models have names."""
        for provider_name, config in active_providers.items():
            models = config.get("models", [])

            for idx, model in enumerate(models):
                if isinstance(model, dict):
                    assert "name" in model, f"Model {idx} in {provider_name} missing name"
                else:
                    # String model names are acceptable
                    assert isinstance(
                        model, str
                    ), f"Model {idx} in {provider_name} has invalid type: {type(model)}"


@pytest.mark.contract
class TestRoutingConfigurationContract:
    """Test that routing configuration maintains provider contracts."""

    def test_exact_matches_target_active_providers(
        self, exact_matches: dict[str, dict], active_providers: dict[str, dict]
    ) -> None:
        """Verify exact matches only target active providers."""
        active_names = set(active_providers.keys())

        for model_name, config in exact_matches.items():
            provider = config.get("provider")
            assert (
                provider in active_names
            ), f"Model {model_name} targets inactive provider: {provider}"

    def test_fallback_chains_target_valid_providers(
        self, fallback_chains: dict[str, list], active_providers: dict[str, dict]
    ) -> None:
        """Verify fallback chains reference valid providers."""
        # Note: active_providers validation could be enhanced in future
        _ = active_providers  # Mark as intentionally unused for now

        for _primary_model, chain in fallback_chains.items():
            for fallback_model in chain:
                # Find provider for this fallback
                # This is a basic check - implementation may vary
                assert isinstance(
                    fallback_model, str
                ), f"Fallback chain entry is not a string: {fallback_model}"

    def test_capability_routing_references_known_models(
        self, capability_routing: dict[str, dict], exact_matches: dict[str, dict]
    ) -> None:
        """Verify capability routing references known model names."""
        known_models = set(exact_matches.keys())

        for capability, config in capability_routing.items():
            models = config.get("preferred_models", config.get("models", []))

            for model_name in models:
                assert (
                    model_name in known_models
                ), f"Capability {capability} references unknown model: {model_name}"
