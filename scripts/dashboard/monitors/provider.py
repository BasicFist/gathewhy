"""Provider monitoring for AI backend dashboard.

This module handles health checking and metrics collection for LLM provider
services including Ollama, vLLM, and llama.cpp variants.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from typing import Literal
from urllib.parse import urljoin, urlparse

import psutil
import requests  # type: ignore[import-untyped]

from ..config import load_providers_config
from ..models import GPUOverview, ServiceMetrics
from .gpu import GPUMonitor

logger = logging.getLogger(__name__)

_SYSTEMCTL_AVAILABLE = shutil.which("systemctl") is not None


def _system_controls_available() -> bool:
    """Return whether systemctl controls are available on this host."""

    return _SYSTEMCTL_AVAILABLE

# Security: Service name allowlist (prevent command injection)
ALLOWED_SERVICES: dict[str, str] = {
    "ollama": "ollama.service",
    "vllm": "vllm.service",
    "llama_cpp_python": "llamacpp-python.service",
    "llama_cpp_native": "llama-server-native.service",
    "litellm_gateway": "litellm.service",
}

ALLOWED_ACTIONS: set[Literal["start", "stop", "restart", "enable", "disable"]] = {
    "start",
    "stop",
    "restart",
    "enable",
    "disable",
}

ERROR_BACKOFF_SECONDS = 60.0
SOFT_ERROR_BACKOFF_SECONDS = 15.0


def _run_systemctl(args: list[str]) -> bool:
    """Run systemctl command with constrained environment."""
    global _SYSTEMCTL_AVAILABLE

    if not _SYSTEMCTL_AVAILABLE:
        logger.warning("System controls unavailable: systemctl not detected on this platform")
        return False

    env = {
        "PATH": "/usr/bin:/bin",
        # Preserve required session metadata for user services
        "DBUS_SESSION_BUS_ADDRESS": os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""),
        "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR", ""),
        "HOME": os.environ.get("HOME", ""),
    }
    try:
        result = subprocess.run(
            ["systemctl", "--user", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
            env=env,
        )
        if result.returncode == 0:
            return True
        stderr = (result.stderr or "").strip()
        logger.warning(
            "systemctl --user %s failed with exit code %s%s",
            " ".join(args),
            result.returncode,
            f": {stderr}" if stderr else "",
        )
        return False
    except FileNotFoundError:
        logger.warning("systemctl binary not found; service controls disabled for this session")
        _SYSTEMCTL_AVAILABLE = False
        return False
    except OSError as exc:  # pragma: no cover - defensive
        logger.warning(
            "systemctl is unavailable on this platform: %s", exc
        )
        _SYSTEMCTL_AVAILABLE = False
        return False
    except subprocess.SubprocessError as exc:  # pragma: no cover - defensive
        logger.debug(f"systemctl {' '.join(args)} failed: {type(exc).__name__}")
        return False


class ProviderMonitor:
    """Collects live diagnostics for each backend LLM provider.

    Monitors provider health through HTTP endpoint checks, collects system
    resource usage (CPU, memory, VRAM), and provides service control via
    systemctl. Supports Ollama, vLLM, and llama.cpp providers.

    Attributes:
        gpu_monitor: GPUMonitor instance for NVIDIA GPU metrics
        PROVIDERS: Registry of provider configurations (endpoint, service, etc.)
    """

    # SECURITY: Allowed endpoint hosts (localhost only, prevent SSRF)
    ALLOWED_HOSTS: set[str] = {"127.0.0.1", "localhost"}
    ALLOWED_PORTS: set[int] = {11434, 8000, 8001, 8002, 8080, 4000}

    DEFAULT_PROVIDERS: dict[str, dict[str, object]] = {
        "ollama": {
            "endpoint": "http://127.0.0.1:11434/api/tags",
            "display": "Ollama",
            "service": "ollama.service",
            "required": False,
            "type": "ollama",
        },
        "vllm": {
            "endpoint": "http://127.0.0.1:8001/v1/models",
            "display": "vLLM",
            "service": "vllm.service",
            "required": True,
            "type": "litellm",
        },
        "llama_cpp_python": {
            "endpoint": "http://127.0.0.1:8000/v1/models",
            "display": "llama.cpp (Python)",
            "service": "llamacpp-python.service",
            "required": False,
            "type": "litellm",
        },
        "llama_cpp_native": {
            "endpoint": "http://127.0.0.1:8080/v1/models",
            "display": "llama.cpp (Native)",
            "service": "llama-server-native.service",
            "required": False,
            "type": "litellm",
        },
        "litellm_gateway": {
            "endpoint": "http://127.0.0.1:4000/v1/models",
            "display": "LiteLLM Gateway",
            "service": "litellm.service",
            "required": True,
            "type": "litellm",
        },
    }

    def __init__(self, http_timeout: float = 3.0) -> None:
        """Initialize provider monitor with validation.

        Args:
            http_timeout: Timeout for HTTP health checks in seconds
        """
        self.gpu_monitor = GPUMonitor()
        self.http_timeout = http_timeout
        self.providers = self._build_provider_registry()
        self._cooldowns: dict[str, float] = {}
        self._last_status: dict[str, str] = {}
        self._last_samples: dict[str, dict[str, float | int]] = {}
        self.system_controls_available = _system_controls_available()
        if not self.system_controls_available:
            logger.warning(
                "systemctl not detected; service control buttons will be disabled"
            )
        # SECURITY: Validate all endpoints at init time
        self._validate_endpoints()

    def _build_provider_registry(self) -> dict[str, dict[str, object]]:
        """Build provider registry by merging defaults with config file.

        Only localhost providers marked active (or preview) are kept. Remote
        endpoints are intentionally excluded to avoid unintended external calls.
        """
        registry = {key: value.copy() for key, value in self.DEFAULT_PROVIDERS.items()}

        config = load_providers_config()
        if not config:
            return registry

        providers_cfg = config.get("providers", {})
        for key, meta in providers_cfg.items():
            status = str(meta.get("status", "active")).lower()

            if status not in {"active", "preview"}:
                registry.pop(key, None)
                continue

            base_url = str(meta.get("base_url", "")).strip()
            health_endpoint = str(meta.get("health_endpoint", "")).strip()

            endpoint = ""
            if base_url and health_endpoint:
                endpoint = urljoin(
                    base_url if base_url.endswith("/") else f"{base_url}/",
                    health_endpoint.lstrip("/"),
                )
            elif base_url:
                endpoint = base_url

            if not endpoint:
                logger.debug(f"Skipping provider {key}: missing endpoint metadata")
                registry.pop(key, None)
                continue

            parsed = urlparse(endpoint)
            if parsed.hostname not in self.ALLOWED_HOSTS:
                logger.debug("Skipping provider %s: host %s not in allowlist", key, parsed.hostname)
                registry.pop(key, None)
                continue

            record = registry.get(
                key,
                {
                    "display": key.replace("_", " ").title(),
                    "required": False,
                },
            )

            record["endpoint"] = endpoint
            record["type"] = meta.get("type", record.get("type", "unknown"))

            if "service" not in record:
                service_override = ALLOWED_SERVICES.get(key)
                if service_override:
                    record["service"] = service_override

            registry[key] = record

        return registry

    def _sync_controls_capability(self) -> None:
        """Refresh cached controls capability flag from module state."""

        self.system_controls_available = _system_controls_available()

    def _validate_endpoints(self) -> None:
        """SECURITY: Validate all provider endpoints against allowlists.

        Prevents SSRF attacks by ensuring all endpoints are localhost only.

        Raises:
            ValueError: If any endpoint fails validation
        """
        invalid_keys: list[str] = []
        for key, cfg in self.providers.items():
            endpoint = str(cfg.get("endpoint", ""))
            parsed = urlparse(endpoint)

            # Validate scheme
            if parsed.scheme not in ("http", "https"):
                logger.warning("Removing provider %s due to invalid scheme: %s", key, parsed.scheme)
                invalid_keys.append(key)
                continue

            # SECURITY: Validate host (localhost only)
            if parsed.hostname not in self.ALLOWED_HOSTS:
                logger.warning(
                    "Removing provider %s due to disallowed host: %s", key, parsed.hostname
                )
                invalid_keys.append(key)
                continue

            # SECURITY: Validate port
            if parsed.port and parsed.port not in self.ALLOWED_PORTS:
                logger.warning("Removing provider %s due to disallowed port: %s", key, parsed.port)
                invalid_keys.append(key)
                continue

            logger.debug(f"✓ Validated endpoint for {key}: {endpoint}")

        for key in invalid_keys:
            self.providers.pop(key, None)

    # --------------------------- System Helpers ---------------------------------

    def _service_name(self, key: str) -> str | None:
        """Get systemd service name for provider key.

        Args:
            key: Provider key (e.g., "ollama", "vllm")

        Returns:
            Service name or None if provider not found
        """
        record = self.providers.get(key)
        if not record:
            return None
        service = record.get("service")
        return str(service) if service else None

    def _get_service_pid(self, key: str) -> int | None:
        """Get process ID for a provider service.

        Args:
            key: Provider key

        Returns:
            Process ID or None if service not running or PID not available
        """
        service = self._service_name(key)
        if not service:
            return None

        try:
            result = subprocess.run(
                ["systemctl", "--user", "show", service, "--property=MainPID", "--value"],
                capture_output=True,
                text=True,
                check=False,
                timeout=2,
                env={
                    "PATH": "/usr/bin:/bin",
                    "DBUS_SESSION_BUS_ADDRESS": os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""),
                    "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR", ""),
                    "HOME": os.environ.get("HOME", ""),
                },
            )
        except (subprocess.SubprocessError, FileNotFoundError):  # pragma: no cover - OS specific
            return None

        value = result.stdout.strip()
        if not value:
            return None
        try:
            pid = int(value)
        except ValueError:
            return None
        return pid if pid > 0 else None

    def _collect_process_metrics(
        self, key: str, pid_override: int | None = None
    ) -> tuple[int | None, float, float]:
        """Collect CPU and memory metrics for a provider process.

        Args:
            key: Provider key

        Returns:
            Tuple of (pid, cpu_percent, memory_mb)
        """
        pid = pid_override if pid_override is not None else self._get_service_pid(key)
        if pid is None:
            return None, 0.0, 0.0

        try:
            proc = psutil.Process(pid)
            cpu = proc.cpu_percent(interval=0.0)
            memory_mb = proc.memory_info().rss / 1024**2
            return pid, cpu, memory_mb
        except psutil.Error:
            return None, 0.0, 0.0

    def _parse_models(self, key: str, response_json: dict) -> int:
        """Parse model count from provider API response.

        Args:
            key: Provider key
            response_json: JSON response from provider endpoint

        Returns:
            Number of models available
        """
        provider_type = str(self.providers[key]["type"])
        try:
            if provider_type == "ollama":
                return len(response_json.get("models", []))
            return len(response_json.get("data", []))
        except Exception:
            return 0

    # ----------------------------- Public API ----------------------------------

    def collect_snapshot(self) -> tuple[list[ServiceMetrics], GPUOverview]:
        """Collect health and resource metrics for all providers.

        Performs HTTP health checks on all registered providers, collects
        system resource usage (CPU, memory, VRAM), and aggregates GPU metrics.

        Returns:
            Tuple of (metrics list, gpu_overview)
        """
        try:
            gpu_info = self.gpu_monitor.get_gpu_info()
            per_pid_vram = self.gpu_monitor.get_process_vram()
            system_memory_total = psutil.virtual_memory().total / 1024**2
        except Exception as e:
            logger.error(f"Error collecting system metrics: {type(e).__name__}: {e}")
            gpu_info = []
            per_pid_vram = {}
            system_memory_total = 1.0

        metrics: list[ServiceMetrics] = []
        now_monotonic = time.monotonic()
        self._sync_controls_capability()

        for key, cfg in self.providers.items():
            notes: list[str] = []
            endpoint = str(cfg["endpoint"])
            required = bool(cfg["required"])
            display = str(cfg["display"])
            cooldown_until = self._cooldowns.get(key, 0.0)
            pid_hint = self._get_service_pid(key)
            elapsed_ms = 0.0
            models = 0
            status = self._last_status.get(key) or (
                "active" if pid_hint else ("degraded" if required else "inactive")
            )
            has_service = bool(cfg.get("service"))
            controls_enabled = has_service and self.system_controls_available

            if not has_service:
                notes.append("Service controls unavailable (no systemd unit)")
            elif not self.system_controls_available:
                notes.append("Service controls unavailable on this platform")

            skip_probe = now_monotonic < cooldown_until

            if skip_probe:
                remaining = max(int(cooldown_until - now_monotonic), 0)
                notes.append(f"Probe skipped ({remaining}s cooldown)")
                last_sample = self._last_samples.get(key, {})
                models = int(last_sample.get("models", 0))
                elapsed_ms = float(last_sample.get("response_ms", 0.0))
            else:
                start = time.perf_counter()
                try:
                    response = requests.get(endpoint, timeout=self.http_timeout)
                    elapsed_ms = (time.perf_counter() - start) * 1000

                    if response.ok:
                        try:
                            payload = response.json()
                            status = "active"
                            models = self._parse_models(key, payload)
                            self._cooldowns.pop(key, None)
                            self._last_samples[key] = {
                                "models": models,
                                "response_ms": elapsed_ms,
                            }
                            logger.debug(
                                f"{key}: ✓ Active with {models} models ({elapsed_ms:.0f}ms)"
                            )
                        except ValueError as e:
                            logger.error(f"{key}: Invalid JSON response: {e}")
                            notes.append("Invalid JSON payload")
                            status = "degraded" if required else "inactive"
                            self._cooldowns[key] = now_monotonic + SOFT_ERROR_BACKOFF_SECONDS
                    else:
                        reason = f"HTTP {response.status_code}"
                        if response.reason:
                            reason += f" ({response.reason})"
                        logger.warning(f"{key}: Provider responded with {reason}")
                        notes.append(reason)
                        status = "degraded" if required else "inactive"
                        self._cooldowns[key] = now_monotonic + SOFT_ERROR_BACKOFF_SECONDS
                except requests.exceptions.Timeout:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    logger.warning(f"{key}: Request timeout after {elapsed_ms:.0f}ms")
                    notes.append(f"Timeout ({elapsed_ms:.0f}ms)")
                    status = "degraded" if required else "inactive"
                    self._cooldowns[key] = now_monotonic + SOFT_ERROR_BACKOFF_SECONDS
                except requests.exceptions.ConnectionError as e:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    logger.warning(f"{key}: Connection error: {str(e)[:50]}")
                    notes.append("Connection refused")
                    status = "degraded" if required else "inactive"
                    self._cooldowns[key] = now_monotonic + ERROR_BACKOFF_SECONDS
                except requests.exceptions.RequestException as e:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    logger.warning(f"{key}: Request failed ({type(e).__name__}): {str(e)[:50]}")
                    notes.append(f"{type(e).__name__}")
                    status = "degraded" if required else "inactive"
                    self._cooldowns[key] = now_monotonic + SOFT_ERROR_BACKOFF_SECONDS
                except Exception as e:  # pragma: no cover - unexpected errors
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    logger.error(f"{key}: Unexpected error: {type(e).__name__}: {e}")
                    notes.append(f"Unexpected error: {type(e).__name__}")
                    status = "degraded" if required else "inactive"
                    self._cooldowns[key] = now_monotonic + SOFT_ERROR_BACKOFF_SECONDS

            pid, cpu_percent, memory_mb = self._collect_process_metrics(key, pid_override=pid_hint)
            memory_percent = (memory_mb / system_memory_total * 100) if system_memory_total else 0.0
            vram_mb, vram_percent = per_pid_vram.get(pid, (0.0, 0.0)) if pid else (0.0, 0.0)

            metrics.append(
                ServiceMetrics(
                    key=key,
                    display=display,
                    required=required,
                    status=status,
                    port=urlparse(endpoint).port,
                    endpoint=endpoint,
                    models=models,
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    memory_percent=memory_percent,
                    vram_mb=vram_mb,
                    vram_percent=vram_percent,
                    response_ms=elapsed_ms,
                    pid=pid,
                    controls_enabled=controls_enabled,
                    notes=notes,
                )
            )
            self._last_status[key] = status

        if gpu_info:
            total_used = sum(entry["memory_used_mb"] for entry in gpu_info)
            total_capacity = sum(entry["memory_total_mb"] for entry in gpu_info)
            peak_util = max(entry["gpu_util_percent"] for entry in gpu_info)
        else:
            total_used = total_capacity = peak_util = 0.0

        overview = GPUOverview(
            detected=bool(gpu_info),
            per_gpu=gpu_info,
            total_used_mb=total_used,
            total_capacity_mb=total_capacity,
            peak_util_percent=peak_util,
        )

        return metrics, overview

    @staticmethod
    def _wait_for_state(service: str, desired: set[str], timeout: float = 8.0) -> bool:
        """Wait until systemd service reaches one of desired states."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                result = subprocess.run(
                    ["systemctl", "--user", "is-active", service],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                    text=True,
                    env={
                        "PATH": "/usr/bin:/bin",
                        "DBUS_SESSION_BUS_ADDRESS": os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""),
                        "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR", ""),
                        "HOME": os.environ.get("HOME", ""),
                    },
                )
            except subprocess.SubprocessError:  # pragma: no cover - defensive
                return False

            state = (result.stdout or "").strip()
            if state in desired:
                return True
            time.sleep(0.5)
        return False

    def systemctl(self, key: str, action: str) -> bool:
        """Execute systemctl command with security validation.

        SECURITY: Validates service name and action against allowlists to prevent
        command injection attacks. Only allows whitelisted services and actions.

        Args:
            key: Provider key (must be in ALLOWED_SERVICES)
            action: Action to execute (must be in ALLOWED_ACTIONS)

        Returns:
            True if command succeeded, False otherwise
        """
        # SECURITY: Validate service key
        if key not in ALLOWED_SERVICES:
            logger.warning(f"Rejected invalid service key: {key}")
            return False

        # SECURITY: Validate action
        if action not in ALLOWED_ACTIONS:
            logger.warning(f"Rejected invalid action: {action}")
            return False

        self._sync_controls_capability()
        if not self.system_controls_available:
            logger.warning("Service controls requested but systemctl is unavailable")
            return False

        if action == "restart":
            # Restart is handled as stop + start to ensure graceful shutdown.
            if not self.systemctl(key, "stop"):
                return False
            return self.systemctl(key, "start")

        service = self._service_name(key)
        if not service:
            return False

        if action == "start":
            if not _run_systemctl(["start", service]):
                return False
            return self._wait_for_state(service, {"active"}, timeout=10.0)

        if action in {"enable", "disable"}:
            return _run_systemctl([action, service])

        if action == "stop":
            if not _run_systemctl(["stop", service]):
                return False

            if self._wait_for_state(service, {"inactive", "failed"}, timeout=10.0):
                return True

            logger.warning(f"Graceful stop timed out for {service}; forcing termination")
            _run_systemctl(["kill", service, "--signal=SIGKILL"])

            return self._wait_for_state(service, {"inactive", "failed"}, timeout=5.0)

        # Should never reach here due to allowlist checks.
        return False
