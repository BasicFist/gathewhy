# AI Backend Unified - Monitoring Dashboards and Observability

**Memory Type**: Monitoring Patterns and Dashboard Implementations
**Created**: 2025-11-11
**Last Updated**: 2025-11-11

## Overview

The AI Backend Unified infrastructure provides dual dashboard implementations for comprehensive real-time monitoring and observability:

1. **Enhanced Textual Dashboard (PTUI)** - Interactive terminal UI with rich visualizations
2. **WTH Dashboard Widgets** - Lightweight shell-based modular monitoring

Both approaches complement each other and can be used simultaneously for different use cases.

---

## Enhanced Textual Dashboard (PTUI)

### Architecture

**File**: `scripts/ai-dashboard-enhanced.py`
**Framework**: Textual (Python TUI framework)
**Size**: 8.7 KB
**Language**: Python 3.8+

**Key Components**:
```python
class ProviderHealthWidget(Static):
    """Display provider health status with visual indicators"""
    # Real-time health checks with emoji status indicators
    # Shows: provider name, latency, model count

class AIEnhancedDashboard(App):
    """Main dashboard application"""
    # Bindings: q=quit, r=refresh, c=config_editor
    # Auto-refresh timer
    # Multi-pane layout with containers
```

### Features

1. **Provider Health Monitoring**
   - Visual indicators (🟢 active, 🔴 inactive)
   - Real-time latency measurements
   - Model count per provider
   - Service status tracking

2. **Performance Comparison**
   - Side-by-side provider latency comparison
   - Request throughput metrics
   - Token usage tracking
   - Cache hit rate display

3. **Configuration Editor**
   - Toggle view with 'c' key
   - Live configuration inspection
   - Model routing visualization

4. **Request Inspector**
   - Live request monitoring
   - Request/response payloads
   - Error tracking with timestamps
   - Performance metrics per request

5. **System Metrics**
   - CPU and memory usage (psutil)
   - Network I/O statistics
   - Active connection count

### Installation

```bash
# Using provided installer
./scripts/install-wth-dashboard.sh

# Manual installation
pip install textual requests psutil

# Verify installation
python3 -c "import textual; print(textual.__version__)"
```

### Usage Patterns

**Basic Monitoring**:
```bash
python3 scripts/ai-dashboard-enhanced.py
# Press 'r' to force refresh
# Press 'q' to quit
```

**Troubleshooting Session**:
```bash
# Terminal 1: Run dashboard
python3 scripts/ai-dashboard-enhanced.py

# Terminal 2: Generate test traffic
./test_kimi_routing.sh

# Observe real-time routing and performance in dashboard
```

**Configuration Inspection**:
```bash
# Launch dashboard
python3 scripts/ai-dashboard-enhanced.py

# Press 'c' to toggle configuration editor
# View current routing rules and provider settings
```

### Customization

**Refresh Interval**:
```python
# In ai-dashboard-enhanced.py
self.set_interval(5)  # Refresh every 5 seconds (default)
```

**Provider Endpoints**:
```python
# Environment variables (future enhancement)
LITELLM_HOST = os.getenv("LITELLM_HOST", "http://localhost:4000")
PROMETHEUS_HOST = os.getenv("PROMETHEUS_HOST", "http://localhost:9090")
```

### Troubleshooting

**Dashboard won't start**:
```bash
# Check dependencies
pip list | grep -E "(textual|requests|psutil)"

# Verify Python version
python3 --version  # Should be 3.8+

# Test LiteLLM connectivity
curl http://localhost:4000/health
```

**No metrics displayed**:
```bash
# Check LiteLLM service
systemctl --user status litellm.service

# Verify Prometheus endpoint
curl http://localhost:9090/metrics
```

**High CPU usage**:
```python
# Increase refresh interval in code
self.set_interval(10)  # 10 seconds instead of 5
```

---

## WTH Dashboard Widgets

### Architecture

**Location**: `wth-widgets/litellm/`
**Framework**: WTH (We're Terminal Here) - Go-based dashboard framework
**Language**: Bash/Shell
**Pattern**: Modular widget architecture

**Directory Structure**:
```
wth-widgets/
├── README.md                    # Documentation
└── litellm/
    ├── bin/                     # Executable widgets
    │   ├── common.sh            # Shared helper functions
    │   ├── health-status.sh     # Service health overview
    │   ├── providers-overview.sh # Provider status matrix
    │   ├── litellm-metrics.sh   # Prometheus metrics sampler
    │   ├── cache-performance.sh # Redis cache statistics
    │   ├── provider-score.sh    # Performance scoring
    │   ├── litellm-logs.sh      # Recent proxy logs
    │   └── litellm-status.sh    # Detailed service status
    └── config/
        └── wth-lite-dashboard.yaml  # Pre-configured layout
```

### Widget Catalog

#### 1. common.sh - Shared Helper Functions

**Purpose**: DRY utilities for all widgets

**Key Functions**:
```bash
check_litellm_health() {
    # Returns 0 if healthy, 1 otherwise
}

get_prometheus_metric() {
    # Fetches specific metric from Prometheus
}

format_with_gum() {
    # Styled output (degrades gracefully without Gum)
}

get_provider_latency() {
    # Calculates P95 latency from metrics
}
```

**Usage in Widgets**:
```bash
#!/bin/bash
source "$(dirname "$0")/common.sh"

if check_litellm_health; then
    echo "✅ LiteLLM is healthy"
else
    echo "❌ LiteLLM is down"
    exit 1
fi
```

#### 2. health-status.sh - Service Health Overview

**Checks**:
- LiteLLM gateway (port 4000)
- Ollama (port 11434)
- vLLM (port 8001)
- llama.cpp (ports 8000, 8080)
- Redis cache (port 6379)

**Output Format**:
```
Service Health Status
━━━━━━━━━━━━━━━━━━━━
✅ LiteLLM    (4000)  UP     12.3ms
✅ Ollama     (11434) UP     45.2ms
✅ vLLM       (8001)  UP     23.1ms
⚠️  llama.cpp (8000)  DOWN   -
✅ Redis      (6379)  UP     1.2ms
```

**Usage**:
```bash
./wth-widgets/litellm/bin/health-status.sh

# In WTH config:
stickers:
  - command: health-status.sh
    refresh: 10s
```

#### 3. providers-overview.sh - Provider Status Matrix

**Information Displayed**:
- Provider name
- Active status
- Model count
- Current load (requests/min)
- Average latency

**Output Format**:
```
Provider Overview
━━━━━━━━━━━━━━━━━
Provider      Status  Models  Load    Latency
ollama        active  3       45/min  123ms
vllm-qwen     active  1       12/min  89ms
ollama_cloud  active  6       8/min   245ms
```

#### 4. litellm-metrics.sh - Prometheus Metrics Sampler

**Metrics Collected**:
- Total requests (counter)
- Requests per minute (rate)
- Average latency (histogram)
- Error rate (ratio)
- Cache hit rate (ratio)

**Output Format**:
```
LiteLLM Metrics (Last 5m)
━━━━━━━━━━━━━━━━━━━━━━━
Requests:    1,234 total (45/min)
Latency:     P50=89ms P95=234ms P99=456ms
Errors:      12 (0.97%)
Cache Hits:  678 (55.0%)
```

#### 5. cache-performance.sh - Redis Cache Statistics

**Statistics**:
- Total keys in cache
- Memory usage
- Hit rate (last hour)
- Eviction count
- TTL distribution

**Output Format**:
```
Redis Cache Performance
━━━━━━━━━━━━━━━━━━━━━
Keys:        1,456
Memory:      23.4 MB
Hit Rate:    67.8%
Evictions:   23
Avg TTL:     1,234s
```

#### 6. provider-score.sh - Provider Performance Scoring

**Scoring Factors**:
- Latency (40% weight)
- Error rate (30% weight)
- Availability (20% weight)
- Throughput (10% weight)

**Output Format**:
```
Provider Performance Scores
━━━━━━━━━━━━━━━━━━━━━━━━━
Provider      Score  Grade  Recommendation
vllm-qwen     92     A      Primary
ollama        85     B+     Secondary
ollama_cloud  71     C      Fallback only
```

#### 7. litellm-logs.sh - Recent Proxy Logs

**Log Sources**:
- journalctl (systemd service logs)
- File-based logs (if configured)
- Error logs (filtered)

**Output Format**:
```
Recent LiteLLM Logs (Last 40 lines)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2025-11-11 14:30:45] INFO: Request routed to ollama
[2025-11-11 14:30:46] INFO: Cache hit for model llama3.1:8b
[2025-11-11 14:30:47] ERROR: Provider vllm timeout
[2025-11-11 14:30:48] INFO: Fallback to ollama successful
```

**Configuration**:
```bash
export LITELLM_LOG_SOURCE="journalctl --user -u litellm.service -n 40"
# or
export LITELLM_LOG_SOURCE="tail -n 40 /var/log/litellm.log"
```

#### 8. litellm-status.sh - Detailed Service Status

**Information**:
- Service uptime
- PID and resource usage
- Active connections
- Configuration hash (detects changes)
- Last restart timestamp

**Output Format**:
```
LiteLLM Service Status
━━━━━━━━━━━━━━━━━━━━━
Status:      active (running)
Uptime:      3d 14h 23m
PID:         12345
CPU:         4.2%
Memory:      234.5 MB
Connections: 12 active
Config:      0a1b2c3d (unchanged)
Last Start:  2025-11-08 00:00:00
```

---

### WTH Configuration

**File**: `wth-widgets/litellm/config/wth-lite-dashboard.yaml`

**Example Layout**:
```yaml
layout:
  - type: horizontal
    stickers:
      - command: health-status.sh
        refresh: 10s
        width: 50%
      - command: providers-overview.sh
        refresh: 15s
        width: 50%

  - type: horizontal
    stickers:
      - command: cache-performance.sh
        refresh: 30s
        width: 33%
      - command: litellm-metrics.sh
        refresh: 5s
        width: 34%
      - command: provider-score.sh
        refresh: 60s
        width: 33%

  - type: vertical
    stickers:
      - command: litellm-logs.sh
        refresh: 5s
        height: 100%
```

**Customization**:
```yaml
# Adjust refresh rates for performance
stickers:
  - command: expensive-widget.sh
    refresh: 60s  # Reduce CPU usage

  - command: critical-widget.sh
    refresh: 2s   # Near real-time
```

---

## Testing Infrastructure

### Kimi K2 Routing Test

**File**: `test_kimi_routing.sh`
**Purpose**: Validate routing, load balancing, and fallback chains

**Test Cases**:

1. **Direct Model Request**
   - Model: `kimi-k2:1t-cloud`
   - Provider: `ollama_cloud`
   - Validates: Exact match routing

2. **Capability-Based Routing**
   - Capability: `reasoning`
   - Expected: Load balanced across model pool
   - Validates: Capability routing and load distribution

**Usage**:
```bash
./test_kimi_routing.sh

# Expected output:
# === Testing Kimi K2 Routing Configuration ===
#
# Test 1: Direct request to kimi-k2:1t-cloud
# [Response from Kimi K2 model]
#
# Test 2: Reasoning capability request
# [Response from load-balanced model]
```

**Troubleshooting Test Failures**:
```bash
# FAILED - Check OLLAMA_API_KEY
echo $OLLAMA_API_KEY
# Should print: Bearer ollama_cloud_...

# Verify routing configuration
grep -A 10 "kimi-k2:1t-cloud" config/model-mappings.yaml

# Check Ollama Cloud connectivity
curl https://ollama.com/api/tags \
  -H "Authorization: Bearer $OLLAMA_API_KEY"

# Test LiteLLM routing
curl http://localhost:4000/v1/models | jq '.data[] | select(.id == "kimi-k2:1t-cloud")'
```

---

## Dashboard Comparison Matrix

| Feature | Enhanced Textual | WTH Widgets |
|---------|-----------------|-------------|
| **Installation** | pip install | go install + scripts |
| **Resource Usage** | Medium (50-100 MB) | Low (5-10 MB) |
| **Interactivity** | High (keybindings) | Medium (manual refresh) |
| **Customization** | Code modification | Config file + shell |
| **Real-time Updates** | Auto-refresh | Configurable intervals |
| **Dependencies** | Python, textual, psutil | WTH, optional Gum |
| **Visual Richness** | High (TUI framework) | Medium (colored text) |
| **Scriptability** | Limited | High (shell-based) |
| **Integration** | Standalone | tmux/screen panes |
| **Learning Curve** | Low | Medium |

---

## Recommended Usage Patterns

### Development Workflow

**Setup**:
```bash
# Terminal multiplexer layout (tmux)
tmux new-session -s ai-backend \; \
  split-window -h \; \
  select-pane -t 0 \; \
  send-keys "python3 scripts/ai-dashboard-enhanced.py" C-m \; \
  select-pane -t 1 \; \
  send-keys "wth run --config ~/.config/wth/wth.yaml" C-m
```

**Use Case**: Interactive development with dual views
- Left pane: Enhanced Textual (detailed exploration)
- Right pane: WTH widgets (persistent monitoring)

### Production Monitoring

**Setup**:
```bash
# Persistent WTH dashboard in detached tmux
tmux new-session -d -s monitoring \
  "wth run --config ~/.config/wth/wth.yaml"

# Attach when needed
tmux attach -t monitoring
```

**Use Case**: Lightweight persistent monitoring
- Low resource overhead
- Always-on monitoring
- Quick attach for investigation

### Incident Response

**Setup**:
```bash
# Quick-launch Enhanced Textual for deep dive
python3 scripts/ai-dashboard-enhanced.py

# Supplement with targeted widgets
./wth-widgets/litellm/bin/litellm-logs.sh
./wth-widgets/litellm/bin/provider-score.sh
```

**Use Case**: High-detail troubleshooting
- Real-time visual feedback
- Request inspector for debugging
- Performance comparison for root cause

### Performance Analysis

**Setup**:
```bash
# Capture baseline metrics
./wth-widgets/litellm/bin/litellm-metrics.sh > baseline-metrics.txt

# Make configuration change
# ...

# Compare after change
./wth-widgets/litellm/bin/litellm-metrics.sh > after-metrics.txt
diff -u baseline-metrics.txt after-metrics.txt
```

**Use Case**: Configuration tuning and validation
- Quantitative before/after comparison
- Provider performance scoring
- Cache effectiveness analysis

---

## Integration with Monitoring Stack

### Prometheus Integration

**Widgets Using Prometheus**:
- `litellm-metrics.sh` - Direct PromQL queries
- `cache-performance.sh` - Redis metrics via Prometheus
- `provider-score.sh` - Latency histograms

**Example PromQL Queries** (from widgets):
```promql
# Request rate
rate(litellm_requests_total[5m])

# P95 latency
histogram_quantile(0.95, litellm_request_duration_seconds_bucket)

# Error rate
rate(litellm_requests_total{status="error"}[5m]) /
rate(litellm_requests_total[5m])

# Cache hit rate
litellm_cache_hits / (litellm_cache_hits + litellm_cache_misses)
```

### Grafana Integration

**Dashboard Widgets as Grafana Alternatives**:
- Lightweight for development environments
- Quick setup without Docker
- Scriptable data export for Grafana import

**Grafana + Dashboard Hybrid**:
- Grafana: Historical analysis and alerting
- Dashboards: Real-time monitoring and debugging
- Export widget metrics to Prometheus for Grafana visualization

---

## Extension Patterns

### Adding Custom Widget

**Template**:
```bash
#!/bin/bash
# wth-widgets/litellm/bin/custom-widget.sh

# Source common helpers
source "$(dirname "$0")/common.sh"

# Widget logic
echo "Custom Widget Output"
echo "━━━━━━━━━━━━━━━━━━"

if check_litellm_health; then
    metric=$(get_prometheus_metric "custom_metric")
    format_with_gum "Metric: $metric"
else
    echo "⚠️ Service unavailable"
fi
```

**Register in WTH**:
```yaml
stickers:
  - command: custom-widget.sh
    refresh: 10s
```

### Extending Enhanced Textual Dashboard

**Add Custom Widget**:
```python
class CustomWidget(Static):
    """Custom monitoring widget"""

    def __init__(self, data_source):
        self.data_source = data_source
        super().__init__()

    def on_mount(self):
        self.set_interval(5, self.refresh_data)

    def refresh_data(self):
        data = self.data_source.fetch()
        self.update(self.render_data(data))

# Add to dashboard
class AIEnhancedDashboard(App):
    def compose(self):
        yield CustomWidget(data_source=MyDataSource())
```

---

## Performance Considerations

### Resource Usage

**Enhanced Textual Dashboard**:
- CPU: 2-5% (idle), 10-15% (active refresh)
- Memory: 50-100 MB (depends on history buffer)
- Network: Minimal (HTTP polling)

**WTH Widgets**:
- CPU: <1% per widget
- Memory: 5-10 MB total
- Network: Minimal (curl requests)

### Optimization Tips

**Reduce Dashboard Overhead**:
```python
# Increase refresh interval
self.set_interval(10)  # 10s instead of 5s

# Limit history buffer
self.max_history = 100  # Reduce from default
```

**Optimize WTH Widgets**:
```bash
# Cache expensive operations
CACHE_FILE="/tmp/widget-cache-$WIDGET_NAME"
CACHE_TTL=30

if [[ -f "$CACHE_FILE" ]] && [[ $(($(date +%s) - $(stat -c %Y "$CACHE_FILE"))) -lt $CACHE_TTL ]]; then
    cat "$CACHE_FILE"
else
    expensive_operation > "$CACHE_FILE"
    cat "$CACHE_FILE"
fi
```

---

## Troubleshooting Guide

### Common Issues

**Dashboard Performance Degradation**:
```bash
# Check for runaway processes
ps aux | grep -E "(python|wth)" | grep -v grep

# Monitor system resources
htop -p $(pgrep -f "ai-dashboard-enhanced.py")

# Reduce refresh rates in configuration
```

**Widget Not Updating**:
```bash
# Check WTH process
ps aux | grep wth

# Verify widget execution
./wth-widgets/litellm/bin/problematic-widget.sh

# Check WTH logs
wth run --debug --config ~/.config/wth/wth.yaml
```

**Missing Metrics**:
```bash
# Verify Prometheus endpoint
curl http://localhost:9090/metrics | grep litellm

# Check LiteLLM Prometheus config
grep -A 5 "prometheus:" config/litellm-unified.yaml

# Restart LiteLLM with metrics enabled
systemctl --user restart litellm.service
```

---

## Future Enhancements

**Planned Features**:
- [ ] Real-time alerts in dashboards
- [ ] Historical trend visualization
- [ ] Export to CSV/JSON for analysis
- [ ] Multi-environment support (dev/staging/prod)
- [ ] Custom alert threshold configuration
- [ ] Mobile-responsive web dashboard
- [ ] Integration with PagerDuty/Slack

**Community Contributions**:
- Additional WTH widgets for specific metrics
- Enhanced Textual themes and customization
- Integration with other monitoring tools
- Performance profiling utilities
