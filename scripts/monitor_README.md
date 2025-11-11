# Monitor Scripts - Archived

**Status**: ⚠️ Archived
**Date**: 2025-11-09

## Notice

The experimental monitor scripts (`monitor`, `monitor-enhanced`, `monitor-lite`, `monitor-unified`) have been **archived** to `scripts/archive/experimental-dashboards/`.

## Current Production Dashboards

Use these production-ready dashboards instead:

### 1. Textual Dashboard (Local Use)
```bash
./scripts/ai-dashboard
# Or using alias:
./scripts/cui
```

**Features**: Full service control, GPU monitoring, real-time events
**Use when**: Local workstation, modern terminal

### 2. PTUI Dashboard (SSH/Remote)
```bash
python3 scripts/ptui_dashboard.py
# Or using alias:
./scripts/pui
```

**Features**: Universal compatibility, lightweight, works everywhere
**Use when**: SSH sessions, remote monitoring

### 3. Grafana (Web Monitoring)
```bash
cd monitoring && docker compose up -d
# Access: http://localhost:3000
```

**Features**: Historical metrics, alerting, professional dashboards
**Use when**: Production monitoring, team collaboration

## Complete Guide

For a comprehensive guide on choosing the right dashboard, see:
**`docs/DASHBOARD-GUIDE.md`**

## Archive Location

Archived scripts can be found in:
**`scripts/archive/experimental-dashboards/`**

See `scripts/archive/experimental-dashboards/README.md` for details.

## Migration

| Old Script | Current Replacement |
|-----------|---------------------|
| `./scripts/monitor` | `./scripts/cui` |
| `./scripts/monitor-enhanced` | `./scripts/ai-dashboard` |
| `./scripts/monitor-lite` | `./scripts/pui` |
| `./scripts/monitor-unified` | `./scripts/cui` |

---

**For questions**, see:
- `docs/DASHBOARD-GUIDE.md` - Dashboard selection guide
- `docs/DASHBOARD-CONSOLIDATION.md` - Consolidation details
- `docs/troubleshooting.md` - Troubleshooting guide
