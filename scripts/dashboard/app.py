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
from textual.widgets import DataTable, Footer, Header, Input

from .config import load_env_config
from .controllers import NavigationController
from .models import GPUOverview, ServiceMetrics
from .monitors import ProviderMonitor
from .state import load_dashboard_state, save_dashboard_state
from .widgets.detail import DetailPanel
from .widgets.layout import DashboardView
from .widgets.service_controls import ServiceControls

logger = logging.getLogger(__name__)


class DashboardApp(App[None]):
    """Interactive command center for AI backend - REDESIGNED.

    Completely redesigned with modern UI, better colors, improved readability,
    and enhanced functionality including vim-style navigation, search,
    global service controls, and real-time alerts.

    New Features:
        - Vim-style navigation (j/k to move, / to search)
        - Instant search across providers
        - Global Start/Stop/Restart controls for the selected service
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
        self.search_query: str = ""
        self.dashboard_view: DashboardView | None = None
        self._controls_alerted = False

        # Try to load previous state
        loaded_state = load_dashboard_state()
        if loaded_state:
            self.metrics, self.selected_key = loaded_state
            logger.info(f"Restored dashboard state with {len(self.metrics)} providers")

    # ========================= LAYOUT =========================

    def compose(self) -> ComposeResult:
        """Compose redesigned dashboard UI layout."""
        self.dashboard_view = DashboardView()
        yield Header(show_clock=True)
        yield self.dashboard_view
        yield Footer()

    # ========================= LIFECYCLE =========================

    def on_mount(self) -> None:
        """Initialize dashboard on mount."""
        logger.info("Dashboard mounted - starting initial metrics collection")

        # Set logging level to DEBUG for GPU monitoring
        logging.getLogger("dashboard.monitors.gpu").setLevel(logging.DEBUG)
        logging.getLogger("dashboard.widgets.gpu_card").setLevel(logging.DEBUG)

        assert self.dashboard_view is not None

        # Initialize navigation controller
        self.nav_controller = NavigationController(self.dashboard_view.service_table)

        # Apply user preferences for layout elements
        self.dashboard_view.configure(self.log_height)
        self.dashboard_view.hide_help()

        self._refresh_table()
        self.refresh_timer = self.set_interval(
            self.refresh_interval, self._refresh_table, pause=not self.auto_refresh_enabled
        )
        self.log_event(f"[cyan]✓[/] Dashboard initialized (refresh: {self.refresh_interval}s)")
        self.add_alert("info", "Dashboard initialized successfully")
        if not self.monitor.system_controls_available:
            self._notify_controls_unavailable()

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
            if self.dashboard_view:
                self.dashboard_view.update_stats(
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
        if self.dashboard_view:
            self.dashboard_view.clear_log()

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
            if self.dashboard_view:
                self.dashboard_view.focus_search()
        except Exception as e:
            logger.debug(f"Error focusing search: {e}")

    def action_blur_search(self) -> None:
        """Blur search input (binding: 'escape')."""
        try:
            self.screen.set_focus(None)
        except Exception as e:
            logger.debug(f"Error blurring search: {e}")

    def action_toggle_help(self) -> None:
        """Toggle the in-app shortcuts and help overlay."""
        try:
            if self.dashboard_view and self.dashboard_view.toggle_help():
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

    def _apply_filters(self) -> None:
        """Apply current search and filter to metrics."""
        filtered = self.metrics

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
            if self.dashboard_view:
                self.dashboard_view.populate_table(self.filtered_metrics, self.selected_key)
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
            if self.dashboard_view:
                self.dashboard_view.update_stats(
                    self.metrics, self.auto_refresh_enabled, float(self.refresh_interval)
                )
                self.dashboard_view.update_overview(self.metrics)
                self.dashboard_view.update_gpu(self.gpu_overview)
                self.dashboard_view.update_detail(self._find_metric(self.selected_key))
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
        if self.dashboard_view:
            self.dashboard_view.write_log(message)

    def add_alert(self, level: Literal["info", "warning", "error"], message: str) -> None:
        """Add alert to alerts panel."""
        if self.dashboard_view:
            self.dashboard_view.add_alert(level, message)

    def _notify_controls_unavailable(self) -> None:
        """Surface a user-facing warning when system controls are disabled."""

        if self._controls_alerted:
            return
        warning = "System controls unavailable: systemctl not present on this platform"
        self.log_event(f"[yellow]⚠[/] {warning}")
        self.add_alert("warning", warning)
        self._controls_alerted = True

    # ========================= EVENT HANDLERS =========================

    @on(DataTable.RowSelected)
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle service table row selection."""
        row_key = getattr(event.row_key, "value", event.row_key)
        key = str(row_key)
        self.selected_key = key
        if self.dashboard_view:
            self.dashboard_view.update_detail(self._find_metric(key))
        self.log_event(
            f"[cyan]👁️[/] Selected: {self._find_metric(key).display if self._find_metric(key) else key}"
        )

    @on(DetailPanel.ServiceAction)
    def handle_service_action(self, event: DetailPanel.ServiceAction) -> None:
        """Handle service control actions."""
        self._execute_service_action(event.action, event.service_key)

    @on(ServiceControls.Request)
    def handle_control_request(self, event: ServiceControls.Request) -> None:
        """Handle top-level service control buttons."""
        if not self.selected_key:
            self.log_event("[yellow]⚠[/] Select a service before issuing controls")
            return
        self._execute_service_action(event.action, self.selected_key)

    def _execute_service_action(self, action: str, service_key: str) -> None:
        logger.info(f"Service action: {action} on {service_key}")
        success = self.monitor.systemctl(service_key, action)

        metric = self._find_metric(service_key)
        display_name = metric.display if metric else service_key

        if success:
            self.log_event(f"[green]✓[/] {action.title()} → {display_name}")
            self.add_alert("info", f"Action '{action}' sent to {display_name}")
            self.set_timer(1.0, self._refresh_table)
        else:
            self.log_event(f"[red]✗[/] Failed: {action} → {display_name}")
            self.add_alert("error", f"Failed to {action} {display_name}")
            if not self.monitor.system_controls_available:
                self._notify_controls_unavailable()
