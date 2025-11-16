#!/usr/bin/env python3
"""Entry point and compatibility layer for the PTUI dashboard."""

from __future__ import annotations

import json
import os as os  # Re-exported for tests that patch ptui_dashboard.os
import subprocess as subprocess  # Re-exported for tests that patch ptui_dashboard.subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ptui_dashboard_core import (
    ASYNC_AVAILABLE,
    AUTO_REFRESH_SECONDS,
    DEFAULT_HTTP_TIMEOUT,
    ActionItem,
    MenuItem,
    Service,
    draw_footer,
    format_latency,
    handle_action_keys,
    handle_menu_keys,
    load_services_from_config as _load_services_from_config,
    render_models,
    render_operations,
    render_overview,
    run_dashboard,
    safe_addstr,
    validate_env_float,
)
from ptui_dashboard_core import monitor as _monitor

SERVICES = _monitor.SERVICES


def _sync_services() -> None:
    """Keep the core monitor module aligned with overridden SERVICES."""

    _monitor.SERVICES = SERVICES


def load_services_from_config() -> list[Service]:
    """Expose configuration loader for legacy tests."""

    services = _load_services_from_config()
    return services


def fetch_json(url: str, timeout: float) -> tuple[dict[str, Any] | None, float | None, str | None]:
    start_time = time.perf_counter()
    try:
        request = Request(url, headers={"User-Agent": "ptui-dashboard"})
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        latency = time.perf_counter() - start_time
        return data, latency, None
    except (HTTPError, URLError, TimeoutError) as exc:
        latency = time.perf_counter() - start_time
        return None, latency, str(exc)
    except Exception as exc:  # pragma: no cover - defensive
        return None, None, str(exc)


def check_service(service: Service, timeout: float) -> dict[str, Any]:
    url = f"{service.url}{service.endpoint}"
    data, latency, error = fetch_json(url, timeout)
    status_ok = data is not None and error is None
    return {"service": service, "status": status_ok, "latency": latency, "error": error}


def get_models(timeout: float) -> dict[str, Any]:
    data, latency, error = fetch_json("http://localhost:4000/v1/models", timeout)
    if not data or "data" not in data:
        return {"models": [], "error": error or "Unable to fetch model list", "latency": latency}

    models = [entry.get("id", "unknown") for entry in data.get("data", [])]
    return {"models": models, "error": None, "latency": latency}


def _summaries(services_status: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    required_ok = sum(1 for entry in services_status if entry["service"].required and entry["status"])
    required_total = sum(1 for entry in services_status if entry["service"].required)
    optional_ok = sum(1 for entry in services_status if not entry["service"].required and entry["status"])
    optional_total = sum(1 for entry in services_status if not entry["service"].required)
    return {"required": (required_ok, required_total), "optional": (optional_ok, optional_total)}


def gather_state(timeout: float) -> dict[str, Any]:
    _sync_services()
    services_status = [check_service(service, timeout) for service in SERVICES]
    models_info = get_models(timeout)
    return {
        "services": services_status,
        "models": models_info,
        "summary": _summaries(services_status),
        "timestamp": datetime.now(),
    }


async def gather_state_async(timeout: float) -> dict[str, Any]:
    _sync_services()
    return await _monitor.gather_state_async(timeout)


def gather_state_smart(timeout: float) -> dict[str, Any]:
    if ASYNC_AVAILABLE:
        _sync_services()
        return _monitor.gather_state_smart(timeout)
    return gather_state(timeout)


def action_refresh_state(_: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    updated_state = gather_state_smart(DEFAULT_HTTP_TIMEOUT)
    mode = "async" if ASYNC_AVAILABLE else "sync"
    return f"Service state refreshed ({mode}).", updated_state


def action_health_probe(_: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    updated_state = gather_state_smart(DEFAULT_HTTP_TIMEOUT)
    summary = updated_state.get("summary", {})
    required_ok, required_total = summary.get("required", (0, 0))
    if required_total == 0 or required_ok == required_total:
        message = "Health probe: all required services online."
    else:
        failing = [
            entry["service"].name
            for entry in updated_state.get("services", [])
            if entry["service"].required and not entry["status"]
        ]
        message = f"Health probe: failing services - {', '.join(failing)}."
    return message, updated_state


VALIDATION_SCRIPT = Path(__file__).resolve().parent / "validate-unified-backend.sh"


def run_validation() -> str:
    script_path = str(VALIDATION_SCRIPT)
    if not os.path.exists(script_path):
        return "Validation script not found."

    try:
        completed = subprocess.run([script_path], capture_output=True, text=True, check=False)
    except Exception as exc:  # pragma: no cover - defensive
        return f"Validation error: {exc}"

    if completed.returncode == 0:
        return "Validation succeeded."
    return f"Validation failed (exit {completed.returncode}). See logs."


def action_run_validation(_: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    return run_validation(), None


ACTION_ITEMS: list[ActionItem] = [
    ActionItem("Refresh State", "Gather latest service and model data.", action_refresh_state),
    ActionItem("Health Probe", "Check required services and report any failures.", action_health_probe),
    ActionItem("Run Validation", "Execute validate-unified-backend.sh.", action_run_validation),
]


__all__ = [
    "ACTION_ITEMS",
    "ASYNC_AVAILABLE",
    "AUTO_REFRESH_SECONDS",
    "DEFAULT_HTTP_TIMEOUT",
    "HTTPError",
    "URLError",
    "ActionItem",
    "MenuItem",
    "Service",
    "SERVICES",
    "action_health_probe",
    "action_refresh_state",
    "action_run_validation",
    "check_service",
    "draw_footer",
    "fetch_json",
    "format_latency",
    "gather_state",
    "gather_state_async",
    "gather_state_smart",
    "get_models",
    "handle_action_keys",
    "handle_menu_keys",
    "load_services_from_config",
    "os",
    "render_models",
    "render_operations",
    "render_overview",
    "run_dashboard",
    "run_validation",
    "safe_addstr",
    "subprocess",
    "urlopen",
    "validate_env_float",
]


def main() -> int:
    """Launch the curses dashboard."""

    return run_dashboard()


if __name__ == "__main__":
    raise SystemExit(main())
