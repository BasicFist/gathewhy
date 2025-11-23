#!/usr/bin/env python3
"""
Simple HTTP server exposing systemctl controls for LLM services.

Endpoints:
    GET  /health                          → {"status": "ok"}
    POST /service/<alias>/<action>        → {"success": bool, "message": str}

This server is intended to run locally and is consumed by the dashboard instead
of invoking `systemctl` directly. It sanitises requests against the same
allowlists used by ProviderMonitor and reuses the GPU headroom checks.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import suppress
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import machinery, util
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AI_DASHBOARD_PATH = PROJECT_ROOT / "scripts" / "dashboard" / "monitors" / "provider.py"

if not AI_DASHBOARD_PATH.exists():  # pragma: no cover - defensive
    raise ImportError(f"Unable to locate ai-dashboard module at {AI_DASHBOARD_PATH}")

loader = machinery.SourceFileLoader("ai_dashboard_provider", str(AI_DASHBOARD_PATH))
spec = util.spec_from_loader(loader.name, loader)
if spec is None or spec.loader is None:  # pragma: no cover - defensive
    raise ImportError("Unable to create module spec for ai-dashboard")
ai_dashboard = util.module_from_spec(spec)
sys.modules[loader.name] = ai_dashboard
loader.exec_module(ai_dashboard)

ProviderMonitor = ai_dashboard.ProviderMonitor  # type: ignore[attr-defined]
ALLOWED_SERVICES = ai_dashboard.ALLOWED_SERVICES  # type: ignore[attr-defined]
ALLOWED_ACTIONS = ai_dashboard.ALLOWED_ACTIONS  # type: ignore[attr-defined]


SERVICE_CONTROL_PORT = int(os.environ.get("SERVICE_CONTROL_PORT", 8070))
_monitor = ProviderMonitor(use_http_endpoint=False)


class ServiceControlHandler(BaseHTTPRequestHandler):
    """Minimal request handler dispatching service control actions."""

    server_version = "ServiceControl/0.1"

    def _json_response(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 - required by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") == "/health":
            self._json_response(HTTPStatus.OK, {"status": "ok"})
        else:
            self._json_response(HTTPStatus.NOT_FOUND, {"success": False, "message": "Not Found"})

    def do_POST(self):  # noqa: N802 - required by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        segments = [segment for segment in parsed.path.strip("/").split("/") if segment]

        if len(segments) != 3 or segments[0] != "service":
            self._json_response(
                HTTPStatus.NOT_FOUND, {"success": False, "message": "Invalid endpoint"}
            )
            return

        key, action = segments[1], segments[2]

        if key not in ALLOWED_SERVICES:
            self._json_response(
                HTTPStatus.BAD_REQUEST,
                {"success": False, "message": f"Unknown service alias '{key}'"},
            )
            return
        if action not in ALLOWED_ACTIONS:
            self._json_response(
                HTTPStatus.BAD_REQUEST,
                {"success": False, "message": f"Unsupported action '{action}'"},
            )
            return

        _monitor.last_error = None
        success = _monitor.systemctl(key, action)
        message = _monitor.last_error or "ok"

        status = HTTPStatus.OK if success else HTTPStatus.BAD_REQUEST
        self._json_response(status, {"success": success, "message": message})

    def log_message(self, format: str, *args) -> None:  # noqa: D401 - silence default logging
        """Suppress base class logging output."""
        return


def run_server(port: int = SERVICE_CONTROL_PORT) -> None:
    with ThreadingHTTPServer(("127.0.0.1", port), ServiceControlHandler) as httpd, suppress(
        KeyboardInterrupt
    ):  # pragma: no cover - manual stop
        httpd.serve_forever()


if __name__ == "__main__":
    print(f"Service control server listening on http://127.0.0.1:{SERVICE_CONTROL_PORT}")
    run_server(SERVICE_CONTROL_PORT)
