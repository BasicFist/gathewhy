"""Main dashboard application for AI backend monitoring - REDESIGNED.

This module contains the completely redesigned DashboardApp with modern UI,
better colors, improved readability, and enhanced functionality.
"""

from __future__ import annotations

import logging
from typing import Literal

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Log,
    Static,
)

from .config import load_env_config
from .models import GPUOverview, ServiceMetrics
from .monitors import ProviderMonitor
from .state import load_dashboard_state, save_dashboard_state
from .widgets import DetailPanel, GPUCard, OverviewPanel, ServiceTable

logger = logging.getLogger(__name__)


class SearchBar(Static):
    """Search bar for filtering providers."""

    def compose(self) -> ComposeResult:
        """Compose search bar widgets."""
        with Horizontal(id="search-container"):
            yield Label("🔍", id="search-icon")
            yield Input(placeholder="Search providers... (Press / to focus)", id="search-input")


class AlertsPanel(VerticalScroll):
    """Panel for displaying system alerts and notifications."""

    def compose(self) -> ComposeResult:
        """Compose alerts panel."""
        yield Label("[b]📢 Alerts & Notifications[/b]", id="alerts-title")
        yield Log(id="alerts-log", highlight=True)

    def add_alert(self, level: Literal["info", "warning", "error"], message: str) -> None:
        """Add an alert to the panel.

        Args:
            level: Alert severity level
            message: Alert message
        """
        try:
            log = self.query_one("#alerts-log", Log)
            icons = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}
            colors = {"info": "cyan", "warning": "yellow", "error": "red"}
            icon = icons.get(level, "•")
            color = colors.get(level, "white")
            log.write(f"[{color}]{icon} {message}[/]")
        except Exception as e:
            logger.debug(f"Error adding alert: {e}")


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


class FilterBar(Static):
    """Filter bar for provider status filtering."""

    def compose(self) -> ComposeResult:
        """Compose filter bar."""
        with Horizontal(id="filter-container"):
            yield Label("Filter:", id="filter-label")
            yield Button("All", id="filter-all", variant="primary")
            yield Button("Active", id="filter-active", variant="success")
            yield Button("Degraded", id="filter-degraded", variant="warning")
            yield Button("Inactive", id="filter-inactive", variant="error")


class DashboardApp(App[None]):
    """Interactive command center for AI backend - REDESIGNED.

    Completely redesigned with modern UI, better colors, improved readability,
    and enhanced functionality including vim-style navigation, search, filtering,
    and real-time alerts.

    New Features:
        - Vim-style navigation (j/k to move, / to search)
        - Search and filter providers
        - Real-time alerts panel
        - Better color scheme and readability
        - Keyboard shortcuts for all actions
        - Status indicators with icons
    """

    CSS = """
    /* ============= MODERN DARK THEME ============= */

    Screen {
        background: $surface;
        layout: vertical;
    }

    Header {
        background: $accent;
        color: $text;
        text-style: bold;
    }

    #stats-bar {
        background: #1a1a2e;
        color: $text;
        height: 1;
        padding: 0 2;
        text-style: bold;
    }

    /* ============= SEARCH BAR ============= */

    #search-container {
        height: 3;
        background: #16213e;
        padding: 0 2;
        align: center middle;
    }

    #search-icon {
        width: 3;
        content-align: center middle;
        color: $accent;
        text-style: bold;
    }

    #search-input {
        width: 1fr;
        background: #0f3460;
        border: solid $accent;
    }

    #search-input:focus {
        border: solid $success;
    }

    /* ============= FILTER BAR ============= */

    #filter-container {
        height: 3;
        background: #16213e;
        padding: 0 2;
        align: center middle;
    }

    #filter-label {
        width: auto;
        margin-right: 2;
        color: $accent;
        text-style: bold;
    }

    #filter-container Button {
        margin-right: 1;
    }

    /* ============= MAIN LAYOUT ============= */

    #body {
        layout: grid;
        grid-size: 3;
        grid-columns: 2fr 3fr 2fr;
        height: 1fr;
        padding: 1 2;
        background: $surface;
    }

    /* ============= LEFT COLUMN ============= */

    #left-column {
        layout: vertical;
        background: #0f3460;
        border: thick #00d9ff;
        border-title-color: #00d9ff;
        border-title-style: bold;
    }

    OverviewPanel {
        height: auto;
        background: #16213e;
        color: $text;
        padding: 2;
        margin: 1;
        border: solid #ff006e;
    }

    GPUCard {
        height: auto;
        background: #16213e;
        color: $text;
        padding: 2;
        margin: 1;
        border: solid #8338ec;
    }

    #alerts-panel {
        height: 1fr;
        background: #16213e;
        margin: 1;
        border: solid #fb5607;
        padding: 1;
    }

    #alerts-title {
        color: #fb5607;
        text-style: bold;
        height: auto;
        margin-bottom: 1;
    }

    #alerts-log {
        height: 1fr;
        border: none;
        background: #0f3460;
    }

    /* ============= CENTER COLUMN ============= */

    #center-column {
        layout: vertical;
        border: thick #00ff00;
        border-title-color: #00ff00;
        border-title-style: bold;
    }

    ServiceTable {
        height: 1fr;
        background: #0f3460;
    }

    ServiceTable > .datatable--header {
        background: #16213e;
        color: #00d9ff;
        text-style: bold;
    }

    ServiceTable > .datatable--cursor {
        background: #ff006e 50%;
    }

    /* ============= RIGHT COLUMN ============= */

    #right-column {
        layout: vertical;
        border: thick #ff006e;
        border-title-color: #ff006e;
        border-title-style: bold;
    }

    #detail-panel {
        height: 1fr;
        background: #0f3460;
        padding: 2;
    }

    #detail-actions {
        padding-top: 1;
    }

    #detail-actions Button {
        margin-right: 1;
    }

    #event-log {
        height: 12;
        background: #16213e;
        border: solid #8338ec;
        padding: 1;
        margin-top: 1;
    }

    /* ============= FOOTER ============= */

    Footer {
        background: $accent;
    }

    Footer .footer--key {
        background: $primary;
        color: $text;
    }

    /* ============= COLOR DEFINITIONS ============= */

    $surface: #0a0e27;
    $accent: #00d9ff;
    $text: #e9ecef;
    $primary: #0f3460;
    $success: #00ff00;
    $warning: #ffb703;
    $error: #ff006e;
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("q", "quit", "Quit", priority=True),
        Binding("a", "toggle_auto", "Auto-refresh", priority=True),
        Binding("ctrl+l", "clear_log", "Clear", priority=True),
        Binding("j", "next_row", "Next", show=False),
        Binding("k", "prev_row", "Previous", show=False),
        Binding("/", "focus_search", "Search", priority=True),
        Binding("escape", "blur_search", "Blur", show=False),
        Binding("f", "show_filters", "Filter", priority=True),
    ]

    def __init__(self) -> None:
        """Initialize redesigned dashboard application."""
        super().__init__()

        # Load configuration
        self.http_timeout, self.refresh_interval, self.log_height = load_env_config()

        # Initialize monitor
        self.monitor = ProviderMonitor(http_timeout=self.http_timeout)

        # State
        self.metrics: list[ServiceMetrics] = []
        self.filtered_metrics: list[ServiceMetrics] = []
        self.gpu_overview = GPUOverview(False, [], 0.0, 0.0, 0.0)
        self.selected_key: str | None = None
        self.refresh_timer = None
        self.auto_refresh_enabled = True
        self.current_filter: str = "all"
        self.search_query: str = ""

        # Try to load previous state
        loaded_state = load_dashboard_state()
        if loaded_state:
            self.metrics, self.selected_key = loaded_state
            logger.info(f"Restored dashboard state with {len(self.metrics)} providers")

    # ========================= LAYOUT =========================

    def compose(self) -> ComposeResult:
        """Compose redesigned dashboard UI layout."""
        yield Header(show_clock=True)
        yield StatsBar(id="stats-bar")
        yield SearchBar()
        yield FilterBar()
        with Container(id="body"):
            with Vertical(id="left-column"):
                self.border_title = "📊 Overview & Alerts"
                yield OverviewPanel(id="overview")
                yield GPUCard(id="gpu")
                yield AlertsPanel(id="alerts-panel")
            with Vertical(id="center-column"):
                self.border_title = "🖥️  Providers"
                yield ServiceTable()
            with Vertical(id="right-column"):
                self.border_title = "🔍 Details & Logs"
                yield DetailPanel()
                yield Log(id="event-log", highlight=True)
        yield Footer()

    # ========================= LIFECYCLE =========================

    def on_mount(self) -> None:
        """Initialize dashboard on mount."""
        logger.info("Dashboard mounted - starting initial metrics collection")

        # Set border titles
        self.query_one("#left-column").border_title = "📊 Overview & Alerts"
        self.query_one("#center-column").border_title = "🖥️  Providers"
        self.query_one("#right-column").border_title = "🔍 Details & Logs"

        self._refresh_table()
        self.refresh_timer = self.set_interval(
            self.refresh_interval, self._refresh_table, pause=not self.auto_refresh_enabled
        )
        self.log_event(f"[cyan]✓[/] Dashboard initialized (refresh: {self.refresh_interval}s)")
        self.add_alert("info", "Dashboard initialized successfully")

    def action_quit(self) -> None:
        """Quit application and save state."""
        logger.info("Dashboard shutting down - saving state")
        save_dashboard_state(self.metrics, self.selected_key)
        super().action_quit()

    def action_toggle_auto(self) -> None:
        """Toggle auto-refresh (binding: 'a')."""
        self.auto_refresh_enabled = not self.auto_refresh_enabled
        if self.auto_refresh_enabled:
            self.refresh_timer.resume()
            self.log_event(f"[green]✓[/] Auto-refresh enabled ({self.refresh_interval}s)")
            self.add_alert("info", "Auto-refresh enabled")
        else:
            self.refresh_timer.pause()
            self.log_event("[yellow]⏸[/] Auto-refresh paused")
            self.add_alert("warning", "Auto-refresh paused")

    def action_refresh(self) -> None:
        """Manual refresh (binding: 'r')."""
        self._refresh_table()
        self.log_event("[cyan]🔄[/] Manual refresh completed")

    def action_clear_log(self) -> None:
        """Clear event log (binding: 'ctrl+l')."""
        try:
            self.query_one("#event-log", Log).clear()
        except Exception as e:
            logger.debug(f"Error clearing log: {e}")

    # ========================= VIM NAVIGATION =========================

    def action_next_row(self) -> None:
        """Move to next row (binding: 'j')."""
        try:
            table = self.query_one(ServiceTable)
            if table.cursor_coordinate.row < table.row_count - 1:
                table.move_cursor(row=table.cursor_coordinate.row + 1)
        except Exception as e:
            logger.debug(f"Error moving to next row: {e}")

    def action_prev_row(self) -> None:
        """Move to previous row (binding: 'k')."""
        try:
            table = self.query_one(ServiceTable)
            if table.cursor_coordinate.row > 0:
                table.move_cursor(row=table.cursor_coordinate.row - 1)
        except Exception as e:
            logger.debug(f"Error moving to previous row: {e}")

    # ========================= SEARCH & FILTER =========================

    def action_focus_search(self) -> None:
        """Focus search input (binding: '/')."""
        try:
            search_input = self.query_one("#search-input", Input)
            search_input.focus()
        except Exception as e:
            logger.debug(f"Error focusing search: {e}")

    def action_blur_search(self) -> None:
        """Blur search input (binding: 'escape')."""
        try:
            self.screen.set_focus(None)
        except Exception as e:
            logger.debug(f"Error blurring search: {e}")

    def action_show_filters(self) -> None:
        """Show filter options (binding: 'f')."""
        self.log_event("[cyan]ℹ️[/] Use filter buttons to show: All | Active | Degraded | Inactive")

    @on(Input.Changed, "#search-input")
    def handle_search(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self.search_query = event.value.lower()
        self._apply_filters()

    @on(Button.Pressed, "#filter-all, #filter-active, #filter-degraded, #filter-inactive")
    def handle_filter(self, event: Button.Pressed) -> None:
        """Handle filter button presses."""
        button_id = event.button.id or ""
        self.current_filter = button_id.replace("filter-", "")
        self._apply_filters()
        self.log_event(f"[cyan]🔍[/] Filter: {self.current_filter.title()}")

    def _apply_filters(self) -> None:
        """Apply current search and filter to metrics."""
        filtered = self.metrics

        # Apply status filter
        if self.current_filter != "all":
            filtered = [m for m in filtered if m.status == self.current_filter]

        # Apply search filter
        if self.search_query:
            filtered = [
                m
                for m in filtered
                if self.search_query in m.display.lower() or self.search_query in m.key.lower()
            ]

        self.filtered_metrics = filtered

        # Update table
        try:
            table = self.query_one(ServiceTable)
            table.populate(self.filtered_metrics, self.selected_key)
        except Exception as e:
            logger.debug(f"Error applying filters: {e}")

    # ========================= REFRESH ENGINE =========================

    def _refresh_table(self) -> None:
        """Refresh all dashboard displays."""
        try:
            self.metrics, self.gpu_overview = self.monitor.collect_snapshot()
            active_count = sum(1 for m in self.metrics if m.status == "active")
            degraded_count = sum(1 for m in self.metrics if m.status == "degraded")
            logger.debug(f"Snapshot collected: {active_count}/{len(self.metrics)} active")

            # Check for degraded services and alert
            if degraded_count > 0:
                self.add_alert("warning", f"{degraded_count} service(s) degraded or offline")

        except Exception as e:
            error_msg = f"{type(e).__name__}"
            logger.error(f"Error collecting snapshot: {error_msg}: {e}")
            self.log_event(f"[red]✗[/] Snapshot failed: {error_msg}")
            self.add_alert("error", f"Snapshot collection failed: {error_msg}")
            return

        # Apply filters
        self._apply_filters()

        try:
            # Update stats bar
            self.query_one(StatsBar).update_stats(self.metrics)

            # Update widgets
            self.query_one(OverviewPanel).update_overview(self.metrics)
            self.query_one(GPUCard).update_overview(self.gpu_overview)

            detail = self.query_one(DetailPanel)
            detail.update_details(self._find_metric(self.selected_key))
        except Exception as e:
            error_msg = f"{type(e).__name__}"
            logger.error(f"Error updating displays: {error_msg}: {e}")
            self.log_event(f"[red]✗[/] Display update failed: {error_msg}")

    def _find_metric(self, key: str | None) -> ServiceMetrics | None:
        """Find ServiceMetrics by provider key."""
        if not key:
            return None
        for metric in self.metrics:
            if metric.key == key:
                return metric
        return None

    # ========================= HELPERS =========================

    def log_event(self, message: str) -> None:
        """Log event to event log."""
        try:
            self.query_one("#event-log", Log).write(message)
        except Exception as e:
            logger.debug(f"Error logging event: {e}")

    def add_alert(self, level: Literal["info", "warning", "error"], message: str) -> None:
        """Add alert to alerts panel."""
        try:
            self.query_one(AlertsPanel).add_alert(level, message)
        except Exception as e:
            logger.debug(f"Error adding alert: {e}")

    # ========================= EVENT HANDLERS =========================

    @on(DataTable.RowSelected)
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle service table row selection."""
        row_key = getattr(event.row_key, "value", event.row_key)
        key = str(row_key)
        self.selected_key = key
        self.query_one(DetailPanel).update_details(self._find_metric(key))
        self.log_event(
            f"[cyan]👁️[/] Selected: {self._find_metric(key).display if self._find_metric(key) else key}"
        )

    @on(DetailPanel.ServiceAction)
    def handle_service_action(self, event: DetailPanel.ServiceAction) -> None:
        """Handle service control actions."""
        logger.info(f"Service action: {event.action} on {event.service_key}")
        success = self.monitor.systemctl(event.service_key, event.action)

        metric = self._find_metric(event.service_key)
        display_name = metric.display if metric else event.service_key

        if success:
            self.log_event(f"[green]✓[/] {event.action.title()} → {display_name}")
            self.add_alert("info", f"Action '{event.action}' sent to {display_name}")
            self.set_timer(1.0, self._refresh_table)
        else:
            self.log_event(f"[red]✗[/] Failed: {event.action} → {display_name}")
            self.add_alert("error", f"Failed to {event.action} {display_name}")
