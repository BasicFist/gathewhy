"""AI Backend Dashboard - Terminal UI for LLM provider monitoring.

This package provides a comprehensive terminal-based dashboard for monitoring
and managing AI backend LLM provider services including Ollama, vLLM, and
llama.cpp. It displays real-time metrics, GPU usage, and system resources,
plus controls to start/stop/restart services.

Usage:
    Run as a module:
        python3 -m dashboard

    Or run directly:
        python3 scripts/dashboard

Key Features:
    - Real-time provider health monitoring
    - GPU (VRAM) utilization tracking
    - System resource monitoring (CPU, memory)
    - Service lifecycle controls (start/stop/restart)
    - State persistence between sessions

Modules:
    models: Data models (ServiceMetrics, GPUOverview)
    config: Configuration loading and validation
    state: Session state persistence
    monitors: GPU and provider monitoring
    widgets: Textual UI components
    app: Main dashboard application

Version: 2.0.0 (Refactored modular architecture)
"""

from .app import DashboardApp
from .models import GPUOverview, ServiceMetrics

__version__ = "2.0.0"
__all__ = ["DashboardApp", "ServiceMetrics", "GPUOverview"]
