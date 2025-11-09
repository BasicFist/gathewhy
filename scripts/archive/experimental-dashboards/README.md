# Experimental Dashboard Archive

This directory contains experimental and legacy dashboard implementations that have been superseded by the production-ready dashboards.

## Archived Scripts

### Monitor Scripts (Legacy)

- **monitor** - Basic dashboard implementation (first iteration)
- **monitor-enhanced** - Enhanced version with VRAM monitoring
- **monitor-lite** - Lightweight information-dense TUI
- **monitor-unified** - Comprehensive dashboard with service control
- **benchmark_dashboard_performance.py** - Performance benchmarking tool

### Status

These scripts are **archived** and no longer actively maintained. They were experimental iterations during dashboard development.

## Current Production Dashboards

Use these instead:

### 1. Textual Dashboard (Recommended for Local Use)
```bash
# Modern, feature-rich dashboard
./scripts/ai-dashboard

# Or using the alias
./scripts/cui
```

**Location**: `scripts/dashboard/` (package) + `scripts/ai-dashboard` (entry point)

**Features**:
- Modern Textual framework
- Real-time provider monitoring
- GPU utilization tracking
- Service control (start/stop/restart)
- Event logging
- Keyboard shortcuts

**Use when**: Running on local machine with modern terminal

### 2. PTUI Dashboard (Recommended for SSH/Remote)
```bash
# Curses-based dashboard for universal compatibility
python3 scripts/ptui_dashboard.py

# Or using the alias
./scripts/pui
```

**Location**: `scripts/ptui_dashboard.py`

**Features**:
- Universal terminal compatibility
- Minimal dependencies (curses)
- Provider health monitoring
- Model discovery
- Lightweight resource usage

**Use when**: SSH sessions, limited terminal capabilities, or resource-constrained environments

## Migration Guide

If you were using any archived scripts:

| Old Script | New Replacement |
|-----------|----------------|
| `./scripts/monitor` | `./scripts/ai-dashboard` or `./scripts/cui` |
| `./scripts/monitor-enhanced` | `./scripts/ai-dashboard` (includes VRAM) |
| `./scripts/monitor-lite` | `./scripts/ptui_dashboard.py` or `./scripts/pui` |
| `./scripts/monitor-unified` | `./scripts/ai-dashboard` (unified features) |

## Why Consolidated?

The experimental scripts were:
1. **Redundant**: Multiple implementations with overlapping features
2. **Unmaintained**: Not kept up-to-date with provider changes
3. **Inconsistent**: Different UIs and behaviors
4. **Confusing**: Users didn't know which to use

The production dashboards provide:
- **Clear purpose**: Textual for local, PTUI for remote
- **Active maintenance**: Updated with new providers and features
- **Better UX**: Consistent, polished interfaces
- **Documentation**: Comprehensive guides in `docs/`

## Restoration

If you need to restore any archived script:

```bash
# Copy back to scripts directory
cp scripts/archive/experimental-dashboards/monitor scripts/

# Make executable
chmod +x scripts/monitor
```

## History

- **2025-11-09**: Archived experimental dashboards during v2.0 consolidation
- **2025-10-25**: Created monitor-unified with comprehensive features
- **2025-10-20**: Added monitor-lite for lightweight use
- **2025-10-15**: Enhanced monitor with VRAM tracking
- **2025-10-10**: Initial monitor script created

## Related Documentation

- `docs/ai-dashboard.md` - Textual dashboard guide
- `docs/ptui-dashboard.md` - PTUI dashboard guide
- `docs/observability.md` - Monitoring and debugging guide
