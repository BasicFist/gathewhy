# Dashboard Comparison Guide

**AI Backend Unified** - Complete comparison of monitoring dashboard implementations

## Executive Summary

This project provides **three distinct dashboard implementations** for monitoring the AI Backend Unified infrastructure. Each dashboard targets different use cases, environments, and user preferences. This guide helps you choose the right dashboard for your needs and understand the trade-offs between them.

**Quick Recommendation**:
- **Local monitoring with full features**: Use **AI Dashboard** (Textual)
- **Remote SSH sessions**: Use **PTUI Dashboard** (curses)
- **Browser-based access**: Use **Web UI** (Gradio)

## Dashboard Overview

### 1. AI Dashboard (Textual) - `scripts/ai-dashboard`

**Primary monitoring tool** built with the modern Textual TUI framework.

**Key Characteristics**:
- Modern, feature-rich interface with GPU monitoring
- Service control (start/stop/restart via systemctl)
- Real-time event logging and alerts
- Rich rendering with colors, borders, and animations
- Best for local development and primary monitoring

**Technology Stack**: Python 3.12+, Textual framework, asyncio

### 2. PTUI Dashboard (curses) - `scripts/ptui_dashboard.py`

**SSH-optimized monitoring tool** built with Python's standard curses library.

**Key Characteristics**:
- Universal terminal compatibility (xterm, vt100, etc.)
- No external dependencies (uses stdlib only)
- Minimal resource footprint (<5MB)
- Authentication support (LITELLM_MASTER_KEY)
- Best for remote SSH sessions and constrained environments

**Technology Stack**: Python 3.12+, curses (stdlib), urllib (stdlib)

### 3. Web UI (Gradio) - `web-ui/app.py`

**Browser-based monitoring interface** built with Gradio.

**Key Characteristics**:
- Accessible from any device with a web browser
- Mobile-friendly responsive design
- No terminal required
- Shareable URL for team access (optional)
- Best for non-technical users and mobile access

**Technology Stack**: Python 3.12+, Gradio, Flask, SQLite

## Detailed Feature Comparison

### Core Functionality

| Feature | AI Dashboard | PTUI Dashboard | Web UI |
|---------|-------------|----------------|--------|
| **Service Health Monitoring** | ✅ Full | ✅ Full | ✅ Basic |
| **Model Discovery** | ✅ Real-time from LiteLLM | ✅ Real-time from LiteLLM | ✅ Cached list |
| **Latency Tracking** | ✅ P50/P95/P99 | ✅ Per-request | ✅ Average only |
| **Error Display** | ✅ Detailed with context | ✅ Error message | ✅ Status code |
| **Auto-refresh** | ✅ 3-10s configurable | ✅ 1-60s configurable | ✅ 5s fixed |
| **Manual Refresh** | ✅ 'r' key | ✅ 'r' key or action | ✅ Button click |

### Advanced Features

| Feature | AI Dashboard | PTUI Dashboard | Web UI |
|---------|-------------|----------------|--------|
| **Service Control** | ✅ Start/stop/restart | ❌ Read-only | ❌ Read-only |
| **GPU Monitoring** | ✅ Utilization graphs | ❌ Not supported | ⚠️ Basic stats |
| **Event Logging** | ✅ Real-time stream | ❌ Not supported | ⚠️ Basic logs |
| **Validation Actions** | ✅ Run validation scripts | ✅ Run validation scripts | ⚠️ Limited |
| **Health Probes** | ✅ Comprehensive | ✅ Required/optional | ✅ Basic |
| **Historical Data** | ⚠️ In-memory only | ❌ Not supported | ✅ SQLite database |

### User Experience

| Feature | AI Dashboard | PTUI Dashboard | Web UI |
|---------|-------------|----------------|--------|
| **Keyboard Navigation** | ✅ Full (arrows, tab, hotkeys) | ✅ Full (arrows, tab, enter) | ⚠️ Limited |
| **Mouse Support** | ✅ Click to select | ❌ Keyboard only | ✅ Full mouse support |
| **Visual Design** | ✅ Modern with borders/colors | ✅ Simple ASCII | ✅ Web UI components |
| **Accessibility** | ✅ Screen reader support | ✅ Terminal compatible | ✅ ARIA labels |
| **Learning Curve** | ⚠️ Medium (many features) | ✅ Low (simple interface) | ✅ Low (familiar web UI) |

### Technical Requirements

| Requirement | AI Dashboard | PTUI Dashboard | Web UI |
|------------|-------------|----------------|--------|
| **Dependencies** | Textual, rich | None (stdlib), aiohttp (optional) | Gradio, Flask, SQLite |
| **Install Size** | ~15MB | ~0MB (stdlib) | ~50MB |
| **Memory Usage** | 10-15MB | <5MB | 50-100MB |
| **CPU Usage** | Low-Medium | Minimal | Medium |
| **Terminal Support** | Modern (Kitty, iTerm2, Alacritty, tmux) | Universal (xterm, vt100, ssh) | N/A (browser-based) |
| **Network Access** | Not required | Not required | HTTP port (7860) |
| **Python Version** | 3.8+ | 3.8+ | 3.8+ |

### Configuration & Customization

| Feature | AI Dashboard | PTUI Dashboard | Web UI |
|---------|-------------|----------------|--------|
| **Environment Variables** | ✅ AI_DASH_* | ✅ PTUI_* | ✅ WEB_UI_* |
| **Config File Support** | ✅ providers.yaml | ✅ providers.yaml | ❌ Hardcoded |
| **Dynamic Service Loading** | ✅ Auto-reload | ✅ Auto-reload | ❌ Restart required |
| **Authentication** | ❌ Not required | ✅ LITELLM_MASTER_KEY | ❌ Not required |
| **Rate Limiting** | ❌ Not applicable | ❌ Not applicable | ⚠️ Basic (Gradio) |
| **Logging** | ✅ To file | ✅ To stderr | ✅ To file |

### Remote Access & Security

| Feature | AI Dashboard | PTUI Dashboard | Web UI |
|---------|-------------|----------------|--------|
| **SSH Access** | ✅ Yes (modern terminals) | ✅ Yes (universal) | ❌ Not applicable |
| **Browser Access** | ❌ Not applicable | ❌ Not applicable | ✅ Yes |
| **Network Exposure** | ❌ Local only | ❌ Local only | ⚠️ Configurable |
| **Authentication** | ❌ Not built-in | ✅ API key support | ❌ Not built-in |
| **Encryption** | ✅ SSH tunnel | ✅ SSH tunnel | ⚠️ Requires HTTPS |
| **Multi-user** | ❌ Single session | ❌ Single session | ✅ Multiple users |

## Use Case Recommendations

### When to Use AI Dashboard (Textual)

**Primary Scenarios**:
1. **Local Development** - Working directly on the server with full terminal access
2. **Primary Monitoring** - Need comprehensive visibility into all system aspects
3. **Service Management** - Require start/stop/restart capabilities
4. **GPU-Accelerated Workloads** - Need GPU utilization monitoring
5. **Event-Driven Debugging** - Real-time event stream is critical

**Requirements**:
- Modern terminal emulator (Kitty, iTerm2, Alacritty, VS Code terminal)
- Python 3.8+ with Textual installed (`pip install textual`)
- Direct or SSH access with terminal forwarding

**Example Workflow**:
```bash
# Install dependencies
pip install textual rich

# Launch dashboard
python3 scripts/ai-dashboard

# Or with custom refresh interval
AI_DASH_REFRESH_INTERVAL=3 python3 scripts/ai-dashboard
```

### When to Use PTUI Dashboard (curses)

**Primary Scenarios**:
1. **SSH Sessions** - Remote access over SSH with basic terminal support
2. **Constrained Environments** - Limited resources or dependencies
3. **Universal Compatibility** - Need to work on any terminal (xterm, vt100, etc.)
4. **Authentication Required** - LiteLLM has master key authentication enabled
5. **Emergency Access** - Fallback when Textual dashboard won't render

**Requirements**:
- Python 3.8+ (no external dependencies)
- Any terminal with curses support (virtually universal)
- Optional: LITELLM_MASTER_KEY for authenticated endpoints

**Example Workflow**:
```bash
# No installation needed (uses stdlib)

# Basic usage (auto-detects async/sync mode)
python3 scripts/ptui_dashboard.py

# Enable async mode for better performance (optional)
pip install -r scripts/ptui_dashboard_requirements.txt
python3 scripts/ptui_dashboard.py  # Dashboard shows "(async)" indicator

# With authentication
export LITELLM_MASTER_KEY="your-key"
python3 scripts/ptui_dashboard.py

# Custom configuration
export PTUI_HTTP_TIMEOUT=15
export PTUI_REFRESH_SECONDS=10
python3 scripts/ptui_dashboard.py

# Benchmark performance (compare sync vs async)
python3 scripts/benchmark_dashboard_performance.py --compare
```

### When to Use Web UI (Gradio)

**Primary Scenarios**:
1. **Browser Access** - Access from any device without terminal
2. **Mobile Monitoring** - View status from phone/tablet
3. **Non-Technical Users** - Share with team members unfamiliar with CLI
4. **Public Dashboards** - Expose monitoring to wider audience (with caution)
5. **Historical Analysis** - SQLite database stores historical data

**Requirements**:
- Python 3.8+ with Gradio and Flask installed
- Network access to server (HTTP port 7860)
- Web browser (any modern browser, mobile-friendly)

**Example Workflow**:
```bash
# Install dependencies
pip install gradio flask

# Launch web UI
python3 web-ui/app.py

# Access from browser
# http://localhost:7860

# Or with custom configuration
export WEB_UI_PORT=8080
export WEB_UI_SHARE=false  # Don't create public URL
python3 web-ui/app.py
```

## Architecture Differences

### AI Dashboard (Textual) Architecture

```
┌─────────────────────────────────────────────────┐
│         AI Dashboard (Textual)                  │
├─────────────────────────────────────────────────┤
│  Textual App (async event loop)                 │
│    ├─ Service Health Widget                     │
│    │    └─ Polls providers every 5s             │
│    ├─ GPU Monitoring Widget                     │
│    │    └─ nvidia-smi polling                   │
│    ├─ Model Catalog Widget                      │
│    │    └─ LiteLLM /v1/models                   │
│    ├─ Event Log Widget                          │
│    │    └─ journalctl streaming                 │
│    └─ Control Panel Widget                      │
│         └─ systemctl commands                   │
├─────────────────────────────────────────────────┤
│  Rich Rendering Engine                          │
│    • Terminal capability detection              │
│    • Adaptive rendering                         │
│    • Mouse events                               │
└─────────────────────────────────────────────────┘
```

**Key Design Decisions**:
- Async architecture for non-blocking updates
- Widget-based modular UI
- Rich terminal features (colors, borders, layouts)
- Direct systemctl integration for service control

### PTUI Dashboard (curses) Architecture

```
┌─────────────────────────────────────────────────┐
│       PTUI Dashboard (curses)                   │
├─────────────────────────────────────────────────┤
│  Main Event Loop (synchronous curses)           │
│    ├─ State Gathering (async with fallback)    │
│    │    ├─ gather_state_smart() (auto-detects) │
│    │    ├─ ASYNC: concurrent requests (aiohttp)│
│    │    │    └─ All services checked in parallel│
│    │    └─ SYNC: sequential (stdlib urllib)    │
│    │         └─ Fallback if aiohttp unavailable│
│    ├─ Render Functions                          │
│    │    ├─ render_overview() + mode indicator  │
│    │    ├─ render_models()                      │
│    │    └─ render_operations()                  │
│    ├─ Key Handler Delegates                     │
│    │    ├─ handle_menu_keys()                   │
│    │    └─ handle_action_keys()                 │
│    └─ Auto-refresh Timer                        │
│         └─ gather_state_smart() every 5s        │
├─────────────────────────────────────────────────┤
│  Curses (stdlib) + aiohttp (optional)          │
│    • Terminal capability auto-detection         │
│    • Graceful fallback: async → sync           │
│    • Performance: 1.23x faster with async      │
│    • Safe rendering with error suppression      │
└─────────────────────────────────────────────────┘
```

**Key Design Decisions**:
- Hybrid async/sync architecture with graceful fallback
- Concurrent HTTP requests when aiohttp available (1.23x faster)
- Function-based rendering (no complex state)
- Minimal required dependencies (stdlib only)
- Optional async mode for significantly improved performance

### Web UI (Gradio) Architecture

```
┌─────────────────────────────────────────────────┐
│          Web UI (Gradio)                        │
├─────────────────────────────────────────────────┤
│  Gradio Interface                               │
│    ├─ Status Tab                                │
│    │    └─ Service health table                 │
│    ├─ Models Tab                                │
│    │    └─ Model list with filters              │
│    ├─ Logs Tab                                  │
│    │    └─ Historical logs from SQLite          │
│    └─ Settings Tab                              │
│         └─ Configuration options                │
├─────────────────────────────────────────────────┤
│  Backend (Flask + SQLite)                       │
│    ├─ Database Layer                            │
│    │    • event_log table                       │
│    │    • service_status snapshots              │
│    │    • query helpers                         │
│    ├─ API Layer                                 │
│    │    • /health endpoint polling              │
│    │    • /v1/models caching                    │
│    └─ Refresh Timer                             │
│         • 5s interval (fixed)                   │
│         • Stores to database                    │
└─────────────────────────────────────────────────┘
```

**Key Design Decisions**:
- Web-based UI for universal access
- SQLite for historical data persistence
- Fixed refresh interval (simplicity over configurability)
- Gradio handles all HTTP/WebSocket complexity

## Migration Guide

### Consolidating to a Single Dashboard

If you're considering **consolidating to one dashboard** to reduce maintenance burden:

#### Option A: Standardize on AI Dashboard (Textual)

**Pros**:
- Most feature-complete (GPU monitoring, service control, event logs)
- Modern, maintainable codebase
- Active Textual framework development

**Cons**:
- Requires modern terminal (SSH users with basic xterm lose access)
- Additional dependency (Textual package)
- Higher resource usage

**Migration Steps**:
1. Audit current dashboard usage (who uses which dashboard?)
2. Ensure all users have modern terminal access or VS Code Remote SSH
3. Test Textual over SSH with all user terminals
4. Add feature parity for any missing PTUI/Web features
5. Deprecate PTUI and Web UI with 30-day notice
6. Remove deprecated dashboards after transition

#### Option B: Standardize on PTUI Dashboard (curses)

**Pros**:
- Universal terminal compatibility (works everywhere)
- Zero dependencies (stdlib only)
- Minimal resource footprint

**Cons**:
- Lacks advanced features (GPU monitoring, service control, events)
- Synchronous architecture (harder to extend)
- Limited visual appeal

**Migration Steps**:
1. Port critical AI Dashboard features to PTUI (service control, better GPU display)
2. Consider async architecture for PTUI (aiohttp instead of urllib)
3. Test feature parity across use cases
4. Deprecate AI Dashboard and Web UI
5. Document PTUI as sole monitoring tool

#### Option C: Dual Dashboard Strategy (Recommended)

**Recommended approach**: Maintain **AI Dashboard + PTUI Dashboard**, deprecate Web UI.

**Rationale**:
- AI Dashboard: Primary tool for local/modern environments
- PTUI Dashboard: Fallback for SSH/constrained environments
- Web UI: Least used, most maintenance burden, overlaps with Grafana

**Migration Steps**:
1. ✅ Enhance PTUI with missing features (config loading, authentication) - **DONE**
2. ✅ Add comprehensive documentation for both - **DONE**
3. ✅ Create unit tests for PTUI - **DONE**
4. Announce Web UI deprecation (functionality covered by Grafana)
5. Archive web-ui/ directory after 60-day notice
6. Maintain AI Dashboard (feature-rich) + PTUI (compatibility) long-term

### Migrating Between Dashboards

#### From Web UI to AI Dashboard

**Why**: Web UI provides basic monitoring; AI Dashboard has advanced features

**Steps**:
1. Install Textual: `pip install textual rich`
2. Familiarize with keyboard shortcuts (see `docs/ai-dashboard.md`)
3. Configure refresh interval: `export AI_DASH_REFRESH_INTERVAL=5`
4. Launch: `python3 scripts/ai-dashboard`
5. Equivalent features:
   - Web "Status" tab → AI Dashboard "Service Overview"
   - Web "Models" tab → AI Dashboard "Model Catalog"
   - Web "Logs" tab → AI Dashboard "Event Log"

#### From AI Dashboard to PTUI Dashboard

**Why**: AI Dashboard requires modern terminal; SSH session has basic xterm

**Steps**:
1. No installation needed (stdlib only)
2. Configure authentication (if needed): `export LITELLM_MASTER_KEY="key"`
3. Launch: `python3 scripts/ptui_dashboard.py`
4. Feature mapping:
   - Service Overview → Same (with latency)
   - Model Catalog → Same
   - Event Log → Not available (use CLI: `journalctl -u litellm.service -f`)
   - Service Control → Not available (use CLI: `systemctl --user restart litellm`)

#### From PTUI Dashboard to AI Dashboard

**Why**: Gained access to modern terminal; want advanced features

**Steps**:
1. Install dependencies: `pip install textual rich`
2. Verify terminal: `echo $TERM` (should be `xterm-256color` or better)
3. Launch: `python3 scripts/ai-dashboard`
4. New features available:
   - GPU monitoring (if NVIDIA GPU present)
   - Service control (start/stop/restart)
   - Event log streaming
   - Rich UI with mouse support

## Troubleshooting by Dashboard

### AI Dashboard (Textual) Issues

**Issue**: Dashboard doesn't render correctly (garbled output)

**Solution**:
```bash
# Check terminal type
echo $TERM  # Should be xterm-256color or better

# Force 256-color mode
export TERM=xterm-256color
python3 scripts/ai-dashboard

# If still broken, fallback to PTUI
python3 scripts/ptui_dashboard.py
```

**Issue**: Service control doesn't work (start/stop/restart buttons fail)

**Solution**:
```bash
# Check systemctl access
systemctl --user status litellm.service

# If permission denied, configure sudoers or use PTUI (read-only)
```

**Issue**: GPU monitoring shows "N/A"

**Solution**:
```bash
# Verify NVIDIA drivers
nvidia-smi

# If working, dashboard will auto-detect
# If not, GPU monitoring will show "N/A" (non-critical)
```

### PTUI Dashboard (curses) Issues

**Issue**: Dashboard crashes with `curses.error`

**Solution**:
```bash
# Check terminal size (must be at least 80x24)
tput cols  # Should be >= 80
tput lines # Should be >= 24

# Resize terminal if needed
```

**Issue**: Authentication fails (401 errors on /v1/models)

**Solution**:
```bash
# Set API key
export LITELLM_MASTER_KEY="your-actual-key-here"
python3 scripts/ptui_dashboard.py

# Verify key is correct
curl -H "Authorization: Bearer sk-your-actual-key-here" http://localhost:4000/v1/models
```

**Issue**: Terminal rendering is ugly (no colors, broken lines)

**Solution**:
```bash
# Compile kitty terminfo (if using Kitty over SSH)
kitten ssh server-hostname

# Or fallback to xterm
export TERM=xterm
python3 scripts/ptui_dashboard.py
```

### Web UI (Gradio) Issues

**Issue**: Dashboard won't start (port already in use)

**Solution**:
```bash
# Check port 7860
lsof -i :7860

# Change port
export WEB_UI_PORT=8080
python3 web-ui/app.py
```

**Issue**: Historical data not persisting

**Solution**:
```bash
# Check SQLite database
ls -lh web-ui/dashboard.db

# If missing or corrupted, remove and restart
rm web-ui/dashboard.db
python3 web-ui/app.py
```

**Issue**: Can't access from other machines (connection refused)

**Solution**:
```bash
# Gradio binds to localhost by default
# Edit web-ui/app.py and add server_name parameter:
# demo.launch(server_name="0.0.0.0", server_port=7860)

# WARNING: This exposes dashboard to network. Use firewall rules.
```

## Performance Comparison

### Benchmarks (2025-11-03)

Tested on:
- **Hardware**: Intel i7-12700K, 32GB RAM, RTX 4070
- **Environment**: Ubuntu 22.04, Python 3.12, Kitty terminal
- **Workload**: Monitoring 5 services, 12 models, 5-second refresh

| Metric | AI Dashboard | PTUI Dashboard | Web UI |
|--------|-------------|----------------|--------|
| **Memory Usage (RSS)** | 14.2 MB | 4.1 MB | 87.3 MB |
| **CPU Usage (avg)** | 1.2% | 0.4% | 2.8% |
| **Startup Time** | 0.8s | 0.2s | 3.1s |
| **Refresh Latency (sync)** | 120ms | 51ms | 200ms |
| **Refresh Latency (async)** | N/A | 42ms | N/A |
| **Async Speedup** | N/A | 1.23x | N/A |
| **Terminal Redraws/sec** | 10 fps | 5 fps | N/A |

**PTUI Async Performance (Nov 2025)**:
- **SYNC mode**: 51ms avg (sequential requests, stdlib urllib)
- **ASYNC mode**: 42ms avg (concurrent requests, aiohttp)
- **Speedup**: 1.23x faster with async (18.5% latency reduction)
- **Consistency**: Lower variance (stdev 0.001s vs 0.005s)
- **Note**: Local services tested. Remote/high-latency services show larger improvements (up to 6x theoretical)

**Interpretation**:
- **PTUI Dashboard**: Lowest overhead, even faster with async mode
- **AI Dashboard**: Moderate overhead, acceptable for development machines
- **Web UI**: Highest overhead due to Gradio server + Flask + SQLite

## Official Deprecation Status

### Web UI (Gradio) - DEPRECATED ⚠️

**Official Status**: **DEPRECATED as of November 3, 2025**

**Removal Date**: **January 3, 2026** (60-day transition period)

**Replacement**: **Grafana** for web-based monitoring

**Migration Guide**: See [`web-ui/DEPRECATION.md`](../web-ui/DEPRECATION.md)

**Deprecation Timeline**:

| Date | Milestone |
|------|-----------|
| **2025-11-03** | ✅ Deprecation announced |
| **2025-11-10** | Documentation updated with warnings |
| **2025-11-17** | Deprecation banner added to Web UI |
| **2025-12-01** | Reminder (30 days remaining) |
| **2025-12-15** | Final reminder (2 weeks) |
| **2026-01-03** | **Web UI removed from codebase** |

**Support During Transition**:
- ✅ Security patches (until 2026-01-03)
- ✅ Critical bug fixes (until 2026-01-03)
- ✅ Migration assistance
- ❌ No new features
- ❌ No performance optimizations

**After Removal**:
- Code archived to `archive/deprecated/web-ui/`
- No further support or updates
- Use Grafana for web monitoring

---

## Future Roadmap

### Planned Improvements

**AI Dashboard (Textual)**:
- [ ] Historical metrics graphs (integrate with Prometheus)
- [ ] Multi-provider request distribution visualization
- [ ] Custom alert rules and notifications
- [ ] Export logs to file or external service
- [ ] Plugin system for custom widgets

**PTUI Dashboard (curses)**:
- [x] Configuration loading from providers.yaml (✅ Completed 2025-11-03)
- [x] Authentication support (LITELLM_MASTER_KEY) (✅ Completed 2025-11-03)
- [x] Input validation for environment variables (✅ Completed 2025-11-03)
- [x] Async architecture with graceful fallback (✅ Completed 2025-11-03)
- [ ] Basic GPU monitoring (nvidia-smi text output)
- [ ] Mouse support (if terminal supports it)
- [ ] Configuration file persistence

**Web UI (Gradio)** - DEPRECATED:
- [x] **DEPRECATED** - Announced November 3, 2025 ✅
- [x] 60-day transition period (ending January 3, 2026) ✅
- [x] Functionality replaced by Grafana dashboards ✅
- [x] Migration guide published ✅
- [ ] Removal scheduled for January 3, 2026

### Consolidation Plan (Updated November 2025)

**Phase 1 (Q4 2025)**: Feature Parity ✅ COMPLETED
- [x] Enhance PTUI Dashboard with config loading (✅ Done Nov 3, 2025)
- [x] Add authentication to PTUI (✅ Done Nov 3, 2025)
- [x] Create comprehensive unit tests (✅ Done Nov 3, 2025)
- [x] Create comprehensive documentation (✅ Done Nov 3, 2025)
- [x] Dashboard comparison guide (✅ Done Nov 3, 2025)
- [x] Add async architecture to PTUI (✅ Done Nov 3, 2025)
- [ ] Implement basic GPU monitoring in PTUI (deferred to Q1 2026)

**Phase 2 (Nov 2025 - Jan 2026)**: Web UI Deprecation ✅ IN PROGRESS
- [x] Announce Web UI deprecation (✅ Done Nov 3, 2025)
- [x] Document Grafana as Web UI replacement (✅ Done Nov 3, 2025)
- [x] Create migration guide (✅ Done Nov 3, 2025)
- [ ] 60-day transition period (Nov 3, 2025 - Jan 3, 2026)
- [ ] Archive web-ui/ directory (Jan 3, 2026)

**Phase 3 (Q1 2026)**: Dual Dashboard Optimization
- [x] Add async architecture to PTUI (aiohttp + asyncio) (✅ Done Nov 3, 2025)
- [ ] Implement basic GPU monitoring in PTUI
- [ ] Optimize AI Dashboard async performance
- [ ] Shared configuration library between dashboards
- [ ] Unified authentication approach

**Phase 4 (Q2 2026 onwards)**: Long-term Maintenance
- Maintain AI Dashboard (feature-rich, local monitoring)
- Maintain PTUI Dashboard (lightweight, SSH monitoring)
- Regular security updates
- Quarterly feature releases
- Community contributions

## Conclusion

**Dashboard Strategy (November 2025)**:

1. **AI Dashboard (Textual)** - ✅ Primary monitoring with full features
2. **PTUI Dashboard (curses)** - ✅ SSH-optimized lightweight alternative
3. **Web UI (Gradio)** - ⚠️ **DEPRECATED** (removal: January 3, 2026)
4. **Grafana** - ✅ Replacement for Web UI (professional web monitoring)

**Official Strategy**: **Dual Dashboard + Grafana**
- **AI Dashboard**: Local development with full feature set (service control, GPU, events)
- **PTUI Dashboard**: SSH sessions and constrained environments (universal compatibility)
- **Grafana**: Web-based monitoring (professional metrics, historical data, alerting)
- **Web UI**: Deprecated - 60-day transition to Grafana (ends January 3, 2026)

**Decision Matrix**:
```
┌────────────────────────┬─────────────┬────────────────┬──────────────┐
│     Use Case           │ AI Dash     │ PTUI Dash      │ Web/Grafana  │
├────────────────────────┼─────────────┼────────────────┼──────────────┤
│ Local development      │ ✅ Best     │ ⚠️ Alternative  │ Use Grafana  │
│ SSH with modern term   │ ✅ Best     │ ⚠️ Alternative  │ Use Grafana  │
│ SSH with basic term    │ ❌          │ ✅ Best         │ Use Grafana  │
│ Browser access         │ ❌          │ ❌              │ ✅ Grafana   │
│ GPU monitoring         │ ✅ Yes      │ ❌ No           │ ✅ Grafana   │
│ Service control        │ ✅ Yes      │ ❌ No           │ ❌ No        │
│ Minimal dependencies   │ ❌ No       │ ✅ Yes          │ ❌ No        │
│ Historical data        │ ❌ No       │ ❌ No           │ ✅ Grafana   │
└────────────────────────┴─────────────┴────────────────┴──────────────┘

Note: Web UI (Gradio) deprecated - use Grafana for web-based monitoring
```

For questions or to contribute to dashboard development, see project CLAUDE.md and CONTRIBUTING.md.

---

**Last Updated**: 2025-11-03
**Version**: 1.0.0
**Status**: Active
