"""Curses user interface for the PTUI dashboard."""

from __future__ import annotations

import curses
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .actions import ACTION_ITEMS
from .config import AUTO_REFRESH_SECONDS, DEFAULT_HTTP_TIMEOUT
from .monitor import ASYNC_AVAILABLE, gather_state_smart
from .models import ActionItem, MenuItem, Service
from .utils import format_latency


def safe_addstr(stdscr: Any, y: int, x: int, text: str, width: int, attr: int = 0) -> None:
    """Safely draw strings without crashing on terminal size issues."""

    if width <= 0:
        return
    from contextlib import suppress

    with suppress(curses.error):
        stdscr.addnstr(y, x, text.ljust(width), width, attr)


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
    summary = state.get("summary", {})
    required_ok, required_total = summary.get("required", (0, 0))
    optional_ok, optional_total = summary.get("optional", (0, 0))

    required_attr = curses.color_pair(1) if required_ok == required_total else curses.color_pair(2)
    optional_attr = curses.color_pair(1) if optional_ok == optional_total else curses.color_pair(3)

    y = top
    safe_addstr(stdscr, y, left, "Service Health", width, curses.color_pair(4) | curses.A_BOLD)
    y += 2
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

    for entry in state.get("services", []):
        if y - top >= height:
            break
        service: Service = entry["service"]
        status_ok = entry["status"]
        latency_text = format_latency(entry["latency"])
        error = entry.get("error")

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

        safe_addstr(stdscr, y, left, f"{status_text} {service.name}", width, row_attr)
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
    models = models_info.get("models", [])
    error = models_info.get("error")
    latency = models_info.get("latency")

    safe_addstr(stdscr, y, left, "LiteLLM Models", width, curses.color_pair(4) | curses.A_BOLD)
    y += 2

    if error:
        safe_addstr(stdscr, y, left, f"⚠ {error}", width, curses.color_pair(3))
        return

    safe_addstr(
        stdscr,
        y,
        left,
        f"Discovered: {len(models)} (fetch {format_latency(latency)})",
        width,
        curses.A_BOLD,
    )
    y += 2

    if not models:
        safe_addstr(stdscr, y, left, "No models available.", width, curses.color_pair(3))
        return

    for model in models:
        if y - top >= height:
            break
        safe_addstr(stdscr, y, left, f"• {model}", width)
        y += 1


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


def draw_footer(stdscr: Any, message: str, last_refresh: datetime, focus_label: str) -> None:
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
    current_item = menu_items[menu_index]

    if key == curses.KEY_UP:
        return (menu_index - 1) % len(menu_items), "menu", ""
    if key == curses.KEY_DOWN:
        return (menu_index + 1) % len(menu_items), "menu", ""
    if key in (curses.KEY_RIGHT, 9) and current_item.supports_actions:
        return menu_index, "content", "Actions focused."
    if key in (curses.KEY_ENTER, 10, 13) and current_item.supports_actions:
        return menu_index, "content", "Actions focused."
    if key == curses.KEY_BTAB:
        return menu_index, "menu", ""
    return menu_index, "menu", ""


def handle_action_keys(key: int, action_selection: int, action_items: list[ActionItem]) -> tuple[int, str, int | None]:
    if not action_items:
        return action_selection, "menu", None

    if key == curses.KEY_UP:
        return (action_selection - 1) % len(action_items), "content", None
    if key == curses.KEY_DOWN:
        return (action_selection + 1) % len(action_items), "content", None
    if key in (curses.KEY_LEFT, curses.KEY_BTAB):
        return action_selection, "menu", None
    if key in (curses.KEY_ENTER, 10, 13):
        return action_selection, "content", action_selection
    return action_selection, "content", None


def init_colors() -> None:
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)


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
        mode_color = curses.color_pair(1) if ASYNC_AVAILABLE else curses.color_pair(3)
        subtitle = f"ptui-dashboard {mode_indicator}"
        safe_addstr(stdscr, 1, 2, subtitle, width - 4, curses.color_pair(5) | mode_color)
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

        safe_addstr(stdscr, body_top, menu_x, "Sections", menu_width, curses.color_pair(4) | curses.A_BOLD)
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
        safe_addstr(stdscr, content_title_y, content_left, current_item.title, content_width, curses.color_pair(4) | curses.A_BOLD)
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
        selection_value = action_selection if current_item.supports_actions else None
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

        focus_label = "Actions" if focus == "content" and current_item.supports_actions else "Menu"
        draw_footer(stdscr, message, last_refresh, focus_label)
        stdscr.refresh()

        key = stdscr.getch()
        now = time.monotonic()

        if key == ord("q"):
            break

        if key in (ord("r"), ord("R")):
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

        if focus == "content" and current_item.supports_actions:
            action_selection, focus, execute_idx = handle_action_keys(key, action_selection, ACTION_ITEMS)
            if execute_idx is not None:
                action = ACTION_ITEMS[execute_idx]
                pre_message = f"{action.title}: running..."
                draw_footer(stdscr, pre_message, last_refresh, "Actions")
                stdscr.refresh()
                action_message, maybe_state = action.handler(state)
                if maybe_state is not None:
                    apply_state(maybe_state)
                else:
                    last_auto_refresh = time.monotonic()
                message = action_message
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
        subprocess.run(["infocmp", term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _compile_kitty_terminfo() -> bool:
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
            subprocess.run(["tic", "-x", "-o", str(destination), str(source)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
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
    except curses.error:
        return False, "curses.error"
    return True, None


def run_dashboard() -> int:
    if not sys.stdout.isatty():
        print("Interactive dashboard requires a TTY.", file=sys.stderr)
        return 1

    original_term = os.environ.get("TERM")
    attempted_terms: list[str | None] = [original_term]

    if original_term in {"xterm-kitty", "kitty"}:
        attempted_terms.extend(["xterm-256color", "xterm"])

    failure_messages: list[str] = []

    for candidate in attempted_terms:
        if candidate is not None:
            os.environ["TERM"] = candidate
        else:
            os.environ.pop("TERM", None)

        _ensure_valid_terminfo(candidate)
        _ensure_term_capabilities(candidate)
        success, error_detail = _launch_dashboard()
        if success:
            return 0
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
    return 1
