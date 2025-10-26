"""UI widgets for AI backend dashboard.

This package contains Textual widgets for displaying provider status,
metrics, and service controls.
"""

from .detail import DetailPanel
from .gpu_card import GPUCard
from .overview import OverviewPanel
from .table import ServiceTable

__all__ = ["OverviewPanel", "ServiceTable", "GPUCard", "DetailPanel"]
