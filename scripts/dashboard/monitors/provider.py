"""Provider monitoring for AI backend dashboard.

This module handles health checking and metrics collection for LLM provider
services including Ollama, vLLM, and llama.cpp variants.
"""

from __future__ import annotations

import logging
import subprocess
import time
from typing import Literal
from urllib.parse import urlparse

import psutil
import requests  # type: ignore[import-untyped]

from ..models import GPUOverview, ServiceMetrics
from .gpu import GPUMonitor

logger = logging.getLogger(__name__)

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
    ALLOWED_PORTS: set[int] = {11434, 8000, 8001, 8080, 4000}

    PROVIDERS: dict[str, dict[str, object]] = {
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
        # SECURITY: Validate all endpoints at init time
        self._validate_endpoints()

    def _validate_endpoints(self) -> None:
        """SECURITY: Validate all provider endpoints against allowlists.

        Prevents SSRF attacks by ensuring all endpoints are localhost only.

        Raises:
            ValueError: If any endpoint fails validation
        """
        for key, cfg in self.PROVIDERS.items():
            endpoint = str(cfg.get("endpoint", ""))
            parsed = urlparse(endpoint)

            # Validate scheme
            if parsed.scheme not in ("http", "https"):
                raise ValueError(f"Invalid endpoint scheme for {key}: {parsed.scheme}")

            # SECURITY: Validate host (localhost only)
            if parsed.hostname not in self.ALLOWED_HOSTS:
                raise ValueError(f"Invalid endpoint host for {key}: {parsed.hostname}")

            # SECURITY: Validate port
            if parsed.port and parsed.port not in self.ALLOWED_PORTS:
                raise ValueError(f"Invalid endpoint port for {key}: {parsed.port}")

            logger.debug(f"✓ Validated endpoint for {key}: {endpoint}")

    # --------------------------- System Helpers ---------------------------------

    def _service_name(self, key: str) -> str | None:
        """Get systemd service name for provider key.

        Args:
            key: Provider key (e.g., "ollama", "vllm")

        Returns:
            Service name or None if provider not found
        """
        record = self.PROVIDERS.get(key)
        return None if record is None else str(record["service"])

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

    def _collect_process_metrics(self, key: str) -> tuple[int | None, float, float]:
        """Collect CPU and memory metrics for a provider process.

        Args:
            key: Provider key

        Returns:
            Tuple of (pid, cpu_percent, memory_mb)
        """
        pid = self._get_service_pid(key)
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
        provider_type = str(self.PROVIDERS[key]["type"])
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
        elapsed_ms = 0.0

        for key, cfg in self.PROVIDERS.items():
            notes: list[str] = []
            endpoint = str(cfg["endpoint"])
            required = bool(cfg["required"])
            display = str(cfg["display"])

            start = time.perf_counter()
            status = "inactive"
            models = 0

            try:
                response = requests.get(endpoint, timeout=self.http_timeout)
                elapsed_ms = (time.perf_counter() - start) * 1000

                if response.ok:
                    try:
                        payload = response.json()
                        status = "active"
                        models = self._parse_models(key, payload)
                        logger.debug(f"{key}: ✓ Active with {models} models ({elapsed_ms:.0f}ms)")
                    except ValueError as e:
                        logger.error(f"{key}: Invalid JSON response: {e}")
                        notes.append("Invalid JSON payload")
                        status = "degraded" if required else "inactive"
                else:
                    reason = f"HTTP {response.status_code}"
                    if response.reason:
                        reason += f" ({response.reason})"
                    logger.warning(f"{key}: Provider responded with {reason}")
                    notes.append(reason)
                    status = "degraded" if required else "inactive"
            except requests.exceptions.Timeout:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.warning(f"{key}: Request timeout after {elapsed_ms:.0f}ms")
                notes.append(f"Timeout ({elapsed_ms:.0f}ms)")
                status = "degraded" if required else "inactive"
            except requests.exceptions.ConnectionError as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.warning(f"{key}: Connection error: {str(e)[:50]}")
                notes.append("Connection refused")
                status = "degraded" if required else "inactive"
            except requests.exceptions.RequestException as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.warning(f"{key}: Request failed ({type(e).__name__}): {str(e)[:50]}")
                notes.append(f"{type(e).__name__}")
                status = "degraded" if required else "inactive"
            except Exception as e:  # pragma: no cover - unexpected errors
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(f"{key}: Unexpected error: {type(e).__name__}: {e}")
                notes.append(f"Unexpected error: {type(e).__name__}")
                status = "degraded" if required else "inactive"

            pid, cpu_percent, memory_mb = self._collect_process_metrics(key)
            memory_percent = (memory_mb / system_memory_total * 100) if system_memory_total else 0.0
            vram_mb, vram_percent = per_pid_vram.get(pid, (0.0, 0.0)) if pid else (0.0, 0.0)

            metrics.append(
                ServiceMetrics(
                    key=key,
                    display=display,
                    required=required,
                    status=status,
                    port=urlparse(endpoint).port,
                    models=models,
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    memory_percent=memory_percent,
                    vram_mb=vram_mb,
                    vram_percent=vram_percent,
                    response_ms=elapsed_ms,
                    pid=pid,
                    notes=notes,
                )
            )

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

        service = self._service_name(key)
        if not service:
            return False

        try:
            subprocess.run(
                ["systemctl", "--user", action, service],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                # SECURITY: Minimal environment to prevent injection
                env={"PATH": "/usr/bin:/bin"},
            )
        except subprocess.SubprocessError as e:
            logger.debug(f"systemctl {action} {key} failed: {type(e).__name__}")
            return False

        return True
