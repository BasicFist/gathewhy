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
    auto_refresh = reactive(True)
    refresh_interval = reactive(5.0)

    def render(self) -> str:
        """Render stats bar content."""
        auto_label = (
            f"[green]AUTO[/] {self.refresh_interval:.0f}s"
            if self.auto_refresh
            else "[red]AUTO OFF[/]"
        )
        return (
            f"[cyan]●[/] {self.active_count}/{self.total_count} Active  "
            f"[green]▲[/] CPU: {self.avg_cpu:.1f}%  "
            f"[magenta]■[/] MEM: {self.avg_mem:.1f}%  "
            f"{auto_label}"
        )

    def update_stats(
        self, metrics: list[ServiceMetrics], auto_refresh: bool, refresh_interval: float
    ) -> None:
        """Update stats with current metrics."""
        self.total_count = len(metrics)
        self.active_count = sum(1 for m in metrics if m.status == "active")
        self.avg_cpu = (
            sum(m.cpu_percent for m in metrics) / self.total_count if self.total_count else 0.0
        )
        self.avg_mem = (
            sum(m.memory_percent for m in metrics) / self.total_count if self.total_count else 0.0
        )
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
