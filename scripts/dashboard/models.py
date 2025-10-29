"""Data models for AI backend dashboard.

This module defines the core data structures used throughout the dashboard
for representing service metrics, GPU information, and system state.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field


@dataclass
class ServiceMetrics:
    """Snapshot of a provider's health and resource usage.

    Attributes:
        key: Unique provider identifier (e.g., "ollama", "vllm")
        display: Human-readable provider name
        required: Whether provider is required for system operation
        status: Current status ("active", "degraded", "inactive")
        port: Port number the provider listens on
        endpoint: Full HTTP endpoint used for health checks
        models: Number of models available
        cpu_percent: CPU usage percentage
        memory_mb: Memory usage in megabytes
        memory_percent: Memory usage as percentage of total system RAM
        vram_mb: GPU VRAM usage in megabytes
        vram_percent: VRAM usage as percentage of GPU capacity
        response_ms: HTTP endpoint response time in milliseconds
        pid: Process ID of the provider service
        notes: List of warning/error messages
        timestamp: Unix timestamp when metrics were collected
    """

    key: str
    display: str
    required: bool
    status: str
    port: int | None
    endpoint: str
    models: int | None
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    vram_mb: float
    vram_percent: float
    response_ms: float
    pid: int | None
    notes: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        data = asdict(self)
        data["notes"] = self.notes or []
        return data

    @classmethod
    def from_json(cls, data: dict) -> ServiceMetrics:
        """Create instance from JSON-serializable dictionary.

        Args:
            data: Dictionary containing ServiceMetrics fields

        Returns:
            ServiceMetrics instance with data from dictionary
        """
        return cls(
            key=data["key"],
            display=data["display"],
            required=data["required"],
            status=data["status"],
            port=data.get("port"),
            endpoint=data.get("endpoint", ""),
            models=data.get("models"),
            cpu_percent=data.get("cpu_percent", 0.0),
            memory_mb=data.get("memory_mb", 0.0),
            memory_percent=data.get("memory_percent", 0.0),
            vram_mb=data.get("vram_mb", 0.0),
            vram_percent=data.get("vram_percent", 0.0),
            response_ms=data.get("response_ms", 0.0),
            pid=data.get("pid"),
            notes=data.get("notes", []),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class GPUOverview:
    """Aggregated GPU utilization information.

    Attributes:
        detected: Whether NVIDIA GPU was detected
        per_gpu: List of per-GPU metrics dictionaries
        total_used_mb: Total VRAM used across all GPUs in megabytes
        total_capacity_mb: Total VRAM capacity across all GPUs in megabytes
        peak_util_percent: Peak GPU utilization percentage across all GPUs
    """

    detected: bool
    per_gpu: list[dict[str, float]]
    total_used_mb: float
    total_capacity_mb: float
    peak_util_percent: float
