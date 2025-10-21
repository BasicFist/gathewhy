#!/usr/bin/env python3
"""
LiteLLM Request Monitor
Real-time monitoring of LiteLLM requests with live updates and filtering.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path


class RequestMonitor:
    """Monitor and display LiteLLM requests in real-time."""

    def __init__(
        self, filter_model=None, filter_provider=None, filter_level=None, show_slow_only=False
    ):
        self.filter_model = filter_model
        self.filter_provider = filter_provider
        self.filter_level = filter_level
        self.show_slow_only = show_slow_only
        self.slow_threshold = 5000  # ms
        self.stats = {
            "total": 0,
            "errors": 0,
            "slow": 0,
        }

    def should_display(self, entry: dict) -> bool:
        """Check if entry should be displayed based on filters."""
        if self.filter_model and entry.get("model") != self.filter_model:
            return False

        if self.filter_provider and entry.get("api_provider") != self.filter_provider:
            return False

        if self.filter_level and entry.get("level") != self.filter_level:
            return False

        if self.show_slow_only:
            latency = entry.get("latency_ms") or entry.get("duration_ms") or 0
            if latency < self.slow_threshold:
                return False

        return True

    def format_entry(self, entry: dict) -> str:
        """Format log entry for display."""
        timestamp = entry.get("timestamp", datetime.now().isoformat())
        level = entry.get("level", "INFO")
        model = entry.get("model", "unknown")
        provider = entry.get("api_provider", "unknown")
        request_id = entry.get("request_id", "no-id")[:8]  # Short ID
        latency = entry.get("latency_ms") or entry.get("duration_ms")
        status = entry.get("status_code", "")
        message = entry.get("message", "")

        # Color codes
        colors = {
            "ERROR": "\033[91m",  # Red
            "WARNING": "\033[93m",  # Yellow
            "INFO": "\033[92m",  # Green
            "DEBUG": "\033[94m",  # Blue
            "RESET": "\033[0m",
        }

        color = colors.get(level, colors["RESET"])
        reset = colors["RESET"]

        # Build formatted line
        parts = [
            f"{color}{timestamp[-12:-4]}{reset}",  # HH:MM:SS
            f"{color}{level:7}{reset}",
            f"[{request_id}]",
            f"{model:20}",
            f"{provider:15}",
        ]

        if latency:
            latency_color = "\033[91m" if latency > self.slow_threshold else reset
            parts.append(f"{latency_color}{latency:>6.0f}ms{reset}")

        if status:
            status_color = "\033[91m" if status >= 400 else "\033[92m"
            parts.append(f"{status_color}{status}{reset}")

        if message:
            parts.append(message[:60])

        return " ".join(parts)

    def update_stats(self, entry: dict) -> None:
        """Update monitoring statistics."""
        self.stats["total"] += 1

        if entry.get("level") == "ERROR":
            self.stats["errors"] += 1

        latency = entry.get("latency_ms") or entry.get("duration_ms") or 0
        if latency > self.slow_threshold:
            self.stats["slow"] += 1

    def print_stats(self) -> None:
        """Print current statistics."""
        print(
            f"\n📊 Stats: {self.stats['total']} total | "
            f"🚨 {self.stats['errors']} errors | "
            f"🐌 {self.stats['slow']} slow (>{self.slow_threshold}ms)"
        )

    def tail_file(self, file_path: Path) -> None:
        """Tail log file and display entries in real-time."""
        print(f"📖 Monitoring: {file_path}")
        print(
            f"🔍 Filters: model={self.filter_model or 'all'} "
            f"provider={self.filter_provider or 'all'} "
            f"level={self.filter_level or 'all'}"
        )
        print("=" * 100)
        print()

        # Open file and seek to end
        with open(file_path) as f:
            f.seek(0, 2)  # Seek to end of file

            while True:
                line = f.readline()
                if line:
                    try:
                        entry = json.loads(line.strip())
                        self.update_stats(entry)

                        if self.should_display(entry):
                            print(self.format_entry(entry))
                            sys.stdout.flush()

                    except json.JSONDecodeError:
                        pass  # Skip invalid JSON
                else:
                    time.sleep(0.1)  # Wait for new data


def main():
    parser = argparse.ArgumentParser(description="Monitor LiteLLM requests in real-time")
    parser.add_argument(
        "log_file",
        type=Path,
        nargs="?",
        default=Path("/var/log/litellm/requests.log"),
        help="Path to log file (default: /var/log/litellm/requests.log)",
    )
    parser.add_argument("--model", help="Filter by model name")
    parser.add_argument("--provider", help="Filter by provider")
    parser.add_argument(
        "--level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Filter by log level"
    )
    parser.add_argument("--slow", action="store_true", help="Show only slow requests (>5s)")
    parser.add_argument(
        "--stats-interval", type=int, default=30, help="Show stats every N seconds (0 to disable)"
    )

    args = parser.parse_args()

    if not args.log_file.exists():
        print(f"❌ Log file not found: {args.log_file}", file=sys.stderr)
        print("💡 Hint: Check if LiteLLM is running and logging is configured", file=sys.stderr)
        sys.exit(1)

    monitor = RequestMonitor(
        filter_model=args.model,
        filter_provider=args.provider,
        filter_level=args.level,
        show_slow_only=args.slow,
    )

    try:
        # Show stats periodically if enabled
        if args.stats_interval > 0:
            import signal

            def show_stats(signum, frame):
                monitor.print_stats()

            signal.signal(signal.SIGALRM, show_stats)
            signal.setitimer(signal.ITIMER_REAL, args.stats_interval, args.stats_interval)

        monitor.tail_file(args.log_file)

    except KeyboardInterrupt:
        monitor.print_stats()
        print("\n\n👋 Monitoring stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
