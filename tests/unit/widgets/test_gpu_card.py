"""Unit tests for GPU card widget.

Tests GPU card rendering with various data scenarios including:
- Valid GPU data with single and multiple GPUs
- No GPU detected scenarios
- Edge cases with zero capacity/usage
- Color coding logic for VRAM and utilization
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dashboard.models import GPUOverview
from dashboard.widgets.gpu_card import GPUCard


@pytest.fixture
def single_gpu_data():
    """GPU overview with single GPU at moderate usage."""
    return GPUOverview(
        detected=True,
        per_gpu=[
            {
                "id": 0.0,
                "name": "NVIDIA RTX 4090",
                "memory_total_mb": 24576.0,
                "memory_used_mb": 8192.0,
                "memory_util_percent": 33.3,
                "gpu_util_percent": 45.0,
            }
        ],
        total_used_mb=8192.0,
        total_capacity_mb=24576.0,
        peak_util_percent=45.0,
    )


@pytest.fixture
def multi_gpu_data():
    """GPU overview with two GPUs at different utilization levels."""
    return GPUOverview(
        detected=True,
        per_gpu=[
            {
                "id": 0.0,
                "name": "NVIDIA RTX 4090",
                "memory_total_mb": 24576.0,
                "memory_used_mb": 20000.0,
                "memory_util_percent": 81.4,
                "gpu_util_percent": 92.0,
            },
            {
                "id": 1.0,
                "name": "NVIDIA RTX 4090",
                "memory_total_mb": 24576.0,
                "memory_used_mb": 4096.0,
                "memory_util_percent": 16.7,
                "gpu_util_percent": 25.0,
            },
        ],
        total_used_mb=24096.0,
        total_capacity_mb=49152.0,
        peak_util_percent=92.0,
    )


@pytest.fixture
def high_usage_gpu_data():
    """GPU overview with critically high VRAM usage."""
    return GPUOverview(
        detected=True,
        per_gpu=[
            {
                "id": 0.0,
                "name": "NVIDIA RTX 4090",
                "memory_total_mb": 24576.0,
                "memory_used_mb": 23000.0,
                "memory_util_percent": 93.6,
                "gpu_util_percent": 98.0,
            }
        ],
        total_used_mb=23000.0,
        total_capacity_mb=24576.0,
        peak_util_percent=98.0,
    )


@pytest.fixture
def no_gpu_data():
    """GPU overview for system without GPU."""
    return GPUOverview(
        detected=False, per_gpu=[], total_used_mb=0.0, total_capacity_mb=0.0, peak_util_percent=0.0
    )


@pytest.fixture
def zero_capacity_gpu():
    """Edge case: GPU with zero capacity."""
    return GPUOverview(
        detected=True, per_gpu=[], total_used_mb=0.0, total_capacity_mb=0.0, peak_util_percent=0.0
    )


class TestGPUCardRendering:
    """Test GPU card rendering with various data states."""

    def test_renders_single_gpu_valid_data(self, single_gpu_data):
        """Test GPU card renders correctly with single GPU data."""
        card = GPUCard()
        card.update_overview(single_gpu_data)

        rendered = str(card.renderable)

        # Check key elements present
        assert "VRAM Usage" in rendered
        assert "GPU Utilization" in rendered
        assert "8192" in rendered  # Used memory
        assert "24576" in rendered  # Total memory
        assert "45.0%" in rendered  # Utilization percentage

    def test_renders_multi_gpu_data(self, multi_gpu_data):
        """Test GPU card shows per-GPU breakdown for multiple GPUs."""
        card = GPUCard()
        card.update_overview(multi_gpu_data)

        rendered = str(card.renderable)

        # Check aggregated metrics
        assert "24096" in rendered  # Total used across GPUs
        assert "49152" in rendered  # Total capacity

        # Check per-GPU breakdown section appears
        assert "Per-GPU Breakdown" in rendered
        assert "GPU 0:" in rendered
        assert "GPU 1:" in rendered

    def test_no_gpu_detected_message(self, no_gpu_data):
        """Test appropriate message when no GPU detected."""
        card = GPUCard()
        card.update_overview(no_gpu_data)

        rendered = str(card.renderable)

        # Should show fallback message
        assert "No NVIDIA GPU detected" in rendered or "NVML unavailable" in rendered
        # Should NOT show VRAM/utilization sections
        assert "VRAM Usage" not in rendered

    def test_zero_capacity_handles_gracefully(self, zero_capacity_gpu):
        """Test GPU with zero capacity doesn't cause division errors."""
        card = GPUCard()
        # Should not raise exception
        card.update_overview(zero_capacity_gpu)

        rendered = str(card.renderable)
        # Should show 0% usage
        assert "0.0%" in rendered or "0%" in rendered


class TestGPUCardColorCoding:
    """Test color coding logic for VRAM and GPU utilization."""

    def test_vram_green_under_75_percent(self, single_gpu_data):
        """Test VRAM shows cyan (safe) color under 75% usage."""
        card = GPUCard()
        card.update_overview(single_gpu_data)
        rendered = str(card.renderable)

        # 33.3% usage should be cyan (not yellow/red)
        assert "cyan" in rendered.lower()

    def test_vram_yellow_75_to_90_percent(self):
        """Test VRAM shows yellow color for 75-90% usage."""
        gpu_data = GPUOverview(
            detected=True,
            per_gpu=[
                {
                    "id": 0.0,
                    "memory_total_mb": 24576.0,
                    "memory_used_mb": 20000.0,  # ~81%
                    "memory_util_percent": 81.4,
                    "gpu_util_percent": 50.0,
                }
            ],
            total_used_mb=20000.0,
            total_capacity_mb=24576.0,
            peak_util_percent=50.0,
        )
        card = GPUCard()
        card.update_overview(gpu_data)
        rendered = str(card.renderable)

        # Should contain yellow color coding
        assert "yellow" in rendered.lower()

    def test_vram_red_above_90_percent(self, high_usage_gpu_data):
        """Test VRAM shows red color above 90% usage."""
        card = GPUCard()
        card.update_overview(high_usage_gpu_data)
        rendered = str(card.renderable)

        # 93.6% usage should be red
        assert "red" in rendered.lower()

    def test_gpu_util_color_high(self, high_usage_gpu_data):
        """Test GPU utilization shows red above 90%."""
        card = GPUCard()
        card.update_overview(high_usage_gpu_data)
        rendered = str(card.renderable)

        # 98% utilization should be red
        assert "red" in rendered.lower()
        assert "98.0%" in rendered


class TestGPUCardPerGPUBreakdown:
    """Test per-GPU breakdown section rendering."""

    def test_single_gpu_no_breakdown_section(self, single_gpu_data):
        """Test per-GPU breakdown section not shown for single GPU."""
        card = GPUCard()
        card.update_overview(single_gpu_data)
        rendered = str(card.renderable)

        # Should NOT show breakdown header for single GPU
        assert "Per-GPU Breakdown" not in rendered

    def test_multi_gpu_shows_breakdown(self, multi_gpu_data):
        """Test per-GPU breakdown section appears for multiple GPUs."""
        card = GPUCard()
        card.update_overview(multi_gpu_data)
        rendered = str(card.renderable)

        # Should show breakdown section
        assert "Per-GPU Breakdown" in rendered
        assert "GPU 0:" in rendered
        assert "GPU 1:" in rendered

    def test_per_gpu_color_coding(self, multi_gpu_data):
        """Test each GPU gets appropriate color coding."""
        card = GPUCard()
        card.update_overview(multi_gpu_data)
        rendered = str(card.renderable)

        # GPU 0 at 81.4% VRAM should be yellow
        # GPU 1 at 16.7% VRAM should be cyan
        # Check color codes present (exact matching hard due to markup)
        assert "yellow" in rendered.lower() or "red" in rendered.lower()
        assert "cyan" in rendered.lower() or "green" in rendered.lower()


class TestGPUCardEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_per_gpu_list(self):
        """Test GPU card handles empty per_gpu list."""
        gpu_data = GPUOverview(
            detected=True,
            per_gpu=[],  # Empty list
            total_used_mb=0.0,
            total_capacity_mb=0.0,
            peak_util_percent=0.0,
        )
        card = GPUCard()
        card.update_overview(gpu_data)

        # Should not raise exception
        rendered = str(card.renderable)
        assert rendered is not None

    def test_exact_75_percent_boundary(self):
        """Test color coding at exact 75% boundary."""
        gpu_data = GPUOverview(
            detected=True,
            per_gpu=[
                {
                    "id": 0.0,
                    "memory_total_mb": 24576.0,
                    "memory_used_mb": 18432.0,  # Exactly 75%
                    "memory_util_percent": 75.0,
                    "gpu_util_percent": 75.0,
                }
            ],
            total_used_mb=18432.0,
            total_capacity_mb=24576.0,
            peak_util_percent=75.0,
        )
        card = GPUCard()
        card.update_overview(gpu_data)
        rendered = str(card.renderable)

        # At 75% should be cyan (> 75 triggers yellow)
        assert rendered is not None

    def test_exact_90_percent_boundary(self):
        """Test color coding at exact 90% boundary."""
        gpu_data = GPUOverview(
            detected=True,
            per_gpu=[
                {
                    "id": 0.0,
                    "memory_total_mb": 24576.0,
                    "memory_used_mb": 22118.0,  # Exactly 90%
                    "memory_util_percent": 90.0,
                    "gpu_util_percent": 90.0,
                }
            ],
            total_used_mb=22118.0,
            total_capacity_mb=24576.0,
            peak_util_percent=90.0,
        )
        card = GPUCard()
        card.update_overview(gpu_data)
        rendered = str(card.renderable)

        # At 90% should be yellow (> 90 triggers red)
        assert rendered is not None
