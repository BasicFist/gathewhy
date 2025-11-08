"""Service table widget for AI backend dashboard - REDESIGNED.

Modern service table with icons, better colors, and improved readability.
"""

from __future__ import annotations

from collections.abc import Iterable

from textual.coordinate import Coordinate
from textual.widgets import DataTable

from ..models import ServiceMetrics


class ServiceTable(DataTable):
    """Tabular view displaying all provider services with modern styling.

    Shows provider name, status with icons, CPU/memory usage, response time,
    and model count. Features zebra striping, row selection, and color-coded
    status indicators for better readability.

    Features:
        - Status icons (✓ ⚠ ✗)
        - Color-coded metrics
        - Zebra striping
        - Vim-style navigation support
    """

    def __init__(self) -> None:
        """Initialize service table with columns."""
        super().__init__(zebra_stripes=True)
        self.cursor_type = "row"
        self.show_header = True
        self.add_columns(
            "Provider",
            "Status",
            "CPU",
            "Memory",
            "VRAM",
            "Response",
            "Models",
            "PID",
        )

    def populate(self, metrics: Iterable[ServiceMetrics], selected: str | None) -> None:
        """Populate table with service metrics and restore selection.

        Args:
            metrics: Iterable of ServiceMetrics to display
            selected: Provider key to select, if available
        """
        self.clear()
        metrics = list(metrics)
        selected_index: int | None = None

        for index, metric in enumerate(metrics):
            # Status with icon
            status_icons = {
                "active": "✓",
                "degraded": "⚠",
                "inactive": "✗",
            }
            status_colors = {
                "active": "green",
                "degraded": "yellow",
                "inactive": "red",
            }
            icon = status_icons.get(metric.status, "•")
            color = status_colors.get(metric.status, "white")
            status_text = f"[{color}]{icon} {metric.status.title()}[/]"

            # CPU with color coding
            cpu_color = (
                "red"
                if metric.cpu_percent > 80
                else "yellow"
                if metric.cpu_percent > 50
                else "green"
            )
            cpu_text = f"[{cpu_color}]{metric.cpu_percent:.1f}%[/]"

            # Memory with color coding
            mem_color = (
                "red"
                if metric.memory_percent > 80
                else "yellow"
                if metric.memory_percent > 50
                else "cyan"
            )
            mem_text = f"[{mem_color}]{metric.memory_mb:.0f}MB[/]"

            # VRAM
            vram_text = "-" if not metric.vram_mb else f"[magenta]{metric.vram_mb:.0f}MB[/]"

            # Response time with color coding
            resp_color = (
                "red"
                if metric.response_ms > 1000
                else "yellow"
                if metric.response_ms > 500
                else "green"
            )
            resp_text = f"[{resp_color}]{metric.response_ms:.0f}ms[/]"

            # Models
            models_text = f"[cyan]{metric.models}[/]" if metric.models else "[dim]0[/]"

            # PID
            pid_text = str(metric.pid) if metric.pid else "[dim]n/a[/]"

            self.add_row(
                f"[bold]{metric.display}[/]",
                status_text,
                cpu_text,
                mem_text,
                vram_text,
                resp_text,
                models_text,
                pid_text,
                key=metric.key,
            )

            if selected and metric.key == selected:
                selected_index = index

        if selected_index is not None:
            self.cursor_coordinate = Coordinate(row=selected_index, column=0)
        elif self.row_count:
            self.cursor_coordinate = Coordinate(row=0, column=0)
