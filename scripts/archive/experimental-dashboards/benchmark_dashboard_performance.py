#!/usr/bin/env python3
"""
Performance benchmark for PTUI dashboard async vs sync architecture.

This script measures the performance difference between synchronous and
asynchronous state gathering to quantify the benefits of async architecture.

Usage:
    python3 benchmark_dashboard_performance.py           # Test current mode
    python3 benchmark_dashboard_performance.py --compare # Test both modes
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from statistics import mean, stdev

# Add scripts directory to path to import ptui_dashboard
sys.path.insert(0, str(Path(__file__).parent))

import ptui_dashboard


def benchmark_gather_state(
    iterations: int = 10, timeout: float = 5.0, mode: str = "current"
) -> dict[str, float]:
    """Benchmark state gathering performance.

    Args:
        iterations: Number of times to run the benchmark
        timeout: Timeout for each request
        mode: "current", "sync", or "async"

    Returns:
        Dictionary with timing statistics (mean, min, max, stdev)
    """
    timings = []

    print(f"Running {iterations} iterations...")
    for i in range(iterations):
        start = time.perf_counter()

        # Select appropriate gathering function based on mode
        if mode == "sync":
            state = ptui_dashboard.gather_state(timeout)
        elif mode == "async":
            state = ptui_dashboard.gather_state_async(timeout)
        else:  # "current"
            state = ptui_dashboard.gather_state_smart(timeout)

        elapsed = time.perf_counter() - start
        timings.append(elapsed)

        # Show progress
        healthy_req = state["summary"]["required"][0]
        total_req = state["summary"]["required"][1]
        print(
            f"  Iteration {i + 1}/{iterations}: {elapsed:.3f}s (services: {healthy_req}/{total_req})"
        )

    return {
        "mean": mean(timings),
        "min": min(timings),
        "max": max(timings),
        "stdev": stdev(timings) if len(timings) > 1 else 0.0,
        "timings": timings,
    }


def format_stats(stats: dict[str, float]) -> str:
    """Format timing statistics for display."""
    return (
        f"Mean: {stats['mean']:.3f}s, "
        f"Min: {stats['min']:.3f}s, "
        f"Max: {stats['max']:.3f}s, "
        f"StdDev: {stats['stdev']:.3f}s"
    )


def run_comparison_benchmark(iterations: int, timeout: float):
    """Run comparison benchmark between sync and async modes."""
    print("=" * 70)
    print("PTUI Dashboard Performance Comparison")
    print("=" * 70)
    print()

    # Check if async is available
    if not ptui_dashboard.ASYNC_AVAILABLE:
        print("✗ Cannot run comparison: aiohttp not installed")
        print("  Install with: pip install -r scripts/ptui_dashboard_requirements.txt")
        return

    print("Configuration:")
    print(f"  Iterations: {iterations}")
    print(f"  Timeout: {timeout}s")
    print(f"  Services: {len(ptui_dashboard.SERVICES)}")
    print()

    # Test SYNC mode
    print("=" * 70)
    print("Testing SYNC mode (sequential requests)...")
    print("=" * 70)
    sync_stats = benchmark_gather_state(iterations=iterations, timeout=timeout, mode="sync")

    print()

    # Test ASYNC mode
    print("=" * 70)
    print("Testing ASYNC mode (concurrent requests)...")
    print("=" * 70)

    # Need to use asyncio.run for async mode
    import asyncio

    async_timings = []
    print(f"Running {iterations} iterations...")
    for i in range(iterations):
        start = time.perf_counter()
        state = asyncio.run(ptui_dashboard.gather_state_async(timeout))
        elapsed = time.perf_counter() - start
        async_timings.append(elapsed)

        healthy_req = state["summary"]["required"][0]
        total_req = state["summary"]["required"][1]
        print(
            f"  Iteration {i + 1}/{iterations}: {elapsed:.3f}s (services: {healthy_req}/{total_req})"
        )

    async_stats = {
        "mean": mean(async_timings),
        "min": min(async_timings),
        "max": max(async_timings),
        "stdev": stdev(async_timings) if len(async_timings) > 1 else 0.0,
        "timings": async_timings,
    }

    # Display comparison
    print()
    print("=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    print()
    print(f"SYNC Mode:  {format_stats(sync_stats)}")
    print(f"ASYNC Mode: {format_stats(async_stats)}")
    print()

    # Calculate speedup
    speedup = sync_stats["mean"] / async_stats["mean"]
    time_saved = sync_stats["mean"] - async_stats["mean"]

    print("Performance Improvement:")
    print(f"  Speedup: {speedup:.2f}x faster")
    print(f"  Time saved: {time_saved:.3f}s per refresh ({time_saved * 1000:.0f}ms)")
    print(
        f"  Efficiency: {(1 - async_stats['mean'] / sync_stats['mean']) * 100:.1f}% reduction in wait time"
    )
    print()

    # Practical impact
    print("Practical Impact:")
    print("  For 100 refreshes:")
    print(f"    SYNC:  {sync_stats['mean'] * 100:.1f}s total")
    print(f"    ASYNC: {async_stats['mean'] * 100:.1f}s total")
    print(f"    Saved: {time_saved * 100:.1f}s ({time_saved * 100 / 60:.1f} minutes)")
    print()


def run_single_benchmark(iterations: int, timeout: float):
    """Run benchmark for current mode only."""
    print("=" * 70)
    print("PTUI Dashboard Performance Benchmark")
    print("=" * 70)
    print()

    # Check if async mode is available
    if ptui_dashboard.ASYNC_AVAILABLE:
        print("✓ Async mode is AVAILABLE (aiohttp installed)")
        print("  Testing with concurrent request execution")
    else:
        print("✗ Async mode is NOT available (aiohttp not installed)")
        print("  Testing with sequential request execution")
    print()

    print("Configuration:")
    print(f"  Iterations: {iterations}")
    print(f"  Timeout: {timeout}s")
    print(f"  Services: {len(ptui_dashboard.SERVICES)}")
    print()

    # Run benchmark
    print("-" * 70)
    print("Running benchmark...")
    print("-" * 70)
    stats = benchmark_gather_state(iterations=iterations, timeout=timeout, mode="current")

    # Display results
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()

    mode = "ASYNC" if ptui_dashboard.ASYNC_AVAILABLE else "SYNC"
    print(f"Mode: {mode}")
    print(f"Statistics: {format_stats(stats)}")
    print()

    # Calculate theoretical comparison
    num_services = len(ptui_dashboard.SERVICES)
    if ptui_dashboard.ASYNC_AVAILABLE:
        print("Performance Analysis:")
        print(f"  With {num_services} services checked concurrently:")
        print(f"    • Total time ≈ slowest individual check (~{stats['mean']:.3f}s)")
        print(f"    • Sequential (sync) would take: ~{num_services}x longer")
        print("    • Architecture advantage: O(1) vs O(N) time complexity")
    else:
        print("Performance Note:")
        print(f"  With {num_services} services checked sequentially:")
        print(f"    • Total time = sum of all checks (~{stats['mean']:.1f}s)")
        print("    • Installing aiohttp would enable concurrent checks")
        print(f"    • Expected speedup with async: ~{num_services:.0f}x faster")
    print()

    # Installation instructions if async not available
    if not ptui_dashboard.ASYNC_AVAILABLE:
        print("=" * 70)
        print("To enable async mode, install dependencies:")
        print("  pip install -r scripts/ptui_dashboard_requirements.txt")
        print("=" * 70)
        print()


def main():
    """Run performance benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark PTUI dashboard performance (async vs sync)"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare sync and async modes side-by-side (requires aiohttp)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of benchmark iterations (default: 10)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Request timeout in seconds (default: 5.0)",
    )

    args = parser.parse_args()

    if args.compare:
        run_comparison_benchmark(args.iterations, args.timeout)
    else:
        run_single_benchmark(args.iterations, args.timeout)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during benchmark: {e}")
        sys.exit(1)
