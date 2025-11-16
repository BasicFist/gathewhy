"""Data models used across the PTUI dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Service:
    """Definition of a provider service monitored by the dashboard."""

    name: str
    url: str
    endpoint: str
    required: bool = True


@dataclass
class ActionItem:
    """Quick action exposed inside the operations panel."""

    title: str
    description: str
    handler: Callable[[dict[str, Any]], tuple[str, dict[str, Any] | None]]


@dataclass
class MenuItem:
    """Top-level navigation entry inside the dashboard."""

    title: str
    description: str
    renderer: Callable[[Any, dict[str, Any], int, int, int, int, int | None, bool], None]
    supports_actions: bool = False
