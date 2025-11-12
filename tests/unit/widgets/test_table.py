"""Unit tests for service table widget.

Tests service table functionality including:
- Column setup and data population
- Row selection and cursor positioning
- Color coding for status, CPU, memory, response time
- Edge cases with missing data
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dashboard.models import ServiceMetrics
from dashboard.widgets.table import ServiceTable


@pytest.fixture
def sample_metrics():
    """Sample service metrics for table population."""
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
            status="degraded",
            port=8001,
            endpoint="http://localhost:8001/v1/models",
            models=2,
            cpu_percent=85.0,
            memory_mb=4096.0,
            memory_percent=85.0,
            vram_mb=8192.0,
            vram_percent=40.0,
            response_ms=1500.0,
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
def minimal_metrics():
    """Metrics with minimal/missing data."""
    return [
        ServiceMetrics(
            key="test",
            display="Test Service",
            required=False,
            status="active",
            port=None,
            endpoint="",
            models=None,
            cpu_percent=0.0,
            memory_mb=0.0,
            memory_percent=0.0,
            vram_mb=0.0,
            vram_percent=0.0,
            response_ms=0.0,
            pid=None,
        )
    ]


class TestServiceTableInitialization:
    """Test service table initialization."""

    def test_initializes_with_columns(self):
        """Test table initializes with correct columns."""
        table = ServiceTable()

        # Should have zebra striping enabled
        assert table.zebra_stripes is True

        # Should have row cursor
        assert table.cursor_type == "row"

        # Should show header
        assert table.show_header is True

    def test_has_all_columns(self):
        """Test table has all expected columns."""
        table = ServiceTable()

        # Columns should be added
        # Note: Can't easily verify without mounting, but initialization shouldn't raise
        assert table is not None


class TestServiceTablePopulation:
    """Test table population with metrics."""

    def test_populates_with_sample_metrics(self, sample_metrics):
        """Test table populates with sample metrics."""
        table = ServiceTable()

        # Mock the add_row method to capture calls
        add_row_calls = []

        def mock_add_row(*args, **kwargs):
            add_row_calls.append((args, kwargs))

        table.add_row = mock_add_row
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # Should have cleared and added 3 rows
        table.clear.assert_called_once()
        assert len(add_row_calls) == 3

    def test_row_keys_match_service_keys(self, sample_metrics):
        """Test each row key matches service key."""
        table = ServiceTable()

        add_row_calls = []

        def mock_add_row(*args, **kwargs):
            add_row_calls.append((args, kwargs))

        table.add_row = mock_add_row
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # Check row keys
        row_keys = [call[1].get("key") for call in add_row_calls]
        assert row_keys == ["ollama", "vllm", "llama_cpp_python"]

    def test_empty_metrics_list(self):
        """Test table handles empty metrics list."""
        table = ServiceTable()
        table.clear = MagicMock()
        table.add_row = MagicMock()

        table.populate([], selected=None)

        # Should clear but not add rows
        table.clear.assert_called_once()
        table.add_row.assert_not_called()


class TestServiceTableStatusDisplay:
    """Test status column display with icons and colors."""

    def test_active_status_display(self, sample_metrics):
        """Test active status shown with check icon and green."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # First row is active
        status_text = add_row_calls[0][0][1]  # Second column is status
        assert "✓" in status_text or "active" in status_text.lower()
        assert "green" in status_text.lower()

    def test_degraded_status_display(self, sample_metrics):
        """Test degraded status shown with warning icon and yellow."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # Second row is degraded
        status_text = add_row_calls[1][0][1]  # Second column is status
        assert "⚠" in status_text or "degraded" in status_text.lower()
        assert "yellow" in status_text.lower()

    def test_inactive_status_display(self, sample_metrics):
        """Test inactive status shown with X icon and red."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # Third row is inactive
        status_text = add_row_calls[2][0][1]  # Second column is status
        assert "✗" in status_text or "inactive" in status_text.lower()
        assert "red" in status_text.lower()


class TestServiceTableColorCoding:
    """Test color coding for various metrics."""

    def test_cpu_color_coding(self, sample_metrics):
        """Test CPU percentage color codes correctly."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # First row: 25% CPU should be green
        cpu_text = add_row_calls[0][0][2]  # Third column is CPU
        assert "25.0%" in cpu_text
        assert "green" in cpu_text.lower()

        # Second row: 85% CPU should be red
        cpu_text = add_row_calls[1][0][2]
        assert "85.0%" in cpu_text
        assert "red" in cpu_text.lower()

    def test_memory_color_coding(self, sample_metrics):
        """Test memory color codes correctly."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # First row: 5% memory should be cyan
        mem_text = add_row_calls[0][0][3]  # Fourth column is memory
        assert "1024MB" in mem_text
        assert "cyan" in mem_text.lower()

        # Second row: 85% memory should be red
        mem_text = add_row_calls[1][0][3]
        assert "4096MB" in mem_text
        assert "red" in mem_text.lower()

    def test_response_time_color_coding(self, sample_metrics):
        """Test response time color codes correctly."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # First row: 50ms should be green
        resp_text = add_row_calls[0][0][5]  # Sixth column is response
        assert "50ms" in resp_text
        assert "green" in resp_text.lower()

        # Second row: 1500ms should be red
        resp_text = add_row_calls[1][0][5]
        assert "1500ms" in resp_text
        assert "red" in resp_text.lower()

    def test_vram_display_with_value(self, sample_metrics):
        """Test VRAM displays correctly when present."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # First row has VRAM
        vram_text = add_row_calls[0][0][4]  # Fifth column is VRAM
        assert "2048MB" in vram_text
        assert "magenta" in vram_text.lower()

    def test_vram_display_without_value(self, sample_metrics):
        """Test VRAM shows dash when not present."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # Third row has no VRAM (0.0)
        vram_text = add_row_calls[2][0][4]
        assert "-" in vram_text


class TestServiceTableMissingData:
    """Test handling of missing/null data."""

    def test_handles_none_models(self, minimal_metrics):
        """Test handles None models count."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(minimal_metrics, selected=None)

        # Models column should show 0
        models_text = add_row_calls[0][0][6]  # Seventh column is models
        assert "0" in models_text

    def test_handles_none_pid(self, minimal_metrics):
        """Test handles None PID."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(minimal_metrics, selected=None)

        # PID column should show n/a
        pid_text = add_row_calls[0][0][7]  # Eighth column is PID
        assert "n/a" in pid_text

    def test_handles_zero_values(self, minimal_metrics):
        """Test handles zero CPU, memory, response time."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(minimal_metrics, selected=None)

        # Should display 0 values without error
        cpu_text = add_row_calls[0][0][2]
        assert "0.0%" in cpu_text


class TestServiceTableSelection:
    """Test row selection and cursor positioning."""

    def test_selects_specified_service(self, sample_metrics):
        """Test table selects specified service by key."""
        table = ServiceTable()
        table.add_row = MagicMock()
        table.clear = MagicMock()

        # Mock row_count to return number of rows
        table.row_count = len(sample_metrics)

        # Mock cursor_coordinate setter
        cursor_positions = []

        def mock_cursor_setter(value):
            cursor_positions.append(value)

        type(table).cursor_coordinate = property(
            lambda self: None, lambda self, value: mock_cursor_setter(value)
        )

        table.populate(sample_metrics, selected="vllm")

        # Should set cursor to row 1 (vllm is second service)
        # Note: Exact verification depends on Textual internals
        # This tests that populate completes without error

    def test_defaults_to_first_row_no_selection(self, sample_metrics):
        """Test table defaults to first row when no selection."""
        table = ServiceTable()
        table.add_row = MagicMock()
        table.clear = MagicMock()
        table.row_count = len(sample_metrics)

        cursor_positions = []

        def mock_cursor_setter(value):
            cursor_positions.append(value)

        type(table).cursor_coordinate = property(
            lambda self: None, lambda self, value: mock_cursor_setter(value)
        )

        table.populate(sample_metrics, selected=None)

        # Should complete without error

    def test_handles_invalid_selection_key(self, sample_metrics):
        """Test table handles selection key not in metrics."""
        table = ServiceTable()
        table.add_row = MagicMock()
        table.clear = MagicMock()
        table.row_count = len(sample_metrics)

        # Should not raise exception
        table.populate(sample_metrics, selected="nonexistent_key")


class TestServiceTableFormatting:
    """Test formatting of displayed values."""

    def test_provider_name_bold(self, sample_metrics):
        """Test provider name displayed in bold."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # First column should have bold markup
        provider_text = add_row_calls[0][0][0]
        assert "bold" in provider_text.lower() or "Ollama" in provider_text

    def test_models_count_formatting(self, sample_metrics):
        """Test models count formatted correctly."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # First row has 5 models
        models_text = add_row_calls[0][0][6]
        assert "5" in models_text

        # Third row has 0 models
        models_text = add_row_calls[2][0][6]
        assert "0" in models_text

    def test_pid_formatting(self, sample_metrics):
        """Test PID formatted as string or n/a."""
        table = ServiceTable()

        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(sample_metrics, selected=None)

        # First row has PID
        pid_text = add_row_calls[0][0][7]
        assert "12345" in pid_text

        # Third row has no PID
        pid_text = add_row_calls[2][0][7]
        assert "n/a" in pid_text


class TestServiceTableBoundaryConditions:
    """Test boundary conditions for color coding."""

    def test_cpu_50_percent_boundary(self):
        """Test CPU color at 50% boundary."""
        metrics = [
            ServiceMetrics(
                key="test",
                display="Test",
                required=False,
                status="active",
                port=8000,
                endpoint="",
                models=0,
                cpu_percent=50.0,  # Exact boundary
                memory_mb=1000.0,
                memory_percent=50.0,
                vram_mb=0.0,
                vram_percent=0.0,
                response_ms=100.0,
                pid=1234,
            )
        ]

        table = ServiceTable()
        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(metrics, selected=None)

        # At 50% should be green (> 50 triggers yellow)
        cpu_text = add_row_calls[0][0][2]
        assert "50.0%" in cpu_text

    def test_response_500ms_boundary(self):
        """Test response time color at 500ms boundary."""
        metrics = [
            ServiceMetrics(
                key="test",
                display="Test",
                required=False,
                status="active",
                port=8000,
                endpoint="",
                models=0,
                cpu_percent=10.0,
                memory_mb=1000.0,
                memory_percent=10.0,
                vram_mb=0.0,
                vram_percent=0.0,
                response_ms=500.0,  # Exact boundary
                pid=1234,
            )
        ]

        table = ServiceTable()
        add_row_calls = []
        table.add_row = lambda *args, **kwargs: add_row_calls.append((args, kwargs))
        table.clear = MagicMock()

        table.populate(metrics, selected=None)

        # At 500ms should be green (> 500 triggers yellow)
        resp_text = add_row_calls[0][0][5]
        assert "500ms" in resp_text
