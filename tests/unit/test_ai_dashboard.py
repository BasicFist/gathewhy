"""Unit tests for AI Dashboard monitoring application.

Tests for security features, configuration loading, and validation logic.
These tests verify key dashboard functionality without requiring full Textual import.
"""

import importlib
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

dashboard_package = importlib.import_module("dashboard")
DashboardApp = importlib.import_module("dashboard.app").DashboardApp
config_module = importlib.import_module("dashboard.config")
load_env_config = config_module.load_env_config
load_providers_config = config_module.load_providers_config
models_module = importlib.import_module("dashboard.models")
ServiceMetrics = models_module.ServiceMetrics
GPUOverview = models_module.GPUOverview
provider_module = importlib.import_module("dashboard.monitors.provider")
GPUMonitor = importlib.import_module("dashboard.monitors.gpu").GPUMonitor
state_module = importlib.import_module("dashboard.state")
STATE_DIR = state_module.STATE_DIR
STATE_FILE = state_module.STATE_FILE
load_dashboard_state = state_module.load_dashboard_state
save_dashboard_state = state_module.save_dashboard_state
DetailPanel = importlib.import_module("dashboard.widgets.detail").DetailPanel
GPUCard = importlib.import_module("dashboard.widgets.gpu_card").GPUCard
OverviewPanel = importlib.import_module("dashboard.widgets.overview").OverviewPanel
ServiceTable = importlib.import_module("dashboard.widgets.table").ServiceTable


class TestDashboardSyntax:
    """Test that ai-dashboard script has valid Python syntax."""

    def test_dashboard_script_syntax(self):
        """Verify ai-dashboard script compiles without syntax errors."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"
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
    """Test that dashboard documentation exists and is complete."""

    def test_dashboard_docs_exist(self):
        """Verify dashboard documentation file exists."""
        docs_path = Path(__file__).parent.parent.parent / "docs" / "ai-dashboard.md"
        assert docs_path.exists(), f"Dashboard documentation not found at {docs_path}"

    def test_dashboard_docs_content(self):
        """Verify dashboard documentation contains key sections."""
        docs_path = Path(__file__).parent.parent.parent / "docs" / "ai-dashboard.md"

        with open(docs_path) as f:
            content = f.read()

        required_sections = [
            "# AI Dashboard",
            "## Quick Start",
            "## Features",
            "## Configuration",
            "## Troubleshooting",
            "## Architecture",
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_readme_mentions_dashboard(self):
        """Verify README mentions AI Dashboard."""
        readme_path = Path(__file__).parent.parent.parent / "README.md"

        with open(readme_path) as f:
            content = f.read()

        assert "AI Dashboard" in content, "README should mention AI Dashboard"
        assert "scripts/ai-dashboard" in content, "README should reference dashboard script"


class TestDashboardConfiguration:
    """Test dashboard configuration validation."""

    def test_provider_config_exists(self):
        """Verify provider configuration files exist."""
        config_path = Path(__file__).parent.parent.parent / "config"
        assert config_path.exists(), "Config directory should exist"

        providers_yaml = config_path / "providers.yaml"
        assert providers_yaml.exists(), "providers.yaml should exist"

    def test_provider_config_valid_yaml(self):
        """Verify providers.yaml is valid YAML."""
        import yaml

        config_path = Path(__file__).parent.parent.parent / "config" / "providers.yaml"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert isinstance(config, dict), "providers.yaml should be a valid YAML dict"
        assert "providers" in config, "providers.yaml should have 'providers' key"


class TestDashboardSecurityFeatures:
    """Test security-related features of the dashboard."""

    def test_allowed_services_hardcoded(self):
        """Verify ALLOWED_SERVICES uses allowlist pattern."""
        services = provider_module.ALLOWED_SERVICES
        assert "ollama" in services
        assert "litellm_gateway" in services

    def test_allowed_actions_hardcoded(self):
        """Verify ALLOWED_ACTIONS uses allowlist pattern."""
        actions = provider_module.ALLOWED_ACTIONS
        assert {"start", "stop", "restart"}.issubset(actions)

    def test_localhost_validation(self):
        """Verify endpoint validation is present."""
        assert "127.0.0.1" in provider_module.ProviderMonitor.ALLOWED_HOSTS
        assert "localhost" in provider_module.ProviderMonitor.ALLOWED_HOSTS
        assert 11434 in provider_module.ProviderMonitor.ALLOWED_PORTS


class TestDashboardErrorHandling:
    """Test error handling features."""

    def test_error_handling_present(self):
        """Verify comprehensive error handling exists."""
        monitor = provider_module.ProviderMonitor(http_timeout=0.01)
        metrics, gpu_info = monitor.collect_snapshot()
        assert isinstance(metrics, list) and metrics, "Should return provider metrics"
        assert isinstance(gpu_info.detected, bool)

    def test_logging_configured(self):
        """Verify logging is configured."""
        assert provider_module.logger.name == "dashboard.monitors.provider"


class TestStatePersistence:
    """Test state persistence functionality."""

    def test_state_persistence_functions_exist(self):
        """Verify state persistence functions are defined."""
        assert callable(save_dashboard_state)
        assert callable(load_dashboard_state)

    def test_state_file_location_defined(self):
        """Verify state file location is defined."""
        assert STATE_DIR.is_absolute()
        assert STATE_FILE.parent == STATE_DIR


class TestDashboardComponents:
    """Test main dashboard components."""

    def test_provider_monitor_defined(self):
        """Verify ProviderMonitor class is defined."""
        assert hasattr(provider_module, "ProviderMonitor")

    def test_gpu_monitor_defined(self):
        """Verify GPUMonitor class is defined."""
        assert GPUMonitor.__name__ == "GPUMonitor"

    def test_dashboard_app_defined(self):
        """Verify DashboardApp class is defined."""
        assert DashboardApp.__name__ == "DashboardApp"

    def test_service_metrics_defined(self):
        """Verify ServiceMetrics dataclass is defined."""
        assert ServiceMetrics.__name__ == "ServiceMetrics"

    def test_gpu_overview_defined(self):
        """Verify GPUOverview dataclass is defined."""
        assert GPUOverview.__name__ == "GPUOverview"


class TestDashboardKeyFeatures:
    """Test that key features are implemented."""

    def test_configuration_loading(self):
        """Verify configuration loading functionality."""
        timeout, refresh, log_height = load_env_config()
        assert 0.5 <= timeout <= 30
        assert 1 <= refresh <= 60
        assert 5 <= log_height <= 50
        providers = load_providers_config()
        assert isinstance(providers, dict)

    def test_service_control(self):
        """Verify service control functionality."""
        monitor = provider_module.ProviderMonitor(http_timeout=0.01)
        assert hasattr(monitor, "systemctl")
        assert any(binding.key == "a" for binding in DashboardApp.BINDINGS)

    def test_event_handling(self):
        """Verify event handling is implemented."""
        detail = DetailPanel()
        assert hasattr(detail, "handle_button")
        app = DashboardApp()
        assert hasattr(app, "handle_service_action")
        assert hasattr(app, "handle_row_selected")

    def test_ui_components(self):
        """Verify UI components are implemented."""
        assert OverviewPanel.__name__ == "OverviewPanel"
        assert ServiceTable.__name__ == "ServiceTable"
        assert GPUCard.__name__ == "GPUCard"
        assert DetailPanel.__name__ == "DetailPanel"


class TestDashboardBindings:
    """Test keyboard bindings are defined."""

    def test_key_bindings_defined(self):
        """Verify key bindings are defined."""
        keys = {binding.key for binding in DashboardApp.BINDINGS}
        assert {"r", "ctrl+q", "a"}.issubset(keys)


class TestDashboardMetricsCollection:
    """Test metrics collection logic."""

    def test_health_check_endpoints(self):
        """Verify health check endpoints are defined."""
        endpoints = [
            provider_module.ProviderMonitor.DEFAULT_PROVIDERS["ollama"]["endpoint"],
            provider_module.ProviderMonitor.DEFAULT_PROVIDERS["llama_cpp_python"]["endpoint"],
            provider_module.ProviderMonitor.DEFAULT_PROVIDERS["vllm"]["endpoint"],
            provider_module.ProviderMonitor.DEFAULT_PROVIDERS["llama_cpp_native"]["endpoint"],
            provider_module.ProviderMonitor.DEFAULT_PROVIDERS["litellm_gateway"]["endpoint"],
        ]
        ports = {urlparse(str(endpoint)).port for endpoint in endpoints}
        assert {11434, 8000, 8001, 8080, 4000}.issubset(ports)

    def test_metrics_parsing(self):
        """Verify metrics parsing is implemented."""
        monitor = provider_module.ProviderMonitor(http_timeout=0.01)
        sample_response = {"models": [{"name": "a"}, {"name": "b"}]}
        assert monitor._parse_models("ollama", sample_response) == 2
        sample_response_llm = {"data": [{"id": "x"}]}
        assert monitor._parse_models("vllm", sample_response_llm) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
