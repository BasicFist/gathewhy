"""
LiteLLM Load Testing with Locust
Tests LiteLLM unified backend under various load patterns.
"""

import json
import random

from locust import HttpUser, between, events, task

# Test prompts for realistic load
PROMPTS = [
    "What is the capital of France?",
    "Write a Python function to calculate fibonacci numbers",
    "Explain quantum computing in simple terms",
    "Translate 'Hello, how are you?' to Spanish",
    "Summarize the importance of clean code",
    "What are the best practices for REST API design?",
    "Debug this Python code: print(hello world)",
    "Compare Python and JavaScript for web development",
    "Explain the SOLID principles",
    "Write a SQL query to find duplicate records",
]

# Model distribution (simulate realistic usage patterns)
MODEL_WEIGHTS = {
    "llama3.1:8b": 0.60,  # Primary model (60% of requests)
    "llama-3.1-8b-instruct": 0.25,  # Secondary (25%)
    "qwen-coder-vllm": 0.15,  # Specialized (15%)
}


class LiteLLMUser(HttpUser):
    """Simulates a user making LLM requests."""

    # Wait 1-5 seconds between requests (realistic user behavior)
    wait_time = between(1, 5)

    def on_start(self):
        """Called when a user starts."""
        self.user_id = f"user_{self.environment.runner.user_count}"
        print(f"User {self.user_id} started")

    @task(weight=10)
    def completion_request(self):
        """Standard completion request (most common)."""

        # Select model based on weights
        model = random.choices(
            list(MODEL_WEIGHTS.keys()), weights=list(MODEL_WEIGHTS.values()), k=1
        )[0]

        prompt = random.choice(PROMPTS)

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": random.choice([50, 100, 150]),
            "metadata": {
                "user_id": self.user_id,
                "environment": "loadtest",
                "test_type": "standard_completion",
            },
        }

        with self.client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="/chat/completions (standard)",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    response.success()
                    print(f"✅ {model}: {tokens} tokens")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                response.failure("Rate limited")
            elif response.status_code >= 500:
                response.failure(f"Server error: {response.status_code}")
            else:
                response.failure(f"Request failed: {response.status_code}")

    @task(weight=3)
    def streaming_request(self):
        """Streaming completion request (less common but important)."""

        model = random.choice(list(MODEL_WEIGHTS.keys()))
        prompt = random.choice(PROMPTS)

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "stream": True,
            "metadata": {
                "user_id": self.user_id,
                "environment": "loadtest",
                "test_type": "streaming",
            },
        }

        with self.client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            catch_response=True,
            name="/chat/completions (streaming)",
        ) as response:
            if response.status_code == 200:
                try:
                    # Count streamed chunks
                    chunks = 0
                    for line in response.iter_lines():
                        if line:
                            chunks += 1
                    response.success()
                    print(f"✅ {model}: {chunks} chunks streamed")
                except Exception as e:
                    response.failure(f"Streaming error: {e}")
            else:
                response.failure(f"Request failed: {response.status_code}")

    @task(weight=1)
    def list_models(self):
        """List available models (lightweight health check)."""

        with self.client.get("/v1/models", catch_response=True, name="/models") as response:
            if response.status_code == 200:
                try:
                    response.json()  # Validate JSON response
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Request failed: {response.status_code}")


class LiteLLMStressUser(HttpUser):
    """High-intensity user for stress testing."""

    wait_time = between(0.1, 0.5)  # Very short wait time

    @task
    def rapid_fire_requests(self):
        """Make rapid requests to test system limits."""

        model = random.choice(["llama3.1:8b", "llama-3.1-8b-instruct"])

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say hello"}],
            "max_tokens": 10,  # Minimal generation for speed
            "metadata": {"test_type": "stress_test"},
        }

        self.client.post(
            "/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            name="/chat/completions (stress)",
        )


# Custom event handlers for detailed statistics


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the load test starts."""
    print("=" * 80)
    print("🚀 LiteLLM Load Test Starting")
    print("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops."""
    print("=" * 80)
    print("🏁 LiteLLM Load Test Complete")
    print("=" * 80)

    # Print summary statistics
    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Success rate: {(1 - stats.total.fail_ratio) * 100:.2f}%")
    print(f"Average response time: {stats.total.avg_response_time:.0f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")
    print(f"50th percentile: {stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.0f}ms")
