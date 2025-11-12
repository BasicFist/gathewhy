"""Search bar widget for AI backend dashboard."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Label, Static


class SearchBar(Static):
    """Search bar for filtering providers."""

    def compose(self) -> ComposeResult:
        """Compose search bar widgets."""
        with Horizontal(id="search-container"):
            yield Label("🔍", id="search-icon")
            yield Input(placeholder="Search providers... (Press / to focus)", id="search-input")
