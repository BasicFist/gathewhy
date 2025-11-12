"""Unit tests for service controls widget.

Tests service control button functionality including:
- Button state management based on service status
- Message emission when buttons pressed
- Handling services with/without controls enabled
- Status message formatting
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
from dashboard.widgets.service_controls import ServiceControls


@pytest.fixture
def active_service():
    """Service metrics for active service with controls enabled."""
    return ServiceMetrics(
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
        controls_enabled=True,
    )


@pytest.fixture
def degraded_service():
    """Service metrics for degraded service."""
    return ServiceMetrics(
        key="vllm",
        display="vLLM",
        required=False,
        status="degraded",
        port=8001,
        endpoint="http://localhost:8001/v1/models",
        models=2,
        cpu_percent=75.0,
        memory_mb=4096.0,
        memory_percent=20.0,
        vram_mb=8192.0,
        vram_percent=40.0,
        response_ms=500.0,
        pid=23456,
        controls_enabled=True,
    )


@pytest.fixture
def inactive_service():
    """Service metrics for inactive service."""
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
    )


@pytest.fixture
def controls_disabled_service():
    """Service metrics with controls disabled."""
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
        controls_enabled=False,  # Controls disabled
    )


class TestServiceControlsInitialization:
    """Test service controls widget initialization."""

    def test_initializes_without_service(self):
        """Test widget initializes with no service selected."""
        controls = ServiceControls()
        assert controls._current is None

    def test_compose_creates_buttons(self):
        """Test compose method creates all control buttons."""
        controls = ServiceControls()
        widgets = list(controls.compose())

        # Should have container with buttons and status
        assert len(widgets) > 0

    @patch("dashboard.widgets.service_controls.Button")
    @patch("dashboard.widgets.service_controls.Static")
    def test_mount_stores_button_references(self, mock_static, mock_button):
        """Test on_mount stores references to buttons."""
        controls = ServiceControls()

        # Mock query_one to return mock buttons
        mock_start = MagicMock()
        mock_stop = MagicMock()
        mock_restart = MagicMock()

        def mock_query_one(selector, widget_type):
            if "start" in selector:
                return mock_start
            if "stop" in selector:
                return mock_stop
            if "restart" in selector:
                return mock_restart
            return MagicMock()

        controls.query_one = mock_query_one
        controls.on_mount()

        # Should have stored button references
        assert "start" in controls._buttons
        assert "stop" in controls._buttons
        assert "restart" in controls._buttons


class TestServiceControlsButtonState:
    """Test button enabled/disabled state management."""

    def test_buttons_disabled_no_service(self):
        """Test buttons disabled when no service selected."""
        controls = ServiceControls()
        controls._buttons = {
            "start": MagicMock(),
            "stop": MagicMock(),
            "restart": MagicMock(),
        }
        controls._status = MagicMock()

        controls.update_state(None)

        # All buttons should be disabled
        for button in controls._buttons.values():
            assert button.disabled is True

    def test_buttons_enabled_active_service(self, active_service):
        """Test buttons enabled for service with controls enabled."""
        controls = ServiceControls()
        controls._buttons = {
            "start": MagicMock(),
            "stop": MagicMock(),
            "restart": MagicMock(),
        }
        controls._status = MagicMock()

        controls.update_state(active_service)

        # All buttons should be enabled
        for button in controls._buttons.values():
            assert button.disabled is False

    def test_buttons_disabled_controls_unavailable(self, controls_disabled_service):
        """Test buttons disabled when service controls unavailable."""
        controls = ServiceControls()
        controls._buttons = {
            "start": MagicMock(),
            "stop": MagicMock(),
            "restart": MagicMock(),
        }
        controls._status = MagicMock()

        controls.update_state(controls_disabled_service)

        # All buttons should be disabled
        for button in controls._buttons.values():
            assert button.disabled is True


class TestServiceControlsStatusMessage:
    """Test status message formatting."""

    def test_status_message_no_service(self):
        """Test status message when no service selected."""
        controls = ServiceControls()
        controls._buttons = {"start": MagicMock(), "stop": MagicMock(), "restart": MagicMock()}
        controls._status = MagicMock()

        controls.update_state(None)

        # Should show selection prompt
        controls._status.update.assert_called()
        call_args = controls._status.update.call_args[0][0]
        assert "Select a service" in call_args.lower()

    def test_status_message_active_service(self, active_service):
        """Test status message for active service."""
        controls = ServiceControls()
        controls._buttons = {"start": MagicMock(), "stop": MagicMock(), "restart": MagicMock()}
        controls._status = MagicMock()

        controls.update_state(active_service)

        # Should show service name and active status
        controls._status.update.assert_called()
        call_args = controls._status.update.call_args[0][0]
        assert "Ollama" in call_args
        assert "active" in call_args.lower()

    def test_status_message_degraded_service(self, degraded_service):
        """Test status message shows degraded status."""
        controls = ServiceControls()
        controls._buttons = {"start": MagicMock(), "stop": MagicMock(), "restart": MagicMock()}
        controls._status = MagicMock()

        controls.update_state(degraded_service)

        # Should show degraded status
        controls._status.update.assert_called()
        call_args = controls._status.update.call_args[0][0]
        assert "degraded" in call_args.lower()

    def test_status_message_inactive_service(self, inactive_service):
        """Test status message shows inactive status."""
        controls = ServiceControls()
        controls._buttons = {"start": MagicMock(), "stop": MagicMock(), "restart": MagicMock()}
        controls._status = MagicMock()

        controls.update_state(inactive_service)

        # Should show inactive status
        controls._status.update.assert_called()
        call_args = controls._status.update.call_args[0][0]
        assert "inactive" in call_args.lower()

    def test_status_message_controls_unavailable(self, controls_disabled_service):
        """Test status message when controls unavailable."""
        controls = ServiceControls()
        controls._buttons = {"start": MagicMock(), "stop": MagicMock(), "restart": MagicMock()}
        controls._status = MagicMock()

        controls.update_state(controls_disabled_service)

        # Should indicate controls unavailable
        controls._status.update.assert_called()
        call_args = controls._status.update.call_args[0][0]
        assert "unavailable" in call_args.lower()


class TestServiceControlsButtonActions:
    """Test button press handling and message emission."""

    def test_button_pressed_emits_request_message(self, active_service):
        """Test button press emits Request message with action."""
        controls = ServiceControls()
        controls._current = active_service

        # Create mock button pressed event
        mock_button = MagicMock()
        mock_button.id = "control-start"
        mock_event = MagicMock()
        mock_event.button = mock_button

        # Mock post_message to capture emitted message
        messages = []

        def capture_message(msg):
            messages.append(msg)

        controls.post_message = capture_message

        controls.on_button_pressed(mock_event)

        # Should have emitted Request message
        assert len(messages) == 1
        assert isinstance(messages[0], ServiceControls.Request)
        assert messages[0].action == "start"

    def test_button_pressed_ignored_no_service(self):
        """Test button press ignored when no service selected."""
        controls = ServiceControls()
        controls._current = None

        mock_button = MagicMock()
        mock_button.id = "control-start"
        mock_event = MagicMock()
        mock_event.button = mock_button

        messages = []
        controls.post_message = lambda msg: messages.append(msg)

        controls.on_button_pressed(mock_event)

        # Should not emit message
        assert len(messages) == 0

    def test_button_pressed_ignored_controls_disabled(self, controls_disabled_service):
        """Test button press ignored when controls disabled."""
        controls = ServiceControls()
        controls._current = controls_disabled_service

        mock_button = MagicMock()
        mock_button.id = "control-start"
        mock_event = MagicMock()
        mock_event.button = mock_button

        messages = []
        controls.post_message = lambda msg: messages.append(msg)

        controls.on_button_pressed(mock_event)

        # Should not emit message
        assert len(messages) == 0

    def test_extracts_action_from_button_id(self, active_service):
        """Test action extracted correctly from button ID."""
        controls = ServiceControls()
        controls._current = active_service

        test_cases = [
            ("control-start", "start"),
            ("control-stop", "stop"),
            ("control-restart", "restart"),
        ]

        for button_id, expected_action in test_cases:
            mock_button = MagicMock()
            mock_button.id = button_id
            mock_event = MagicMock()
            mock_event.button = mock_button

            messages = []
            controls.post_message = lambda msg: messages.append(msg)

            controls.on_button_pressed(mock_event)

            assert len(messages) == 1
            assert messages[0].action == expected_action

    def test_ignores_non_control_buttons(self, active_service):
        """Test non-control buttons are ignored."""
        controls = ServiceControls()
        controls._current = active_service

        mock_button = MagicMock()
        mock_button.id = "some-other-button"
        mock_event = MagicMock()
        mock_event.button = mock_button

        messages = []
        controls.post_message = lambda msg: messages.append(msg)

        controls.on_button_pressed(mock_event)

        # Should not emit message
        assert len(messages) == 0


class TestServiceControlsEdgeCases:
    """Test edge cases and error handling."""

    def test_update_buttons_before_mount(self):
        """Test _update_buttons handles being called before mount."""
        controls = ServiceControls()
        # _buttons dict not yet populated
        assert controls._buttons == {}

        # Should not raise exception
        controls._update_buttons()

    def test_update_state_with_missing_status(self):
        """Test update_state handles missing _status widget."""
        controls = ServiceControls()
        controls._buttons = {"start": MagicMock(), "stop": MagicMock(), "restart": MagicMock()}
        controls._status = None  # Status widget not available

        # Should not raise exception
        controls.update_state(None)

    def test_status_icons_complete_coverage(
        self, active_service, degraded_service, inactive_service
    ):
        """Test all status values have corresponding icons."""
        controls = ServiceControls()
        controls._buttons = {"start": MagicMock(), "stop": MagicMock(), "restart": MagicMock()}
        controls._status = MagicMock()

        # Test each status
        for service in [active_service, degraded_service, inactive_service]:
            controls.update_state(service)
            # Should not raise exception and should format message
            controls._status.update.assert_called()
