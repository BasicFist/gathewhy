#!/usr/bin/env python3
"""
LiteLLM Log Analyzer
Analyzes JSON-formatted LiteLLM request logs for debugging and performance analysis.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_log_file(log_path: Path) -> list[dict[str, Any]]:
    """Parse JSON log file and return list of log entries."""
    entries = []
    with open(log_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"⚠️  Line {line_num}: Invalid JSON - {e}", file=sys.stderr)
    return entries


def analyze_errors(entries: list[dict[str, Any]]) -> None:
    """Analyze and display error patterns."""
    errors = [
        e for e in entries if e.get("level") == "ERROR" or "error" in e.get("message", "").lower()
    ]

    if not errors:
        print("✅ No errors found")
        return

    print(f"\n🚨 ERRORS ({len(errors)} total)")
    print("=" * 80)

    # Group by error type
    error_types = Counter()
    error_models = Counter()
    error_providers = Counter()

    for error in errors:
        msg = error.get("message", "")
        error_types[msg] += 1
        error_models[error.get("model", "unknown")] += 1
        error_providers[error.get("api_provider", "unknown")] += 1

    print("\nMost common errors:")
    for error_msg, count in error_types.most_common(10):
        print(f"  {count:>3}x {error_msg[:100]}")

    print("\nErrors by model:")
    for model, count in error_models.most_common(5):
        print(f"  {count:>3}x {model}")

    print("\nErrors by provider:")
    for provider, count in error_providers.most_common(5):
        print(f"  {count:>3}x {provider}")


def analyze_performance(entries: list[dict[str, Any]]) -> None:
    """Analyze request latency and performance."""
    latencies = []
    latency_by_model = defaultdict(list)
    latency_by_provider = defaultdict(list)
    slow_requests = []

    for entry in entries:
        latency = entry.get("latency_ms") or entry.get("duration_ms")
        if latency:
            latencies.append(latency)

            model = entry.get("model", "unknown")
            provider = entry.get("api_provider", "unknown")
            latency_by_model[model].append(latency)
            latency_by_provider[provider].append(latency)

            if latency > 5000:  # > 5 seconds
                slow_requests.append((latency, model, provider, entry.get("request_id", "unknown")))

    if not latencies:
        print("\n⚠️  No latency data found")
        return

    print(f"\n⚡ PERFORMANCE ({len(latencies)} requests)")
    print("=" * 80)

    avg_latency = sum(latencies) / len(latencies)
    sorted_latencies = sorted(latencies)
    p50 = sorted_latencies[len(sorted_latencies) // 2]
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
    p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]

    print("\nOverall latency:")
    print(f"  Average: {avg_latency:.0f} ms")
    print(f"  P50:     {p50:.0f} ms")
    print(f"  P95:     {p95:.0f} ms")
    print(f"  P99:     {p99:.0f} ms")
    print(f"  Min:     {min(latencies):.0f} ms")
    print(f"  Max:     {max(latencies):.0f} ms")

    print("\nLatency by model:")
    for model, model_latencies in sorted(
        latency_by_model.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True
    )[:5]:
        avg = sum(model_latencies) / len(model_latencies)
        print(f"  {avg:>6.0f} ms  {model} ({len(model_latencies)} requests)")

    print("\nLatency by provider:")
    for provider, prov_latencies in sorted(
        latency_by_provider.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True
    ):
        avg = sum(prov_latencies) / len(prov_latencies)
        print(f"  {avg:>6.0f} ms  {provider} ({len(prov_latencies)} requests)")

    if slow_requests:
        print(f"\n🐌 Slow requests (> 5s): {len(slow_requests)}")
        for latency, model, provider, req_id in sorted(slow_requests, reverse=True)[:10]:
            print(f"  {latency:>7.0f} ms  {model:20} {provider:15} {req_id}")


def analyze_usage(entries: list[dict[str, Any]]) -> None:
    """Analyze token usage and request patterns."""
    total_tokens = 0
    tokens_by_model = defaultdict(int)
    requests_by_model = Counter()
    requests_by_provider = Counter()

    for entry in entries:
        tokens = entry.get("total_tokens", 0)
        total_tokens += tokens

        model = entry.get("model", "unknown")
        provider = entry.get("api_provider", "unknown")

        tokens_by_model[model] += tokens
        requests_by_model[model] += 1
        requests_by_provider[provider] += 1

    print(f"\n📊 USAGE ({len(entries)} total requests)")
    print("=" * 80)

    print(f"\nTotal tokens: {total_tokens:,}")

    print("\nRequests by model:")
    for model, count in requests_by_model.most_common(10):
        tokens = tokens_by_model[model]
        avg_tokens = tokens / count if count > 0 else 0
        print(f"  {count:>4}x  {tokens:>10,} tokens (avg {avg_tokens:>6.0f})  {model}")

    print("\nRequests by provider:")
    for provider, count in requests_by_provider.most_common():
        pct = (count / len(entries) * 100) if entries else 0
        print(f"  {count:>4}x ({pct:>5.1f}%)  {provider}")


def trace_request(entries: list[dict[str, Any]], request_id: str) -> None:
    """Trace a specific request through the logs."""
    request_entries = [e for e in entries if e.get("request_id") == request_id]

    if not request_entries:
        print(f"❌ No entries found for request_id: {request_id}")
        return

    print(f"\n🔍 REQUEST TRACE: {request_id}")
    print("=" * 80)

    for entry in sorted(request_entries, key=lambda x: x.get("timestamp", "")):
        timestamp = entry.get("timestamp", "unknown")
        level = entry.get("level", "INFO")
        message = entry.get("message", "")

        print(f"\n[{timestamp}] {level}")
        print(f"  {message}")

        # Show important fields
        for key in ["model", "api_provider", "status_code", "latency_ms", "total_tokens", "error"]:
            if key in entry:
                print(f"  {key}: {entry[key]}")


def main():
    parser = argparse.ArgumentParser(description="Analyze LiteLLM request logs")
    parser.add_argument("log_file", type=Path, help="Path to log file")
    parser.add_argument("--errors", action="store_true", help="Analyze errors only")
    parser.add_argument("--performance", action="store_true", help="Analyze performance only")
    parser.add_argument("--usage", action="store_true", help="Analyze usage only")
    parser.add_argument("--trace", metavar="REQUEST_ID", help="Trace specific request")
    parser.add_argument("--all", action="store_true", help="Show all analyses (default)")

    args = parser.parse_args()

    if not args.log_file.exists():
        print(f"❌ Log file not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    print(f"📖 Reading {args.log_file}...")
    entries = parse_log_file(args.log_file)
    print(f"Found {len(entries)} log entries\n")

    if args.trace:
        trace_request(entries, args.trace)
    elif args.errors:
        analyze_errors(entries)
    elif args.performance:
        analyze_performance(entries)
    elif args.usage:
        analyze_usage(entries)
    else:
        # Show all by default
        analyze_errors(entries)
        analyze_performance(entries)
        analyze_usage(entries)


if __name__ == "__main__":
    main()
