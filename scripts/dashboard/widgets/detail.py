"""Detail panel widget for AI backend dashboard - REDESIGNED.

Modern detail panel with better visualization and enhanced controls.
"""

from __future__ import annotations

import logging

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Label, Log

from ..models import ServiceMetrics

logger = logging.getLogger(__name__)


class DetailPanel(Vertical):
    """Shows focused service details with modern styling and controls.

    Displays comprehensive metrics for selected service with icons, color-coded
    status, resource usage bars, and enhanced service control buttons.

    Features:
        - Status icons and color coding
        - Resource usage visualization
        - Enhanced button styling
        - Warning/error notifications
        - PID and port information

    Messages:
        ServiceAction: Posted when user clicks a service control button
    """

    class ServiceAction(Message):
        """Message posted when user clicks a service control button.

        Attributes:
            action: Control action (start, stop, restart, enable, disable)
            service_key: Provider key targeted by the action
        """

        def __init__(self, action: str, service_key: str) -> None:
            """Initialize service action message.

            Args:
                action: Service control action
                service_key: Provider key
            """
            super().__init__()
            self.action = action
            self.service_key = service_key

    def __init__(self) -> None:
        """Initialize detail panel."""
        super().__init__(id="detail-panel")
        self._current: ServiceMetrics | None = None

    def compose(self) -> ComposeResult:
        """Compose detail panel widgets.

        Returns:
            Iterator of widget components
        """
        yield Label("[dim]Select a provider to inspect[/]", id="detail-title")
        yield Label(id="detail-status")
        yield Label(id="detail-resources")
        yield Label(id="detail-metadata")
        with Horizontal(id="detail-actions"):
            yield Button("▶️ Start", id="action-start", variant="success")
            yield Button("⏹️ Stop", id="action-stop", variant="error")
            yield Button("🔄 Restart", id="action-restart", variant="warning")
            yield Button("✓ Enable", id="action-enable", variant="primary")
            yield Button("✗ Disable", id="action-disable", variant="primary")
        yield Log(id="detail-notes", highlight=True)

    def update_details(self, metrics: ServiceMetrics | None) -> None:
        """Update detail panel with metrics for selected service.

        Args:
            metrics: ServiceMetrics for the selected provider, or None to clear.
        """
        self._current = metrics

        try:
            title = self.query_one("#detail-title", Label)
            status_label = self.query_one("#detail-status", Label)
            resources_label = self.query_one("#detail-resources", Label)
            metadata_label = self.query_one("#detail-metadata", Label)
            notes_log = self.query_one(Log)
            start_btn = self.query_one("#action-start", Button)
            stop_btn = self.query_one("#action-stop", Button)
            restart_btn = self.query_one("#action-restart", Button)
            enable_btn = self.query_one("#action-enable", Button)
            disable_btn = self.query_one("#action-disable", Button)
        except Exception as e:
            logger.warning(f"Failed to query detail panel widgets: {type(e).__name__}: {e}")
            return

        if not metrics:
            try:
                title.update("[dim]Select a provider to inspect[/]")
                status_label.update("")
                resources_label.update("")
                metadata_label.update("")
                notes_log.clear()
                for button in (start_btn, stop_btn, restart_btn, enable_btn, disable_btn):
                    button.disabled = False
                    button.tooltip = None
            except Exception as e:
                logger.debug(f"Error clearing detail panel: {e}")
            return

        try:
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
            icon = status_icons.get(metrics.status, "•")
            color = status_colors.get(metrics.status, "white")

            # Required indicator
            req_badge = "[cyan]REQUIRED[/]" if metrics.required else "[dim]optional[/]"

            title.update(f"[b cyan]{metrics.display}[/] {req_badge}")

            status_label.update(
                f"[b]Status:[/] [{color}]{icon} {metrics.status.upper()}[/]  "
                f"[b]Response:[/] [cyan]{metrics.response_ms:.0f}ms[/]"
            )

            # Resource usage with color coding
            cpu_color = (
                "red"
                if metrics.cpu_percent > 80
                else "yellow"
                if metrics.cpu_percent > 50
                else "green"
            )
            mem_color = (
                "red"
                if metrics.memory_percent > 80
                else "yellow"
                if metrics.memory_percent > 50
                else "cyan"
            )

            vram_display = (
                f"[magenta]{metrics.vram_mb:.1f} MB ({metrics.vram_percent:.1f}%)[/]"
                if metrics.vram_mb
                else "[dim]n/a[/]"
            )

            resources_label.update(
                f"[b cyan]⚡ Resources[/]\n"
                f"[{cpu_color}]▲[/] CPU: [{cpu_color}]{metrics.cpu_percent:.1f}%[/]  "
                f"[{mem_color}]■[/] Memory: [{mem_color}]{metrics.memory_mb:.1f} MB ({metrics.memory_percent:.1f}%)[/]  "
                f"💾 VRAM: {vram_display}"
            )

            metadata_label.update(
                f"[b cyan]📋 Metadata[/]\n"
                f"Endpoint: [cyan]{metrics.endpoint or 'n/a'}[/]\n"
                f"Port: [cyan]{metrics.port or 'n/a'}[/]  "
                f"Models: [cyan]{metrics.models}[/]  "
                f"PID: [cyan]{metrics.pid or 'n/a'}[/]"
            )

            control_hint = None
            if not metrics.controls_enabled:
                control_hint = "Service controls unavailable for this provider"

            for button in (start_btn, stop_btn, restart_btn, enable_btn, disable_btn):
                button.disabled = not metrics.controls_enabled
                button.tooltip = control_hint if control_hint else None

            notes_log.clear()
            if metrics.notes:
                notes_log.write("[b yellow]⚠️  Warnings & Errors[/]")
                for line in metrics.notes:
                    notes_log.write(f"[red]→[/] {line}")
            else:
                notes_log.write("[green]✓ No warnings recorded[/]")
        except Exception as e:
            logger.warning(f"Error updating detail panel: {type(e).__name__}: {e}")

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed) -> None:
        """Handle button press events for service control.

        Args:
            event: Button press event
        """
        if not self._current:
            return
        if not self._current.controls_enabled:
            event.stop()
            return
        action = event.button.id or ""
        if not action.startswith("action-"):
            return
        self.post_message(self.ServiceAction(action.replace("action-", ""), self._current.key))
