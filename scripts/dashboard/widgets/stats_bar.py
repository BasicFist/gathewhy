"""Stats bar widget for AI backend dashboard."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static

from ..models import ServiceMetrics


class StatsBar(Static):
    """Compact statistics bar showing key metrics."""

    active_count = reactive(0)
    total_count = reactive(0)
    avg_cpu = reactive(0.0)
    avg_mem = reactive(0.0)

    def render(self) -> str:
        """Render stats bar content."""
        return (
            f"[cyan]●[/] {self.active_count}/{self.total_count} Active  "
            f"[green]▲[/] CPU: {self.avg_cpu:.1f}%  "
            f"[magenta]■[/] MEM: {self.avg_mem:.1f}%"
        )

    def update_stats(self, metrics: list[ServiceMetrics]) -> None:
        """Update stats with current metrics."""
        self.total_count = len(metrics)
        self.active_count = sum(1 for m in metrics if m.status == "active")
        self.avg_cpu = (
            sum(m.cpu_percent for m in metrics) / self.total_count if self.total_count else 0.0
        )
        self.avg_mem = (
            sum(m.memory_percent for m in metrics) / self.total_count if self.total_count else 0.0
        )
