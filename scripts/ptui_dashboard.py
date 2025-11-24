#!/usr/bin/env python3
"""
Interactive PTUI dashboard implemented with curses.
Provides a live view of service health, model availability, and key actions.

Performance: Async architecture with aiohttp for concurrent requests.
"""

from __future__ import annotations

import asyncio
import curses
import json
import os
import re  # Moved to top
import subprocess
import sys
import time
import traceback  # Moved to top
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Try to import aiohttp for async operations (optional dependency)
try:
    import aiohttp

    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

# Try to import pynvml for GPU stats
try:
    import pynvml

    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


def validate_env_float(name: str, default: str, min_val: float, max_val: float) -> float:
    """Validate environment variable as float within bounds."""
    value_str = os.getenv(name, default)
    try:
        value = float(value_str)
        if not min_val <= value <= max_val:
            raise ValueError(f"{name} must be {min_val}-{max_val}, got {value}")
        return value
    except ValueError as e:
        print(f"Invalid {name}: {e}. Using default: {default}", file=sys.stderr)
        return float(default)


DEFAULT_HTTP_TIMEOUT = validate_env_float("PTUI_HTTP_TIMEOUT", "10", 0.5, 120.0)
AUTO_REFRESH_SECONDS = validate_env_float("PTUI_REFRESH_SECONDS", "5", 1.0, 60.0)


@dataclass
class Service:
    name: str
    url: str
    endpoint: str
    required: bool = True


@dataclass
class ActionItem:
    title: str
    description: str
    handler: Callable[[dict[str, Any]], tuple[str, dict[str, Any] | None]]


@dataclass
class MenuItem:
    title: str
    description: str
    renderer: Callable[[Any, dict[str, Any], int, int, int, int, int | None, bool], None]
    supports_actions: bool = False


def safe_addstr(
    stdscr: Any,
    y: int,
    x: int,
    text: str,
    width: int,
    attr: int = 0,
) -> None:
    if width <= 0:
        return
    from contextlib import suppress

    with suppress(curses.error):
        stdscr.addnstr(y, x, text.ljust(width), width, attr)


def _resolve_env_var(value: str) -> str:
    """Resolve shell-style env vars like ${VAR:-default}."""
    if not isinstance(value, str):
        return value

    # Match ${VAR:-default} or ${VAR}
    pattern = r"\$\{([A-Z0-9_]+)(?::-(.*?))?\}"
    match = re.match(pattern, value)

    if match:
        var_name = match.group(1)
        default_val = match.group(2) or ""
        return os.environ.get(var_name, default_val)

    return value


def load_services_from_config() -> list[Service]:
    """Load services from config/providers.yaml with fallback to defaults."""
    config_path = Path(__file__).parent.parent / "config" / "providers.yaml"

    # Default fallback services
    default_services = [
        Service("LiteLLM Gateway", "http://localhost:4000", "/health/liveliness", required=True),
        Service("Ollama", "http://localhost:11434", "/api/tags", required=True),
        Service("llama.cpp (Python)", "http://localhost:8000", "/v1/models", required=False),
        Service("llama.cpp (Native)", "http://localhost:8080", "/v1/models", required=False),
        Service("vLLM", "http://localhost:8001", "/v1/models", required=False),
    ]

    if not config_path.exists():
        return default_services

    try:
        # Try to load YAML (only if available)
        try:
            import yaml
        except ImportError:
            return default_services

        with open(config_path) as f:
            config = yaml.safe_load(f)

        if not config or "providers" not in config:
            return default_services

        services = []
        providers = config["providers"]

        # Map provider keys to display names
        provider_map = {
            "ollama": ("Ollama", "/api/tags", True),
            "vllm": ("vLLM", "/v1/models", False),
            "llama_cpp_python": ("llama.cpp (Python)", "/v1/models", False),
            "llama_cpp_native": ("llama.cpp (Native)", "/v1/models", False),
            "litellm_gateway": ("LiteLLM Gateway", "/health/liveliness", True),
        }

        for key, provider_data in providers.items():
            if provider_data.get("status") != "active":
                continue

            raw_url = provider_data.get("base_url", "")
            base_url = _resolve_env_var(raw_url)

            if key in provider_map:
                display_name, endpoint, required = provider_map[key]
            else:
                display_name = provider_data.get("description", key)
                endpoint = "/health"
                required = False

            services.append(Service(display_name, base_url, endpoint, required))

        # Always ensure LiteLLM Gateway is present
        if not any(s.name == "LiteLLM Gateway" for s in services):
            services.insert(
                0, Service("LiteLLM Gateway", "http://localhost:4000", "/health/liveliness", True)
            )

        return services if services else default_services

    except Exception as e:
        print(f"Warning: Failed to load providers config: {e}", file=sys.stderr)
        return default_services


def load_model_mappings() -> dict[str, Any]:
    """Load model mappings from config/model-mappings.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "model-mappings.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml

        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Failed to load model mappings: {e}", file=sys.stderr)
        return {}


MODEL_MAPPINGS = load_model_mappings()

SERVICES: list[Service] = load_services_from_config()


def fetch_json(url: str, timeout: float) -> tuple[dict[str, Any] | None, float | None, str | None]:
    """Fetch JSON from URL (synchronous)."""
    start_time = time.perf_counter()
    try:
        headers = {"User-Agent": "ptui-dashboard"}

        request = Request(url, headers=headers)
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        latency = time.perf_counter() - start_time
        return data, latency, None
    except (HTTPError, URLError, TimeoutError) as exc:
        latency = time.perf_counter() - start_time
        return None, latency, str(exc)
    except Exception as exc:  # pragma: no cover - safety net
        return None, None, str(exc)


async def fetch_json_async(
    session: aiohttp.ClientSession, url: str, timeout: float
) -> tuple[dict[str, Any] | None, float | None, str | None]:
    """Fetch JSON from URL (asynchronous)."""
    start_time = time.perf_counter()
    try:
        headers = {"User-Agent": "ptui-dashboard"}

        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        async with session.get(url, headers=headers, timeout=timeout_obj) as response:
            data = await response.json()
        latency = time.perf_counter() - start_time
        return data, latency, None
    except TimeoutError:
        latency = time.perf_counter() - start_time
        return None, latency, "Request timed out"
    except aiohttp.ClientError as exc:
        latency = time.perf_counter() - start_time
        return None, latency, str(exc)
    except Exception as exc:  # pragma: no cover - safety net
        return None, None, str(exc)


def check_service(service: Service, timeout: float) -> dict[str, Any]:
    """Check service health synchronously."""
    url = f"{service.url}{service.endpoint}"
    data, latency, error = fetch_json(url, timeout)
    status_ok = data is not None and error is None
    return {
        "service": service,
        "status": status_ok,
        "latency": latency,
        "error": error,
    }


async def check_service_async(
    session: aiohttp.ClientSession, service: Service, timeout: float
) -> dict[str, Any]:
    """Check service health asynchronously."""
    url = f"{service.url}{service.endpoint}"
    data, latency, error = await fetch_json_async(session, url, timeout)
    status_ok = data is not None and error is None
    return {
        "service": service,
        "status": status_ok,
        "latency": latency,
        "error": error,
    }


def get_models(timeout: float) -> dict[str, Any]:
    """Fetch model list from LiteLLM gateway (synchronous)."""
    data, latency, error = fetch_json("http://localhost:4000/v1/models", timeout)
    if not data or "data" not in data:
        return {"models": [], "error": error or "Unable to fetch model list", "latency": latency}

    models = [entry.get("id", "unknown") for entry in data.get("data", [])]
    return {"models": models, "error": None, "latency": latency}


async def get_models_async(session: aiohttp.ClientSession, timeout: float) -> dict[str, Any]:
    """Fetch model list from LiteLLM gateway (asynchronous)."""
    data, latency, error = await fetch_json_async(
        session, "http://localhost:4000/v1/models", timeout
    )
    if not data or "data" not in data:
        return {"models": [], "error": error or "Unable to fetch model list", "latency": latency}

    models = [entry.get("id", "unknown") for entry in data.get("data", [])]
    return {"models": models, "error": None, "latency": latency}


def format_latency(latency: float | None) -> str:
    if latency is None:
        return "--"
    if latency >= 1:
        return f"{latency:.2f}s"
    return f"{latency * 1000:.0f}ms"


def run_validation() -> str:
    script_path = os.path.join(os.path.dirname(__file__), "validate-unified-backend.sh")
    if not os.path.exists(script_path):
        return "Validation script not found."

    try:
        completed = subprocess.run(
            [script_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            return "Validation succeeded."
        return f"Validation failed (exit {completed.returncode}). See logs."
    except Exception as exc:  # pragma: no cover
        return f"Validation error: {exc}"


def get_gpu_stats() -> dict[str, Any] | None:
    """Fetch GPU statistics using pynvml."""
    if not GPU_AVAILABLE:
        return None

    try:
        pynvml.nvmlInit()
        # Just get the first GPU for now
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        # pynvml returns bytes in older versions, str in newer. decode if needed
        if isinstance(name, bytes):
            name = name.decode("utf-8")

        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

        return {
            "name": name,
            "memory_used": mem_info.used / 1024**2,  # MB
            "memory_total": mem_info.total / 1024**2,  # MB
            "gpu_util": utilization.gpu,
            "mem_util": utilization.memory,
        }
    except Exception:
        return None
    # We don't shutdown nvml here to keep it efficient for repeated polling


def gather_state(timeout: float) -> dict[str, Any]:
    """Gather all state synchronously (fallback when async not available)."""
    services_status = [check_service(service, timeout) for service in SERVICES]
    models_info = get_models(timeout)
    gpu_stats = get_gpu_stats()

    healthy_required = sum(
        1 for entry in services_status if entry["service"].required and entry["status"]
    )
    total_required = sum(1 for entry in services_status if entry["service"].required)
    healthy_optional = sum(
        1 for entry in services_status if not entry["service"].required and entry["status"]
    )
    total_optional = sum(1 for entry in services_status if not entry["service"].required)

    return {
        "services": services_status,
        "models": models_info,
        "gpu": gpu_stats,
        "summary": {
            "required": (healthy_required, total_required),
            "optional": (healthy_optional, total_optional),
        },
        "timestamp": datetime.now(),
    }


async def gather_state_async(timeout: float) -> dict[str, Any]:
    """Gather all state asynchronously with concurrent requests.

    This is significantly faster than the synchronous version as all
    service health checks run concurrently instead of sequentially.
    """
    async with aiohttp.ClientSession() as session:
        # Create tasks for concurrent execution
        service_tasks = [check_service_async(session, service, timeout) for service in SERVICES]
        models_task = get_models_async(session, timeout)

        # Execute all service checks concurrently + models fetch
        services_status, models_info = await asyncio.gather(
            asyncio.gather(*service_tasks), models_task
        )

    gpu_stats = get_gpu_stats()

    # Calculate summary statistics
    healthy_required = sum(
        1 for entry in services_status if entry["service"].required and entry["status"]
    )
    total_required = sum(1 for entry in services_status if entry["service"].required)
    healthy_optional = sum(
        1 for entry in services_status if not entry["service"].required and entry["status"]
    )
    total_optional = sum(1 for entry in services_status if not entry["service"].required)

    return {
        "services": services_status,
        "models": models_info,
        "gpu": gpu_stats,
        "summary": {
            "required": (healthy_required, total_required),
            "optional": (healthy_optional, total_optional),
        },
        "timestamp": datetime.now(),
    }


def gather_state_smart(timeout: float) -> dict[str, Any]:
    """Gather state using async if available, otherwise fallback to sync.

    This is the main entry point that other code should use.
    """
    if ASYNC_AVAILABLE:
        # Use async version for better performance
        return asyncio.run(gather_state_async(timeout))

    # Fallback to synchronous version
    return gather_state(timeout)


def action_refresh_state(_: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Refresh state action using smart async/sync selection."""
    updated_state = gather_state_smart(DEFAULT_HTTP_TIMEOUT)
    mode = "async" if ASYNC_AVAILABLE else "sync"
    return f"Service state refreshed ({mode}).", updated_state


def action_health_probe(_: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Health probe action using smart async/sync selection."""
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
        if failing:
            message = f"Health probe: failing services - {', '.join(failing)}."
        else:
            message = "Health probe completed."
    return message, updated_state


def action_run_validation(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    message = run_validation()
    return message, None


def call_service_control(alias: str, action: str) -> tuple[bool, str]:
    """Call the local service control API."""
    port = os.environ.get("SERVICE_CONTROL_PORT", "8070")
    url = f"http://localhost:{port}/service/{alias}/{action}"
    try:
        req = Request(url, method="POST")
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("success", False), data.get("message", "Unknown response")
    except Exception as e:
        return False, str(e)


def action_start_vllm(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    success, msg = call_service_control("vllm", "start")
    return f"Start vLLM: {'OK' if success else 'Failed'} ({msg})", None


def action_restart_litellm(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    success, msg = call_service_control("litellm", "restart")
    return f"Restart LiteLLM: {'OK' if success else 'Failed'} ({msg})", None


def action_regenerate_config(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    try:
        subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "generate-litellm-config.py")],
            capture_output=True,
            text=True,
            check=True,
        )
        return "Config regenerated successfully.", None
    except subprocess.CalledProcessError as e:
        return f"Regeneration failed: {e.stderr}", None


def action_inspect_config(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "print-logical-config.py")],
            capture_output=True,
            text=True,
            check=True,
        )
        # Just show success, content is too big for footer
        return f"Config snapshot: {len(result.stdout)} bytes", None
    except subprocess.CalledProcessError as e:
        return f"Inspection failed: {e.stderr}", None


def action_view_logs(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    log_path = Path(__file__).parent.parent / "logs" / "service_control.log"
    if not log_path.exists():
        return "Log file not found.", None

    try:
        # Read last 5 lines
        with open(log_path, "rb") as f:
            # Minimal implementation of tail
            f.seek(0, 2)
            file_size = f.tell()
            lines_to_read = 5
            block_size = 1024
            block_end_byte = file_size
            lines = []

            while block_end_byte > 0 and len(lines) < lines_to_read:
                block_end_byte = max(0, block_end_byte - block_size)
                f.seek(block_end_byte)
                block_data = f.read(min(block_size, file_size - block_end_byte))
                # Split and keep lines
                lines = block_data.decode("utf-8", errors="ignore").splitlines()[-lines_to_read:]

            content = " | ".join(lines)
            return f"Last logs: {content}", None
    except Exception as e:
        return f"Error reading logs: {e}", None


def action_validate_schema(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    try:
        cmd = [sys.executable, "scripts/validate-config-schema.py"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            return "Schema Validation: ✅ PASSED", None

        err_lines = [line for line in result.stdout.splitlines() if "❌" in line or "Error" in line]
        err_msg = err_lines[0] if err_lines else "Unknown error"
        return f"Schema Validation: ❌ FAILED - {err_msg}", None
    except Exception as e:
        return f"Validation error: {e}", None


def action_test_completion(model: str) -> tuple[str, dict[str, Any] | None]:
    cmd = [
        "curl",
        "-s",
        "-X",
        "POST",
        "http://localhost:4000/v1/chat/completions",
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps(
            {"model": model, "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 5}
        ),
    ]
    try:
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        duration = time.time() - start

        if result.returncode != 0:
            return f"Test {model}: Curl failed", None

        try:
            resp = json.loads(result.stdout)
            if "error" in resp:
                err = resp["error"].get("message", str(resp["error"]))
                return f"Test {model}: ❌ API Error ({err[:40]}...)", None

            # content = resp.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            model_used = resp.get("model", "unknown")
            return f"Test {model}: ✅ OK ({duration:.2f}s) via {model_used}", None
        except json.JSONDecodeError:
            return f"Test {model}: ❌ Invalid JSON response", None

    except subprocess.TimeoutExpired:
        return f"Test {model}: ❌ Timeout (>15s)", None
    except Exception as e:
        return f"Test {model}: ❌ Error {e}", None


def action_test_chat(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    return action_test_completion("llama3.1:latest")


def action_test_code(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    return action_test_completion("qwen-coder-vllm")


def action_test_cloud(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    return action_test_completion("gpt-oss:20b-cloud")


def action_switch_vllm_qwen(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    try:
        script = os.path.join(os.path.dirname(__file__), "vllm-model-switch.sh")
        subprocess.Popen([script, "qwen"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Switching vLLM to Qwen (async)...", None
    except Exception as e:
        return f"Switch error: {e}", None


def action_switch_vllm_dolphin(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    try:
        script = os.path.join(os.path.dirname(__file__), "vllm-model-switch.sh")
        subprocess.Popen([script, "dolphin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Switching vLLM to Dolphin (async)...", None
    except Exception as e:
        return f"Switch error: {e}", None


def action_check_budgets(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    db_path = Path(__file__).parent.parent / "runtime" / "usage" / "llm_usage.db"
    if not db_path.exists():
        return "No usage DB found.", None

    try:
        import sqlite3

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(cost_usd), COUNT(*) FROM usage_logs")
            row = cursor.fetchone()
            total_spend = row[0] if row[0] else 0.0
            count = row[1]

            # Get today's spend
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT SUM(cost_usd) FROM usage_logs WHERE timestamp LIKE ?", (f"{today}%",)
            )
            row_today = cursor.fetchone()
            today_spend = row_today[0] if row_today[0] else 0.0

        return f"Total Spend: ${total_spend:.4f} ({count} reqs) | Today: ${today_spend:.4f}", None
    except Exception as e:
        return f"Budget check failed: {e}", None


ACTION_ITEMS: list[ActionItem] = [
    ActionItem("Refresh State", "Gather latest service and model data.", action_refresh_state),
    ActionItem("Validate Schema", "Run config schema validation.", action_validate_schema),
    ActionItem("Check Budgets", "View total and daily spend.", action_check_budgets),
    ActionItem("Test Chat (Local)", "Test llama3.1 routing.", action_test_chat),
    ActionItem("Test Code (vLLM)", "Test qwen-coder routing.", action_test_code),
    ActionItem("Test Cloud", "Test gpt-oss:20b-cloud routing.", action_test_cloud),
    ActionItem(
        "Regenerate Config", "Re-build LiteLLM config from sources.", action_regenerate_config
    ),
    ActionItem("Inspect Config", "Check logical configuration snapshot.", action_inspect_config),
    ActionItem("View Logs", "Show recent service control logs.", action_view_logs),
    ActionItem("Start vLLM", "Attempt to start the vLLM service via systemctl.", action_start_vllm),
    ActionItem("Switch vLLM -> Qwen", "Hot-swap vLLM to Qwen2.5-Coder.", action_switch_vllm_qwen),
    ActionItem(
        "Switch vLLM -> Dolphin", "Hot-swap vLLM to Dolphin-Mistral.", action_switch_vllm_dolphin
    ),
    ActionItem("Restart LiteLLM", "Restart the main gateway service.", action_restart_litellm),
]


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # success
    curses.init_pair(2, curses.COLOR_RED, -1)  # error
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # warning
    curses.init_pair(4, curses.COLOR_CYAN, -1)  # accent
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # instructions


def render_overview(
    stdscr: Any,
    state: dict[str, Any],
    top: int,
    left: int,
    width: int,
    height: int,
    selection: int | None = None,
    focused: bool = False,
) -> None:
    y = top

    # --- Hardware Section ---
    safe_addstr(stdscr, y, left, "Hardware Resources", width, curses.color_pair(4) | curses.A_BOLD)
    y += 2

    gpu_stats = state.get("gpu")
    if gpu_stats:
        name = gpu_stats["name"]
        mem_used = gpu_stats["memory_used"]
        mem_total = gpu_stats["memory_total"]
        gpu_util = gpu_stats["gpu_util"]

        # Color logic for utilization
        util_attr = curses.color_pair(1)
        if gpu_util > 80:
            util_attr = curses.color_pair(2)
        elif gpu_util > 50:
            util_attr = curses.color_pair(3)

        safe_addstr(stdscr, y, left, f"GPU: {name}", width, curses.A_BOLD)
        y += 1
        safe_addstr(stdscr, y, left, f"VRAM: {mem_used:.0f}MB / {mem_total:.0f}MB", width)
        y += 1
        safe_addstr(stdscr, y, left, f"Load: {gpu_util}%", width, util_attr)
    else:
        safe_addstr(stdscr, y, left, "GPU telemetry unavailable", width, curses.A_DIM)

    y += 2
    if y - top >= height:
        return

    # --- Service Health Section ---
    summary = state.get("summary", {})
    required_ok, required_total = summary.get("required", (0, 0))
    optional_ok, optional_total = summary.get("optional", (0, 0))

    required_attr = curses.color_pair(1) if required_ok == required_total else curses.color_pair(2)
    optional_attr = curses.color_pair(1) if optional_ok == optional_total else curses.color_pair(3)

    safe_addstr(stdscr, y, left, "Service Health", width, curses.color_pair(4) | curses.A_BOLD)
    y += 1
    if focused:
        safe_addstr(
            stdscr, y, left, "Controls: [s]tart [k]ill [r]estart", width, curses.color_pair(5)
        )
    y += 1
    if y - top >= height:
        return

    safe_addstr(
        stdscr,
        y,
        left,
        f"Required services: {required_ok}/{required_total} healthy",
        width,
        required_attr | curses.A_BOLD,
    )
    y += 1
    safe_addstr(
        stdscr,
        y,
        left,
        f"Optional services: {optional_ok}/{optional_total} online",
        width,
        optional_attr,
    )
    y += 2

    services = state.get("services", [])
    for idx, entry in enumerate(services):
        if y - top >= height:
            break
        service: Service = entry["service"]
        status_ok = entry["status"]
        latency_text = format_latency(entry["latency"])
        error = entry["error"]

        is_selected = idx == selection
        indicator = "➤" if is_selected else " "

        row_attr = 0
        if status_ok:
            status_text = "ONLINE "
            row_attr = curses.color_pair(1) | curses.A_BOLD
        else:
            if service.required:
                row_attr = curses.color_pair(2) | curses.A_BOLD
                status_text = "OFFLINE"
            else:
                row_attr = curses.color_pair(3) | curses.A_BOLD
                status_text = "MISSING "

        if is_selected and focused:
            row_attr |= curses.A_REVERSE

        safe_addstr(stdscr, y, left, f"{indicator} {status_text} {service.name}", width, row_attr)
        y += 1
        if y - top >= height:
            break
        safe_addstr(
            stdscr,
            y,
            left + 2,
            f"Latency: {latency_text}   URL: {service.url}",
            width - 2,
            curses.A_DIM,
        )
        y += 1
        if not status_ok and error and y - top < height:
            safe_addstr(stdscr, y, left + 2, f"⚠ {error}", width - 2, curses.color_pair(3))
            y += 1
        y += 1


def render_models(
    stdscr: Any,
    state: dict[str, Any],
    top: int,
    left: int,
    width: int,
    height: int,
    selection: int | None = None,
    focused: bool = False,
) -> None:
    y = top
    models_info = state.get("models", {})
    available_models = set(models_info.get("models", []))
    error = models_info.get("error")
    latency = models_info.get("latency")

    safe_addstr(
        stdscr, y, left, "Logical Models & Routing", width, curses.color_pair(4) | curses.A_BOLD
    )
    y += 2

    if error:
        safe_addstr(stdscr, y, left, f"⚠ {error}", width, curses.color_pair(3))
        return

    # Extract logical models from mappings
    exact_matches = MODEL_MAPPINGS.get("exact_matches", {})
    fallbacks = MODEL_MAPPINGS.get("fallback_chains", {})

    if not exact_matches:
        safe_addstr(stdscr, y, left, "No logical models configured.", width, curses.A_DIM)
        return

    # Display header
    header = f"{'Model Name':<30} {'Provider':<15} {'Status':<10} {'Fallback Chain'}"
    safe_addstr(stdscr, y, left, header, width, curses.A_UNDERLINE)
    y += 1

    for model_name, config in exact_matches.items():
        if y - top >= height:
            break

        provider = config.get("provider", "unknown")
        status_attr = (
            curses.color_pair(1) if model_name in available_models else curses.color_pair(3)
        )
        status_text = "READY" if model_name in available_models else "UNAVAIL"

        # Get fallback chain
        chain = fallbacks.get(model_name, {}).get("chain", [])
        chain_text = " -> ".join(chain) if chain else "None"
        if len(chain_text) > 40:
            chain_text = chain_text[:37] + "..."

        line = f"{model_name:<30} {provider:<15} {status_text:<10} {chain_text}"
        safe_addstr(stdscr, y, left, line, width, status_attr)
        y += 1

    y += 1
    if y - top < height:
        safe_addstr(
            stdscr, y, left, f"LiteLLM Latency: {format_latency(latency)}", width, curses.A_DIM
        )


def render_operations(
    stdscr: Any,
    state: dict[str, Any],
    top: int,
    left: int,
    width: int,
    height: int,
    selection: int | None,
    focused: bool,
) -> None:
    y = top
    safe_addstr(stdscr, y, left, "Quick Actions", width, curses.color_pair(4) | curses.A_BOLD)
    y += 1
    safe_addstr(
        stdscr,
        y,
        left,
        "Tab to focus actions, Enter to run. Shift-Tab to return.",
        width,
        curses.color_pair(5),
    )
    y += 2

    if not ACTION_ITEMS:
        safe_addstr(stdscr, y, left, "No operations available.", width, curses.color_pair(3))
        return

    for idx, action in enumerate(ACTION_ITEMS):
        if y - top >= height:
            break
        indicator = "➤" if idx == selection else " "
        attr = curses.A_BOLD if idx == selection else curses.A_NORMAL
        if idx == selection and focused:
            attr |= curses.A_REVERSE
        safe_addstr(stdscr, y, left, f"{indicator} {action.title}", width, attr)
        y += 1
        if y - top >= height:
            break
        safe_addstr(stdscr, y, left + 4, action.description, width - 4, curses.A_DIM)
        y += 2


def draw_footer(
    stdscr: Any,
    message: str,
    last_refresh: datetime,
    focus_label: str,
) -> None:
    height, width = stdscr.getmaxyx()
    if height < 6:
        return
    footer_y = height - 4
    from contextlib import suppress

    with suppress(curses.error):
        stdscr.hline(footer_y, 1, curses.ACS_HLINE, width - 2)
    instructions = "Arrows navigate • Tab switch panel • Enter run • r refresh • q quit"
    safe_addstr(stdscr, footer_y + 1, 2, instructions, width - 4, curses.color_pair(5))
    focus_line = f"Focus: {focus_label}    Last refresh: {last_refresh.strftime('%H:%M:%S')}"
    safe_addstr(stdscr, footer_y + 2, 2, focus_line, width - 4, curses.color_pair(5))
    if message:
        safe_addstr(stdscr, footer_y + 3, 2, message, width - 4)


def handle_menu_keys(key: int, menu_index: int, menu_items: list[MenuItem]) -> tuple[int, str, str]:
    """Handle keyboard input when menu is focused.

    Args:
        key: Curses key code
        menu_index: Current menu selection index
        menu_items: List of menu items

    Returns:
        Tuple of (new_menu_index, new_focus, message)
    """
    current_item = menu_items[menu_index]

    if key == curses.KEY_UP:
        return (menu_index - 1) % len(menu_items), "menu", ""
    if key == curses.KEY_DOWN:
        return (menu_index + 1) % len(menu_items), "menu", ""
    if key in (curses.KEY_RIGHT, 9) and current_item.supports_actions:  # Tab
        return menu_index, "content", "Actions focused."
    if key in (curses.KEY_ENTER, 10, 13) and current_item.supports_actions:
        return menu_index, "content", "Actions focused."
    if key == curses.KEY_BTAB:  # Shift-Tab
        return menu_index, "menu", ""

    return menu_index, "menu", ""


def handle_action_keys(
    key: int, action_selection: int, action_items: list[ActionItem]
) -> tuple[int, str, str | None]:
    """Handle keyboard input when actions panel is focused.

    Args:
        key: Curses key code
        action_selection: Current action selection index
        action_items: List of available actions

    Returns:
        Tuple of (new_action_selection, new_focus, execute_action_index or None)
    """
    if not action_items:
        return action_selection, "menu", None

    if key == curses.KEY_UP:
        return (action_selection - 1) % len(action_items), "content", None
    if key == curses.KEY_DOWN:
        return (action_selection + 1) % len(action_items), "content", None
    if key in (curses.KEY_LEFT, curses.KEY_BTAB):  # Left arrow or Shift-Tab
        return action_selection, "menu", "Menu focused."
    if key in (9,):  # Tab
        return action_selection, "menu", "Menu focused."
    if key in (curses.KEY_ENTER, 10, 13):  # Enter
        return action_selection, "content", action_selection

    return action_selection, "content", None


SERVICE_ALIAS_MAP = {
    "LiteLLM Gateway": "litellm",
    "Ollama": "ollama",
    "vLLM": "vllm",
    "vLLM high-throughput inference with AWQ quantization (Qwen model)": "vllm",
    "llama.cpp (Python)": "llamacpp_python",
    "llama.cpp (Native)": "llamacpp_native",
}


def handle_service_keys(
    key: int, selection: int, services: list[dict[str, Any]]
) -> tuple[int, str, str | None]:
    """Handle keys for the Service Overview panel."""
    if not services:
        return selection, "menu", None

    if key == curses.KEY_UP:
        return (selection - 1) % len(services), "content", None
    if key == curses.KEY_DOWN:
        return (selection + 1) % len(services), "content", None
    if key in (curses.KEY_LEFT, curses.KEY_BTAB):
        return selection, "menu", "Menu focused."
    if key in (9,):  # Tab
        return selection, "menu", "Menu focused."

    # Actions
    action = None
    if key == ord("s"):
        action = "start"
    if key == ord("k") or key == ord("x"):
        action = "stop"
    if key == ord("r"):
        action = "restart"

    if action:
        entry = services[selection]
        service_name = entry["service"].name
        # Try exact match or partial match
        alias = SERVICE_ALIAS_MAP.get(service_name)
        if not alias:
            # Fallback: try to find partial match
            for k, v in SERVICE_ALIAS_MAP.items():
                if service_name.startswith(k) or k in service_name:
                    alias = v
                    break

        if alias:
            success, msg = call_service_control(alias, action)
            return selection, "content", f"{action.title()} {alias}: {msg}"

        return selection, "content", f"No control alias for '{service_name}'"

    return selection, "content", None


def interactive_dashboard(stdscr: Any) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    init_colors()

    menu_items: list[MenuItem] = [
        MenuItem(
            "Service Overview",
            "Live status, latency, and errors for required services.",
            render_overview,
            supports_actions=True,  # This was missing
        ),
        MenuItem(
            "Model Catalog",
            "Current LiteLLM routing targets discovered from the gateway.",
            render_models,
        ),
        MenuItem(
            "Operations",
            "Run common PTUI automation and validation tasks.",
            render_operations,
            supports_actions=True,
        ),
    ]

    action_selection = 0 if ACTION_ITEMS else -1
    service_selection = 0

    menu_index = 0
    focus = "menu"
    message = ""
    state = gather_state_smart(DEFAULT_HTTP_TIMEOUT)
    last_refresh = datetime.now()
    last_auto_refresh = time.monotonic()

    def apply_state(new_state: dict[str, Any]) -> None:
        nonlocal state, last_refresh, last_auto_refresh
        state = new_state
        last_refresh = datetime.now()
        last_auto_refresh = time.monotonic()

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        header_title = "AI Backend Unified - PTUI Command Center"
        safe_addstr(stdscr, 0, 2, header_title, width - 4, curses.color_pair(4) | curses.A_BOLD)

        mode_indicator = "(async)" if ASYNC_AVAILABLE else "(sync)"

        # Cloud Status Check
        has_cloud_key = "OLLAMA_API_KEY" in os.environ
        cloud_text = "CLOUD: ON" if has_cloud_key else "CLOUD: OFF"
        cloud_attr = curses.color_pair(1) if has_cloud_key else curses.color_pair(3)

        # Draw subtitle with mixed colors manually since safe_addstr handles one attr
        safe_addstr(
            stdscr, 1, 2, f"ptui-dashboard {mode_indicator}  |  ", width - 4, curses.color_pair(5)
        )
        safe_addstr(
            stdscr,
            1,
            2 + len(f"ptui-dashboard {mode_indicator}  |  "),
            cloud_text,
            width,
            cloud_attr | curses.A_BOLD,
        )

        from contextlib import suppress

        with suppress(curses.error):
            stdscr.hline(2, 1, curses.ACS_HLINE, width - 2)

        body_top = 3
        footer_height = 4
        menu_width = max(22, min(30, width // 4))
        menu_x = 2
        content_left = menu_x + menu_width + 2
        content_width = max(10, width - content_left - 2)
        available_height = max(3, height - body_top - footer_height)

        current_item = menu_items[menu_index]
        if focus == "content" and not current_item.supports_actions:
            focus = "menu"

        if ACTION_ITEMS:
            action_selection = max(0, action_selection)
            action_selection = min(action_selection, len(ACTION_ITEMS) - 1)
        else:
            action_selection = -1

        safe_addstr(
            stdscr, body_top, menu_x, "Sections", menu_width, curses.color_pair(4) | curses.A_BOLD
        )
        menu_y = body_top + 2
        for idx, item in enumerate(menu_items):
            if menu_y >= height - footer_height:
                break
            indicator = "➤" if idx == menu_index else " "
            attr = curses.A_BOLD if idx == menu_index else curses.A_DIM
            if idx == menu_index and focus == "menu":
                attr |= curses.A_REVERSE
            safe_addstr(stdscr, menu_y, menu_x, f"{indicator} {item.title}", menu_width, attr)
            menu_y += 1

        content_title_y = body_top
        safe_addstr(
            stdscr,
            content_title_y,
            content_left,
            current_item.title,
            content_width,
            curses.color_pair(4) | curses.A_BOLD,
        )
        safe_addstr(
            stdscr,
            content_title_y + 1,
            content_left,
            current_item.description,
            content_width,
            curses.color_pair(5),
        )

        content_top = content_title_y + 3
        content_height = max(1, available_height - 3)

        # Determine which selection to pass to renderer
        if current_item.title == "Service Overview":
            selection_value = service_selection
        elif current_item.supports_actions:
            selection_value = action_selection
        else:
            selection_value = None

        current_item.renderer(
            stdscr,
            state,
            content_top,
            content_left,
            content_width,
            content_height,
            selection_value,
            focus == "content" and current_item.supports_actions,
        )

        focus_label = "Content" if focus == "content" and current_item.supports_actions else "Menu"
        draw_footer(stdscr, message, last_refresh, focus_label)
        stdscr.refresh()

        key = stdscr.getch()
        now = time.monotonic()

        if key == ord("q"):
            break

        if key in (ord("r"), ord("R")) and not (
            focus == "content" and current_item.title == "Service Overview"
        ):
            apply_state(gather_state_smart(DEFAULT_HTTP_TIMEOUT))
            mode = "async" if ASYNC_AVAILABLE else "sync"
            message = f"Service state refreshed ({mode})."
            continue

        if key == curses.KEY_RESIZE:
            message = "Window resized."
            continue

        if key in (ord("g"), ord("G")):
            apply_state(gather_state_smart(DEFAULT_HTTP_TIMEOUT))
            mode = "async" if ASYNC_AVAILABLE else "sync"
            message = f"State gathered ({mode})."
            continue

        if focus == "menu":
            menu_index, focus, message = handle_menu_keys(key, menu_index, menu_items)
            continue

        # Handle Service Overview interactions
        if focus == "content" and current_item.title == "Service Overview":
            service_selection, focus, status_msg = handle_service_keys(
                key, service_selection, state.get("services", [])
            )
            if status_msg:
                message = status_msg
                # If an action was performed, auto-refresh after a delay
                if "Start" in status_msg or "Stop" in status_msg or "Restart" in status_msg:
                    last_auto_refresh = (
                        time.monotonic() - AUTO_REFRESH_SECONDS + 2
                    )  # Force refresh soon
            continue

        # Handle Operations interactions
        if focus == "content" and current_item.title == "Operations":
            action_selection, focus, result = handle_action_keys(
                key, action_selection, ACTION_ITEMS
            )

            if isinstance(result, int):
                # Execute the action
                action = ACTION_ITEMS[result]
                pre_message = f"{action.title}: running..."
                draw_footer(stdscr, pre_message, last_refresh, "Actions")
                stdscr.refresh()
                action_message, maybe_state = action.handler(state)
                if maybe_state is not None:
                    apply_state(maybe_state)
                else:
                    last_auto_refresh = time.monotonic()
                message = action_message
            elif isinstance(result, str):
                message = result

            continue

        if key == -1 and (now - last_auto_refresh) > AUTO_REFRESH_SECONDS:
            apply_state(gather_state_smart(DEFAULT_HTTP_TIMEOUT))
            mode = "async" if ASYNC_AVAILABLE else "sync"
            message = f"Auto-refreshed ({mode})."
            continue

        time.sleep(0.05)


def _ensure_valid_terminfo(term: str | None) -> None:
    terminfo_dir = os.environ.get("TERMINFO")
    if not terminfo_dir:
        return
    subdir = (term or "_")[:1] or "_"
    candidate = os.path.join(terminfo_dir, subdir, term or "")
    if not os.path.exists(candidate):
        os.environ.pop("TERMINFO", None)


def _has_terminfo(term: str | None) -> bool:
    if not term:
        return False
    try:
        subprocess.run(
            ["infocmp", term],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _compile_kitty_terminfo() -> bool:
    # Try locating kitty.terminfo in common install paths
    candidate_paths = []
    terminfo_env = os.environ.get("TERMINFO")
    if terminfo_env:
        candidate_paths.append(Path(terminfo_env))
    candidate_paths.extend(
        [
            Path.home() / ".local" / "kitty.app" / "lib" / "kitty" / "terminfo",
            Path.home() / ".local" / "share" / "kitty" / "terminfo",
        ]
    )

    for base in candidate_paths:
        if not base:
            continue
        source = base / "kitty.terminfo"
        if not source.exists():
            continue
        destination = Path.home() / ".terminfo"
        destination.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["tic", "-x", "-o", str(destination), str(source)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return False


def _ensure_term_capabilities(term: str | None) -> None:
    if not term:
        return
    if _has_terminfo(term):
        return
    if "kitty" in term.lower():
        _compile_kitty_terminfo()


def _launch_dashboard() -> tuple[bool, str | None]:
    try:
        curses.wrapper(interactive_dashboard)
    except KeyboardInterrupt:
        return True, None
    except Exception:
        return False, traceback.format_exc()
    return True, None


def main() -> None:
    if not sys.stdout.isatty():
        print("Interactive dashboard requires a TTY.", file=sys.stderr)
        sys.exit(1)

    original_term = os.environ.get("TERM")
    # Attempted terms logic removed, as user's TERM is proven to work.
    attempted_terms: list[str | None] = [original_term]

    failure_messages: list[str] = []

    for candidate in attempted_terms:
        if candidate is not None:
            os.environ["TERM"] = candidate
        else:
            os.environ.pop("TERM", None)

        # Bypassing these functions as they might be causing interference
        # _ensure_valid_terminfo(candidate)
        # _ensure_term_capabilities(candidate)
        success, error_detail = _launch_dashboard()
        if success:
            return
        if error_detail:
            failure_messages.append(f"{candidate or '<unset>'}: {error_detail}")

    last_term = os.environ.get("TERM", "unknown")
    tried = ", ".join(value or "<unset>" for value in attempted_terms)
    details = "\n".join(failure_messages) if failure_messages else "no detailed error available"
    print(
        (
            "Unable to start the PTUI dashboard (curses initialization failed).\n"
            f"Tried TERM values: {tried} (last attempt used TERM={last_term}).\n"
            "Install an appropriate terminfo entry (e.g. `sudo apt install ncurses-term`) "
            "or run with `TERM=xterm-256color` and ensure full terminal emulator support.\n"
            f"Failure details:\n{details}"
        ),
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
