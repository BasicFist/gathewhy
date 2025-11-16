"""Modular PTUI dashboard implementation."""

from __future__ import annotations

from .actions import ACTION_ITEMS, action_health_probe, action_refresh_state, action_run_validation, run_validation
from .config import AUTO_REFRESH_SECONDS, DEFAULT_HTTP_TIMEOUT, load_services_from_config, validate_env_float
from .models import ActionItem, MenuItem, Service
from .monitor import (
    ASYNC_AVAILABLE,
    SERVICES,
    check_service,
    check_service_async,
    gather_state,
    gather_state_async,
    gather_state_smart,
    get_models,
    get_models_async,
)
from .network import fetch_json, fetch_json_async
from .ui import (
    draw_footer,
    handle_action_keys,
    handle_menu_keys,
    init_colors,
    render_models,
    render_operations,
    render_overview,
    run_dashboard,
    safe_addstr,
)
from .utils import format_latency

__all__ = [
    "ACTION_ITEMS",
    "ActionItem",
    "MenuItem",
    "Service",
    "ASYNC_AVAILABLE",
    "AUTO_REFRESH_SECONDS",
    "DEFAULT_HTTP_TIMEOUT",
    "SERVICES",
    "action_health_probe",
    "action_refresh_state",
    "action_run_validation",
    "check_service",
    "check_service_async",
    "draw_footer",
    "fetch_json",
    "fetch_json_async",
    "format_latency",
    "gather_state",
    "gather_state_async",
    "gather_state_smart",
    "get_models",
    "get_models_async",
    "handle_action_keys",
    "handle_menu_keys",
    "init_colors",
    "load_services_from_config",
    "render_models",
    "render_operations",
    "render_overview",
    "run_dashboard",
    "run_validation",
    "safe_addstr",
    "validate_env_float",
]
