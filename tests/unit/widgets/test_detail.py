"""Unit tests for detail panel widget.

Tests detail panel functionality including:
- Service detail display with various statuses
- Button state management
- Message emission for service actions
- Notes/warnings display
- Handling of missing data
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dashboard.models import ServiceMetrics
from dashboard.widgets.detail import DetailPanel


@pytest.fixture
def active_service_with_notes():
    """Active service with warning notes."""
    return ServiceMetrics(
        key="ollama",
        display="Ollama",
        required=True,
        status="active",
        port=11434,
        endpoint="http://localhost:11434/api/tags",
        models=5,
        cpu_percent=65.0,
        memory_mb=2048.0,
        memory_percent=15.0,
        vram_mb=4096.0,
        vram_percent=20.0,
        response_ms=75.0,
        pid=12345,
        controls_enabled=True,
        notes=["High CPU usage detected", "Memory usage above 50% threshold"],
    )


@pytest.fixture
def degraded_service():
    """Degraded service without notes."""
    return ServiceMetrics(
        key="vllm",
        display="vLLM",
        required=False,
        status="degraded",
        port=8001,
        endpoint="http://localhost:8001/v1/models",
        models=2,
        cpu_percent=85.0,
        memory_mb=8192.0,
        memory_percent=85.0,
        vram_mb=16384.0,
        vram_percent=75.0,
        response_ms=1200.0,
        pid=23456,
        controls_enabled=True,
        notes=[],
    )


@pytest.fixture
def inactive_service():
    """Inactive service."""
    return ServiceMetrics(
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
        controls_enabled=True,
        notes=[],
    )


@pytest.fixture
def controls_disabled_service():
    """Service with controls disabled."""
    return ServiceMetrics(
        key="litellm_gateway",
        display="LiteLLM Gateway",
        required=True,
        status="active",
        port=4000,
        endpoint="http://localhost:4000/health",
        models=None,
        cpu_percent=10.0,
        memory_mb=512.0,
        memory_percent=2.5,
        vram_mb=0.0,
        vram_percent=0.0,
        response_ms=25.0,
        pid=34567,
        controls_enabled=False,
        notes=[],
    )


@pytest.fixture
def minimal_service():
    """Service with minimal data."""
    return ServiceMetrics(
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
        controls_enabled=True,
        notes=[],
    )


class TestDetailPanelInitialization:
    """Test detail panel initialization."""

    def test_initializes_with_no_service(self):
        """Test panel initializes with no service selected."""
        panel = DetailPanel()
        assert panel._current is None

    def test_compose_creates_widgets(self):
        """Test compose creates all child widgets."""
        panel = DetailPanel()
        widgets = list(panel.compose())

        # Should have labels, buttons, and log widget
        assert len(widgets) > 0


class TestDetailPanelDisplay:
    """Test detail panel display for various service states."""

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_displays_active_service(
        self, mock_log, mock_button, mock_label, active_service_with_notes
    ):
        """Test displays active service details correctly."""
        panel = DetailPanel()

        # Mock query_one
        mock_widgets = {
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:  # Log query
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(active_service_with_notes)

        # Should have updated title with service name
        mock_widgets["#detail-title"].update.assert_called()
        title_text = mock_widgets["#detail-title"].update.call_args[0][0]
        assert "Ollama" in title_text
        assert "REQUIRED" in title_text

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_displays_degraded_status(self, mock_log, mock_button, mock_label, degraded_service):
        """Test displays degraded status correctly."""
        panel = DetailPanel()

        mock_widgets = {
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(degraded_service)

        # Should show degraded in status
        mock_widgets["#detail-status"].update.assert_called()
        status_text = mock_widgets["#detail-status"].update.call_args[0][0]
        assert "DEGRADED" in status_text

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_displays_inactive_status(self, mock_log, mock_button, mock_label, inactive_service):
        """Test displays inactive status correctly."""
        panel = DetailPanel()

        mock_widgets = {
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(inactive_service)

        # Should show inactive in status
        mock_widgets["#detail-status"].update.assert_called()
        status_text = mock_widgets["#detail-status"].update.call_args[0][0]
        assert "INACTIVE" in status_text

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_clears_display_when_none(self, mock_log, mock_button, mock_label):
        """Test clears display when no service selected."""
        panel = DetailPanel()

        mock_widgets = {
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(None)

        # Should show selection prompt
        mock_widgets["#detail-title"].update.assert_called()
        title_text = mock_widgets["#detail-title"].update.call_args[0][0]
        assert "Select a provider" in title_text


class TestDetailPanelResourceDisplay:
    """Test resource usage display."""

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_shows_resource_usage(
        self, mock_log, mock_button, mock_label, active_service_with_notes
    ):
        """Test shows CPU, memory, and VRAM usage."""
        panel = DetailPanel()

        mock_widgets = {
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(active_service_with_notes)

        # Should show resources
        mock_widgets["#detail-resources"].update.assert_called()
        resources_text = mock_widgets["#detail-resources"].update.call_args[0][0]
        assert "CPU" in resources_text
        assert "Memory" in resources_text
        assert "VRAM" in resources_text

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_shows_na_for_missing_vram(self, mock_log, mock_button, mock_label, minimal_service):
        """Test shows n/a for missing VRAM."""
        panel = DetailPanel()

        mock_widgets = {
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(minimal_service)

        # Should show n/a for VRAM
        mock_widgets["#detail-resources"].update.assert_called()
        resources_text = mock_widgets["#detail-resources"].update.call_args[0][0]
        assert "n/a" in resources_text


class TestDetailPanelMetadata:
    """Test metadata display."""

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_shows_metadata(self, mock_log, mock_button, mock_label, active_service_with_notes):
        """Test shows endpoint, port, models, PID."""
        panel = DetailPanel()

        mock_widgets = {
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(active_service_with_notes)

        # Should show metadata
        mock_widgets["#detail-metadata"].update.assert_called()
        metadata_text = mock_widgets["#detail-metadata"].update.call_args[0][0]
        assert "Endpoint" in metadata_text
        assert "Port" in metadata_text
        assert "Models" in metadata_text
        assert "PID" in metadata_text
        assert "12345" in metadata_text  # Actual PID value


class TestDetailPanelNotes:
    """Test notes/warnings display."""

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_displays_warning_notes(
        self, mock_log, mock_button, mock_label, active_service_with_notes
    ):
        """Test displays warning notes in log widget."""
        panel = DetailPanel()

        mock_widgets = {
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(active_service_with_notes)

        # Should write notes to log
        mock_log_widget.clear.assert_called()
        assert mock_log_widget.write.call_count >= 3  # Header + 2 notes

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_shows_no_warnings_message(self, mock_log, mock_button, mock_label, degraded_service):
        """Test shows 'no warnings' when notes empty."""
        panel = DetailPanel()

        mock_widgets = {
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(degraded_service)

        # Should show no warnings message
        mock_log_widget.clear.assert_called()
        # Check write calls contain success message
        write_calls = [call[0][0] for call in mock_log_widget.write.call_args_list]
        assert any("No warnings" in call for call in write_calls)


class TestDetailPanelButtonState:
    """Test button enabled/disabled state."""

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_enables_buttons_for_active_service(
        self, mock_log, mock_button, mock_label, active_service_with_notes
    ):
        """Test enables buttons when controls available."""
        panel = DetailPanel()

        mock_buttons = {
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_widgets = {
            **mock_buttons,
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(active_service_with_notes)

        # All buttons should be enabled
        for button in mock_buttons.values():
            assert button.disabled is False

    @patch("dashboard.widgets.detail.Label")
    @patch("dashboard.widgets.detail.Button")
    @patch("dashboard.widgets.detail.Log")
    def test_disables_buttons_when_controls_unavailable(
        self, mock_log, mock_button, mock_label, controls_disabled_service
    ):
        """Test disables buttons when controls unavailable."""
        panel = DetailPanel()

        mock_buttons = {
            "#action-start": MagicMock(),
            "#action-stop": MagicMock(),
            "#action-restart": MagicMock(),
            "#action-enable": MagicMock(),
            "#action-disable": MagicMock(),
        }

        mock_widgets = {
            **mock_buttons,
            "#detail-title": MagicMock(),
            "#detail-status": MagicMock(),
            "#detail-resources": MagicMock(),
            "#detail-metadata": MagicMock(),
        }

        mock_log_widget = MagicMock()

        def mock_query_one(selector, widget_type=None):
            if widget_type is None:
                return mock_log_widget
            return mock_widgets.get(selector, MagicMock())

        panel.query_one = mock_query_one

        panel.update_details(controls_disabled_service)

        # All buttons should be disabled
        for button in mock_buttons.values():
            assert button.disabled is True


class TestDetailPanelButtonActions:
    """Test button action handling."""

    def test_button_pressed_emits_service_action(self, active_service_with_notes):
        """Test button press emits ServiceAction message."""
        panel = DetailPanel()
        panel._current = active_service_with_notes

        # Mock button pressed event
        mock_button = MagicMock()
        mock_button.id = "action-start"
        mock_event = MagicMock()
        mock_event.button = mock_button

        messages = []
        panel.post_message = lambda msg: messages.append(msg)

        panel.handle_button(mock_event)

        # Should emit ServiceAction
        assert len(messages) == 1
        assert isinstance(messages[0], DetailPanel.ServiceAction)
        assert messages[0].action == "start"
        assert messages[0].service_key == "ollama"

    def test_button_pressed_ignored_no_service(self):
        """Test button press ignored when no service."""
        panel = DetailPanel()
        panel._current = None

        mock_button = MagicMock()
        mock_button.id = "action-start"
        mock_event = MagicMock()
        mock_event.button = mock_button

        messages = []
        panel.post_message = lambda msg: messages.append(msg)

        panel.handle_button(mock_event)

        # Should not emit message
        assert len(messages) == 0

    def test_button_pressed_stopped_when_controls_disabled(self, controls_disabled_service):
        """Test button press event stopped when controls disabled."""
        panel = DetailPanel()
        panel._current = controls_disabled_service

        mock_button = MagicMock()
        mock_button.id = "action-start"
        mock_event = MagicMock()
        mock_event.button = mock_button

        messages = []
        panel.post_message = lambda msg: messages.append(msg)

        panel.handle_button(mock_event)

        # Should stop event and not emit message
        mock_event.stop.assert_called()
        assert len(messages) == 0

    def test_extracts_action_from_button_id(self, active_service_with_notes):
        """Test extracts action correctly from button ID."""
        panel = DetailPanel()
        panel._current = active_service_with_notes

        test_cases = [
            ("action-start", "start"),
            ("action-stop", "stop"),
            ("action-restart", "restart"),
            ("action-enable", "enable"),
            ("action-disable", "disable"),
        ]

        for button_id, expected_action in test_cases:
            mock_button = MagicMock()
            mock_button.id = button_id
            mock_event = MagicMock()
            mock_event.button = mock_button

            messages = []
            panel.post_message = lambda msg: messages.append(msg)

            panel.handle_button(mock_event)

            assert len(messages) == 1
            assert messages[0].action == expected_action

    def test_ignores_non_action_buttons(self, active_service_with_notes):
        """Test ignores buttons without action- prefix."""
        panel = DetailPanel()
        panel._current = active_service_with_notes

        mock_button = MagicMock()
        mock_button.id = "some-other-button"
        mock_event = MagicMock()
        mock_event.button = mock_button

        messages = []
        panel.post_message = lambda msg: messages.append(msg)

        panel.handle_button(mock_event)

        # Should not emit message
        assert len(messages) == 0
