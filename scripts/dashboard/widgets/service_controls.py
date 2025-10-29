"""Service control buttons for start/stop/restart actions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, Static

from ..models import ServiceMetrics


class ServiceControls(Static):
    """Top-level controls for managing the selected service."""

    class Request(Message):
        """Message emitted when a control button is pressed."""

        def __init__(self, action: str) -> None:
            self.action = action
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._buttons: dict[str, Button] = {}
        self._current: ServiceMetrics | None = None
        self._status = Static("Select a service to enable controls", id="control-status")

    def compose(self) -> ComposeResult:
        with Horizontal(id="service-controls"):
            yield Button("▶ Start", id="control-start", variant="success")
            yield Button("⏹ Stop", id="control-stop", variant="error")
            yield Button("⟳ Restart", id="control-restart", variant="warning")
            yield self._status

    def on_mount(self) -> None:
        self._buttons = {
            "start": self.query_one("#control-start", Button),
            "stop": self.query_one("#control-stop", Button),
            "restart": self.query_one("#control-restart", Button),
        }
        self._update_buttons()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self._current or not self._current.controls_enabled:
            return
        action = event.button.id or ""
        if action.startswith("control-"):
            self.post_message(self.Request(action.replace("control-", "")))

    def update_state(self, metric: ServiceMetrics | None) -> None:
        """Update enabled state based on selected metric."""
        self._current = metric
        self._update_buttons()

    def _update_buttons(self) -> None:
        if not self._buttons:
            return
        enabled = bool(self._current and self._current.controls_enabled)
        for button in self._buttons.values():
            button.disabled = not enabled
        if not self._status:
            return
        if not self._current:
            self._status.update("[dim]Select a service to enable controls[/]")
        elif not self._current.controls_enabled:
            self._status.update(
                f"[yellow]{self._current.display}[/]\n[dim]Controls unavailable for this service[/]"
            )
        else:
            self._status.update(
                f"[green]{self._current.display}[/]\n[dim]{self._current.status.title()} - ready[/]"
            )
