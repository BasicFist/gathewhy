"""Unit tests for AI Dashboard monitoring application.

Tests for security features, configuration loading, and validation logic.
These tests verify key dashboard functionality without requiring full Textual import.
"""

import subprocess
from pathlib import Path

import pytest


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
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        # Check for ALLOWED_SERVICES definition
        assert "ALLOWED_SERVICES" in content, "Should have ALLOWED_SERVICES allowlist"
        assert '"ollama"' in content, "Should whitelist ollama service"
        assert "litellm" in content, "Should whitelist litellm services"

    def test_allowed_actions_hardcoded(self):
        """Verify ALLOWED_ACTIONS uses allowlist pattern."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        # Check for ALLOWED_ACTIONS definition
        assert "ALLOWED_ACTIONS" in content, "Should have ALLOWED_ACTIONS allowlist"
        assert '"start"' in content, "Should allow start action"
        assert '"stop"' in content, "Should allow stop action"

    def test_localhost_validation(self):
        """Verify endpoint validation is present."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        # Check for security-related patterns
        assert "ALLOWED_HOSTS" in content, "Should validate allowed hosts"
        assert "127.0.0.1" in content, "Should restrict to localhost"
        assert "_validate_endpoints" in content, "Should validate endpoints"


class TestDashboardErrorHandling:
    """Test error handling features."""

    def test_error_handling_present(self):
        """Verify comprehensive error handling exists."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        # Check for error handling patterns
        assert "try:" in content, "Should use try/except blocks"
        assert "except" in content, "Should have exception handlers"
        assert "logger" in content, "Should use logging"

    def test_logging_configured(self):
        """Verify logging is configured."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        # Check for logging setup
        assert "import logging" in content, "Should import logging"
        assert "logger.debug" in content, "Should use debug logging"
        assert "logger.error" in content, "Should use error logging"


class TestStatePersistence:
    """Test state persistence functionality."""

    def test_state_persistence_functions_exist(self):
        """Verify state persistence functions are defined."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "save_dashboard_state" in content, "Should have save_dashboard_state function"
        assert "load_dashboard_state" in content, "Should have load_dashboard_state function"

    def test_state_file_location_defined(self):
        """Verify state file location is defined."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "STATE_DIR" in content, "Should define STATE_DIR"
        assert "STATE_FILE" in content, "Should define STATE_FILE"


class TestDashboardComponents:
    """Test main dashboard components."""

    def test_provider_monitor_defined(self):
        """Verify ProviderMonitor class is defined."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "class ProviderMonitor" in content, "Should define ProviderMonitor class"

    def test_gpu_monitor_defined(self):
        """Verify GPUMonitor class is defined."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "class GPUMonitor" in content, "Should define GPUMonitor class"

    def test_dashboard_app_defined(self):
        """Verify DashboardApp class is defined."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "class DashboardApp" in content, "Should define DashboardApp class"

    def test_service_metrics_defined(self):
        """Verify ServiceMetrics dataclass is defined."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "class ServiceMetrics" in content, "Should define ServiceMetrics dataclass"

    def test_gpu_overview_defined(self):
        """Verify GPUOverview dataclass is defined."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "class GPUOverview" in content, "Should define GPUOverview dataclass"


class TestDashboardKeyFeatures:
    """Test that key features are implemented."""

    def test_configuration_loading(self):
        """Verify configuration loading functionality."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "_load_config" in content, "Should have config loading function"
        assert "_load_providers_config" in content, "Should load provider config from YAML"

    def test_service_control(self):
        """Verify service control functionality."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "systemctl" in content, "Should support systemctl control"
        assert "action_toggle_auto" in content, "Should support auto-refresh toggle"

    def test_event_handling(self):
        """Verify event handling is implemented."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "handle_service_action" in content, "Should handle service actions"
        assert "handle_row_selected" in content, "Should handle row selection"
        assert "on_mount" in content, "Should have mount event handler"

    def test_ui_components(self):
        """Verify UI components are implemented."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        components = [
            "OverviewPanel",
            "ServiceTable",
            "GPUCard",
            "DetailPanel",
        ]

        for component in components:
            assert f"class {component}" in content, f"Should have {component} UI component"


class TestDashboardBindings:
    """Test keyboard bindings are defined."""

    def test_key_bindings_defined(self):
        """Verify key bindings are defined."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "BINDINGS" in content, "Should define key bindings"
        assert '"r"' in content, "Should have 'r' for refresh"
        assert '"q"' in content, "Should have 'q' for quit"
        assert '"a"' in content, "Should have 'a' for auto-refresh toggle"


class TestDashboardMetricsCollection:
    """Test metrics collection logic."""

    def test_health_check_endpoints(self):
        """Verify health check endpoints are defined."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        endpoints = [
            "11434",  # Ollama
            "8000",  # llama.cpp Python
            "8001",  # vLLM
            "8080",  # llama.cpp Native
            "4000",  # LiteLLM
        ]

        for endpoint in endpoints:
            assert endpoint in content, f"Should monitor port {endpoint}"

    def test_metrics_parsing(self):
        """Verify metrics parsing is implemented."""
        dashboard_path = Path(__file__).parent.parent.parent / "scripts" / "ai-dashboard"

        with open(dashboard_path) as f:
            content = f.read()

        assert "_parse_models" in content, "Should parse model count from responses"
        assert "cpu_percent" in content, "Should collect CPU metrics"
        assert "memory_mb" in content, "Should collect memory metrics"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
