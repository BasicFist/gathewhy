"""Help overlay widget for AI backend dashboard."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static


class HelpOverlay(Static):
    """Fullscreen overlay displaying keyboard shortcuts and tips."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._visible = True

    def compose(self) -> ComposeResult:
        """Compose overlay content."""
        with Vertical(id="help-panel"):
            yield Label("[b cyan]AI Dashboard Shortcuts[/]", id="help-title")
            yield Static(
                "\n".join(
                    [
                        "[green]r[/] → Refresh metrics",
                        "[green]a[/] → Toggle auto-refresh",
                        "[green]/[/] → Focus search",
                        "[green]f[/] → Filter providers",
                        "[green]j[/]/[green]k[/] → Navigate services",
                        "[green]Ctrl+L[/] → Clear event log",
                        "[green]Ctrl+Q[/] → Quit dashboard",
                        "[green]?[/] → Toggle this help overlay",
                    ]
                ),
                id="help-body",
            )
            yield Label("[dim]Press Esc or ? to close[/]", id="help-footer")

    def on_mount(self) -> None:
        """Start hidden by default."""
        self.hide()

    def show(self) -> None:
        """Display the overlay."""
        self._visible = True
        self.display = True
        self.focus()

    def hide(self) -> None:
        """Hide the overlay."""
        self._visible = False
        self.display = False

    def toggle(self) -> None:
        """Toggle overlay visibility."""
        if self._visible:
            self.hide()
        else:
            self.show()

    @property
    def visible(self) -> bool:
        """Current visibility state."""
        return self._visible

    def on_key(self, event: events.Key) -> None:
        """Allow ESC or '?' to close the overlay quickly."""
        if event.key in ("escape", "?") and self._visible:
            self.hide()
            event.stop()
