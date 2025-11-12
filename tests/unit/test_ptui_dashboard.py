"""Unit tests for PTUI Dashboard (curses-based monitoring interface).

Tests for configuration, validation, authentication, key handling, and core functionality.
These tests verify dashboard logic without requiring curses terminal setup.
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, mock_open, patch
from urllib.error import HTTPError, URLError

import pytest
import yaml


# Import functions from ptui_dashboard
# We'll use dynamic import to avoid curses initialization issues
@pytest.fixture
def ptui_module():
    """Import ptui_dashboard module dynamically."""
    import sys
    from importlib import import_module

    # Add scripts directory to path
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    # Import the module
    module = import_module("ptui_dashboard")
    return module


class TestDashboardSyntax:
    """Test that ptui_dashboard script has valid Python syntax."""

    def test_dashboard_script_syntax(self):
        """Verify ptui_dashboard.py compiles without syntax errors."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ptui_dashboard.py"
        assert dashboard_path.exists(), f"Dashboard script not found at {dashboard_path}"

        # Compile the script to check for syntax errors
        compile_result = subprocess.run(
            ["python3", "-m", "py_compile", str(dashboard_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert (
            compile_result.returncode == 0
        ), f"Dashboard script has syntax errors:\n{compile_result.stderr}"


class TestDashboardDocumentation:
    """Test that PTUI dashboard documentation exists and is complete."""

    def test_dashboard_docs_exist(self):
        """Verify ptui-dashboard documentation file exists."""
        docs_path = Path(__file__).parent.parent.parent / "docs" / "ptui-dashboard.md"
        assert docs_path.exists(), f"Dashboard documentation not found at {docs_path}"

    def test_dashboard_docs_content(self):
        """Verify ptui-dashboard documentation contains key sections."""
        docs_path = Path(__file__).parent.parent.parent / "docs" / "ptui-dashboard.md"

        with open(docs_path) as f:
            content = f.read()

        required_sections = [
            "# PTUI Dashboard",
            "## Quick Start",
            "## Features",
            "## Configuration",
            "## Troubleshooting",
            "## Architecture",
            "## Key Bindings",
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_docs_mentions_connection_model(self):
        """Verify documentation explains the authentication model."""
        docs_path = Path(__file__).parent.parent.parent / "docs" / "ptui-dashboard.md"

        with open(docs_path) as f:
            content = f.read()

        lowered = content.lower()
        assert "connection model" in lowered, "Docs should describe connection model"
        assert "does not require authentication" in lowered, "Docs should state auth is optional"


class TestEnvironmentValidation:
    """Test environment variable validation logic."""

    def test_validate_env_float_valid_value(self, ptui_module):
        """Test valid environment variable passes validation."""
        with patch.dict(os.environ, {"TEST_VAR": "5.5"}):
            result = ptui_module.validate_env_float("TEST_VAR", "10", 1.0, 10.0)
            assert result == 5.5

    def test_validate_env_float_default_value(self, ptui_module):
        """Test missing environment variable returns default."""
        with patch.dict(os.environ, {}, clear=True):
            result = ptui_module.validate_env_float("MISSING_VAR", "7.5", 1.0, 10.0)
            assert result == 7.5

    def test_validate_env_float_below_min(self, ptui_module):
        """Test value below minimum returns default."""
        with patch.dict(os.environ, {"TEST_VAR": "0.1"}):
            result = ptui_module.validate_env_float("TEST_VAR", "5.0", 1.0, 10.0)
            assert result == 5.0

    def test_validate_env_float_above_max(self, ptui_module):
        """Test value above maximum returns default."""
        with patch.dict(os.environ, {"TEST_VAR": "15.0"}):
            result = ptui_module.validate_env_float("TEST_VAR", "5.0", 1.0, 10.0)
            assert result == 5.0

    def test_validate_env_float_invalid_format(self, ptui_module):
        """Test invalid float format returns default."""
        with patch.dict(os.environ, {"TEST_VAR": "not-a-number"}):
            result = ptui_module.validate_env_float("TEST_VAR", "5.0", 1.0, 10.0)
            assert result == 5.0

    def test_validate_env_float_edge_cases(self, ptui_module):
        """Test boundary values are accepted."""
        with patch.dict(os.environ, {"TEST_VAR": "1.0"}):
            result = ptui_module.validate_env_float("TEST_VAR", "5.0", 1.0, 10.0)
            assert result == 1.0

        with patch.dict(os.environ, {"TEST_VAR": "10.0"}):
            result = ptui_module.validate_env_float("TEST_VAR", "5.0", 1.0, 10.0)
            assert result == 10.0


class TestConfigLoading:
    """Test configuration loading from providers.yaml."""

    def test_load_services_default_when_no_config(self, ptui_module, tmp_path):
        """Test default services returned when config doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            services = ptui_module.load_services_from_config()

        assert len(services) == 5
        assert any(s.name == "LiteLLM Gateway" for s in services)
        assert any(s.name == "Ollama" for s in services)
        assert any(s.name == "vLLM" for s in services)

    def test_load_services_from_valid_yaml(self, ptui_module, tmp_path):
        """Test services loaded from valid YAML configuration."""
        config_content = {
            "providers": {
                "ollama": {
                    "type": "ollama",
                    "base_url": "http://localhost:11434",
                    "status": "active",
                },
                "vllm": {
                    "type": "vllm",
                    "base_url": "http://localhost:8001",
                    "status": "active",
                },
            }
        }

        config_path = tmp_path / "providers.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        with patch.object(Path, "__truediv__", return_value=config_path):
            with patch.object(Path, "exists", return_value=True):
                services = ptui_module.load_services_from_config()

        # Should have loaded services from config
        assert len(services) >= 2
        assert any(s.name == "Ollama" for s in services)

    def test_load_services_inactive_provider_skipped(self, ptui_module, tmp_path):
        """Test inactive providers are not loaded."""
        config_content = {
            "providers": {
                "ollama": {
                    "type": "ollama",
                    "base_url": "http://localhost:11434",
                    "status": "active",
                },
                "vllm": {
                    "type": "vllm",
                    "base_url": "http://localhost:8001",
                    "status": "inactive",
                },
            }
        }

        config_path = tmp_path / "providers.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        with patch.object(Path, "__truediv__", return_value=config_path):
            with patch.object(Path, "exists", return_value=True):
                services = ptui_module.load_services_from_config()

        # Inactive provider should not be loaded
        assert not any(s.name == "vLLM" for s in services if s.url == "http://localhost:8001")

    def test_load_services_yaml_error_returns_defaults(self, ptui_module):
        """Test defaults returned when YAML parsing fails."""
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid: yaml: content:")):
                services = ptui_module.load_services_from_config()

        # Should return defaults on error
        assert len(services) == 5
        assert any(s.name == "LiteLLM Gateway" for s in services)

    def test_load_services_no_yaml_library(self, ptui_module):
        """Test defaults returned when yaml library not available."""
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'yaml'")):
                services = ptui_module.load_services_from_config()

        # Should return defaults when yaml unavailable
        assert len(services) == 5


class TestFetchJSON:
    """Test JSON fetching from LiteLLM."""

    def test_fetch_json_success_no_auth(self, ptui_module):
        """Test successful JSON fetch without authentication."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"status": "ok"}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("ptui_dashboard.urlopen", return_value=mock_response):
            data, latency, error = ptui_module.fetch_json("http://localhost:4000/health", 10.0)

        assert data == {"status": "ok"}
        assert latency is not None
        assert latency >= 0
        assert error is None

    def test_fetch_json_sets_user_agent_only(self, ptui_module):
        """Test JSON fetch uses a static User-Agent without auth headers."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"models": []}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("ptui_dashboard.urlopen", return_value=mock_response):
            with patch("ptui_dashboard.Request") as mock_request:
                data, latency, error = ptui_module.fetch_json(
                    "http://localhost:4000/v1/models", 10.0
                )

                call_args = mock_request.call_args
                assert call_args is not None
                headers = call_args[1]["headers"]
                assert headers == {"User-Agent": "ptui-dashboard"}

        assert data == {"models": []}
        assert error is None

    def test_fetch_json_http_error(self, ptui_module):
        """Test HTTP error handling."""
        with patch(
            "ptui_dashboard.urlopen", side_effect=HTTPError("url", 500, "Server Error", {}, None)
        ):
            data, latency, error = ptui_module.fetch_json("http://localhost:4000/fail", 10.0)

        assert data is None
        assert latency is not None
        assert error is not None
        assert "500" in error

    def test_fetch_json_url_error(self, ptui_module):
        """Test URL error handling (connection refused, etc)."""
        with patch("ptui_dashboard.urlopen", side_effect=URLError("Connection refused")):
            data, latency, error = ptui_module.fetch_json("http://localhost:9999", 10.0)

        assert data is None
        assert latency is not None
        assert error is not None
        assert "Connection refused" in error

    def test_fetch_json_timeout_error(self, ptui_module):
        """Test timeout error handling."""
        with patch("ptui_dashboard.urlopen", side_effect=TimeoutError("Request timed out")):
            data, latency, error = ptui_module.fetch_json("http://localhost:4000/slow", 1.0)

        assert data is None
        assert latency is not None
        assert error is not None


class TestServiceChecking:
    """Test service health checking logic."""

    def test_check_service_healthy(self, ptui_module):
        """Test service check returns healthy status."""
        service = ptui_module.Service("Test Service", "http://localhost:4000", "/health", True)

        with patch("ptui_dashboard.fetch_json", return_value=({"status": "ok"}, 0.1, None)):
            result = ptui_module.check_service(service, 10.0)

        assert result["service"] == service
        assert result["status"] is True
        assert result["latency"] == 0.1
        assert result["error"] is None

    def test_check_service_unhealthy(self, ptui_module):
        """Test service check returns unhealthy status."""
        service = ptui_module.Service("Test Service", "http://localhost:9999", "/health", True)

        with patch("ptui_dashboard.fetch_json", return_value=(None, 0.5, "Connection refused")):
            result = ptui_module.check_service(service, 10.0)

        assert result["service"] == service
        assert result["status"] is False
        assert result["latency"] == 0.5
        assert result["error"] == "Connection refused"


class TestModelFetching:
    """Test model list fetching from LiteLLM."""

    def test_get_models_success(self, ptui_module):
        """Test successful model list retrieval."""
        mock_data = {"data": [{"id": "llama3.1:8b"}, {"id": "qwen2.5-coder:7b"}]}

        with patch("ptui_dashboard.fetch_json", return_value=(mock_data, 0.2, None)):
            result = ptui_module.get_models(10.0)

        assert result["models"] == ["llama3.1:8b", "qwen2.5-coder:7b"]
        assert result["error"] is None
        assert result["latency"] == 0.2

    def test_get_models_calls_gateway_without_auth(self, ptui_module):
        """Test model fetching hits LiteLLM without auth headers."""
        mock_data = {"data": [{"id": "model1"}]}

        with patch("ptui_dashboard.fetch_json", return_value=(mock_data, 0.1, None)) as mock_fetch:
            ptui_module.get_models(10.0)

            mock_fetch.assert_called_once_with("http://localhost:4000/v1/models", 10.0)

    def test_get_models_error(self, ptui_module):
        """Test model fetching handles errors."""
        with patch("ptui_dashboard.fetch_json", return_value=(None, 0.5, "Auth failed")):
            result = ptui_module.get_models(10.0)

        assert result["models"] == []
        assert result["error"] == "Auth failed"
        assert result["latency"] == 0.5

    def test_get_models_empty_response(self, ptui_module):
        """Test model fetching handles empty data."""
        with patch("ptui_dashboard.fetch_json", return_value=({}, 0.1, None)):
            result = ptui_module.get_models(10.0)

        assert result["models"] == []
        assert result["error"] is not None


class TestLatencyFormatting:
    """Test latency formatting utility."""

    def test_format_latency_none(self, ptui_module):
        """Test None latency returns placeholder."""
        assert ptui_module.format_latency(None) == "--"

    def test_format_latency_milliseconds(self, ptui_module):
        """Test sub-second latency formatted as milliseconds."""
        assert ptui_module.format_latency(0.0123) == "12ms"
        assert ptui_module.format_latency(0.456) == "456ms"
        assert ptui_module.format_latency(0.999) == "999ms"

    def test_format_latency_seconds(self, ptui_module):
        """Test multi-second latency formatted as seconds."""
        assert ptui_module.format_latency(1.0) == "1.00s"
        assert ptui_module.format_latency(2.5) == "2.50s"
        assert ptui_module.format_latency(10.123) == "10.12s"

    def test_format_latency_edge_cases(self, ptui_module):
        """Test edge cases in latency formatting."""
        assert ptui_module.format_latency(0.0) == "0ms"
        assert ptui_module.format_latency(0.0001) == "0ms"
        assert ptui_module.format_latency(1.0) == "1.00s"


class TestStateGathering:
    """Test state gathering and aggregation."""

    def test_gather_state_all_healthy(self, ptui_module):
        """Test state gathering with all services healthy."""
        mock_services = [
            ptui_module.Service("Service1", "http://localhost:4000", "/health", True),
            ptui_module.Service("Service2", "http://localhost:11434", "/health", True),
        ]

        with patch("ptui_dashboard.SERVICES", mock_services):
            with patch("ptui_dashboard.check_service") as mock_check:
                mock_check.side_effect = [
                    {"service": mock_services[0], "status": True, "latency": 0.1, "error": None},
                    {"service": mock_services[1], "status": True, "latency": 0.2, "error": None},
                ]
                with patch(
                    "ptui_dashboard.get_models",
                    return_value={"models": ["model1"], "error": None, "latency": 0.1},
                ):
                    state = ptui_module.gather_state(10.0)

        assert len(state["services"]) == 2
        assert state["summary"]["required"] == (2, 2)
        assert "models" in state
        assert "timestamp" in state

    def test_gather_state_mixed_health(self, ptui_module):
        """Test state gathering with mixed service health."""
        mock_services = [
            ptui_module.Service("RequiredService", "http://localhost:4000", "/health", True),
            ptui_module.Service("OptionalService", "http://localhost:8001", "/health", False),
        ]

        with patch("ptui_dashboard.SERVICES", mock_services):
            with patch("ptui_dashboard.check_service") as mock_check:
                mock_check.side_effect = [
                    {"service": mock_services[0], "status": True, "latency": 0.1, "error": None},
                    {
                        "service": mock_services[1],
                        "status": False,
                        "latency": 0.5,
                        "error": "Connection refused",
                    },
                ]
                with patch(
                    "ptui_dashboard.get_models",
                    return_value={"models": [], "error": None, "latency": 0.1},
                ):
                    state = ptui_module.gather_state(10.0)

        assert state["summary"]["required"] == (1, 1)
        assert state["summary"]["optional"] == (0, 1)


class TestActions:
    """Test action handlers."""

    def test_action_refresh_state(self, ptui_module):
        """Test refresh state action."""
        mock_state = {
            "services": [],
            "models": {"models": [], "error": None},
            "summary": {"required": (1, 1), "optional": (0, 0)},
        }

        with patch("ptui_dashboard.gather_state_smart", return_value=mock_state):
            message, new_state = ptui_module.action_refresh_state({})

        assert "refreshed" in message.lower()
        assert new_state == mock_state

    def test_action_health_probe_all_healthy(self, ptui_module):
        """Test health probe with all services healthy."""
        mock_state = {
            "services": [
                {
                    "service": ptui_module.Service("S1", "url", "/h", True),
                    "status": True,
                    "latency": 0.1,
                    "error": None,
                }
            ],
            "models": {"models": [], "error": None},
            "summary": {"required": (1, 1), "optional": (0, 0)},
        }

        with patch("ptui_dashboard.gather_state_smart", return_value=mock_state):
            message, new_state = ptui_module.action_health_probe({})

        assert "all required services online" in message.lower()
        assert new_state == mock_state

    def test_action_health_probe_failures(self, ptui_module):
        """Test health probe with failing services."""
        mock_services = [
            ptui_module.Service("FailingService", "url", "/h", True),
        ]
        mock_state = {
            "services": [
                {
                    "service": mock_services[0],
                    "status": False,
                    "latency": 0.5,
                    "error": "Connection refused",
                }
            ],
            "models": {"models": [], "error": None},
            "summary": {"required": (0, 1), "optional": (0, 0)},
        }

        with patch("ptui_dashboard.gather_state_smart", return_value=mock_state):
            message, new_state = ptui_module.action_health_probe({})

        assert "failing" in message.lower()
        assert "FailingService" in message

    def test_action_run_validation_success(self, ptui_module):
        """Test validation action succeeds."""
        with patch("ptui_dashboard.run_validation", return_value="Validation succeeded."):
            message, new_state = ptui_module.action_run_validation({})

        assert "succeeded" in message.lower()
        assert new_state is None

    def test_action_run_validation_failure(self, ptui_module):
        """Test validation action handles failure."""
        with patch(
            "ptui_dashboard.run_validation", return_value="Validation failed (exit 1). See logs."
        ):
            message, new_state = ptui_module.action_run_validation({})

        assert "failed" in message.lower()
        assert new_state is None


class TestKeyHandlers:
    """Test keyboard input handlers."""

    def test_handle_menu_keys_up_down(self, ptui_module):
        """Test menu navigation with up/down arrows."""
        import curses

        menu_items = [
            ptui_module.MenuItem("Item1", "desc1", None, False),
            ptui_module.MenuItem("Item2", "desc2", None, False),
            ptui_module.MenuItem("Item3", "desc3", None, False),
        ]

        # Down arrow
        new_index, focus, msg = ptui_module.handle_menu_keys(curses.KEY_DOWN, 0, menu_items)
        assert new_index == 1
        assert focus == "menu"

        # Up arrow (wrap around)
        new_index, focus, msg = ptui_module.handle_menu_keys(curses.KEY_UP, 0, menu_items)
        assert new_index == 2
        assert focus == "menu"

    def test_handle_menu_keys_focus_content(self, ptui_module):
        """Test switching focus to content panel."""
        import curses

        menu_items = [
            ptui_module.MenuItem("Operations", "desc", None, supports_actions=True),
        ]

        # Tab key should switch to content
        new_index, focus, msg = ptui_module.handle_menu_keys(9, 0, menu_items)  # Tab = 9
        assert focus == "content"
        assert "focused" in msg.lower()

        # Enter key should also switch
        new_index, focus, msg = ptui_module.handle_menu_keys(curses.KEY_ENTER, 0, menu_items)
        assert focus == "content"

    def test_handle_menu_keys_no_actions(self, ptui_module):
        """Test Tab on item without actions stays in menu."""

        menu_items = [
            ptui_module.MenuItem("Overview", "desc", None, supports_actions=False),
        ]

        # Tab should not switch focus if item doesn't support actions
        new_index, focus, msg = ptui_module.handle_menu_keys(9, 0, menu_items)
        assert focus == "menu"

    def test_handle_action_keys_navigation(self, ptui_module):
        """Test action panel navigation."""
        import curses

        action_items = [
            ptui_module.ActionItem("Action1", "desc1", None),
            ptui_module.ActionItem("Action2", "desc2", None),
            ptui_module.ActionItem("Action3", "desc3", None),
        ]

        # Down arrow
        new_sel, focus, execute = ptui_module.handle_action_keys(curses.KEY_DOWN, 0, action_items)
        assert new_sel == 1
        assert focus == "content"
        assert execute is None

        # Up arrow (wrap around)
        new_sel, focus, execute = ptui_module.handle_action_keys(curses.KEY_UP, 0, action_items)
        assert new_sel == 2
        assert focus == "content"

    def test_handle_action_keys_execute(self, ptui_module):
        """Test action execution on Enter."""
        import curses

        action_items = [
            ptui_module.ActionItem("Action1", "desc1", None),
        ]

        # Enter should return action index for execution
        new_sel, focus, execute = ptui_module.handle_action_keys(curses.KEY_ENTER, 0, action_items)
        assert execute == 0
        assert focus == "content"

    def test_handle_action_keys_return_to_menu(self, ptui_module):
        """Test returning focus to menu."""
        import curses

        action_items = [
            ptui_module.ActionItem("Action1", "desc1", None),
        ]

        # Left arrow should return to menu
        new_sel, focus, execute = ptui_module.handle_action_keys(curses.KEY_LEFT, 0, action_items)
        assert focus == "menu"

        # Shift-Tab should also return to menu
        new_sel, focus, execute = ptui_module.handle_action_keys(curses.KEY_BTAB, 0, action_items)
        assert focus == "menu"

    def test_handle_action_keys_empty_actions(self, ptui_module):
        """Test action keys with no actions available."""
        import curses

        # Empty action list should immediately return to menu
        new_sel, focus, execute = ptui_module.handle_action_keys(curses.KEY_DOWN, 0, [])
        assert focus == "menu"
        assert execute is None


class TestValidationScript:
    """Test validation script execution."""

    def test_run_validation_script_exists(self, ptui_module):
        """Test validation when script exists and succeeds."""
        mock_result = Mock()
        mock_result.returncode = 0

        with patch("ptui_dashboard.subprocess.run", return_value=mock_result):
            with patch("ptui_dashboard.os.path.exists", return_value=True):
                result = ptui_module.run_validation()

        assert "succeeded" in result.lower()

    def test_run_validation_script_fails(self, ptui_module):
        """Test validation when script fails."""
        mock_result = Mock()
        mock_result.returncode = 1

        with patch("ptui_dashboard.subprocess.run", return_value=mock_result):
            with patch("ptui_dashboard.os.path.exists", return_value=True):
                result = ptui_module.run_validation()

        assert "failed" in result.lower()

    def test_run_validation_script_missing(self, ptui_module):
        """Test validation when script doesn't exist."""
        with patch("ptui_dashboard.os.path.exists", return_value=False):
            result = ptui_module.run_validation()

        assert "not found" in result.lower()


class TestDataClasses:
    """Test data class structures."""

    def test_service_dataclass(self, ptui_module):
        """Test Service dataclass."""
        service = ptui_module.Service("Test", "http://localhost:4000", "/health", True)

        assert service.name == "Test"
        assert service.url == "http://localhost:4000"
        assert service.endpoint == "/health"
        assert service.required is True

    def test_action_item_dataclass(self, ptui_module):
        """Test ActionItem dataclass."""

        def handler(state):
            return ("message", None)

        action = ptui_module.ActionItem("Test Action", "Description", handler)

        assert action.title == "Test Action"
        assert action.description == "Description"
        assert callable(action.handler)

    def test_menu_item_dataclass(self, ptui_module):
        """Test MenuItem dataclass."""

        def renderer(*args):
            return None

        menu_item = ptui_module.MenuItem("Test Menu", "Description", renderer, True)

        assert menu_item.title == "Test Menu"
        assert menu_item.description == "Description"
        assert callable(menu_item.renderer)
        assert menu_item.supports_actions is True


class TestIntegrationReadiness:
    """Test dashboard is ready for integration with monitoring stack."""

    def test_constants_defined(self, ptui_module):
        """Test required constants are defined."""
        assert hasattr(ptui_module, "DEFAULT_HTTP_TIMEOUT")
        assert hasattr(ptui_module, "AUTO_REFRESH_SECONDS")
        assert hasattr(ptui_module, "SERVICES")
        assert hasattr(ptui_module, "ACTION_ITEMS")

    def test_constants_valid_types(self, ptui_module):
        """Test constants have valid types."""
        assert isinstance(ptui_module.DEFAULT_HTTP_TIMEOUT, (int, float))
        assert isinstance(ptui_module.AUTO_REFRESH_SECONDS, (int, float))
        assert isinstance(ptui_module.SERVICES, list)
        assert isinstance(ptui_module.ACTION_ITEMS, list)

    def test_constants_valid_ranges(self, ptui_module):
        """Test constants are in valid ranges."""
        assert 0.5 <= ptui_module.DEFAULT_HTTP_TIMEOUT <= 120.0
        assert 1.0 <= ptui_module.AUTO_REFRESH_SECONDS <= 60.0

    def test_action_items_not_empty(self, ptui_module):
        """Test action items list is populated."""
        assert len(ptui_module.ACTION_ITEMS) > 0

    def test_services_not_empty(self, ptui_module):
        """Test services list is populated."""
        assert len(ptui_module.SERVICES) > 0
