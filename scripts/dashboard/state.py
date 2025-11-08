"""State persistence for AI backend dashboard.

This module handles saving and loading dashboard state between sessions,
including provider metrics and UI selections.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from .models import ServiceMetrics

logger = logging.getLogger(__name__)

# State persistence directory and file
STATE_DIR = Path.home() / ".cache" / "ai-dashboard"
STATE_FILE = STATE_DIR / "dashboard_state.json"


def save_dashboard_state(metrics: list[ServiceMetrics], selected_key: str | None) -> bool:
    """Save dashboard state for recovery between sessions.

    Args:
        metrics: List of ServiceMetrics to save
        selected_key: Currently selected provider key

    Returns:
        True if save succeeded, False otherwise
    """
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state = {
            "timestamp": time.time(),
            "selected_key": selected_key,
            "metrics": [m.to_json() for m in metrics],
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        logger.debug(f"Saved dashboard state to {STATE_FILE}")
        return True
    except Exception as e:
        logger.warning(f"Failed to save dashboard state: {type(e).__name__}: {e}")
        return False


def load_dashboard_state() -> tuple[list[ServiceMetrics], str | None] | None:
    """Load dashboard state from previous session.

    Returns:
        Tuple of (metrics list, selected_key) or None if load failed
    """
    if not STATE_FILE.exists():
        return None

    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        metrics = [ServiceMetrics.from_json(m) for m in state.get("metrics", [])]
        selected_key = state.get("selected_key")
        logger.debug(f"Loaded dashboard state from {STATE_FILE}")
        return metrics, selected_key
    except Exception as e:
        logger.warning(f"Failed to load dashboard state: {type(e).__name__}: {e}")
        return None
