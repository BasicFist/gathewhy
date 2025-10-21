#!/usr/bin/env python3
"""
LiteLLM Latency Profiler
Measures end-to-end request latency with detailed breakdown and statistics.
"""

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any

import requests


@dataclass
class LatencyMeasurement:
    """Single latency measurement."""

    request_id: str
    model: str
    provider: str
    total_ms: float
    ttfb_ms: float  # Time to first byte
    network_ms: float
    tokens_generated: int
    tokens_per_second: float
    success: bool
    error: str = ""


class LatencyProfiler:
    """Profile request latency with detailed metrics."""

    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url.rstrip("/")
        self.measurements: list[LatencyMeasurement] = []

    def measure_request(self, model: str, prompt: str, max_tokens: int = 100) -> LatencyMeasurement:
        """Measure latency for a single request."""

        request_data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": False,
        }

        # Start timing
        start_time = time.time()
        ttfb = None
        error_msg = ""
        tokens_generated = 0
        success = False

        try:
            # Make request
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=120,
                stream=True,  # Stream to measure TTFB
            )

            # Measure time to first byte
            for _chunk in response.iter_content(chunk_size=1):
                if ttfb is None:
                    ttfb = (time.time() - start_time) * 1000
                break

            # Read rest of response
            response_text = response.content.decode("utf-8")
            total_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = json.loads(response_text)
                tokens_generated = data.get("usage", {}).get("completion_tokens", 0)
                success = True
            else:
                error_msg = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            total_time = (time.time() - start_time) * 1000
            error_msg = "Request timeout"
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            error_msg = str(e)

        # Calculate metrics
        ttfb_ms = ttfb if ttfb else total_time
        network_ms = total_time - ttfb_ms if ttfb else 0
        tokens_per_second = (
            (tokens_generated / (total_time / 1000))
            if total_time > 0 and tokens_generated > 0
            else 0
        )

        # Extract provider from model name (simplified)
        provider = "unknown"
        if "vllm" in model:
            provider = "vllm"
        elif "cpp" in model or "instruct" in model:
            provider = "llamacpp"
        else:
            provider = "ollama"

        measurement = LatencyMeasurement(
            request_id=f"req_{int(time.time() * 1000)}",
            model=model,
            provider=provider,
            total_ms=total_time,
            ttfb_ms=ttfb_ms,
            network_ms=network_ms,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_second,
            success=success,
            error=error_msg,
        )

        self.measurements.append(measurement)
        return measurement

    def run_profile(self, model: str, prompt: str, iterations: int = 10, warmup: int = 2) -> None:
        """Run profiling with multiple iterations."""

        print("🔥 Latency Profiler")
        print(f"   Model: {model}")
        print(f"   Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
        print(f"   Iterations: {iterations} (+ {warmup} warmup)")
        print()

        # Warmup phase
        if warmup > 0:
            print(f"🏃 Warmup phase ({warmup} requests)...")
            for i in range(warmup):
                result = self.measure_request(model, prompt)
                print(f"   Warmup {i+1}: {result.total_ms:.0f}ms", end="")
                print(" ✅" if result.success else f" ❌ {result.error}")

            # Clear warmup measurements
            self.measurements.clear()
            print()

        # Profiling phase
        print(f"📊 Profiling ({iterations} requests)...")
        for i in range(iterations):
            result = self.measure_request(model, prompt)
            print(
                f"   Request {i+1:2d}/{iterations}: "
                f"{result.total_ms:6.0f}ms "
                f"(TTFB: {result.ttfb_ms:5.0f}ms, "
                f"Tokens: {result.tokens_generated:3d}, "
                f"Speed: {result.tokens_per_second:5.1f} t/s)",
                end="",
            )
            print(" ✅" if result.success else f" ❌ {result.error}")

        print()
        self.print_statistics()

    def print_statistics(self) -> None:
        """Print statistical summary of measurements."""

        if not self.measurements:
            print("No measurements recorded")
            return

        successful = [m for m in self.measurements if m.success]
        failed = [m for m in self.measurements if not m.success]

        print("=" * 80)
        print("📈 STATISTICS")
        print("=" * 80)

        # Success rate
        success_rate = (len(successful) / len(self.measurements)) * 100
        print(
            f"\nSuccess rate: {len(successful)}/{len(self.measurements)} " f"({success_rate:.1f}%)"
        )

        if not successful:
            print("\n❌ No successful requests to analyze")
            if failed:
                print("\nFailures:")
                for m in failed:
                    print(f"  - {m.error}")
            return

        # Total latency statistics
        total_latencies = [m.total_ms for m in successful]
        ttfb_latencies = [m.ttfb_ms for m in successful]
        token_speeds = [m.tokens_per_second for m in successful if m.tokens_per_second > 0]

        print("\n⏱️  Total Latency:")
        self._print_stats(total_latencies)

        print("\n⚡ Time to First Byte (TTFB):")
        self._print_stats(ttfb_latencies)

        if token_speeds:
            print("\n🚀 Generation Speed (tokens/second):")
            self._print_stats(token_speeds)

        # Failures
        if failed:
            print(f"\n❌ Failures ({len(failed)}):")
            error_counts = {}
            for m in failed:
                error_counts[m.error] = error_counts.get(m.error, 0) + 1
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {count:2d}x {error}")

    def _print_stats(self, values: list[float]) -> None:
        """Print statistics for a list of values."""
        if not values:
            print("   No data")
            return

        sorted_values = sorted(values)
        n = len(sorted_values)

        stats = {
            "Mean": statistics.mean(sorted_values),
            "Median": statistics.median(sorted_values),
            "Std Dev": statistics.stdev(sorted_values) if n > 1 else 0,
            "Min": min(sorted_values),
            "Max": max(sorted_values),
            "P50": sorted_values[int(n * 0.50)],
            "P90": sorted_values[int(n * 0.90)],
            "P95": sorted_values[int(n * 0.95)],
            "P99": sorted_values[int(n * 0.99)] if n >= 100 else sorted_values[-1],
        }

        for name, value in stats.items():
            print(f"   {name:8s}: {value:8.2f}")

    def export_json(self, output_file: str) -> None:
        """Export measurements to JSON file."""
        data = {
            "measurements": [asdict(m) for m in self.measurements],
            "summary": self._get_summary(),
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n📁 Exported to: {output_file}")

    def _get_summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        successful = [m for m in self.measurements if m.success]

        if not successful:
            return {"success_rate": 0, "total_requests": len(self.measurements)}

        total_latencies = [m.total_ms for m in successful]

        return {
            "total_requests": len(self.measurements),
            "successful": len(successful),
            "failed": len(self.measurements) - len(successful),
            "success_rate": (len(successful) / len(self.measurements)) * 100,
            "mean_latency_ms": statistics.mean(total_latencies),
            "median_latency_ms": statistics.median(total_latencies),
            "p95_latency_ms": sorted(total_latencies)[int(len(total_latencies) * 0.95)],
        }


def main():
    parser = argparse.ArgumentParser(description="Profile LiteLLM request latency")
    parser.add_argument("--url", default="http://localhost:4000", help="LiteLLM base URL")
    parser.add_argument("--model", default="llama3.1:8b", help="Model to profile")
    parser.add_argument("--prompt", default="Count from 1 to 10.", help="Test prompt")
    parser.add_argument("--iterations", type=int, default=10, help="Number of profiling iterations")
    parser.add_argument("--warmup", type=int, default=2, help="Number of warmup requests")
    parser.add_argument("--export", type=str, help="Export results to JSON file")

    args = parser.parse_args()

    profiler = LatencyProfiler(base_url=args.url)

    try:
        profiler.run_profile(
            model=args.model, prompt=args.prompt, iterations=args.iterations, warmup=args.warmup
        )

        if args.export:
            profiler.export_json(args.export)

    except KeyboardInterrupt:
        print("\n\n⚠️  Profiling interrupted")
        if profiler.measurements:
            profiler.print_statistics()
        sys.exit(1)


if __name__ == "__main__":
    main()
