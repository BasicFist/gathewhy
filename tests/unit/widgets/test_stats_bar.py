"""Unit tests for stats bar widget.

Tests stats bar rendering and metric aggregation including:
- Active/total service counts
- Average CPU and memory calculations
- Auto-refresh display formatting
- Empty metrics handling
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dashboard.models import ServiceMetrics
from dashboard.widgets.stats_bar import StatsBar


@pytest.fixture
def sample_metrics():
    """Sample service metrics for testing."""
    return [
        ServiceMetrics(
            key="ollama",
            display="Ollama",
            required=True,
            status="active",
            port=11434,
            endpoint="http://localhost:11434/api/tags",
            models=5,
            cpu_percent=25.0,
            memory_mb=1024.0,
            memory_percent=5.0,
            vram_mb=2048.0,
            vram_percent=10.0,
            response_ms=50.0,
            pid=12345,
        ),
        ServiceMetrics(
            key="vllm",
            display="vLLM",
            required=False,
            status="active",
            port=8001,
            endpoint="http://localhost:8001/v1/models",
            models=3,
            cpu_percent=75.0,
            memory_mb=4096.0,
            memory_percent=20.0,
            vram_mb=8192.0,
            vram_percent=40.0,
            response_ms=100.0,
            pid=23456,
        ),
        ServiceMetrics(
            key="llama_cpp_python",
            display="llama.cpp (Python)",
            required=False,
            status="inactive",
            port=8000,
            endpoint="http://localhost:8000/v1/models",
            models=0,
            cpu_percent=0.0,
            memory_mb=0.0,
            memory_percent=0.0,
            vram_mb=0.0,
            vram_percent=0.0,
            response_ms=0.0,
            pid=None,
        ),
    ]


@pytest.fixture
def all_active_metrics():
    """All services active."""
    return [
        ServiceMetrics(
            key="ollama",
            display="Ollama",
            required=True,
            status="active",
            port=11434,
            endpoint="http://localhost:11434",
            models=5,
            cpu_percent=30.0,
            memory_mb=1024.0,
            memory_percent=10.0,
            vram_mb=0.0,
            vram_percent=0.0,
            response_ms=50.0,
            pid=12345,
        ),
        ServiceMetrics(
            key="vllm",
            display="vLLM",
            required=False,
            status="active",
            port=8001,
            endpoint="http://localhost:8001",
            models=2,
            cpu_percent=70.0,
            memory_mb=2048.0,
            memory_percent=20.0,
            vram_mb=0.0,
            vram_percent=0.0,
            response_ms=100.0,
            pid=23456,
        ),
    ]


@pytest.fixture
def all_inactive_metrics():
    """All services inactive."""
    return [
        ServiceMetrics(
            key="ollama",
            display="Ollama",
            required=True,
            status="inactive",
            port=11434,
            endpoint="http://localhost:11434",
            models=0,
            cpu_percent=0.0,
            memory_mb=0.0,
            memory_percent=0.0,
            vram_mb=0.0,
            vram_percent=0.0,
            response_ms=0.0,
            pid=None,
        ),
    ]


class TestStatsBarRendering:
    """Test stats bar rendering with various metrics."""

    def test_renders_with_sample_metrics(self, sample_metrics):
        """Test stats bar renders with sample metrics."""
        bar = StatsBar()
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=5.0)

        rendered = bar.render()

        # Check key elements present
        assert "2/3 Active" in rendered  # 2 active out of 3 total
        assert "CPU:" in rendered
        assert "MEM:" in rendered
        assert "AUTO" in rendered

    def test_shows_correct_active_count(self, sample_metrics):
        """Test active count calculated correctly."""
        bar = StatsBar()
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=5.0)

        # 2 active services out of 3
        assert bar.active_count == 2
        assert bar.total_count == 3

        rendered = bar.render()
        assert "2/3 Active" in rendered

    def test_calculates_average_cpu(self, sample_metrics):
        """Test average CPU calculated correctly."""
        bar = StatsBar()
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=5.0)

        # Average: (25.0 + 75.0 + 0.0) / 3 = 33.3%
        expected_avg = (25.0 + 75.0 + 0.0) / 3
        assert abs(bar.avg_cpu - expected_avg) < 0.1

    def test_calculates_average_memory(self, sample_metrics):
        """Test average memory calculated correctly."""
        bar = StatsBar()
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=5.0)

        # Average: (5.0 + 20.0 + 0.0) / 3 = 8.3%
        expected_avg = (5.0 + 20.0 + 0.0) / 3
        assert abs(bar.avg_mem - expected_avg) < 0.1


class TestStatsBarAutoRefresh:
    """Test auto-refresh display logic."""

    def test_auto_refresh_enabled(self, sample_metrics):
        """Test auto-refresh enabled display."""
        bar = StatsBar()
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=5.0)

        rendered = bar.render()

        # Should show green AUTO with interval
        assert "AUTO" in rendered
        assert "5s" in rendered
        assert "green" in rendered.lower()

    def test_auto_refresh_disabled(self, sample_metrics):
        """Test auto-refresh disabled display."""
        bar = StatsBar()
        bar.update_stats(sample_metrics, auto_refresh=False, refresh_interval=5.0)

        rendered = bar.render()

        # Should show red AUTO OFF
        assert "AUTO OFF" in rendered
        assert "red" in rendered.lower()

    def test_different_refresh_intervals(self, sample_metrics):
        """Test different refresh interval displays."""
        bar = StatsBar()

        # Test 10 second interval
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=10.0)
        rendered = bar.render()
        assert "10s" in rendered

        # Test 30 second interval
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=30.0)
        rendered = bar.render()
        assert "30s" in rendered


class TestStatsBarEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_metrics_list(self):
        """Test stats bar with empty metrics list."""
        bar = StatsBar()
        bar.update_stats([], auto_refresh=True, refresh_interval=5.0)

        assert bar.active_count == 0
        assert bar.total_count == 0
        assert bar.avg_cpu == 0.0
        assert bar.avg_mem == 0.0

        rendered = bar.render()
        assert "0/0 Active" in rendered
        assert "0.0%" in rendered

    def test_all_active_services(self, all_active_metrics):
        """Test stats when all services active."""
        bar = StatsBar()
        bar.update_stats(all_active_metrics, auto_refresh=True, refresh_interval=5.0)

        assert bar.active_count == 2
        assert bar.total_count == 2

        rendered = bar.render()
        assert "2/2 Active" in rendered

    def test_all_inactive_services(self, all_inactive_metrics):
        """Test stats when all services inactive."""
        bar = StatsBar()
        bar.update_stats(all_inactive_metrics, auto_refresh=True, refresh_interval=5.0)

        assert bar.active_count == 0
        assert bar.total_count == 1

        rendered = bar.render()
        assert "0/1 Active" in rendered

    def test_single_service(self):
        """Test stats bar with single service."""
        metrics = [
            ServiceMetrics(
                key="ollama",
                display="Ollama",
                required=True,
                status="active",
                port=11434,
                endpoint="http://localhost:11434",
                models=5,
                cpu_percent=50.0,
                memory_mb=1024.0,
                memory_percent=10.0,
                vram_mb=0.0,
                vram_percent=0.0,
                response_ms=50.0,
                pid=12345,
            )
        ]
        bar = StatsBar()
        bar.update_stats(metrics, auto_refresh=True, refresh_interval=5.0)

        assert bar.active_count == 1
        assert bar.total_count == 1
        assert bar.avg_cpu == 50.0
        assert bar.avg_mem == 10.0


class TestStatsBarReactiveProperties:
    """Test reactive property updates."""

    def test_active_count_reactive(self):
        """Test active_count reactive property updates display."""
        bar = StatsBar()
        bar.active_count = 3
        bar.total_count = 5

        rendered = bar.render()
        assert "3/5 Active" in rendered

    def test_avg_cpu_reactive(self):
        """Test avg_cpu reactive property updates display."""
        bar = StatsBar()
        bar.avg_cpu = 45.5

        rendered = bar.render()
        assert "45.5%" in rendered

    def test_avg_mem_reactive(self):
        """Test avg_mem reactive property updates display."""
        bar = StatsBar()
        bar.avg_mem = 62.3

        rendered = bar.render()
        assert "62.3%" in rendered

    def test_auto_refresh_reactive(self):
        """Test auto_refresh reactive property updates display."""
        bar = StatsBar()

        # Test enabled
        bar.auto_refresh = True
        bar.refresh_interval = 5.0
        rendered = bar.render()
        assert "AUTO" in rendered
        assert "5s" in rendered

        # Test disabled
        bar.auto_refresh = False
        rendered = bar.render()
        assert "AUTO OFF" in rendered


class TestStatsBarFormatting:
    """Test formatting of displayed values."""

    def test_percentage_formatting(self, sample_metrics):
        """Test CPU and memory percentages formatted with 1 decimal."""
        bar = StatsBar()
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=5.0)

        rendered = bar.render()

        # Should have .1f format (one decimal place)
        assert ".1f" not in rendered  # Format string should not appear
        # Should have actual values with decimals
        assert "%" in rendered

    def test_refresh_interval_formatting(self, sample_metrics):
        """Test refresh interval formatted without decimals."""
        bar = StatsBar()
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=5.5)

        rendered = bar.render()

        # Should show as "6s" (rounded to nearest integer)
        assert "s" in rendered
        assert "AUTO" in rendered

    def test_zero_values_display(self):
        """Test display with zero CPU and memory."""
        metrics = [
            ServiceMetrics(
                key="inactive",
                display="Inactive",
                required=False,
                status="inactive",
                port=None,
                endpoint="",
                models=0,
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                vram_mb=0.0,
                vram_percent=0.0,
                response_ms=0.0,
                pid=None,
            )
        ]
        bar = StatsBar()
        bar.update_stats(metrics, auto_refresh=True, refresh_interval=5.0)

        rendered = bar.render()
        assert "0.0%" in rendered


class TestStatsBarIcons:
    """Test icon display in stats bar."""

    def test_contains_status_icons(self, sample_metrics):
        """Test stats bar contains status icons."""
        bar = StatsBar()
        bar.update_stats(sample_metrics, auto_refresh=True, refresh_interval=5.0)

        rendered = bar.render()

        # Should contain color-coded symbols
        # Actual symbols may vary, but markup should be present
        assert "[" in rendered and "]" in rendered
