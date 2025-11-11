#!/usr/bin/env python3
"""
Advanced Load Balancing for LiteLLM Gateway.

Implements intelligent load balancing algorithms beyond simple round-robin,
including health-weighted, latency-based, cost-optimized, and capacity-aware
routing strategies.

Features:
- Health-weighted routing (avoid unhealthy providers)
- Latency-based routing (prefer fastest providers)
- Cost-optimized routing (minimize API costs)
- Capacity-aware routing (consider rate limits and quotas)
- Token-aware routing (route based on context requirements)
- Hybrid strategies (combine multiple factors)
- Real-time provider metrics integration

Usage:
    from advanced_load_balancer import LoadBalancer, RoutingStrategy

    lb = LoadBalancer()

    # Select provider using cost-optimized strategy
    provider = lb.select_provider(
        model="gpt-4o",
        strategy=RoutingStrategy.COST_OPTIMIZED,
        context_tokens=5000
    )

Configuration:
    Set environment variables:
    - REDIS_HOST: Redis server host (default: 127.0.0.1)
    - REDIS_PORT: Redis server port (default: 6379)
    - HEALTH_CHECK_INTERVAL: Seconds between health checks (default: 60)
    - LATENCY_WINDOW_SIZE: Number of requests for latency average (default: 100)
"""

import enum
import json
import random
import time
from dataclasses import dataclass
from typing import Any, Optional

import redis
from loguru import logger


class RoutingStrategy(enum.Enum):
    """Load balancing routing strategies."""

    ROUND_ROBIN = "round_robin"  # Simple round-robin
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # Weighted by capacity
    HEALTH_WEIGHTED = "health_weighted"  # Weighted by health scores
    LATENCY_BASED = "latency_based"  # Route to fastest provider
    COST_OPTIMIZED = "cost_optimized"  # Minimize costs
    CAPACITY_AWARE = "capacity_aware"  # Consider rate limits
    LEAST_LOADED = "least_loaded"  # Route to least busy provider
    TOKEN_AWARE = "token_aware"  # Consider context window requirements
    HYBRID = "hybrid"  # Combine multiple factors


@dataclass
class ProviderMetrics:
    """
    Real-time metrics for a provider.

    Attributes:
        provider_name: Provider identifier
        health_score: Health score 0.0-1.0 (1.0 = perfectly healthy)
        avg_latency_ms: Average response latency in milliseconds
        error_rate: Error rate 0.0-1.0
        current_load: Current concurrent requests
        rate_limit_remaining: Requests remaining in current window
        cost_per_1k_tokens: Cost per 1000 tokens
        capacity_score: Available capacity 0.0-1.0
        last_updated: Timestamp of last metric update
    """

    provider_name: str
    health_score: float = 1.0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    current_load: int = 0
    rate_limit_remaining: Optional[int] = None
    cost_per_1k_tokens: float = 0.0
    capacity_score: float = 1.0
    last_updated: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "provider_name": self.provider_name,
            "health_score": self.health_score,
            "avg_latency_ms": self.avg_latency_ms,
            "error_rate": self.error_rate,
            "current_load": self.current_load,
            "rate_limit_remaining": self.rate_limit_remaining,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "capacity_score": self.capacity_score,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderMetrics":
        """Create from dictionary."""
        return cls(**data)


class LoadBalancer:
    """
    Advanced load balancer with multiple routing strategies.

    Tracks provider metrics in real-time and makes intelligent routing
    decisions based on health, latency, cost, and capacity.
    """

    def __init__(
        self,
        redis_host: str = "127.0.0.1",
        redis_port: int = 6379,
        health_check_interval: int = 60,
        latency_window_size: int = 100,
    ):
        """
        Initialize load balancer.

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            health_check_interval: Seconds between health checks
            latency_window_size: Number of requests for latency average
        """
        self.health_check_interval = health_check_interval
        self.latency_window_size = latency_window_size

        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=3,  # Separate database for load balancer
                decode_responses=True,
            )
            self.redis_client.ping()
            logger.info("Load balancer connected to Redis", host=redis_host, port=redis_port)
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis for load balancer: {e}")
            raise

        # Round-robin state
        self.round_robin_index = {}

    def _get_metrics_key(self, provider: str) -> str:
        """Get Redis key for provider metrics."""
        return f"lb_metrics::{provider}"

    def _get_latency_key(self, provider: str) -> str:
        """Get Redis key for latency tracking."""
        return f"lb_latency::{provider}"

    def update_metrics(
        self,
        provider: str,
        health_score: Optional[float] = None,
        latency_ms: Optional[float] = None,
        error: bool = False,
        rate_limit_remaining: Optional[int] = None,
        cost_per_1k_tokens: Optional[float] = None,
    ) -> None:
        """
        Update provider metrics.

        Args:
            provider: Provider identifier
            health_score: New health score (0.0-1.0)
            latency_ms: Request latency in milliseconds
            error: Whether request resulted in error
            rate_limit_remaining: Requests remaining in rate limit window
            cost_per_1k_tokens: Cost per 1000 tokens
        """
        metrics_key = self._get_metrics_key(provider)

        # Get existing metrics or create new
        metrics_data = self.redis_client.get(metrics_key)
        if metrics_data:
            metrics = ProviderMetrics.from_dict(json.loads(metrics_data))
        else:
            metrics = ProviderMetrics(provider_name=provider)

        # Update fields
        if health_score is not None:
            metrics.health_score = health_score

        if latency_ms is not None:
            # Update average latency using moving average
            latency_key = self._get_latency_key(provider)
            self.redis_client.lpush(latency_key, latency_ms)
            self.redis_client.ltrim(latency_key, 0, self.latency_window_size - 1)

            latencies = [float(l) for l in self.redis_client.lrange(latency_key, 0, -1)]
            metrics.avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0

        if error:
            # Exponentially decaying error rate
            metrics.error_rate = metrics.error_rate * 0.9 + 0.1
        else:
            metrics.error_rate = metrics.error_rate * 0.9

        if rate_limit_remaining is not None:
            metrics.rate_limit_remaining = rate_limit_remaining
            # Calculate capacity score based on remaining quota
            max_limit = 1000  # Assumed max, could be configured
            metrics.capacity_score = rate_limit_remaining / max_limit

        if cost_per_1k_tokens is not None:
            metrics.cost_per_1k_tokens = cost_per_1k_tokens

        metrics.last_updated = time.time()

        # Store updated metrics
        self.redis_client.setex(
            metrics_key,
            self.health_check_interval * 2,  # TTL
            json.dumps(metrics.to_dict()),
        )

    def get_metrics(self, provider: str) -> Optional[ProviderMetrics]:
        """
        Get current metrics for provider.

        Args:
            provider: Provider identifier

        Returns:
            ProviderMetrics or None: Current metrics if available
        """
        metrics_key = self._get_metrics_key(provider)
        metrics_data = self.redis_client.get(metrics_key)

        if metrics_data:
            return ProviderMetrics.from_dict(json.loads(metrics_data))
        return None

    def select_provider(
        self,
        providers: list[str],
        strategy: RoutingStrategy = RoutingStrategy.HEALTH_WEIGHTED,
        context_tokens: int = 0,
        **kwargs
    ) -> Optional[str]:
        """
        Select best provider using specified strategy.

        Args:
            providers: List of available provider names
            strategy: Routing strategy to use
            context_tokens: Number of context tokens in request
            **kwargs: Additional parameters for specific strategies

        Returns:
            str or None: Selected provider name, or None if none available
        """
        if not providers:
            return None

        if len(providers) == 1:
            return providers[0]

        # Route to appropriate strategy
        if strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin(providers)

        elif strategy == RoutingStrategy.HEALTH_WEIGHTED:
            return self._health_weighted(providers)

        elif strategy == RoutingStrategy.LATENCY_BASED:
            return self._latency_based(providers)

        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._cost_optimized(providers, context_tokens)

        elif strategy == RoutingStrategy.CAPACITY_AWARE:
            return self._capacity_aware(providers)

        elif strategy == RoutingStrategy.LEAST_LOADED:
            return self._least_loaded(providers)

        elif strategy == RoutingStrategy.TOKEN_AWARE:
            return self._token_aware(providers, context_tokens)

        elif strategy == RoutingStrategy.HYBRID:
            return self._hybrid(providers, context_tokens, **kwargs)

        else:
            logger.warning(f"Unknown strategy: {strategy}, using round-robin")
            return self._round_robin(providers)

    def _round_robin(self, providers: list[str]) -> str:
        """Simple round-robin selection."""
        key = ",".join(sorted(providers))
        index = self.round_robin_index.get(key, 0)
        selected = providers[index % len(providers)]
        self.round_robin_index[key] = index + 1
        return selected

    def _health_weighted(self, providers: list[str]) -> str:
        """Select provider weighted by health scores."""
        weights = []
        for provider in providers:
            metrics = self.get_metrics(provider)
            health = metrics.health_score if metrics else 0.5
            weights.append(max(0.1, health))  # Minimum weight to allow recovery

        return random.choices(providers, weights=weights, k=1)[0]

    def _latency_based(self, providers: list[str]) -> str:
        """Select provider with lowest latency."""
        provider_latencies = []

        for provider in providers:
            metrics = self.get_metrics(provider)
            latency = metrics.avg_latency_ms if metrics else float("inf")
            provider_latencies.append((provider, latency))

        # Sort by latency (ascending)
        provider_latencies.sort(key=lambda x: x[1])

        # Return provider with lowest latency
        return provider_latencies[0][0]

    def _cost_optimized(self, providers: list[str], tokens: int) -> str:
        """Select provider with lowest cost for this request."""
        provider_costs = []

        for provider in providers:
            metrics = self.get_metrics(provider)
            cost_per_1k = metrics.cost_per_1k_tokens if metrics else 1.0
            total_cost = (tokens / 1000.0) * cost_per_1k
            provider_costs.append((provider, total_cost))

        # Sort by cost (ascending)
        provider_costs.sort(key=lambda x: x[1])

        # Return cheapest provider
        return provider_costs[0][0]

    def _capacity_aware(self, providers: list[str]) -> str:
        """Select provider with most available capacity."""
        provider_capacity = []

        for provider in providers:
            metrics = self.get_metrics(provider)
            capacity = metrics.capacity_score if metrics else 0.5
            provider_capacity.append((provider, capacity))

        # Sort by capacity (descending)
        provider_capacity.sort(key=lambda x: x[1], reverse=True)

        # Return provider with most capacity
        return provider_capacity[0][0]

    def _least_loaded(self, providers: list[str]) -> str:
        """Select provider with least current load."""
        provider_loads = []

        for provider in providers:
            metrics = self.get_metrics(provider)
            load = metrics.current_load if metrics else 0
            provider_loads.append((provider, load))

        # Sort by load (ascending)
        provider_loads.sort(key=lambda x: x[1])

        # Return least loaded provider
        return provider_loads[0][0]

    def _token_aware(self, providers: list[str], context_tokens: int) -> str:
        """Select provider based on context window requirements."""
        # Filter providers that can handle this context size
        suitable_providers = []

        # Context window sizes (hardcoded, could be from config)
        context_limits = {
            "openai": 128000,  # GPT-4 Turbo
            "anthropic": 200000,  # Claude 3
            "ollama": 8192,  # Local models
            "vllm-qwen": 4096,  # vLLM configured limit
        }

        for provider in providers:
            limit = context_limits.get(provider, 8192)  # Default 8K
            if context_tokens <= limit:
                suitable_providers.append(provider)

        if not suitable_providers:
            logger.warning(
                "No providers can handle context size",
                tokens=context_tokens,
                providers=providers,
            )
            return providers[0]  # Fallback

        # Among suitable providers, use health-weighted selection
        return self._health_weighted(suitable_providers)

    def _hybrid(
        self,
        providers: list[str],
        context_tokens: int,
        health_weight: float = 0.4,
        latency_weight: float = 0.3,
        cost_weight: float = 0.2,
        capacity_weight: float = 0.1,
    ) -> str:
        """
        Hybrid strategy combining multiple factors.

        Args:
            providers: Available providers
            context_tokens: Request context size
            health_weight: Weight for health score
            latency_weight: Weight for latency
            cost_weight: Weight for cost
            capacity_weight: Weight for capacity

        Returns:
            str: Selected provider
        """
        scores = []

        for provider in providers:
            metrics = self.get_metrics(provider)

            if not metrics:
                scores.append((provider, 0.5))
                continue

            # Normalize each factor to 0-1 scale
            health = metrics.health_score

            # Latency (invert so lower is better)
            max_latency = 5000  # 5 seconds max
            latency = 1.0 - min(metrics.avg_latency_ms / max_latency, 1.0)

            # Cost (invert so lower is better)
            max_cost = 0.1  # $0.1 per 1K tokens max
            cost = 1.0 - min(metrics.cost_per_1k_tokens / max_cost, 1.0)

            # Capacity
            capacity = metrics.capacity_score

            # Weighted sum
            total_score = (
                health * health_weight
                + latency * latency_weight
                + cost * cost_weight
                + capacity * capacity_weight
            )

            scores.append((provider, total_score))

        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)

        selected = scores[0][0]
        logger.info(
            "Hybrid routing selected provider",
            provider=selected,
            score=f"{scores[0][1]:.3f}",
        )

        return selected

    def increment_load(self, provider: str) -> None:
        """Increment current load for provider."""
        metrics = self.get_metrics(provider)
        if metrics:
            metrics.current_load += 1
            self.redis_client.setex(
                self._get_metrics_key(provider),
                self.health_check_interval * 2,
                json.dumps(metrics.to_dict()),
            )

    def decrement_load(self, provider: str) -> None:
        """Decrement current load for provider."""
        metrics = self.get_metrics(provider)
        if metrics:
            metrics.current_load = max(0, metrics.current_load - 1)
            self.redis_client.setex(
                self._get_metrics_key(provider),
                self.health_check_interval * 2,
                json.dumps(metrics.to_dict()),
            )


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load Balancer Testing")
    parser.add_argument("--test", action="store_true", help="Run test selection")
    parser.add_argument("--update-metrics", type=str, help="Update metrics for provider")
    parser.add_argument("--view-metrics", type=str, help="View metrics for provider")

    args = parser.parse_args()

    lb = LoadBalancer()

    if args.test:
        providers = ["openai", "anthropic", "ollama", "vllm-qwen"]

        print("Testing different routing strategies:\n")

        for strategy in RoutingStrategy:
            selected = lb.select_provider(providers, strategy, context_tokens=5000)
            print(f"{strategy.value:20s} -> {selected}")

    elif args.update_metrics:
        # Simulate metrics update
        lb.update_metrics(
            args.update_metrics,
            health_score=0.95,
            latency_ms=250.0,
            cost_per_1k_tokens=0.005,
        )
        print(f"Updated metrics for {args.update_metrics}")

    elif args.view_metrics:
        metrics = lb.get_metrics(args.view_metrics)
        if metrics:
            print(json.dumps(metrics.to_dict(), indent=2))
        else:
            print(f"No metrics available for {args.view_metrics}")
