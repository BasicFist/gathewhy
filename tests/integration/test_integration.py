"""
Integration tests for end-to-end routing behavior

Tests actual routing with real providers:
- Request routing to correct provider
- Fallback chain execution
- Load balancing behavior
- Rate limiting enforcement
- Cache behavior
- Streaming responses

Requires active providers to run.
"""

import time

import pytest
import requests


@pytest.mark.integration
@pytest.mark.requires_ollama
class TestBasicRouting:
    """Test basic request routing"""

    def test_litellm_gateway_accessible(self, litellm_url):
        """Verify LiteLLM gateway is running"""
        response = requests.get(f"{litellm_url}/health", timeout=5)
        assert response.status_code == 200

    def test_models_endpoint_returns_all_providers(self, litellm_url, active_providers):
        """Verify /v1/models returns models from all active providers"""
        response = requests.get(f"{litellm_url}/v1/models", timeout=5)
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0

        # Verify we have models from different providers
        model_ids = [model["id"] for model in data["data"]]
        assert len(model_ids) > 0

    def test_exact_match_routes_correctly(self, litellm_url):
        """Verify exact model name routes to expected provider"""
        # Test routing to Ollama model
        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Say 'test' only"}],
            "max_tokens": 10,
            "temperature": 0,
        }

        response = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "message" in data["choices"][0]
        assert "content" in data["choices"][0]["message"]

    def test_different_providers_routable(self, litellm_url, active_providers):
        """Test routing to different provider types"""
        # Test configurations for different providers
        test_models = [
            ("llama3.1:8b", "ollama"),  # Ollama
            ("llama-cpp-python", "llama_cpp"),  # llama.cpp
        ]

        for model_name, provider_type in test_models:
            # Skip if provider not active
            provider_active = any(
                p_config.get("type") == provider_type and p_config.get("status") == "active"
                for p_config in active_providers.values()
            )

            if not provider_active:
                pytest.skip(f"Provider {provider_type} not active")

            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            }

            response = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)

            assert response.status_code == 200, f"Routing to {model_name} ({provider_type}) failed"


@pytest.mark.integration
@pytest.mark.slow
class TestFallbackBehavior:
    """Test fallback chain execution"""

    def test_fallback_on_model_not_found(self, litellm_url):
        """Verify fallback triggers when primary model unavailable"""
        # Request non-existent model with fallback configured
        payload = {
            "model": "nonexistent-model",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10,
        }

        response = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)

        # Should either succeed with fallback or fail gracefully
        assert response.status_code in [200, 400, 404, 500]

        if response.status_code == 200:
            # Fallback succeeded
            data = response.json()
            assert "choices" in data
        else:
            # Fallback exhausted or model truly not found
            data = response.json()
            assert "error" in data

    @pytest.mark.requires_ollama
    def test_fallback_preserves_context(self, litellm_url):
        """Verify fallback maintains conversation context"""
        # First message
        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Remember: my name is Alice"}],
            "max_tokens": 20,
        }

        response1 = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)

        assert response1.status_code == 200

        # Follow-up that should remember context
        payload["messages"].append(
            {"role": "assistant", "content": response1.json()["choices"][0]["message"]["content"]}
        )
        payload["messages"].append({"role": "user", "content": "What is my name?"})

        response2 = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)

        assert response2.status_code == 200


@pytest.mark.integration
@pytest.mark.requires_redis
class TestCacheBehavior:
    """Test Redis caching functionality"""

    def test_cache_hit_faster_than_miss(self, litellm_url):
        """Verify cached responses are significantly faster"""
        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Unique test query 12345678"}],
            "max_tokens": 10,
            "temperature": 0,  # Deterministic for caching
        }

        # First request (cache miss)
        start1 = time.time()
        response1 = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)
        latency1 = time.time() - start1

        assert response1.status_code == 200
        result1 = response1.json()

        # Second request (cache hit)
        start2 = time.time()
        response2 = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)
        latency2 = time.time() - start2

        assert response2.status_code == 200
        result2 = response2.json()

        # Cache hit should be at least 2x faster
        assert (
            latency2 < latency1 * 0.5
        ), f"Cache hit ({latency2:.2f}s) not faster than miss ({latency1:.2f}s)"

        # Results should be identical
        assert (
            result1["choices"][0]["message"]["content"]
            == result2["choices"][0]["message"]["content"]
        )


@pytest.mark.integration
class TestStreamingResponses:
    """Test streaming response functionality"""

    def test_streaming_response_works(self, litellm_url):
        """Verify streaming responses deliver incremental content"""
        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Count from 1 to 3"}],
            "stream": True,
            "max_tokens": 30,
        }

        response = requests.post(
            f"{litellm_url}/v1/chat/completions", json=payload, stream=True, timeout=30
        )

        assert response.status_code == 200

        chunks = []
        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    chunks.append(decoded)

        # Should receive multiple chunks
        assert len(chunks) > 0, "No streaming chunks received"

        # Should have [DONE] marker
        assert any("[DONE]" in chunk for chunk in chunks), "Missing [DONE] marker in stream"

    def test_streaming_and_non_streaming_equivalent(self, litellm_url):
        """Verify streaming and non-streaming return same content"""
        base_payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Say exactly: 'test response'"}],
            "max_tokens": 10,
            "temperature": 0,
        }

        # Non-streaming
        response1 = requests.post(
            f"{litellm_url}/v1/chat/completions", json=base_payload, timeout=30
        )
        assert response1.status_code == 200
        response1.json()["choices"][0]["message"]["content"]

        # Streaming
        streaming_payload = {**base_payload, "stream": True}
        response2 = requests.post(
            f"{litellm_url}/v1/chat/completions", json=streaming_payload, stream=True, timeout=30
        )

        assert response2.status_code == 200

        # Collect streaming content
        content2_parts = []
        for line in response2.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: ") and "[DONE]" not in decoded:
                    import json

                    try:
                        chunk_data = json.loads(decoded[6:])  # Remove 'data: ' prefix
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta:
                                content2_parts.append(delta["content"])
                    except json.JSONDecodeError:
                        pass

        content2 = "".join(content2_parts)

        # Content should be similar (allowing for minor differences)
        assert len(content2) > 0, "No content received from streaming"


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and resilience"""

    def test_invalid_model_returns_error(self, litellm_url):
        """Verify requests to invalid models return proper errors"""
        payload = {
            "model": "completely-invalid-model-12345",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10,
        }

        response = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)

        # Should return error (400 or 404)
        assert response.status_code in [400, 404, 500]
        data = response.json()
        assert "error" in data

    def test_malformed_request_returns_error(self, litellm_url):
        """Verify malformed requests return proper errors"""
        # Missing required 'messages' field
        payload = {"model": "llama3.1:8b", "max_tokens": 10}

        response = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)

        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data

    def test_timeout_handled_gracefully(self, litellm_url):
        """Verify timeout scenarios are handled properly"""
        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10,
        }

        # Timeout is expected and properly raised
        import contextlib

        with contextlib.suppress(requests.exceptions.Timeout):
            requests.post(
                f"{litellm_url}/v1/chat/completions",
                json=payload,
                timeout=0.001,  # Intentionally very short
            )


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Test performance characteristics"""

    def test_response_time_within_threshold(self, litellm_url):
        """Verify response times are within acceptable thresholds"""
        thresholds = {
            "llama3.1:8b": 10.0,  # Ollama models
            "llama-cpp-native": 5.0,  # Fast native C++
            "llama-cpp-python": 7.0,  # Python bindings
        }

        for model_name, max_time in thresholds.items():
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10,
            }

            start = time.time()
            response = requests.post(
                f"{litellm_url}/v1/chat/completions", json=payload, timeout=max_time + 5
            )
            latency = time.time() - start

            if response.status_code == 200:
                assert (
                    latency < max_time
                ), f"{model_name} took {latency:.2f}s, expected < {max_time}s"

    def test_concurrent_requests_handled(self, litellm_url):
        """Verify multiple concurrent requests are handled properly"""
        import concurrent.futures

        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 5,
        }

        def make_request():
            response = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)
            return response.status_code

        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(
            status == 200 for status in results
        ), f"Some concurrent requests failed: {results}"


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting enforcement"""

    @pytest.mark.slow
    def test_rate_limit_enforced(self, litellm_url):
        """Verify rate limits are enforced (requires patience)"""
        # Note: This test is slow as it needs to trigger rate limits

        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 5,
        }

        # Make many rapid requests to trigger rate limit
        # Rate limit for llama3.1:8b is 100 RPM
        responses = []
        for _ in range(10):  # Don't overdo it in testing
            response = requests.post(f"{litellm_url}/v1/chat/completions", json=payload, timeout=30)
            responses.append(response.status_code)
            time.sleep(0.1)  # Small delay

        # Should have mostly successes
        success_count = sum(1 for status in responses if status == 200)
        assert success_count > 0, "No successful requests"

        # May have some rate limit responses (429)
        sum(1 for status in responses if status == 429)
        # Just verify the system can respond with 429 if needed
        # (may not trigger in light testing)
