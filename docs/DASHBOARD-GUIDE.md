# Dashboard Guide: Unified Backend Monitoring

**Last Updated**: 2025-11-09

This guide helps you choose and use the right dashboard for monitoring the AI Unified Backend infrastructure.

## Quick Selection

**Choose based on your environment:**

| Scenario | Recommended Dashboard | Command |
|----------|---------------------|---------|
| Local workstation, modern terminal | **Textual Dashboard** | `./scripts/ai-dashboard` or `./scripts/cui` |
| SSH session, remote server | **PTUI Dashboard** | `python3 scripts/ptui_dashboard.py` or `./scripts/pui` |
| Monitoring stack (web) | **Grafana** | http://localhost:3000 |
| Command-line checks | **Validation Script** | `./scripts/validate-unified-backend.sh` |

## Dashboard Comparison

### 1. Textual Dashboard ⭐ (Primary for Local Use)

**Path**: `scripts/dashboard/` (package) + `scripts/ai-dashboard` (entry point)

**Launch**:
```bash
# Direct launch
./scripts/ai-dashboard

# Using alias
./scripts/cui

# With Python
python3 scripts/ai-dashboard
```

**Features**:
- ✅ Modern Textual framework with rich UI
- ✅ Real-time provider monitoring (Ollama, vLLM, llama.cpp, OpenAI, Anthropic)
- ✅ GPU utilization tracking (VRAM, temperature, usage)
- ✅ Service control (start, stop, restart, enable, disable)
- ✅ Live event logging with filtering
- ✅ Model discovery and listing
- ✅ Performance metrics (latency, requests/s)
- ✅ Keyboard shortcuts and navigation

**Requirements**:
- Modern terminal emulator (Kitty, iTerm2, Alacritty, Windows Terminal)
- Python 3.8+
- textual package
- GPU monitoring: pynvml (optional)

**Configuration**:
```bash
# Environment variables
export AI_DASH_HTTP_TIMEOUT=3.0        # Request timeout (0.5-30s)
export AI_DASH_REFRESH_INTERVAL=5      # Refresh interval (1-60s)
export AI_DASH_LOG_HEIGHT=12           # Event log height (5-50 lines)
```

**Keyboard Shortcuts**:
- `r` - Manual refresh
- `q` - Quit
- `a` - Toggle auto-refresh
- `Ctrl+l` - Clear event log
- `↑/↓` - Navigate
- `Tab` - Switch panels

**When to Use**:
- ✅ Local development and testing
- ✅ Interactive monitoring and debugging
- ✅ Service management and control
- ✅ Real-time performance analysis
- ❌ NOT for headless servers without terminal
- ❌ NOT for basic SSH sessions

**Documentation**: `docs/ai-dashboard.md`

---

### 2. PTUI Dashboard (Primary for SSH/Remote)

**Path**: `scripts/ptui_dashboard.py`

**Launch**:
```bash
# Direct launch
python3 scripts/ptui_dashboard.py

# Using alias
./scripts/pui

# With wrapper
./scripts/ptui
```

**Features**:
- ✅ Universal terminal compatibility (works on ANY terminal)
- ✅ Minimal dependencies (Python curses module)
- ✅ Provider health monitoring
- ✅ Model discovery and listing
- ✅ Latency tracking
- ✅ Auto-refresh (configurable)
- ✅ Lightweight resource usage
- ⚠️ Read-only (no service control)
- ⚠️ Basic UI (no colors on older terminals)

**Requirements**:
- Python 3.6+
- curses module (included in Python stdlib)
- No external dependencies

**Configuration**:
```bash
# Environment variables
export PTUI_HTTP_TIMEOUT=10            # Request timeout (seconds)
export PTUI_REFRESH_SECONDS=5          # Refresh interval (seconds)
export PTUI_CLI_NAME="pui"             # CLI name for display
```

**Keyboard Shortcuts**:
- `r` - Manual refresh
- `q` - Quit
- `a` - Toggle auto-refresh
- `h` - Help

**When to Use**:
- ✅ SSH sessions to remote servers
- ✅ Limited terminal capabilities
- ✅ Resource-constrained environments
- ✅ Basic xterm or older terminals
- ✅ Quick health checks
- ❌ NOT for service management (read-only)
- ❌ NOT for GPU monitoring

**Documentation**: `docs/ptui-dashboard.md`

---

### 3. Grafana (Web Monitoring)

**Path**: `monitoring/docker-compose.yml`

**Launch**:
```bash
cd monitoring
docker compose up -d
```

**Access**: http://localhost:3000 (admin/admin)

**Features**:
- ✅ Professional web-based dashboards
- ✅ 5 pre-built dashboards (overview, tokens, performance, health, system)
- ✅ Historical metrics with 30-day retention
- ✅ Prometheus integration for metrics
- ✅ Alerting capabilities
- ✅ Mobile app support
- ✅ Multi-user access
- ✅ Customizable dashboards

**Requirements**:
- Docker and Docker Compose
- 500MB+ disk space for metrics
- Network access to :3000 and :9090

**Dashboards**:
1. **Overview** - Request rates, error rates, latency
2. **Token Usage** - Cost tracking, consumption by model
3. **Performance** - Latency percentiles (P50/P95/P99), heatmaps
4. **Provider Health** - Success rates, failure analysis
5. **System Health** - Redis metrics, cache hit rate

**When to Use**:
- ✅ Production monitoring and alerting
- ✅ Historical analysis and trending
- ✅ Team collaboration (multi-user)
- ✅ Mobile monitoring via app
- ✅ SLA tracking and reporting
- ❌ NOT for quick health checks
- ❌ NOT for service control

**Documentation**: `docs/observability.md`, `monitoring/README.md`

---

### 4. Validation Script (CLI Health Checks)

**Path**: `scripts/validate-unified-backend.sh`

**Launch**:
```bash
# Quick validation
./scripts/validate-unified-backend.sh

# JSON output
./scripts/validate-unified-backend.sh --json

# Verbose mode
./scripts/validate-unified-backend.sh --verbose
```

**Features**:
- ✅ Fast health checks (< 5 seconds)
- ✅ Provider endpoint testing
- ✅ Model discovery validation
- ✅ JSON output for scripting
- ✅ Exit codes for automation
- ⚠️ No real-time monitoring

**When to Use**:
- ✅ CI/CD pipeline health checks
- ✅ Cron job monitoring
- ✅ Pre-deployment validation
- ✅ Scripted automation
- ❌ NOT for interactive monitoring
- ❌ NOT for troubleshooting

---

## Installation

### Textual Dashboard

```bash
# Install dependencies
pip install textual rich psutil requests pynvml

# Or from requirements
pip install -r scripts/dashboard/requirements.txt

# Launch
./scripts/ai-dashboard
```

### PTUI Dashboard

```bash
# No installation needed (uses stdlib curses)
python3 scripts/ptui_dashboard.py
```

### Grafana

```bash
cd monitoring
docker compose up -d

# Wait for startup (30-60 seconds)
# Access at http://localhost:3000
```

## Choosing the Right Dashboard

### Decision Tree

```
Do you need web-based access?
├─ Yes → Use Grafana
└─ No
   │
   Are you on an SSH session?
   ├─ Yes → Use PTUI Dashboard
   └─ No
      │
      Do you need service control?
      ├─ Yes → Use Textual Dashboard
      └─ No
         │
         Do you need historical metrics?
         ├─ Yes → Use Grafana
         └─ No → Use PTUI Dashboard (faster)
```

### Use Case Examples

**Scenario 1: Local Development**
- **Dashboard**: Textual Dashboard (`./scripts/cui`)
- **Why**: Full features, GPU monitoring, service control

**Scenario 2: Remote SSH Monitoring**
- **Dashboard**: PTUI Dashboard (`./scripts/pui`)
- **Why**: Universal compatibility, lightweight, works on any terminal

**Scenario 3: Production Monitoring**
- **Dashboard**: Grafana (http://localhost:3000)
- **Why**: Historical data, alerting, team access

**Scenario 4: Quick Health Check**
- **Dashboard**: Validation Script (`./scripts/validate-unified-backend.sh`)
- **Why**: Fast, scriptable, exit codes

**Scenario 5: Troubleshooting Performance**
- **Dashboard**: Textual Dashboard + Grafana
- **Why**: Real-time debugging (Textual) + historical analysis (Grafana)

**Scenario 6: CI/CD Pipeline**
- **Dashboard**: Validation Script (JSON output)
- **Why**: Automation-friendly, parseable output

## Common Tasks

### Check Provider Health
```bash
# Textual Dashboard
./scripts/ai-dashboard
# Look at provider status (top panel)

# PTUI Dashboard
./scripts/pui
# View provider table

# Validation Script
./scripts/validate-unified-backend.sh
```

### Monitor GPU Usage
```bash
# Textual Dashboard (only option with GPU monitoring)
./scripts/ai-dashboard
# View GPU panel (bottom right)

# Or use nvidia-smi directly
watch -n 1 nvidia-smi
```

### Discover Available Models
```bash
# Textual Dashboard
./scripts/ai-dashboard
# Navigate to Models tab

# PTUI Dashboard
./scripts/pui
# Press 'm' for model list

# cURL
curl http://localhost:4000/v1/models | jq
```

### Control Services
```bash
# Textual Dashboard (interactive)
./scripts/ai-dashboard
# Use service control panel

# Or systemctl directly
systemctl --user restart vllm.service
systemctl --user status ollama.service
```

### View Historical Metrics
```bash
# Grafana only
# Access http://localhost:3000
# Select dashboard from left menu
```

## Troubleshooting

### Textual Dashboard Issues

**Problem**: "textual module not found"
```bash
Solution: pip install textual rich
```

**Problem**: GPU monitoring not working
```bash
Solution: pip install pynvml
# Or disable GPU monitoring in config
```

**Problem**: Terminal rendering issues
```bash
Solution: Use a modern terminal emulator
- Kitty: https://sw.kovidgoyal.net/kitty/
- iTerm2 (macOS): https://iterm2.com/
- Windows Terminal: https://aka.ms/terminal
```

### PTUI Dashboard Issues

**Problem**: Display corruption
```bash
Solution: Clear screen and relaunch
clear && python3 scripts/ptui_dashboard.py
```

**Problem**: Colors not showing
```bash
Solution: Normal for basic terminals (still functional)
# Or set TERM environment variable
export TERM=xterm-256color
```

### Grafana Issues

**Problem**: Cannot access :3000
```bash
Solution: Check if Grafana is running
docker compose -f monitoring/docker-compose.yml ps

# Restart if needed
docker compose -f monitoring/docker-compose.yml restart
```

**Problem**: No data in dashboards
```bash
Solution: Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Verify LiteLLM is exposing metrics
curl http://localhost:4000/metrics
```

## Performance Considerations

### Resource Usage

| Dashboard | CPU | Memory | Disk | Network |
|-----------|-----|--------|------|---------|
| Textual | 2-5% | 50MB | None | Minimal |
| PTUI | 1-2% | 20MB | None | Minimal |
| Grafana | 5-10% | 200MB | 500MB+ | Moderate |
| Validation | <1% | 10MB | None | Minimal |

### Refresh Intervals

**Recommended settings**:
- **Textual**: 5 seconds (configurable 1-60s)
- **PTUI**: 5 seconds (configurable)
- **Grafana**: 5-30 seconds per dashboard
- **Validation**: On-demand or cron (e.g., every 5 minutes)

## Migration from Experimental Dashboards

If you were using archived experimental dashboards:

| Old Script | New Replacement |
|-----------|----------------|
| `./scripts/monitor` | `./scripts/ai-dashboard` |
| `./scripts/monitor-enhanced` | `./scripts/ai-dashboard` |
| `./scripts/monitor-lite` | `./scripts/pui` |
| `./scripts/monitor-unified` | `./scripts/ai-dashboard` |

**All experimental scripts archived in**: `scripts/archive/experimental-dashboards/`

## Additional Resources

- **Textual Dashboard**: `docs/ai-dashboard.md`
- **PTUI Dashboard**: `docs/ptui-dashboard.md`
- **Grafana Monitoring**: `docs/observability.md`
- **Provider Configuration**: `config/providers.yaml`
- **Troubleshooting**: `docs/troubleshooting.md`

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│              AI UNIFIED BACKEND DASHBOARDS                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LOCAL MONITORING                                            │
│  ├─ Textual Dashboard ..... ./scripts/ai-dashboard (or cui) │
│  └─ Quick Check ........... ./scripts/validate-unified-...  │
│                                                              │
│  REMOTE MONITORING (SSH)                                     │
│  └─ PTUI Dashboard ........ ./scripts/pui                   │
│                                                              │
│  WEB MONITORING                                              │
│  └─ Grafana ............... http://localhost:3000           │
│                                                              │
│  SHORTCUTS                                                   │
│  ├─ cui ................... Textual Dashboard alias         │
│  └─ pui ................... PTUI Dashboard alias            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

**Last Updated**: 2025-11-09
**Version**: 2.0
**Maintainer**: AI Backend Infrastructure Team
