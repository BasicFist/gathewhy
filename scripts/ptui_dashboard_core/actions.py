"""Action handlers exposed via the operations panel."""

from __future__ import annotations

import subprocess
from typing import Any

from .config import DEFAULT_HTTP_TIMEOUT, SCRIPTS_DIR
from .monitor import ASYNC_AVAILABLE, gather_state_smart
from .models import ActionItem

VALIDATION_SCRIPT = SCRIPTS_DIR / "validate-unified-backend.sh"


def run_validation() -> str:
    """Run the validation script and return a friendly status message."""

    if not VALIDATION_SCRIPT.exists():
        return "Validation script not found."

    try:
        completed = subprocess.run([str(VALIDATION_SCRIPT)], capture_output=True, text=True, check=False)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return f"Validation error: {exc}"

    if completed.returncode == 0:
        return "Validation succeeded."
    return f"Validation failed (exit {completed.returncode}). See logs."


def action_refresh_state(_: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    state = gather_state_smart(DEFAULT_HTTP_TIMEOUT)
    mode = "async" if ASYNC_AVAILABLE else "sync"
    return f"Service state refreshed ({mode}).", state


def action_health_probe(_: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    state = gather_state_smart(DEFAULT_HTTP_TIMEOUT)
    summary = state.get("summary", {})
    required_ok, required_total = summary.get("required", (0, 0))
    if required_total == 0 or required_ok == required_total:
        return "Health probe: all required services online.", state

    failing = [
        entry["service"].name for entry in state.get("services", []) if entry["service"].required and not entry["status"]
    ]
    if failing:
        return f"Health probe: failing services - {', '.join(failing)}.", state
    return "Health probe completed.", state


def action_run_validation(_: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    return run_validation(), None


ACTION_ITEMS: list[ActionItem] = [
    ActionItem("Refresh State", "Gather latest service and model data.", action_refresh_state),
    ActionItem("Health Probe", "Check required services and report any failures.", action_health_probe),
    ActionItem("Run Validation", "Execute validate-unified-backend.sh.", action_run_validation),
]
