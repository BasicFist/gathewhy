"""Miscellaneous helpers shared across modules."""

from __future__ import annotations


def format_latency(latency: float | None) -> str:
    """Format latency values for human-friendly display."""

    if latency is None:
        return "--"
    if latency >= 1:
        return f"{latency:.2f}s"
    return f"{latency * 1000:.0f}ms"
