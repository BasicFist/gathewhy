#!/usr/bin/env python3
"""
LiteLLM Provider Comparison Tool
Compare performance across different providers and models.
"""

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass

import requests


@dataclass
class ProviderBenchmark:
    """Benchmark result for a provider/model."""

    provider: str
    model: str
    iterations: int
    successful: int
    failed: int
    mean_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    mean_tokens_per_second: float
    total_tokens: int
    errors: list[str]


class ProviderComparator:
    """Compare performance across providers."""

    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url.rstrip("/")
        self.results: list[ProviderBenchmark] = []

    def benchmark_model(self, model: str, prompt: str, iterations: int = 10) -> ProviderBenchmark:
        """Benchmark a single model."""

        print(f"\n🔬 Benchmarking: {model}")
        print(f"   Iterations: {iterations}")

        latencies = []
        token_speeds = []
        total_tokens = 0
        errors = []

        for i in range(iterations):
            start_time = time.time()

            try:
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 100,
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=120,
                )

                latency = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    tokens = data.get("usage", {}).get("completion_tokens", 0)
                    total_tokens += tokens

                    if tokens > 0 and latency > 0:
                        tokens_per_second = tokens / (latency / 1000)
                        token_speeds.append(tokens_per_second)

                    latencies.append(latency)

                    print(
                        f"   Request {i+1:2d}: {latency:6.0f}ms "
                        f"({tokens} tokens, "
                        f"{tokens_per_second if tokens > 0 else 0:.1f} t/s) ✅"
                    )
                else:
                    error_msg = f"HTTP {response.status_code}"
                    errors.append(error_msg)
                    print(f"   Request {i+1:2d}: {error_msg} ❌")

            except Exception as e:
                error_msg = str(e)
                errors.append(error_msg)
                print(f"   Request {i+1:2d}: {error_msg[:50]} ❌")

        # Calculate statistics
        if latencies:
            sorted_latencies = sorted(latencies)
            mean_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)
            p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            min_latency = min(latencies)
            max_latency = max(latencies)
        else:
            mean_latency = median_latency = p95_latency = 0
            min_latency = max_latency = 0

        mean_tps = statistics.mean(token_speeds) if token_speeds else 0

        # Determine provider from model name
        provider = "unknown"
        if "vllm" in model.lower():
            provider = "vLLM"
        elif "cpp" in model.lower() or "instruct" in model.lower():
            provider = "llama.cpp"
        else:
            provider = "Ollama"

        return ProviderBenchmark(
            provider=provider,
            model=model,
            iterations=iterations,
            successful=len(latencies),
            failed=len(errors),
            mean_latency_ms=mean_latency,
            median_latency_ms=median_latency,
            p95_latency_ms=p95_latency,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            mean_tokens_per_second=mean_tps,
            total_tokens=total_tokens,
            errors=errors,
        )

    def compare_models(self, models: list[str], prompt: str, iterations: int = 10) -> None:
        """Compare multiple models."""

        print("🏁 Provider Comparison")
        print(f"   Models: {', '.join(models)}")
        print(f"   Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
        print(f"   Iterations per model: {iterations}")

        for model in models:
            result = self.benchmark_model(model, prompt, iterations)
            self.results.append(result)
            time.sleep(1)  # Brief pause between models

        self.print_comparison()

    def print_comparison(self) -> None:
        """Print comparison table."""

        if not self.results:
            print("\nNo results to compare")
            return

        print("\n" + "=" * 120)
        print("📊 PROVIDER COMPARISON")
        print("=" * 120)

        # Table header
        print(
            f"\n{'Provider':<12} | {'Model':<25} | "
            f"{'Success':<7} | {'Median (ms)':>11} | {'P95 (ms)':>9} | "
            f"{'Tokens/s':>9} | {'Total Tokens':>12}"
        )
        print("-" * 120)

        # Sort by median latency (fastest first)
        sorted_results = sorted(
            self.results,
            key=lambda r: r.median_latency_ms if r.median_latency_ms > 0 else float("inf"),
        )

        for result in sorted_results:
            success_rate = (
                (result.successful / result.iterations) * 100 if result.iterations > 0 else 0
            )

            print(
                f"{result.provider:<12} | {result.model:<25} | "
                f"{success_rate:6.1f}% | "
                f"{result.median_latency_ms:11.0f} | "
                f"{result.p95_latency_ms:9.0f} | "
                f"{result.mean_tokens_per_second:9.1f} | "
                f"{result.total_tokens:12d}"
            )

        # Summary statistics
        print("\n" + "=" * 120)
        print("📈 SUMMARY")
        print("=" * 120)

        successful_results = [r for r in self.results if r.successful > 0]

        if successful_results:
            fastest = min(successful_results, key=lambda r: r.median_latency_ms)
            slowest = max(successful_results, key=lambda r: r.median_latency_ms)
            fastest_tokens = max(successful_results, key=lambda r: r.mean_tokens_per_second)

            print(
                f"\n🏆 Fastest (median latency): {fastest.model} "
                f"({fastest.median_latency_ms:.0f}ms)"
            )

            print(
                f"🐌 Slowest (median latency): {slowest.model} "
                f"({slowest.median_latency_ms:.0f}ms)"
            )

            print(
                f"🚀 Fastest generation: {fastest_tokens.model} "
                f"({fastest_tokens.mean_tokens_per_second:.1f} tokens/s)"
            )

            speedup = (
                slowest.median_latency_ms / fastest.median_latency_ms
                if fastest.median_latency_ms > 0
                else 1
            )
            print(f"\n📊 Speedup (fastest vs slowest): {speedup:.2f}x")

        # Provider averages
        provider_stats = {}
        for result in successful_results:
            if result.provider not in provider_stats:
                provider_stats[result.provider] = []
            provider_stats[result.provider].append(result.median_latency_ms)

        if provider_stats:
            print("\n📋 Provider Averages:")
            for provider in sorted(provider_stats.keys()):
                avg_latency = statistics.mean(provider_stats[provider])
                print(f"   {provider:12s}: {avg_latency:6.0f} ms (median)")

    def export_json(self, output_file: str) -> None:
        """Export comparison results to JSON."""
        data = {"results": [asdict(r) for r in self.results], "timestamp": time.time()}

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n📁 Exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Compare LiteLLM provider performance")
    parser.add_argument("--url", default="http://localhost:4000", help="LiteLLM base URL")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["llama3.1:8b", "llama-3.1-8b-instruct", "qwen-coder-vllm"],
        help="Models to compare",
    )
    parser.add_argument(
        "--prompt", default="Write a Python function to calculate factorial.", help="Test prompt"
    )
    parser.add_argument("--iterations", type=int, default=10, help="Iterations per model")
    parser.add_argument("--export", type=str, help="Export results to JSON file")

    args = parser.parse_args()

    comparator = ProviderComparator(base_url=args.url)

    try:
        comparator.compare_models(
            models=args.models, prompt=args.prompt, iterations=args.iterations
        )

        if args.export:
            comparator.export_json(args.export)

    except KeyboardInterrupt:
        print("\n\n⚠️  Comparison interrupted")
        if comparator.results:
            comparator.print_comparison()
        sys.exit(1)


if __name__ == "__main__":
    main()
