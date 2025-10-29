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
from textual.containers import Container, Vertical
from textual.widgets import Button, DataTable, Footer, Header, Input, Log

from .config import load_env_config
from .controllers import NavigationController
from .models import GPUOverview, ServiceMetrics
from .monitors import ProviderMonitor
from .state import load_dashboard_state, save_dashboard_state
from .widgets import (
    AlertsPanel,
    DetailPanel,
    FilterBar,
    GPUCard,
    HelpOverlay,
    OverviewPanel,
    SearchBar,
    ServiceTable,
    StatsBar,
)

logger = logging.getLogger(__name__)


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

    # Load external CSS file
    CSS_PATH = "dashboard.tcss"

    BINDINGS = [
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("a", "toggle_auto", "Auto-refresh", priority=True),
        Binding("ctrl+l", "clear_log", "Clear", priority=True),
        Binding("j", "next_row", "Next", show=False),
        Binding("k", "prev_row", "Previous", show=False),
        Binding("/", "focus_search", "Search", priority=True),
        Binding("escape", "blur_search", "Blur", show=False),
        Binding("f", "show_filters", "Filter", priority=True),
        Binding("?", "toggle_help", "Help", priority=True),
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
        yield HelpOverlay(id="help-overlay")

    # ========================= LIFECYCLE =========================

    def on_mount(self) -> None:
        """Initialize dashboard on mount."""
        logger.info("Dashboard mounted - starting initial metrics collection")

        # Set logging level to DEBUG for GPU monitoring
        logging.getLogger("dashboard.monitors.gpu").setLevel(logging.DEBUG)
        logging.getLogger("dashboard.widgets.gpu_card").setLevel(logging.DEBUG)

        # Set border titles
        self.query_one("#left-column").border_title = "📊 Overview & Alerts"
        self.query_one("#center-column").border_title = "🖥️  Providers"
        self.query_one("#right-column").border_title = "🔍 Details & Logs"

        # Initialize navigation controller
        table = self.query_one(ServiceTable)
        self.nav_controller = NavigationController(table)

        # Apply user preferences for layout elements
        try:
            event_log = self.query_one("#event-log", Log)
            event_log.styles.height = self.log_height
        except Exception as e:
            logger.debug(f"Unable to apply log height: {e}")

        try:
            self.query_one(FilterBar).set_active(self.current_filter)
        except Exception as e:
            logger.debug(f"Unable to initialize filter bar state: {e}")

        try:
            self.query_one(HelpOverlay).hide()
        except Exception as e:
            logger.debug(f"Unable to hide help overlay on mount: {e}")

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

        try:
            self.query_one(StatsBar).update_stats(
                self.metrics, self.auto_refresh_enabled, float(self.refresh_interval)
            )
        except Exception as e:
            logger.debug(f"Unable to update stats bar auto-refresh state: {e}")

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
        self.nav_controller.move_next()

    def action_prev_row(self) -> None:
        """Move to previous row (binding: 'k')."""
        self.nav_controller.move_previous()

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

    def action_toggle_help(self) -> None:
        """Toggle the in-app shortcuts and help overlay."""
        try:
            overlay = self.query_one(HelpOverlay)
            overlay.toggle()
            if overlay.visible:
                self.log_event("[cyan]❔[/] Help overlay opened")
            else:
                self.log_event("[cyan]❔[/] Help overlay closed")
        except Exception as e:
            logger.debug(f"Error toggling help overlay: {e}")

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
            self.query_one(FilterBar).set_active(self.current_filter)
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
            self.query_one(StatsBar).update_stats(
                self.metrics, self.auto_refresh_enabled, float(self.refresh_interval)
            )

            # Update widgets
            self.query_one(OverviewPanel).update_overview(self.metrics)

            # Update GPU widget
            gpu_widget = self.query_one(GPUCard)
            if gpu_widget:
                logger.debug(
                    f"Updating GPU widget with detected={self.gpu_overview.detected}, total_used={self.gpu_overview.total_used_mb}"
                )
                gpu_widget.update_overview(self.gpu_overview)
            else:
                logger.warning("GPU Card widget not found")

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
