"""Alerts panel widget for AI backend dashboard."""

from __future__ import annotations

import logging
from typing import Literal

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Label, Log

logger = logging.getLogger(__name__)


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
