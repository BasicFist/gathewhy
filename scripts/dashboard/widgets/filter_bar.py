"""Filter bar widget for AI backend dashboard."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Label, Static


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
