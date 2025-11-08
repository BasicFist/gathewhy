# AI Dashboard (PTUI) - Purpose and Architecture

**Date**: October 26, 2025
**Documentation**: Comprehensive understanding of the ai-dashboard terminal UI

---

## Executive Summary

The **AI Dashboard** (also called PTUI - Python Terminal UI) is a **real-time terminal-based monitoring and management interface** for the AI Unified Backend Infrastructure. It provides a single command-center view of all LLM providers (Ollama, vLLM, llama.cpp, LiteLLM) with live metrics, health status, and service controls.

**Key Purpose**: Replace the need to manually check multiple endpoints and services by providing a unified, interactive dashboard for monitoring and managing the entire AI backend infrastructure from one terminal interface.

---

## Core Purpose

### Primary Functions

1. **Real-Time Monitoring**
   - Monitor health of all LLM providers simultaneously
   - Track CPU, memory, GPU (VRAM) usage per provider
   - Display API response times and model counts
   - Visual status indicators (active, degraded, inactive)

2. **Service Management**
   - Start/stop/restart services via systemctl
   - Enable/disable services at boot
   - Quick access to service controls from the UI
   - Validation and security (allowlist-based)

3. **Resource Tracking**
   - System-wide CPU and memory averages
   - Per-provider resource consumption
   - GPU utilization and VRAM usage (NVIDIA only)
   - Response time tracking (latency monitoring)

4. **Event Logging**
   - Real-time event feed
   - Service action confirmations
   - Error notifications
   - Persistent log history

5. **State Persistence**
   - Saves dashboard state between sessions
   - Restores provider metrics and selections
   - Cached in `~/.cache/ai-dashboard/dashboard_state.json`

---

## Why It Exists

### Problem Solved

**Before ai-dashboard**:
```bash
# Manual checking of each provider (tedious)
curl http://localhost:11434/api/tags       # Ollama
curl http://localhost:8001/v1/models       # vLLM
curl http://localhost:8000/v1/models       # llama.cpp
curl http://localhost:4000/v1/models       # LiteLLM

# Manual service management
systemctl --user status ollama.service
systemctl --user status vllm.service
systemctl --user restart litellm.service

# Manual resource tracking
htop | grep ollama
nvidia-smi

# No unified view, context switching, error-prone
```

**After ai-dashboard**:
```bash
# Single command, unified view
./ai-dashboard

# All providers visible at once
# Real-time updates every 5 seconds
# Interactive service controls
# GPU metrics included
# Event logging built-in
```

### Value Proposition

1. **Operational Efficiency**: Monitor 5 providers in one view vs 5 separate terminal windows
2. **Faster Troubleshooting**: Immediately see which provider is down or degraded
3. **Resource Awareness**: Track CPU/memory/GPU usage without external tools
4. **Service Management**: Control services without memorizing systemctl commands
5. **Real-Time Feedback**: Live updates, no manual refreshing needed

---

## Architecture

### Technology Stack

**Current Implementation** (scripts/ai-dashboard):
- **Framework**: [Textual](https://textualize.io/) - Modern Python TUI framework
- **Size**: 43k (sophisticated, feature-rich)
- **Language**: Python 3.7+
- **Dependencies**: textual, psutil, pyyaml, requests, pynvml (optional for GPU)

**Legacy Implementation** (scripts/ptui_dashboard.py):
- **Framework**: curses (stdlib)
- **Size**: 23k (simpler, less features)
- **Status**: Likely deprecated or alternative version

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AI Dashboard Application                   │
│                     (Textual TUI)                           │
└────────────┬────────────────────────────────────────────────┘
             │
   ┌─────────┴─────────┬─────────────┬─────────────┐
   │                   │             │             │
   ▼                   ▼             ▼             ▼
┌──────────┐    ┌──────────┐   ┌────────┐   ┌──────────┐
│ Provider │    │   GPU    │   │ System │   │ Service  │
│ Monitor  │    │ Monitor  │   │ Metrics│   │ Control  │
└────┬─────┘    └────┬─────┘   └───┬────┘   └────┬─────┘
     │               │             │             │
     ▼               ▼             ▼             ▼
HTTP Checks     NVML (GPU)    psutil       systemctl
to endpoints    (if NVIDIA)   (CPU/mem)    (services)
```

### Data Flow

```
1. Dashboard starts → Load config from config/providers.yaml
                   → Restore state from ~/.cache/ai-dashboard/

2. Every 5 seconds (default):
   → ProviderMonitor queries each endpoint (HTTP)
   → GPUMonitor queries GPU metrics (NVML)
   → SystemMonitor collects CPU/memory (psutil)
   → Update UI reactively (Textual framework)

3. User interaction:
   → Select provider → View details panel
   → Click button → Execute systemctl command
   → Press 'r' → Manual refresh all metrics
   → Press 'q' → Save state and exit

4. On exit:
   → Save dashboard_state.json
   → Clean shutdown
```

---

## UI Layout

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                         AI Backend Dashboard                              ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌─────────────────────────┐  ┌────────────────────────────────────┐   ║
║  │   Overview Panel        │  │      GPU Card                      │   ║
║  │                         │  │                                    │   ║
║  │  Services: 3/5 active   │  │  VRAM: 0.0 MB (0.0%)              │   ║
║  │  Avg CPU: 0.0%          │  │  GPU Util: 0%                     │   ║
║  │  Avg Mem: 0.1%          │  │                                    │   ║
║  │                         │  │  No NVIDIA GPU detected           │   ║
║  │  Attention:             │  │                                    │   ║
║  │  - llama.cpp (Python)   │  │                                    │   ║
║  │  - llama.cpp (Native)   │  │                                    │   ║
║  └─────────────────────────┘  └────────────────────────────────────┘   ║
║                                                                           ║
║  ┌───────────────────────────────────────────────────────────────────┐  ║
║  │                     Provider Status Table                        │  ║
║  ├─────────┬────────┬─────┬─────┬──────┬────────┬────────┬────────┤  ║
║  │Provider │ Status │ CPU │ Mem │ VRAM │  Resp  │ Models │  PID   │  ║
║  ├─────────┼────────┼─────┼─────┼──────┼────────┼────────┼────────┤  ║
║  │ Ollama  │ Active │ 0%  │217MB│  -   │  2ms   │   7    │ 12345  │  ║
║  │ vLLM    │ Active │ 0%  │ 8MB │  -   │  3ms   │   1    │  n/a   │  ║
║  │llama.cpp│Inactive│ 0%  │ 0MB │  -   │   -    │   0    │  n/a   │  ║
║  │LiteLLM  │ Active │ 0%  │127MB│  -   │  2ms   │   5    │ 67890  │  ║
║  └─────────┴────────┴─────┴─────┴──────┴────────┴────────┴────────┘  ║
║                                                                           ║
║  ┌─────────────────────────┐  ┌────────────────────────────────────┐   ║
║  │   Detail Panel          │  │      Event Log                     │   ║
║  │   (vLLM selected)       │  │                                    │   ║
║  │                         │  │  [green] Dashboard initialized     │   ║
║  │  Status: ACTIVE         │  │  [green] Ollama: Active (7 models) │   ║
║  │  Port: 8001             │  │  [yellow] vLLM: No GPU detected    │   ║
║  │  Models: 1              │  │  [red] llama.cpp: Inactive         │   ║
║  │  Resp: 3ms              │  │                                    │   ║
║  │  Mem: 0.0 MB (0.0%)     │  │                                    │   ║
║  │  VRAM: -                │  │                                    │   ║
║  │                         │  │                                    │   ║
║  │  [Start] [Stop]         │  │                                    │   ║
║  │  [Restart] [Enable]     │  │                                    │   ║
║  │  [Disable]              │  │                                    │   ║
║  └─────────────────────────┘  └────────────────────────────────────┘   ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ r refresh │ q quit │ a toggle-auto │ ^l clear-log │ ↑↓ navigate        ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Monitored Providers

| Provider | Port | Endpoint | Type | Purpose |
|----------|------|----------|------|---------|
| **Ollama** | 11434 | `/api/tags` | Optional | Local models, general-purpose |
| **vLLM** | 8001 | `/v1/models` | Required | High-throughput production inference |
| **llama.cpp (Python)** | 8000 | `/v1/models` | Optional | Python bindings server |
| **llama.cpp (Native)** | 8080 | `/v1/models` | Optional | C++ native server |
| **LiteLLM Gateway** | 4000 | `/v1/models` | Required | Unified API endpoint |

---

## Key Features Deep Dive

### 1. Real-Time Health Monitoring

**How it works**:
- Every 5 seconds (configurable), dashboard sends HTTP GET to each provider's health endpoint
- Parses response to extract model count and status
- Tracks response time (latency)
- Updates UI reactively via Textual's reactive attributes

**Status Determination**:
- ✅ **Active**: HTTP 200 OK, endpoint responding, models available
- ⚠️ **Degraded**: Required provider offline or returned error
- ❌ **Inactive**: Optional provider offline

### 2. Resource Tracking

**CPU & Memory**:
- Uses `psutil` to track per-process resource usage
- Finds provider processes by port (netstat/lsof logic)
- Calculates percentage of system resources
- Updates every refresh cycle

**GPU (VRAM)**:
- Uses `pynvml` (NVIDIA Management Library) to query GPU metrics
- Per-process VRAM usage attribution
- Total GPU utilization percentage
- Gracefully handles systems without NVIDIA GPUs

### 3. Service Control

**Security Model**:
- **Allowlist-based**: Only predefined services can be controlled
- **User-level systemctl**: No sudo required, uses `--user` flag
- **Input validation**: Service names and actions validated before execution
- **Command injection prevention**: No shell execution, direct subprocess calls

**Allowed Services**:
```python
ALLOWED_SERVICES = {
    "ollama": "ollama.service",
    "vllm": "vllm.service",
    "llama_cpp_python": "llamacpp-python.service",
    "llama_cpp_native": "llama-cpp-native.service",
    "litellm_gateway": "litellm.service",
}
```

**Allowed Actions**:
- `start` - Start the service
- `stop` - Stop the service
- `restart` - Restart gracefully
- `enable` - Enable at boot
- `disable` - Disable at boot

### 4. Configuration

**Environment Variables**:
```bash
AI_DASH_HTTP_TIMEOUT=3.0        # HTTP timeout (0.5-30s)
AI_DASH_REFRESH_INTERVAL=5      # Refresh rate (1-60s)
AI_DASH_LOG_HEIGHT=12           # Log display lines (5-50)
```

**Configuration Files**:
- `config/providers.yaml` - Provider registry
- `config/model-mappings.yaml` - Model routing rules

**State Persistence**:
- Location: `~/.cache/ai-dashboard/dashboard_state.json`
- Saved: Provider metrics, selected provider, timestamp
- Restored: On startup (if available)

---

## Use Cases

### 1. Daily Operations

**Scenario**: Developer starting work, needs to ensure all services are healthy.

```bash
# Launch dashboard
./ai-dashboard

# Quick visual scan:
# - 3/5 services active (Ollama, vLLM, LiteLLM)
# - llama.cpp instances inactive (expected)
# - No alerts or warnings
# - CPU/memory normal

# Action: Ready to work
```

### 2. Troubleshooting

**Scenario**: API requests to vLLM failing.

```bash
# Launch dashboard
./ai-dashboard

# Observations:
# - vLLM shows "Inactive" status
# - Event log: "Connection refused: http://localhost:8001"
# - Detail panel: PID n/a, Models: 0

# Action: Click "Start" button
# Result: Service starts, status → Active, models appear
```

### 3. Resource Monitoring

**Scenario**: System running slow, need to identify resource hog.

```bash
# Launch dashboard
./ai-dashboard

# Observations:
# - Ollama: 45% CPU, 2.5 GB RAM
# - vLLM: 20% CPU, 8 GB RAM
# - GPU: 90% utilization, 12 GB VRAM

# Action: Identify Ollama as potential issue
# Investigation: Check Ollama logs for high usage reason
```

### 4. Service Management

**Scenario**: Need to restart LiteLLM after configuration change.

```bash
# Launch dashboard
./ai-dashboard

# Actions:
# 1. Select "LiteLLM Gateway" in provider table
# 2. Click "Restart" in detail panel
# 3. Wait ~3 seconds
# 4. Event log: "LiteLLM restarted successfully"
# 5. Status updates to Active with new model count
```

### 5. GPU Monitoring

**Scenario**: Training model, need to monitor GPU usage.

```bash
# Launch dashboard
./ai-dashboard

# GPU Card shows:
# - Total VRAM: 24 GB
# - Used: 18 GB (75%)
# - GPU Utilization: 98%
# - vLLM process: 16 GB VRAM

# Continuous monitoring without nvidia-smi
```

---

## Performance Characteristics

### Resource Usage

- **Memory**: 50-100 MB baseline
- **CPU**: <5% idle, <20% during refresh
- **Network**: Minimal (health check pings only)

### Timing

- **Dashboard refresh**: 200-500ms (depends on provider count)
- **Service control**: 2-5 seconds (systemctl operation)
- **GPU metrics**: 100-200ms (if NVIDIA GPU available)

### Refresh Intervals

- **Default**: 5 seconds (balanced)
- **Recommended**: 3-10 seconds
- **Fast**: 1 second (high CPU usage)
- **Slow**: 60 seconds (minimal overhead)

---

## Security Considerations

### SSRF Prevention
- Only connects to `127.0.0.1` (localhost)
- Validates ports against allowlist
- Prevents arbitrary endpoint connections

### Command Injection Prevention
- Service names validated against `ALLOWED_SERVICES`
- Actions validated against `ALLOWED_ACTIONS`
- Uses `subprocess` with minimal environment
- No shell interpretation

### Service Control Authorization
- User-level systemctl only (no sudo)
- Services must be user-enabled
- Validates all inputs before execution

---

## Comparison: ai-dashboard vs ptui_dashboard.py

| Aspect | ai-dashboard (Textual) | ptui_dashboard.py (curses) |
|--------|------------------------|----------------------------|
| **Framework** | Textual (modern) | curses (stdlib) |
| **Size** | 43k (sophisticated) | 23k (simpler) |
| **UI Quality** | Rich, colorful, responsive | Basic, functional |
| **Features** | Full feature set | Limited features |
| **GPU Support** | Yes (pynvml) | Unknown |
| **Service Controls** | Yes | Unknown |
| **State Persistence** | Yes | Unknown |
| **Status** | Active, recommended | Likely deprecated |

**Recommendation**: Use `scripts/ai-dashboard` (Textual version) for best experience.

---

## Integration with AI Backend Infrastructure

### Role in Ecosystem

```
LAB Projects
     ↓
LiteLLM Gateway :4000 ← ← ← ← ← ai-dashboard monitors
     ↓                           ↓
┌────┴────┬────────┬──────────┐ Provides unified view
│         │        │          │ Controls services
Ollama  vLLM  llama.cpp       │ Tracks resources
:11434  :8001  :8000/:8080    │ Event logging
                               ↓
                        Dashboard TUI
```

### Complementary Tools

**Dashboard** (ai-dashboard):
- Real-time monitoring
- Interactive service control
- Visual health overview
- Single-terminal interface

**Scripts** (validate-unified-backend.sh):
- Batch health checks
- Non-interactive validation
- CI/CD integration
- Automated testing

**Monitoring Stack** (Prometheus + Grafana):
- Historical metrics
- Long-term trends
- Alerting rules
- Web-based dashboards

**Usage Pattern**:
```bash
# Daily work: ai-dashboard
./ai-dashboard

# Pre-deployment: validation script
./scripts/validate-unified-backend.sh

# Long-term monitoring: Prometheus + Grafana
cd monitoring && docker compose up
```

---

## Future Enhancements (Roadmap)

From `docs/ai-dashboard.md`:

- [ ] Network monitoring (bandwidth, packet stats)
- [ ] Historical metrics storage and trending
- [ ] Custom alert thresholds
- [ ] Multi-provider health scoring
- [ ] Web UI version (Textual Web)
- [ ] Remote monitoring support
- [ ] Integration with Prometheus/Grafana

---

## Quick Reference

### Launch
```bash
cd ai-backend-unified
./ai-dashboard
# or
python3 scripts/ai-dashboard
```

### Key Bindings
- `r` - Refresh manually
- `q` - Quit and save state
- `a` - Toggle auto-refresh
- `ctrl+l` - Clear event log
- `↑/↓` - Navigate provider table

### Configuration
```bash
# Custom refresh rate
AI_DASH_REFRESH_INTERVAL=3 ./ai-dashboard

# Increase timeout for slow networks
AI_DASH_HTTP_TIMEOUT=5.0 ./ai-dashboard
```

### Troubleshooting
```bash
# Check dependencies
python3 -c "import textual; import psutil; import yaml; print('OK')"

# Install if missing
pip install textual psutil pyyaml requests pynvml

# View logs
python3 scripts/ai-dashboard 2>dashboard.log
```

---

## Conclusion

The **AI Dashboard** is a **critical operational tool** for the AI Unified Backend Infrastructure. It provides:

1. **Unified Monitoring**: Single view of all LLM providers
2. **Real-Time Feedback**: Live status updates every 5 seconds
3. **Service Management**: Interactive systemctl controls
4. **Resource Tracking**: CPU, memory, GPU metrics
5. **Event Logging**: Persistent activity feed

**Primary Value**: Replaces manual checking of 5+ endpoints and services with a single, interactive, real-time dashboard that saves time and reduces errors during operations and troubleshooting.

**Target Users**:
- Developers working with AI backend
- System administrators managing services
- Anyone troubleshooting provider issues
- Operations monitoring infrastructure health

**Status**: Production-ready, actively maintained, recommended tool for daily AI backend operations.

---

**See Also**:
- Full documentation: `docs/ai-dashboard.md`
- User guide: `docs/ptui-user-guide.md`
- Observability stack: `docs/observability.md`
- Troubleshooting: `docs/troubleshooting.md`

**Last Updated**: October 26, 2025
