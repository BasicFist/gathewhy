# AI Dashboard - Terminal User Interface for Backend Monitoring

## Overview

The **AI Dashboard** is a sophisticated terminal-based user interface (TUI) for monitoring and managing AI backend LLM provider services including Ollama, vLLM, and llama.cpp. It provides real-time metrics, GPU usage tracking, system resource monitoring, and service lifecycle controls.

**Built with**: [Textual](https://textualize.io/) - a lean TUI framework for Python

## Quick Start

### Launch the Dashboard

```bash
cd ai-backend-unified
python3 scripts/ai-dashboard

# Or if you have execute permissions
./scripts/ai-dashboard
```

### Key Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `r` | Refresh | Manually refresh all metrics |
| `q` | Quit | Exit dashboard and save state |
| `a` | Toggle auto-refresh | Enable/disable automatic updates |
| `ctrl+l` | Clear log | Clear the event log |
| `↑/↓` | Navigate | Select provider rows |

## Features

### 1. Real-Time Provider Monitoring

Monitors all configured LLM providers with live status updates:

- **Provider Status**: Active, degraded, or inactive
- **CPU Usage**: Per-process CPU consumption (%)
- **System Memory**: Current memory usage (MB and %)
- **VRAM Usage**: GPU memory (if NVIDIA GPU available)
- **Response Time**: API endpoint latency (ms)
- **Model Count**: Number of models served by provider

### 2. Service Status Dashboard

**Overview Panel** (top-left):
- Active/total service count
- Average CPU and memory usage across all providers
- List of services requiring attention

**Service Table** (center):
- Quick view of all providers
- Color-coded status (green=active, yellow=degraded, red=inactive)
- Essential metrics at a glance

### 3. GPU Monitoring

**GPU Card** (top-right):
- Total VRAM usage and capacity
- Peak GPU utilization percentage
- Per-GPU breakdown with memory stats
- Gracefully handles systems without NVIDIA GPUs

### 4. Detailed Service View

**Detail Panel** (bottom-right):
- Comprehensive metrics for selected provider
- Port and process ID (PID) information
- Service control buttons
- Alert/warning log

**Service Controls**:
- ✅ **Start**: Start the service
- 🛑 **Stop**: Stop the service
- 🔄 **Restart**: Gracefully restart the service
- 🔒 **Enable**: Enable service at boot
- 🔓 **Disable**: Disable service at boot

### 5. Global Service Controls

**Control Bar** (beneath search):
- Quick access Start/Stop/Restart buttons for the selected provider
- Status message that reflects which service is armed for control
- Buttons stay disabled until a service row is selected
- Honors provider-level restrictions (disabled when controls are unavailable)

### 6. Event Logging

**Event Log** (bottom-right):
- Real-time dashboard events
- Service action confirmations
- Error notifications
- Clear with `ctrl+l`

## Configuration

### Environment Variables

Control dashboard behavior via environment variables:

```bash
# HTTP timeout for provider health checks (0.5-30 seconds, default: 3.0)
export AI_DASH_HTTP_TIMEOUT=3.0

# Refresh interval for metrics updates (1-60 seconds, default: 5)
export AI_DASH_REFRESH_INTERVAL=5

# Event log display height (5-50 lines, default: 12)
export AI_DASH_LOG_HEIGHT=12

# Run with custom configuration
AI_DASH_REFRESH_INTERVAL=3 python3 scripts/ai-dashboard
```

### Configuration Files

The dashboard automatically loads provider information from:

- **`config/providers.yaml`**: Provider registry with endpoints and models
- **`config/model-mappings.yaml`**: Model routing rules

These files are read on startup to populate the provider list. The dashboard works even if these files are unavailable (using hardcoded defaults).

## State Persistence

The dashboard automatically saves its state between sessions:

- **Location**: `~/.cache/ai-dashboard/dashboard_state.json`
- **Saved Information**:
  - List of providers and their metrics
  - Currently selected provider
  - Timestamp of last session
- **Restored On**: Dashboard startup (if available)

### Manual State Management

```bash
# View saved state
cat ~/.cache/ai-dashboard/dashboard_state.json | jq .

# Clear saved state
rm ~/.cache/ai-dashboard/dashboard_state.json
```

## Provider Monitoring Details

### Health Check Process

1. **HTTP Request**: Dashboard sends GET request to provider endpoint
2. **Response Parsing**:
   - If successful: Parse JSON and extract model count
   - If failed: Record error type and reason
3. **Status Determination**:
   - ✅ **Active**: Endpoint responded successfully (200 OK)
   - ⚠️ **Degraded**: Required provider offline or returned error
   - ❌ **Inactive**: Optional provider offline

### Supported Providers

| Provider | Port | Endpoint | Type |
|----------|------|----------|------|
| **Ollama** | 11434 | `/api/tags` | Optional |
| **llama.cpp (Python)** | 8000 | `/v1/models` | Optional |
| **llama.cpp (Native)** | 8080 | `/v1/models` | Optional |
| **vLLM** | 8001 | `/v1/models` | Required |
| **LiteLLM Gateway** | 4000 | `/v1/models` | Required |

### Adding Custom Providers

1. **Edit `config/providers.yaml`**:
   ```yaml
   providers:
     my_provider:
       type: "litellm"
       base_url: "http://127.0.0.1:8888"
       status: "active"
       models:
         - name: "model-1"
   ```

2. **Restart Dashboard**:
   ```bash
   python3 scripts/ai-dashboard
   ```

The dashboard will automatically include the new provider in monitoring.

## Troubleshooting

### Dashboard Won't Start

```bash
# Check for Python dependencies
python3 -c "import textual; import psutil; import yaml; print('OK')"

# If missing, install:
pip install textual psutil pyyaml
```

### Providers Show as "Inactive" or "Degraded"

1. **Check if provider is running**:
   ```bash
   # Ollama
   curl http://localhost:11434/api/tags

   # vLLM
   curl http://localhost:8001/v1/models

   # llama.cpp
   curl http://localhost:8000/v1/models
   ```

2. **Check systemctl service status**:
   ```bash
   systemctl --user status ollama.service
   systemctl --user status vllm.service
   ```

3. **Verify network connectivity**:
   ```bash
   nc -zv 127.0.0.1 8001  # Test vLLM port
   ```

### GPU Metrics Not Showing

- **NVIDIA GPU required**: Dashboard uses NVIDIA NVML for GPU metrics
- **Check CUDA installation**: `nvidia-smi`
- **Check pynvml**: `python3 -c "import pynvml; print('OK')"`

### Service Controls Not Working

1. **User-level systemctl** (default): Services must be user-level
2. **Check service file**:
   ```bash
   systemctl --user list-unit-files | grep service
   ```
3. **Manual control** (if dashboard fails):
   ```bash
   systemctl --user start vllm.service
   systemctl --user stop ollama.service
   ```

### Performance Issues

- **Increase refresh interval**: `AI_DASH_REFRESH_INTERVAL=10`
- **Increase HTTP timeout**: `AI_DASH_HTTP_TIMEOUT=5.0`
- **Reduce log height**: `AI_DASH_LOG_HEIGHT=5`

## Advanced Usage

### Integration with Monitoring Stack

Use dashboard alongside the observability stack for comprehensive monitoring:

```bash
# Terminal 1: Dashboard
python3 scripts/ai-dashboard

# Terminal 2: Prometheus (in separate window)
cd monitoring && docker compose up

# Terminal 3: View logs
./scripts/debugging/tail-requests.py
```

### Batch Monitoring

Run health checks without dashboard:

```bash
./scripts/validate-unified-backend.sh
```

### Logs and Debugging

Dashboard logs are written to stderr. Capture them:

```bash
python3 scripts/ai-dashboard 2>dashboard.log

# View live logs
tail -f dashboard.log
```

## Architecture

### Component Breakdown

#### GPUMonitor
- Queries NVIDIA GPU information via NVML
- Collects per-process VRAM usage
- Gracefully handles systems without GPUs

#### ProviderMonitor
- Monitors all provider endpoints
- Collects system metrics (CPU, memory)
- Controls services via systemctl

#### UI Components
- **OverviewPanel**: Service summary
- **ServiceTable**: All providers at a glance
- **GPUCard**: GPU utilization stats
- **DetailPanel**: Selected provider details
- **Event Log**: Live activity feed

#### Textual Framework
- **Reactive Attributes**: Auto-refresh UI on data changes
- **Event Handling**: Keyboard shortcuts and button interactions
- **Layout System**: Grid-based responsive layout

### Data Flow

```
┌─────────────────────────────────────┐
│     Dashboard Application           │
└──────────────┬──────────────────────┘
               │
        ┌──────▼────────┐
        │ ProviderMonitor│
        └──────┬────────┘
               │
        ┌──────┴────────┬──────────┐
        │               │          │
   ┌────▼─────┐  ┌─────▼────┐  ┌──▼───────┐
   │HTTP Check│  │CPU/Memory│  │GPU Metrics
   │Endpoints │  │Collection│  │Collection
   └──────────┘  └──────────┘  └───────────┘
```

## Performance Characteristics

### Resource Usage

- **Memory**: ~50-100 MB baseline
- **CPU**: <5% idle, <20% during refresh
- **Network**: Minimal (health check pings only)

### Refresh Intervals

- **Default**: 5 seconds
- **Recommended**: 3-10 seconds
- **Minimum**: 1 second (high CPU usage)
- **Maximum**: 60 seconds

### Response Times

- **Dashboard refresh**: ~200-500ms (depends on provider count)
- **Service control**: ~2-5 seconds (systemctl operation)
- **GPU metrics**: ~100-200ms (if available)

## Security Considerations

### SSRF Prevention
- Only connects to localhost (127.0.0.1)
- Validates ports against allowlist
- Prevents arbitrary endpoint connections

### Command Injection Prevention
- Validates service names against allowlist
- Validates actions (start/stop/restart/etc.)
- Uses subprocess with minimal environment

### Service Control Authorization
- Uses user-level systemctl (no sudo required)
- Services must be user-enabled
- Validates all inputs before execution

## API Reference

### ServiceMetrics

```python
@dataclass
class ServiceMetrics:
    key: str                    # Provider identifier
    display: str                # Display name
    required: bool              # Required for system
    status: str                 # "active", "degraded", "inactive"
    port: int | None            # Service port
    models: int | None          # Model count
    cpu_percent: float          # CPU usage (%)
    memory_mb: float            # RAM usage (MB)
    memory_percent: float       # RAM usage (%)
    vram_mb: float              # VRAM usage (MB)
    vram_percent: float         # VRAM usage (%)
    response_ms: float          # API latency (ms)
    pid: int | None             # Process ID
    notes: list[str]            # Warning/error messages
    timestamp: float            # Collection timestamp
```

### DashboardApp Bindings

```python
BINDINGS = [
    Binding("r", "refresh", "Refresh"),
    Binding("q", "quit", "Quit"),
    Binding("a", "toggle_auto", "Toggle auto-refresh"),
    Binding("ctrl+l", "clear_log", "Clear log"),
]
```

## Contributing & Development

### Code Organization

```
scripts/ai-dashboard          # Main application
├── ProviderMonitor           # Health check logic
├── GPUMonitor                # GPU metrics collection
├── DashboardApp              # Textual TUI app
├── UI Components             # Widget implementations
└── Data Models               # ServiceMetrics, GPUOverview
```

### Adding Features

1. **New Provider**: Update `ProviderMonitor.PROVIDERS`
2. **New UI Widget**: Extend `Static` or `Container`
3. **New Metric**: Add to `ServiceMetrics` dataclass

### Testing

```bash
# Run without dependencies (basic tests)
python3 -m pytest tests/

# Integration tests require active providers
python3 -m pytest tests/ -m integration
```

## Known Limitations

- Textual requires Python 3.7+
- GPU metrics require NVIDIA GPU and pynvml
- Service controls require user-level systemctl
- Dashboard designed for local monitoring only

## Future Enhancements

- [ ] Network monitoring (bandwidth, packet stats)
- [ ] Historical metrics storage and trending
- [ ] Custom alert thresholds
- [ ] Multi-provider health scoring
- [ ] Web UI version (Textual Web)
- [ ] Remote monitoring support
- [ ] Integration with Prometheus/Grafana

## See Also

- **Monitoring Stack**: `docs/observability.md`
- **Provider Configuration**: `config/providers.yaml`
- **Service Management**: `docs/troubleshooting.md`
- **API Usage**: `docs/consuming-api.md`

## License

Part of the LAB ecosystem.
