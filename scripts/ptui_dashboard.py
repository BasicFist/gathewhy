#!/usr/bin/env python3
"""
Interactive PTUI dashboard implemented with curses.
Provides a live view of service health, model availability, and key actions.
"""

from __future__ import annotations

import curses
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_HTTP_TIMEOUT = float(os.getenv("PTUI_HTTP_TIMEOUT", "10"))
AUTO_REFRESH_SECONDS = float(os.getenv("PTUI_REFRESH_SECONDS", "5"))


@dataclass
class Service:
    name: str
    url: str
    endpoint: str
    required: bool = True


SERVICES: list[Service] = [
    Service("LiteLLM Gateway", "http://localhost:4000", "/health", required=True),
    Service("Ollama", "http://localhost:11434", "/api/tags", required=True),
    Service("llama.cpp (Python)", "http://localhost:8000", "/v1/models", required=False),
    Service("llama.cpp (Native)", "http://localhost:8080", "/v1/models", required=False),
    Service("vLLM", "http://localhost:8001", "/v1/models", required=False),
]


def fetch_json(url: str, timeout: float) -> tuple[dict[str, Any] | None, float | None, str | None]:
    start_time = time.perf_counter()
    try:
        request = Request(url, headers={"User-Agent": "ptui-dashboard"})
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        latency = time.perf_counter() - start_time
        return data, latency, None
    except (HTTPError, URLError, TimeoutError) as exc:
        return None, None, str(exc)
    except Exception as exc:  # pragma: no cover - safety net
        return None, None, str(exc)


def check_service(service: Service, timeout: float) -> dict[str, Any]:
    url = f"{service.url}{service.endpoint}"
    data, latency, error = fetch_json(url, timeout)
    status_ok = data is not None and error is None
    return {
        "service": service,
        "status": status_ok,
        "latency": latency,
        "error": error,
    }


def get_models(timeout: float) -> dict[str, Any]:
    data, latency, error = fetch_json("http://localhost:4000/v1/models", timeout)
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


def gather_state(timeout: float) -> dict[str, Any]:
    services_status = [check_service(service, timeout) for service in SERVICES]
    models_info = get_models(timeout)
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
        "summary": {
            "required": (healthy_required, total_required),
            "optional": (healthy_optional, total_optional),
        },
        "timestamp": datetime.now(),
    }


def init_colors() -> None:
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # success
    curses.init_pair(2, curses.COLOR_RED, -1)  # error
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # warning
    curses.init_pair(4, curses.COLOR_CYAN, -1)  # accent
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # instructions


def draw_services(stdscr: curses._CursesWindow, state: dict[str, Any], start_y: int) -> int:
    y = start_y
    stdscr.addstr(y, 2, "Service Status", curses.color_pair(4) | curses.A_BOLD)
    y += 2

    for entry in state["services"]:
        service: Service = entry["service"]
        status_ok: bool = entry["status"]
        latency = entry["latency"]
        error = entry["error"]
        label = f"{service.name} ({service.url})"
        latency_text = format_latency(latency)

        if status_ok:
            color = curses.color_pair(1)
            status_text = "ONLINE "
        else:
            color = curses.color_pair(3) if not service.required else curses.color_pair(2)
            status_text = "OFFLINE" if service.required else "MISSING"

        stdscr.addstr(y, 4, status_text, color | curses.A_BOLD)
        stdscr.addstr(y, 13, label)
        stdscr.addstr(y, 13 + len(label) + 1, f"[{latency_text}]")

        if error and not status_ok:
            stdscr.addstr(y + 1, 13, f"⚠ {error}", curses.color_pair(3))
            y += 1
        y += 1

    return y + 1


def draw_models_panel(
    stdscr: curses._CursesWindow, state: dict[str, Any], start_y: int, height: int
) -> int:
    models_info = state["models"]
    stdscr.addstr(start_y, 2, "LiteLLM Models", curses.color_pair(4) | curses.A_BOLD)
    stdscr.addstr(start_y, 25, "(press 'm' to refresh)", curses.color_pair(5))

    models = models_info.get("models", [])
    error = models_info.get("error")

    y = start_y + 2
    max_display = max(1, height - (y + 4))

    if error:
        stdscr.addstr(y, 4, f"⚠ {error}", curses.color_pair(3))
        y += 2
    elif not models:
        stdscr.addstr(y, 4, "No models available.", curses.color_pair(3))
        y += 2
    else:
        for idx, model in enumerate(models[:max_display]):
            stdscr.addstr(y + idx, 4, f"• {model}")
        if len(models) > max_display:
            stdscr.addstr(y + max_display, 4, f"... +{len(models) - max_display} more")
        y += min(len(models), max_display) + 1

    return y + 1


def draw_footer(stdscr: curses._CursesWindow, message: str, last_refresh: datetime) -> None:
    height, width = stdscr.getmaxyx()
    footer_y = height - 3
    stdscr.hline(footer_y, 1, curses.ACS_HLINE, width - 2)
    stdscr.addstr(
        footer_y + 1,
        2,
        "Commands: [r] Refresh  [m] Refresh models  [v] Validate  [q] Quit",
        curses.color_pair(5),
    )
    timestamp_text = f"Last refresh: {last_refresh.strftime('%H:%M:%S')}"
    stdscr.addstr(footer_y + 2, 2, timestamp_text, curses.color_pair(5))
    if message:
        stdscr.addstr(
            footer_y + 2, len(timestamp_text) + 4, message[: width - len(timestamp_text) - 6]
        )


def interactive_dashboard(stdscr: curses._CursesWindow) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    init_colors()

    message = ""
    state = gather_state(DEFAULT_HTTP_TIMEOUT)
    last_refresh = datetime.now()
    last_auto_refresh = time.monotonic()

    while True:
        stdscr.erase()
        height, _ = stdscr.getmaxyx()

        stdscr.addstr(
            0, 2, "AI Backend Unified - PTUI Dashboard", curses.color_pair(4) | curses.A_BOLD
        )
        stdscr.addstr(
            1,
            2,
            f"Version {os.getenv('PTUI_VERSION', '2.0.0')}  |  Interactive Mode",
            curses.color_pair(5),
        )

        y = draw_services(stdscr, state, start_y=3)
        y = draw_models_panel(stdscr, state, start_y=y, height=height)

        draw_footer(stdscr, message, last_refresh)
        stdscr.refresh()

        key = stdscr.getch()

        now = time.monotonic()
        if key == ord("q"):
            break

        if key == ord("r"):
            state = gather_state(DEFAULT_HTTP_TIMEOUT)
            last_refresh = datetime.now()
            last_auto_refresh = now
            message = "Refreshed manually."
            continue

        if key == ord("m"):
            state["models"] = get_models(DEFAULT_HTTP_TIMEOUT)
            last_refresh = datetime.now()
            last_auto_refresh = now
            message = "Model list updated."
            continue

        if key == ord("v"):
            stdscr.nodelay(False)
            draw_footer(stdscr, "Running validation... (this may take a while)", last_refresh)
            stdscr.refresh()
            result_message = run_validation()
            message = result_message
            stdscr.nodelay(True)
            continue

        if key == curses.KEY_RESIZE:
            message = "Window resized."
            continue

        if key == -1 and (now - last_auto_refresh) > AUTO_REFRESH_SECONDS:
            state = gather_state(DEFAULT_HTTP_TIMEOUT)
            last_refresh = datetime.now()
            last_auto_refresh = now
            message = "Auto-refreshed."

        time.sleep(0.05)


def main() -> None:
    if not sys.stdout.isatty():
        print("Interactive dashboard requires a TTY.", file=sys.stderr)
        sys.exit(1)

    term = os.environ.get("TERM", "unknown")
    terminfo_dir = os.environ.get("TERMINFO")
    if terminfo_dir:
        subdir = term[0] if term else "_"
        candidate = os.path.join(terminfo_dir, subdir, term)
        if not os.path.exists(candidate):
            # fall back to system terminfo database if kitty-specific entry missing
            os.environ.pop("TERMINFO", None)

    try:
        curses.wrapper(interactive_dashboard)
    except KeyboardInterrupt:
        pass
    except curses.error:
        term = os.environ.get("TERM", "unknown")
        print(
            (
                "Unable to start the PTUI dashboard (curses initialization failed).\n"
                f"Detected TERM={term}. Ensure you're running inside a full terminal emulator "
                "with terminfo installed (e.g. install the 'ncurses-term' package, or set TERM=xterm-256color)."
            ),
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
