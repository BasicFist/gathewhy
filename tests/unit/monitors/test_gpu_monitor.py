"""Unit tests for GPU monitor.

Tests GPU monitoring functionality including:
- NVML initialization handling
- GPU information retrieval
- Process VRAM usage tracking
- Error handling for missing GPUs or drivers
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dashboard.monitors.gpu import GPUMonitor


class TestGPUMonitorInitialization:
    """Test GPU monitor initialization."""

    @patch("dashboard.monitors.gpu.warnings")
    def test_initializes_without_pynvml(self, mock_warnings):
        """Test initialization when pynvml not available."""
        with patch.dict("sys.modules", {"pynvml": None}):
            with patch("builtins.__import__", side_effect=ImportError("pynvml not found")):
                monitor = GPUMonitor()

                assert monitor.initialized is False
                assert monitor.device_count == 0

    @patch("dashboard.monitors.gpu.warnings")
    def test_initializes_with_pynvml_success(self, mock_warnings):
        """Test successful initialization with pynvml."""
        mock_pynvml = MagicMock()
        mock_pynvml.nvmlDeviceGetCount.return_value = 2

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()

                # Should initialize successfully
                mock_pynvml.nvmlInit.assert_called_once()
                assert monitor.initialized is True
                assert monitor.device_count == 2

    @patch("dashboard.monitors.gpu.warnings")
    def test_handles_nvml_init_failure(self, mock_warnings):
        """Test handles NVML initialization failure."""
        mock_pynvml = MagicMock()
        mock_pynvml.nvmlInit.side_effect = RuntimeError("NVML initialization failed")

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()

                assert monitor.initialized is False
                assert monitor.device_count == 0

    @patch("dashboard.monitors.gpu.warnings")
    def test_handles_os_error(self, mock_warnings):
        """Test handles OS error during initialization."""
        mock_pynvml = MagicMock()
        mock_pynvml.nvmlInit.side_effect = OSError("No NVIDIA driver")

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()

                assert monitor.initialized is False


class TestGPUMonitorGetGPUInfo:
    """Test GPU information retrieval."""

    def test_returns_empty_when_not_initialized(self):
        """Test returns empty list when not initialized."""
        monitor = GPUMonitor()
        monitor.initialized = False

        gpu_info = monitor.get_gpu_info()

        assert gpu_info == []

    @patch("dashboard.monitors.gpu.warnings")
    def test_returns_gpu_info_single_gpu(self, mock_warnings):
        """Test returns GPU info for single GPU."""
        mock_pynvml = MagicMock()

        # Mock device handle and info
        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_pynvml.nvmlDeviceGetName.return_value = "NVIDIA RTX 4090"

        # Mock memory info
        mock_memory = MagicMock()
        mock_memory.total = 24 * 1024**3  # 24 GB
        mock_memory.used = 8 * 1024**3  # 8 GB
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory

        # Mock utilization
        mock_util = MagicMock()
        mock_util.gpu = 75
        mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = mock_util

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 1

                gpu_info = monitor.get_gpu_info()

                assert len(gpu_info) == 1
                assert gpu_info[0]["id"] == 0.0
                assert gpu_info[0]["name"] == "NVIDIA RTX 4090"
                assert abs(gpu_info[0]["memory_total_mb"] - 24576.0) < 1
                assert abs(gpu_info[0]["memory_used_mb"] - 8192.0) < 1
                assert gpu_info[0]["gpu_util_percent"] == 75.0

    @patch("dashboard.monitors.gpu.warnings")
    def test_returns_gpu_info_multiple_gpus(self, mock_warnings):
        """Test returns GPU info for multiple GPUs."""
        mock_pynvml = MagicMock()

        # Mock two different GPUs
        def mock_get_name(handle):
            if handle == "handle_0":
                return "NVIDIA RTX 4090"
            return "NVIDIA RTX 3090"

        mock_pynvml.nvmlDeviceGetName.side_effect = mock_get_name

        def mock_get_handle(index):
            return f"handle_{index}"

        mock_pynvml.nvmlDeviceGetHandleByIndex.side_effect = mock_get_handle

        # Mock memory for both
        mock_memory = MagicMock()
        mock_memory.total = 24 * 1024**3
        mock_memory.used = 8 * 1024**3
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory

        # Mock utilization
        mock_util = MagicMock()
        mock_util.gpu = 50
        mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = mock_util

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 2

                gpu_info = monitor.get_gpu_info()

                assert len(gpu_info) == 2
                assert gpu_info[0]["id"] == 0.0
                assert gpu_info[1]["id"] == 1.0

    @patch("dashboard.monitors.gpu.warnings")
    def test_handles_gpu_query_error(self, mock_warnings):
        """Test handles error querying specific GPU."""
        mock_pynvml = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.side_effect = OSError("GPU query failed")

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 1

                gpu_info = monitor.get_gpu_info()

                # Should return empty list (skipped failed GPU)
                assert gpu_info == []

    @patch("dashboard.monitors.gpu.warnings")
    def test_handles_bytes_gpu_name(self, mock_warnings):
        """Test handles GPU name returned as bytes (old pynvml)."""
        mock_pynvml = MagicMock()

        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_pynvml.nvmlDeviceGetName.return_value = b"NVIDIA RTX 4090"  # Bytes

        mock_memory = MagicMock()
        mock_memory.total = 24 * 1024**3
        mock_memory.used = 8 * 1024**3
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory

        mock_util = MagicMock()
        mock_util.gpu = 50
        mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = mock_util

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 1

                gpu_info = monitor.get_gpu_info()

                # Should decode bytes to string
                assert gpu_info[0]["name"] == "NVIDIA RTX 4090"


class TestGPUMonitorGetProcessVRAM:
    """Test process VRAM usage tracking."""

    def test_returns_empty_when_not_initialized(self):
        """Test returns empty dict when not initialized."""
        monitor = GPUMonitor()
        monitor.initialized = False

        vram_usage = monitor.get_process_vram()

        assert vram_usage == {}

    @patch("dashboard.monitors.gpu.warnings")
    def test_returns_process_vram_single_process(self, mock_warnings):
        """Test returns VRAM usage for single process."""
        mock_pynvml = MagicMock()

        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle

        # Mock memory info
        mock_memory = MagicMock()
        mock_memory.total = 24 * 1024**3  # 24 GB
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory

        # Mock process using 4 GB
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.usedGpuMemory = 4 * 1024**3  # 4 GB
        mock_pynvml.nvmlDeviceGetComputeRunningProcesses.return_value = [mock_process]

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 1

                vram_usage = monitor.get_process_vram()

                assert 12345 in vram_usage
                used_mb, percent = vram_usage[12345]
                assert abs(used_mb - 4096.0) < 1
                assert abs(percent - (4096.0 / 24576.0 * 100)) < 0.1

    @patch("dashboard.monitors.gpu.warnings")
    def test_aggregates_vram_across_multiple_gpus(self, mock_warnings):
        """Test aggregates VRAM usage when process uses multiple GPUs."""
        mock_pynvml = MagicMock()

        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle

        # Both GPUs have same process
        mock_memory = MagicMock()
        mock_memory.total = 24 * 1024**3
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory

        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.usedGpuMemory = 2 * 1024**3  # 2 GB per GPU
        mock_pynvml.nvmlDeviceGetComputeRunningProcesses.return_value = [mock_process]

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 2

                vram_usage = monitor.get_process_vram()

                # Should aggregate across both GPUs
                assert 12345 in vram_usage
                used_mb, percent = vram_usage[12345]
                assert abs(used_mb - 4096.0) < 1  # 2 GB * 2 GPUs

    @patch("dashboard.monitors.gpu.warnings")
    def test_handles_multiple_processes(self, mock_warnings):
        """Test handles multiple processes on same GPU."""
        mock_pynvml = MagicMock()

        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle

        mock_memory = MagicMock()
        mock_memory.total = 24 * 1024**3
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory

        # Two processes
        mock_proc1 = MagicMock()
        mock_proc1.pid = 12345
        mock_proc1.usedGpuMemory = 4 * 1024**3

        mock_proc2 = MagicMock()
        mock_proc2.pid = 23456
        mock_proc2.usedGpuMemory = 2 * 1024**3

        mock_pynvml.nvmlDeviceGetComputeRunningProcesses.return_value = [mock_proc1, mock_proc2]

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 1

                vram_usage = monitor.get_process_vram()

                assert 12345 in vram_usage
                assert 23456 in vram_usage

    @patch("dashboard.monitors.gpu.warnings")
    def test_handles_process_query_error(self, mock_warnings):
        """Test handles error querying processes."""
        mock_pynvml = MagicMock()

        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_pynvml.nvmlDeviceGetMemoryInfo.side_effect = OSError("Query failed")

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 1

                vram_usage = monitor.get_process_vram()

                # Should return empty dict (skipped failed GPU)
                assert vram_usage == {}

    @patch("dashboard.monitors.gpu.warnings")
    def test_skips_invalid_process_records(self, mock_warnings):
        """Test skips process records with invalid data."""
        mock_pynvml = MagicMock()

        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle

        mock_memory = MagicMock()
        mock_memory.total = 24 * 1024**3
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory

        # Invalid process records
        mock_proc_no_pid = MagicMock()
        mock_proc_no_pid.pid = None
        mock_proc_no_pid.usedGpuMemory = 1024**3

        mock_proc_negative_mem = MagicMock()
        mock_proc_negative_mem.pid = 12345
        mock_proc_negative_mem.usedGpuMemory = -1

        mock_proc_valid = MagicMock()
        mock_proc_valid.pid = 23456
        mock_proc_valid.usedGpuMemory = 2 * 1024**3

        mock_pynvml.nvmlDeviceGetComputeRunningProcesses.return_value = [
            mock_proc_no_pid,
            mock_proc_negative_mem,
            mock_proc_valid,
        ]

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 1

                vram_usage = monitor.get_process_vram()

                # Should only include valid process
                assert 23456 in vram_usage
                assert 12345 not in vram_usage
                assert None not in vram_usage


class TestGPUMonitorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_device_count(self):
        """Test handles zero GPUs detected."""
        monitor = GPUMonitor()
        monitor.initialized = True
        monitor.device_count = 0
        monitor._pynvml = MagicMock()

        gpu_info = monitor.get_gpu_info()
        vram_usage = monitor.get_process_vram()

        assert gpu_info == []
        assert vram_usage == {}

    @patch("dashboard.monitors.gpu.warnings")
    def test_handles_zero_total_memory(self, mock_warnings):
        """Test handles GPU with zero total memory."""
        mock_pynvml = MagicMock()

        mock_handle = MagicMock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_pynvml.nvmlDeviceGetName.return_value = "Test GPU"

        # Zero total memory
        mock_memory = MagicMock()
        mock_memory.total = 0
        mock_memory.used = 0
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory

        mock_util = MagicMock()
        mock_util.gpu = 0
        mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = mock_util

        with patch.dict("sys.modules", {"pynvml": mock_pynvml}):
            with patch("builtins.__import__", return_value=mock_pynvml):
                monitor = GPUMonitor()
                monitor._pynvml = mock_pynvml
                monitor.initialized = True
                monitor.device_count = 1

                gpu_info = monitor.get_gpu_info()

                # Should handle gracefully
                assert len(gpu_info) == 1
                assert gpu_info[0]["memory_util_percent"] == 0.0
