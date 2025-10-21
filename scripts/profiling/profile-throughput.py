#!/usr/bin/env python3
"""
LiteLLM Throughput Profiler
Measures concurrent request handling capacity and requests per second.
"""

import argparse
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class ThroughputResult:
    """Throughput measurement result."""

    total_requests: int
    successful: int
    failed: int
    total_duration_s: float
    requests_per_second: float
    mean_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    errors: dict[str, int]


class ThroughputProfiler:
    """Profile concurrent request throughput."""

    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url.rstrip("/")

    def make_request(self, model: str, prompt: str, request_num: int) -> dict[str, Any]:
        """Make a single request and return timing data."""
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 50,
                    "metadata": {"request_num": request_num},
                },
                headers={"Content-Type": "application/json"},
                timeout=120,
            )

            duration = (time.time() - start_time) * 1000

            return {
                "request_num": request_num,
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "latency_ms": duration,
                "error": None if response.status_code == 200 else f"HTTP {response.status_code}",
            }

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "request_num": request_num,
                "success": False,
                "status_code": 0,
                "latency_ms": duration,
                "error": str(e),
            }

    def run_throughput_test(
        self, model: str, prompt: str, total_requests: int, concurrency: int, ramp_up: bool = False
    ) -> ThroughputResult:
        """Run throughput test with specified concurrency."""

        print("\n🚀 Throughput Test")
        print(f"   Model: {model}")
        print(f"   Total requests: {total_requests}")
        print(f"   Concurrency: {concurrency}")
        print(f"   Ramp-up: {ramp_up}")
        print()

        results = []
        start_time = time.time()

        # Progress display
        completed = 0
        print_interval = max(1, total_requests // 20)  # Print 20 updates

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # Submit all requests
            futures = {
                executor.submit(self.make_request, model, prompt, i): i
                for i in range(total_requests)
            }

            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                completed += 1

                if completed % print_interval == 0 or completed == total_requests:
                    elapsed = time.time() - start_time
                    rps = completed / elapsed if elapsed > 0 else 0
                    success_count = sum(1 for r in results if r["success"])
                    success_rate = (success_count / completed) * 100

                    print(
                        f"   Progress: {completed:4d}/{total_requests} "
                        f"({success_rate:5.1f}% success, {rps:6.2f} req/s)"
                    )

        total_duration = time.time() - start_time

        # Calculate statistics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        if successful:
            latencies = [r["latency_ms"] for r in successful]
            sorted_latencies = sorted(latencies)
            mean_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)
            p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        else:
            mean_latency = median_latency = p95_latency = 0

        # Count errors
        errors = {}
        for r in failed:
            error = r.get("error", "Unknown error")
            errors[error] = errors.get(error, 0) + 1

        return ThroughputResult(
            total_requests=total_requests,
            successful=len(successful),
            failed=len(failed),
            total_duration_s=total_duration,
            requests_per_second=total_requests / total_duration,
            mean_latency_ms=mean_latency,
            median_latency_ms=median_latency,
            p95_latency_ms=p95_latency,
            errors=errors,
        )

    def run_concurrency_sweep(
        self,
        model: str,
        prompt: str,
        requests_per_level: int = 50,
        concurrency_levels: list[int] = None,
    ) -> list[ThroughputResult]:
        """Test different concurrency levels to find optimal throughput."""

        if concurrency_levels is None:
            concurrency_levels = [1, 2, 5, 10, 20, 50]

        print("🔬 Concurrency Sweep")
        print(f"   Model: {model}")
        print(f"   Requests per level: {requests_per_level}")
        print(f"   Concurrency levels: {concurrency_levels}")
        print()

        results = []

        for concurrency in concurrency_levels:
            result = self.run_throughput_test(
                model=model,
                prompt=prompt,
                total_requests=requests_per_level,
                concurrency=concurrency,
            )
            results.append(result)

            print(
                f"\n   Concurrency {concurrency:3d}: "
                f"{result.requests_per_second:6.2f} req/s "
                f"(latency: {result.median_latency_ms:6.0f}ms, "
                f"success: {result.successful}/{result.total_requests})"
            )

            # Brief pause between tests
            time.sleep(2)

        return results

    def print_result(self, result: ThroughputResult) -> None:
        """Print throughput test result."""

        print("\n" + "=" * 80)
        print("📊 THROUGHPUT RESULTS")
        print("=" * 80)

        print("\nRequests:")
        print(f"   Total:      {result.total_requests}")
        print(
            f"   Successful: {result.successful} ({result.successful/result.total_requests*100:.1f}%)"
        )
        print(f"   Failed:     {result.failed} ({result.failed/result.total_requests*100:.1f}%)")

        print("\nThroughput:")
        print(f"   Duration:   {result.total_duration_s:.2f} seconds")
        print(f"   RPS:        {result.requests_per_second:.2f} requests/second")

        print("\nLatency:")
        print(f"   Mean:       {result.mean_latency_ms:.0f} ms")
        print(f"   Median:     {result.median_latency_ms:.0f} ms")
        print(f"   P95:        {result.p95_latency_ms:.0f} ms")

        if result.errors:
            print("\nErrors:")
            for error, count in sorted(result.errors.items(), key=lambda x: x[1], reverse=True):
                print(f"   {count:3d}x {error}")

    def print_sweep_summary(self, results: list[ThroughputResult]) -> None:
        """Print summary of concurrency sweep."""

        print("\n" + "=" * 80)
        print("📈 CONCURRENCY SWEEP SUMMARY")
        print("=" * 80)

        print(f"\n{'Concurrency':>12} | {'RPS':>8} | {'Median Latency':>15} | {'Success Rate':>12}")
        print("-" * 80)

        for i, result in enumerate(results):
            concurrency = [1, 2, 5, 10, 20, 50][i] if i < 6 else i + 1
            success_rate = (result.successful / result.total_requests) * 100

            print(
                f"{concurrency:12d} | "
                f"{result.requests_per_second:8.2f} | "
                f"{result.median_latency_ms:12.0f} ms | "
                f"{success_rate:11.1f}%"
            )

        # Find optimal concurrency
        best_result = max(results, key=lambda r: r.requests_per_second)
        best_concurrency = [1, 2, 5, 10, 20, 50][results.index(best_result)]

        print(
            f"\n🎯 Optimal concurrency: ~{best_concurrency} "
            f"({best_result.requests_per_second:.2f} req/s)"
        )


def main():
    parser = argparse.ArgumentParser(description="Profile LiteLLM throughput")
    parser.add_argument("--url", default="http://localhost:4000", help="LiteLLM base URL")
    parser.add_argument("--model", default="llama3.1:8b", help="Model to profile")
    parser.add_argument("--prompt", default="Say hello.", help="Test prompt")
    parser.add_argument("--requests", type=int, default=100, help="Total requests to make")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--sweep", action="store_true", help="Test multiple concurrency levels")

    args = parser.parse_args()

    profiler = ThroughputProfiler(base_url=args.url)

    try:
        if args.sweep:
            results = profiler.run_concurrency_sweep(
                model=args.model, prompt=args.prompt, requests_per_level=args.requests
            )
            profiler.print_sweep_summary(results)
        else:
            result = profiler.run_throughput_test(
                model=args.model,
                prompt=args.prompt,
                total_requests=args.requests,
                concurrency=args.concurrency,
            )
            profiler.print_result(result)

    except KeyboardInterrupt:
        print("\n\n⚠️  Profiling interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()
