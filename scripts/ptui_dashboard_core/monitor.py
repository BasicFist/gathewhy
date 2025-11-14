"""State gathering utilities for the PTUI dashboard."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from .config import load_services_from_config
from .models import Service
from .network import ASYNC_AVAILABLE, fetch_json, fetch_json_async

SERVICES: list[Service] = load_services_from_config()
MODEL_ENDPOINT = "http://localhost:4000/v1/models"


def check_service(service: Service, timeout: float) -> dict[str, Any]:
    """Check service health synchronously."""

    url = f"{service.url}{service.endpoint}"
    data, latency, error = fetch_json(url, timeout)
    status_ok = data is not None and error is None
    return {"service": service, "status": status_ok, "latency": latency, "error": error}


async def check_service_async(session: Any, service: Service, timeout: float) -> dict[str, Any]:
    """Check service health asynchronously using aiohttp."""

    url = f"{service.url}{service.endpoint}"
    data, latency, error = await fetch_json_async(session, url, timeout)
    status_ok = data is not None and error is None
    return {"service": service, "status": status_ok, "latency": latency, "error": error}


def get_models(timeout: float) -> dict[str, Any]:
    """Fetch the LiteLLM model catalog synchronously."""

    data, latency, error = fetch_json(MODEL_ENDPOINT, timeout)
    if not data or "data" not in data:
        return {"models": [], "error": error or "Unable to fetch model list", "latency": latency}

    models = [entry.get("id", "unknown") for entry in data.get("data", [])]
    return {"models": models, "error": None, "latency": latency}


async def get_models_async(session: Any, timeout: float) -> dict[str, Any]:
    """Fetch the LiteLLM model catalog asynchronously."""

    data, latency, error = await fetch_json_async(session, MODEL_ENDPOINT, timeout)
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
    """Gather the latest dashboard state synchronously."""

    services_status = [check_service(service, timeout) for service in SERVICES]
    models_info = get_models(timeout)
    return {"services": services_status, "models": models_info, "summary": _summaries(services_status), "timestamp": datetime.now()}


async def gather_state_async(timeout: float) -> dict[str, Any]:
    """Gather the latest dashboard state asynchronously."""

    import aiohttp  # Local import for optional dependency

    async with aiohttp.ClientSession() as session:
        service_tasks = [check_service_async(session, service, timeout) for service in SERVICES]
        services_status, models_info = await asyncio.gather(asyncio.gather(*service_tasks), get_models_async(session, timeout))
    return {"services": services_status, "models": models_info, "summary": _summaries(services_status), "timestamp": datetime.now()}


def gather_state_smart(timeout: float) -> dict[str, Any]:
    """Gather state using async implementation when possible."""

    if ASYNC_AVAILABLE:
        return asyncio.run(gather_state_async(timeout))
    return gather_state(timeout)
