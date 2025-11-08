"""Overview panel widget for AI backend dashboard - REDESIGNED.

Modern overview panel with better colors, icons, and readability.
"""

from __future__ import annotations

from collections.abc import Iterable

from textual.widgets import Static

from ..models import ServiceMetrics


class OverviewPanel(Static):
    """Displays condensed summary of all services with modern styling.

    Shows count of active/inactive services, average CPU/memory usage,
    and lists any services requiring attention with visual indicators.
    """

    def update_overview(self, metrics: Iterable[ServiceMetrics]) -> None:
        """Update overview with current metrics.

        Args:
            metrics: Iterable of ServiceMetrics to summarize
        """
        metrics = list(metrics)
        total = len(metrics)
        active = sum(1 for m in metrics if m.status == "active")
        degraded = sum(1 for m in metrics if m.status == "degraded")
        inactive = sum(1 for m in metrics if m.status == "inactive")

        avg_cpu = sum(m.cpu_percent for m in metrics) / total if total else 0.0
        avg_mem = sum(m.memory_percent for m in metrics) / total if total else 0.0

        # Build status summary with icons
        status_lines = [
            f"[green]✓ Active:[/] {active}",
            f"[yellow]⚠ Degraded:[/] {degraded}",
            f"[red]✗ Inactive:[/] {inactive}",
        ]

        # Build attention list
        attention_providers = [m for m in metrics if m.status != "active"]
        if attention_providers:
            attention_text = "\n".join(
                f"  [yellow]→[/] {m.display} [{m.status}]" for m in attention_providers
            )
        else:
            attention_text = "  [green]All systems operational ✓[/]"

        self.update(
            f"[b cyan]📊 Service Status[/]\n"
            f"{' • '.join(status_lines)}\n\n"
            f"[b cyan]⚡ Resource Usage[/]\n"
            f"[green]▲[/] Average CPU: [bold]{avg_cpu:.1f}%[/]\n"
            f"[magenta]■[/] Average Memory: [bold]{avg_mem:.1f}%[/]\n\n"
            f"[b yellow]⚠️  Attention Required[/]\n"
            f"{attention_text}"
        )
