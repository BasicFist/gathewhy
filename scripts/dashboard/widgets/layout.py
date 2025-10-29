"""Composite layout widget for the AI dashboard UI."""

from __future__ import annotations

from textual.containers import Container, Vertical
from textual.widgets import Input, Log

from ..models import GPUOverview, ServiceMetrics
from .alerts_panel import AlertsPanel
from .detail import DetailPanel
from .gpu_card import GPUCard
from .help import HelpOverlay
from .overview import OverviewPanel
from .search_bar import SearchBar
from .service_controls import ServiceControls
from .stats_bar import StatsBar
from .table import ServiceTable


class DashboardView(Vertical):
    """High-level container that assembles all dashboard widgets."""

    def compose(self):
        yield StatsBar(id="stats-bar")
        yield SearchBar()
        yield ServiceControls(id="service-controls-bar")
        with Container(id="body"):
            with Vertical(id="left-column"):
                yield OverviewPanel(id="overview")
                yield GPUCard(id="gpu")
                yield AlertsPanel(id="alerts-panel")
            with Vertical(id="center-column"):
                yield ServiceTable()
            with Vertical(id="right-column"):
                yield DetailPanel()
                yield Log(id="event-log", highlight=True)
        yield HelpOverlay(id="help-overlay")

    def on_mount(self) -> None:
        self.stats_bar = self.query_one(StatsBar)
        self.search_input = self.query_one("#search-input", Input)
        self.service_controls = self.query_one(ServiceControls)
        self.overview_panel = self.query_one(OverviewPanel)
        self.gpu_card = self.query_one(GPUCard)
        self.alerts_panel = self.query_one(AlertsPanel)
        self.service_table = self.query_one(ServiceTable)
        self.detail_panel = self.query_one(DetailPanel)
        self.event_log = self.query_one("#event-log", Log)
        self.help_overlay = self.query_one(HelpOverlay)

    # ----- configuration -------------------------------------------------
    def configure(self, log_height: int) -> None:
        self.event_log.styles.height = log_height

    def hide_help(self) -> None:
        self.help_overlay.hide()

    def toggle_help(self) -> bool:
        self.help_overlay.toggle()
        return self.help_overlay.visible

    def focus_search(self) -> None:
        self.search_input.focus()

    # ----- update helpers ------------------------------------------------
    def update_stats(
        self, metrics: list[ServiceMetrics], auto_refresh_enabled: bool, refresh_interval: float
    ) -> None:
        self.stats_bar.update_stats(metrics, auto_refresh_enabled, refresh_interval)

    def update_overview(self, metrics: list[ServiceMetrics]) -> None:
        self.overview_panel.update_overview(metrics)

    def update_gpu(self, gpu_overview: GPUOverview) -> None:
        self.gpu_card.update_overview(gpu_overview)

    def update_detail(self, metric: ServiceMetrics | None) -> None:
        self.detail_panel.update_details(metric)
        self.service_controls.update_state(metric)

    def populate_table(self, metrics: list[ServiceMetrics], selected_key: str | None) -> None:
        self.service_table.populate(metrics, selected_key)

    # ----- log and alerts ------------------------------------------------
    def write_log(self, message: str) -> None:
        self.event_log.write(message)

    def clear_log(self) -> None:
        self.event_log.clear()

    def add_alert(self, level: str, message: str) -> None:
        self.alerts_panel.add_alert(level, message)
