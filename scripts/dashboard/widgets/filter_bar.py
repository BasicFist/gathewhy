"""Filter bar widget for AI backend dashboard."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Label, Static


class FilterBar(Static):
    """Filter bar for provider status filtering."""

    def __init__(self) -> None:
        """Initialize filter bar and button registry."""
        super().__init__()
        self._buttons: dict[str, Button] = {}

    def compose(self) -> ComposeResult:
        """Compose filter bar."""
        with Horizontal(id="filter-container"):
            yield Label("Filter:", id="filter-label")
            yield Button("All", id="filter-all", variant="primary")
            yield Button("Active", id="filter-active", variant="success")
            yield Button("Degraded", id="filter-degraded", variant="warning")
            yield Button("Inactive", id="filter-inactive", variant="error")

    def on_mount(self) -> None:
        """Cache button references for quick updates."""
        self._buttons = {
            "all": self.query_one("#filter-all", Button),
            "active": self.query_one("#filter-active", Button),
            "degraded": self.query_one("#filter-degraded", Button),
            "inactive": self.query_one("#filter-inactive", Button),
        }
        self.set_active("all")

    def set_active(self, key: str) -> None:
        """Highlight the active status filter button."""
        if not self._buttons:
            return
        for name, button in self._buttons.items():
            button.set_class(name == key, "active-filter")
