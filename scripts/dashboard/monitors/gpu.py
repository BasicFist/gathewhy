"""GPU monitoring utilities for AI backend dashboard.

This module provides GPU metrics collection using NVIDIA's NVML library,
including VRAM usage and per-process GPU memory attribution.
"""

from __future__ import annotations

import logging
import warnings

logger = logging.getLogger(__name__)


class GPUMonitor:
    """Utility helpers around NVIDIA's NVML for VRAM insight.

    Provides methods to query GPU information and per-process VRAM usage.
    Gracefully handles systems without NVIDIA GPUs or CUDA drivers installed.

    Attributes:
        initialized: Whether NVML was successfully initialized
        device_count: Number of NVIDIA GPUs detected
    """

    def __init__(self) -> None:
        """Initialize GPU monitor with NVML.

        Attempts to initialize NVIDIA Management Library. If initialization
        fails (no GPU, no drivers, etc.), sets initialized=False and all
        methods return empty results.
        """
        self.initialized = False
        self.device_count = 0
        self._pynvml = None

        try:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="The pynvml package is deprecated",
                    category=FutureWarning,
                )
                import pynvml

            pynvml.nvmlInit()
            self._pynvml = pynvml
            self.initialized = True
            self.device_count = pynvml.nvmlDeviceGetCount()
            logger.debug(f"GPU monitoring initialized: {self.device_count} device(s) detected")
        except ImportError as e:
            logger.debug(f"NVIDIA GPU driver not available: {e}")
            self.initialized = False
        except (OSError, RuntimeError) as e:
            logger.debug(f"NVIDIA NVML initialization failed: {e}")
            self.initialized = False
        except Exception as e:  # pragma: no cover - unexpected errors
            logger.warning(f"Unexpected error initializing GPU monitor: {type(e).__name__}: {e}")
            self.initialized = False

    def get_gpu_info(self) -> list[dict[str, float]]:
        """Query all GPU information and memory stats.

        Returns:
            List of GPU info dicts with memory and utilization metrics.
            Each dict contains:
                - id: GPU index
                - name: GPU model name
                - memory_total_mb: Total GPU memory in megabytes
                - memory_used_mb: Used GPU memory in megabytes
                - memory_util_percent: Memory utilization percentage
                - gpu_util_percent: GPU compute utilization percentage
            Empty list if GPU monitoring not available.
        """
        if not self.initialized or self._pynvml is None:
            return []

        pynvml = self._pynvml
        info: list[dict[str, float]] = []

        for index in range(self.device_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(index)
                name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            except (OSError, AttributeError, UnicodeDecodeError) as e:
                logger.debug(f"Error querying GPU {index}: {type(e).__name__}: {e}")
                continue
            except Exception as e:  # pragma: no cover - unexpected errors
                logger.warning(f"Unexpected error querying GPU {index}: {type(e).__name__}: {e}")
                continue

            total_mb = memory.total / 1024**2
            used_mb = memory.used / 1024**2

            info.append(
                {
                    "id": float(index),
                    "name": name,
                    "memory_total_mb": total_mb,
                    "memory_used_mb": used_mb,
                    "memory_util_percent": (used_mb / total_mb * 100) if total_mb else 0.0,
                    "gpu_util_percent": float(util.gpu),
                }
            )

        return info

    def get_process_vram(self) -> dict[int, tuple[float, float]]:
        """Return VRAM usage per PID as (used_mb, percentage of associated GPUs).

        Queries all GPUs for running compute processes and aggregates VRAM
        usage per process ID.

        Returns:
            Dict mapping process PIDs to (vram_mb, vram_percent) tuples.
            Empty dict if GPU monitoring not available.
        """
        if not self.initialized or self._pynvml is None:
            return {}

        pynvml = self._pynvml
        usage: dict[int, dict[str, float]] = {}

        for index in range(self.device_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(index)
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_mb = memory.total / 1024**2 if memory.total else 0.0
                processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
            except (OSError, AttributeError) as e:
                logger.debug(f"Error querying GPU {index} processes: {type(e).__name__}: {e}")
                continue
            except Exception as e:  # pragma: no cover - unexpected errors
                logger.warning(
                    f"Unexpected error querying GPU {index} processes: {type(e).__name__}: {e}"
                )
                continue

            for record in processes or []:
                pid = getattr(record, "pid", None)
                used_bytes = getattr(record, "usedGpuMemory", 0)
                if pid is None or used_bytes is None or used_bytes < 0:
                    continue

                used_mb = used_bytes / 1024**2
                bucket = usage.setdefault(pid, {"used": 0.0, "total": 0.0})
                bucket["used"] += used_mb
                if total_mb > 0:
                    bucket["total"] += total_mb

        per_pid: dict[int, tuple[float, float]] = {}
        for pid, values in usage.items():
            total = values["total"] or 0.0
            used = values["used"]
            per_pid[pid] = (used, (used / total * 100) if total else 0.0)

        return per_pid
