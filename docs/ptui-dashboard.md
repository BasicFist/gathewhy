# PTUI Dashboard - Lightweight Curses Monitoring Interface

## Overview

The **PTUI Dashboard** (`scripts/ptui_dashboard.py`) is a lightweight, terminal-based monitoring interface for AI backend services. Built with Python's standard `curses` library, it provides real-time service health monitoring without requiring external dependencies.

**Key Characteristics:**
- **Zero dependencies** - Uses only Python standard library
- **Fast startup** - Launches in <100ms (vs ~2s for Textual dashboard)
- **Portable** - Runs anywhere Python 3.9+ is installed
- **Excellent terminal support** - Auto-detects and fixes terminfo issues

## When to Use

**Choose PTUI Dashboard when:**
- Installing pip packages is restricted/not allowed
- You need minimal resource overhead
- Working in SSH sessions with limited terminal emulators
- You prefer classic curses aesthetics
- Fast startup time is critical

**Choose Textual Dashboard (`ai-dashboard`) when:**
- You want full feature set (GPU monitoring, resource metrics, service controls)
- You can install dependencies
- You need state persistence between sessions
- You want comprehensive testing and documentation

## Quick Start

### Installation

No installation needed! Uses Python standard library only.

Optional: Install PyYAML for dynamic config loading (graceful fallback if missing):
```bash
pip install pyyaml
```

### Launch

```bash
cd /home/miko/LAB/ai/backend/ai-backend-unified
python3 scripts/ptui_dashboard.py
```

Or make executable:
```bash
chmod +x scripts/ptui_dashboard.py
./scripts/ptui_dashboard.py
```

### Configuration

Configure via environment variables:

```bash
# HTTP request timeout (default: 10s, range: 0.5-120s)
export PTUI_HTTP_TIMEOUT=15

# Auto-refresh interval (default: 5s, range: 1-60s)
export PTUI_REFRESH_SECONDS=10

# LiteLLM API key (if authentication enabled)
export LITELLM_MASTER_KEY=your-api-key-here

# Launch with custom config
PTUI_REFRESH_SECONDS=3 python3 scripts/ptui_dashboard.py
```

## UI Layout

```
┌────────────────────────────────────────────────────────────┐
│ AI Backend Unified - PTUI Command Center                   │
│ ai-dashboard                                               │
├────────────────────────────────────────────────────────────┤
│ Sections          │ Service Overview                       │
│ ➤ Service Overview│ Required services: 2/2 healthy         │
│   Model Catalog   │ Optional services: 1/3 online          │
│   Operations      │                                        │
│                   │ ONLINE LiteLLM Gateway                 │
│                   │   Latency: 12ms   URL: http://...      │
│                   │                                        │
│                   │ ONLINE Ollama                          │
│                   │   Latency: 45ms   URL: http://...      │
│                   │                                        │
│                   │ MISSING llama.cpp (Python)             │
│                   │   ⚠ Connection refused                 │
├────────────────────────────────────────────────────────────┤
│ Arrows navigate • Tab switch panel • Enter run • r refresh │
│ Focus: Menu    Last refresh: 14:11:05                      │
│ Service state refreshed.                                   │
└────────────────────────────────────────────────────────────┘
```

### Panels

**1. Service Overview** (default view)
- Real-time service health status
- Response latency for each service
- Color-coded status (Green=online, Red=offline, Yellow=optional missing)
- Error messages for failed services

**2. Model Catalog**
- Lists all models available through LiteLLM gateway
- Model count
- Fetch latency

**3. Operations**
- Quick actions menu
- Refresh state
- Health probe (checks required services)
- Run validation script

## Key Bindings

### Global Keys
| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit dashboard |
| `r` / `R` | Refresh | Manually refresh all data |
| `g` / `G` | Gather | Force state collection |

### Navigation
| Key | Action | Description |
|-----|--------|-------------|
| `↑` / `↓` | Navigate | Move selection up/down |
| `Tab` | Switch focus | Move between menu and actions |
| `Shift-Tab` | Return | Return to menu from actions |
| `Enter` | Activate | Enter panel or execute action |
| `←` | Back | Return to menu from actions |
| `→` | Forward | Enter actions panel |

### Auto-Refresh

Dashboard automatically refreshes every 5 seconds (configurable). Watch the "Last refresh" timestamp in the footer.

## Features

### Dynamic Config Loading

Automatically loads services from `config/providers.yaml`:

```yaml
providers:
  ollama:
    status: active
    base_url: http://127.0.0.1:11434
    # ... ptui_dashboard detects and monitors

  llama_cpp_native:
    status: disabled
    # ... ptui_dashboard skips (not monitored)
```

**Fallback**: If YAML loading fails or file not found, uses hardcoded defaults.

### Authentication Support

Supports LiteLLM authentication via `LITELLM_MASTER_KEY`:

```bash
# Read from environment
export LITELLM_MASTER_KEY=r2nnYAVIsE5DXPMmYLzKpRnu_OsS-zwu0cl8QTx8E8g

# Or from direnv
# (automatically loaded in LAB environment)
```

Dashboard passes `Authorization: Bearer sk-{key}` header to authenticated endpoints.

**Note**: Uses `/health/liveliness` endpoint for LiteLLM which doesn't require auth.

### Terminal Compatibility

Sophisticated terminal handling with automatic fallbacks:

```python
# Auto-detection sequence
1. Try current TERM (e.g., xterm-kitty)
2. Fallback to xterm-256color
3. Fallback to xterm
4. Clear error message if all fail
```

**Special handling for Kitty**:
- Auto-compiles missing `kitty.terminfo` if detected
- Searches common install locations
- Compiles to `~/.terminfo`

Works on:
- ✅ xterm, xterm-256color
- ✅ Kitty (auto-fixes terminfo)
- ✅ Alacritty
- ✅ tmux, screen
- ✅ gnome-terminal, konsole
- ✅ iTerm2 (macOS)

### Health Check Logic

**Service Status Determination:**

| Status | Condition | Color | Description |
|--------|-----------|-------|-------------|
| `ONLINE` | HTTP 200 + valid JSON | Green | Service healthy |
| `OFFLINE` | Connection failed + required | Red | Critical failure |
| `MISSING` | Connection failed + optional | Yellow | Optional service unavailable |

**Required vs Optional Services:**
- **Required**: LiteLLM Gateway, Ollama (system breaks if down)
- **Optional**: llama.cpp, vLLM (nice-to-have, graceful degradation)

### Latency Measurement

Response times measured with `time.perf_counter()`:

- **<1s**: Displayed in milliseconds (e.g., "45ms")
- **≥1s**: Displayed in seconds (e.g., "2.34s")
- **Failed**: Displayed as "--"

Latency includes:
- DNS resolution
- TCP connection
- HTTP request/response
- JSON parsing

## Operations (Quick Actions)

### 1. Refresh State
- **Shortcut**: `r` (global)
- **Action**: Re-polls all service endpoints
- **Use**: Manual refresh when suspicious of stale data

### 2. Health Probe
- **Action**: Checks required services and reports failures
- **Output**: "all required services online" or lists failing services
- **Use**: Quick health check before deployments

### 3. Run Validation
- **Action**: Executes `scripts/validate-unified-backend.sh`
- **Output**: "Validation succeeded" or failure message
- **Use**: Comprehensive system validation (11 checks)

## Troubleshooting

### Dashboard Won't Start

**Error: "Interactive dashboard requires a TTY"**

**Solution**: Run in interactive terminal, not piped/scripted.

```bash
# Won't work
python3 scripts/ptui_dashboard.py < input.txt

# Will work
python3 scripts/ptui_dashboard.py
```

---

**Error: "curses initialization failed"**

**Cause**: Missing terminfo entry

**Solution 1** - Install terminfo:
```bash
# Debian/Ubuntu
sudo apt install ncurses-term

# Arch
sudo pacman -S ncurses

# macOS
brew install ncurses
```

**Solution 2** - Use compatible TERM:
```bash
TERM=xterm-256color python3 scripts/ptui_dashboard.py
```

---

**Error: Color rendering issues**

**Cause**: Terminal doesn't support colors

**Solution**: Use 256-color capable terminal:
```bash
echo $TERM  # Check current
export TERM=xterm-256color  # Set to 256-color
```

### Services Show as Offline

**Check 1**: Verify service is actually running
```bash
curl http://localhost:11434/api/tags      # Ollama
curl http://localhost:4000/health/liveliness  # LiteLLM
curl http://localhost:8001/v1/models      # vLLM
```

**Check 2**: Check systemd status
```bash
systemctl --user status ollama.service
systemctl --user status litellm.service
systemctl --user status vllm.service
```

**Check 3**: Network connectivity
```bash
nc -zv 127.0.0.1 11434  # Test Ollama port
nc -zv 127.0.0.1 4000   # Test LiteLLM port
```

**Check 4**: Authentication issues
```bash
# If LiteLLM shows errors, check API key
echo $LITELLM_MASTER_KEY

# Test with key
curl -H "Authorization: Bearer sk-$LITELLM_MASTER_KEY" \
  http://localhost:4000/v1/models
```

### Auto-Refresh Not Working

**Symptom**: Dashboard doesn't update automatically

**Solution 1**: Check refresh interval
```bash
# Default is 5s, try increasing
PTUI_REFRESH_SECONDS=10 python3 scripts/ptui_dashboard.py
```

**Solution 2**: Manual refresh
```bash
# Press 'r' key to force refresh
```

### Keyboard Not Responding

**Cause**: Terminal not in raw mode or focus issues

**Solution**: Restart dashboard
```bash
# Exit with Ctrl-C if 'q' doesn't work
# Then restart
python3 scripts/ptui_dashboard.py
```

### Models Not Appearing

**Symptom**: Model Catalog shows "No models available"

**Cause 1**: LiteLLM not running
```bash
systemctl --user status litellm.service
```

**Cause 2**: No models configured
```bash
curl http://localhost:4000/v1/models | jq '.data[] | .id'
```

**Cause 3**: Authentication required but key missing
```bash
export LITELLM_MASTER_KEY=your-key-here
python3 scripts/ptui_dashboard.py
```

## Architecture

### Code Structure

```
ptui_dashboard.py (720 lines)
├── Configuration (39 lines)
│   ├── validate_env_float()       # Input validation
│   ├── DEFAULT_HTTP_TIMEOUT
│   ├── AUTO_REFRESH_SECONDS
│   └── LITELLM_API_KEY
│
├── Data Models (3 dataclasses)
│   ├── Service                    # Service definition
│   ├── ActionItem                 # Quick action
│   └── MenuItem                   # Menu panel
│
├── Config Loading (67 lines)
│   └── load_services_from_config() # YAML → Service list
│
├── Utilities (5 functions)
│   ├── safe_addstr()              # Safe terminal write
│   ├── fetch_json()               # HTTP with auth
│   ├── check_service()            # Health check
│   ├── get_models()               # Fetch model list
│   └── format_latency()           # Format timing
│
├── Data Collection (2 functions)
│   ├── gather_state()             # Collect all metrics
│   └── run_validation()           # Run validation script
│
├── Actions (3 functions)
│   ├── action_refresh_state()     # Manual refresh
│   ├── action_health_probe()      # Health check
│   └── action_run_validation()    # Validation
│
├── Rendering (5 functions)
│   ├── init_colors()              # Color pairs
│   ├── render_overview()          # Services panel
│   ├── render_models()            # Models panel
│   ├── render_operations()        # Actions panel
│   └── draw_footer()              # Footer
│
├── Event Handling (2 functions)
│   ├── handle_menu_keys()         # Menu navigation
│   └── handle_action_keys()       # Action navigation
│
├── Terminal Setup (4 functions)
│   ├── _ensure_valid_terminfo()   # Fix TERMINFO
│   ├── _has_terminfo()            # Check terminfo
│   ├── _compile_kitty_terminfo()  # Compile kitty
│   └── _ensure_term_capabilities() # Ensure terminal works
│
└── Main (3 functions)
    ├── interactive_dashboard()    # Main loop (140 lines)
    ├── _launch_dashboard()        # Wrapper
    └── main()                     # Entry point
```

### Data Flow

```
┌─────────────────────┐
│  main()             │
│  - Check TTY        │
│  - Try TERM values  │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ interactive_dashboard()
│ - Init curses       │
│ - Load config       │
│ - Main event loop   │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ gather_state()      │
│ - Poll endpoints    │
│ - Measure latency   │
│ - Collect errors    │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ Render UI           │
│ - Draw panels       │
│ - Update colors     │
│ - Show footer       │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ Handle Input        │
│ - Menu keys         │
│ - Action keys       │
│ - Global keys       │
└─────────────────────┘
```

### Performance

| Operation | Time | Notes |
|-----------|------|-------|
| **Startup** | <100ms | No pip dependencies |
| **Refresh cycle** | 200-500ms | Depends on service count |
| **Health check (per service)** | 10-100ms | Network latency |
| **UI render** | <10ms | Curses is fast |
| **Memory usage** | ~30MB | Minimal footprint |

## Comparison with Textual Dashboard

| Feature | PTUI (curses) | Textual (`ai-dashboard`) | Winner |
|---------|---------------|--------------------------|--------|
| **Dependencies** | stdlib only | textual, psutil, pynvml, requests | PTUI |
| **Startup time** | <100ms | ~2s | PTUI |
| **Size** | 720 LOC | 1,185 LOC | PTUI |
| **Service monitoring** | ✅ Yes | ✅ Yes | Tie |
| **GPU/VRAM monitoring** | ❌ No | ✅ Yes | Textual |
| **CPU/Memory metrics** | ❌ No | ✅ Yes | Textual |
| **Service controls** | ❌ No | ✅ start/stop/restart | Textual |
| **State persistence** | ❌ No | ✅ Yes | Textual |
| **Config loading** | ✅ Yes | ✅ Yes | Tie |
| **Authentication** | ✅ Yes | ❌ No (same bug, now fixed) | PTUI |
| **Documentation** | ✅ This doc | ✅ 450 lines | Tie |
| **Tests** | ⚠️ Minimal | ✅ 25 tests (100%) | Textual |
| **Terminal support** | ✅ Excellent | ✅ Excellent | Tie |
| **Portability** | ✅ Runs anywhere | ⚠️ Needs deps | PTUI |

**Bottom Line:**
- **PTUI**: Lightweight, portable, fast startup, basic monitoring
- **Textual**: Full-featured, rich UI, comprehensive metrics, service controls

## Development

### Running Tests

```bash
# Run PTUI tests (subset of full test suite)
pytest tests/unit/test_ptui_dashboard.py -v

# Or all tests
pytest -v
```

### Adding a New Service

Edit `config/providers.yaml`:
```yaml
providers:
  my_new_service:
    type: openai  # or ollama, vllm, etc.
    base_url: http://localhost:8888
    status: active
    health_endpoint: /v1/models
```

Restart dashboard - it auto-loads the new service!

### Adding a New Action

Edit `scripts/ptui_dashboard.py`:

```python
def action_my_new_action(state: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    """My new action implementation."""
    # Do something
    updated_state = gather_state(DEFAULT_HTTP_TIMEOUT)
    return "Action completed!", updated_state

# Add to ACTION_ITEMS list
ACTION_ITEMS.append(
    ActionItem("My Action", "Description of my action", action_my_new_action)
)
```

### Customizing UI

Colors defined in `init_colors()`:
```python
curses.init_pair(1, curses.COLOR_GREEN, -1)    # Success
curses.init_pair(2, curses.COLOR_RED, -1)      # Error
curses.init_pair(3, curses.COLOR_YELLOW, -1)   # Warning
curses.init_pair(4, curses.COLOR_CYAN, -1)     # Accent
curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # Instructions
```

## Security Considerations

### Localhost Only

All services hardcoded/loaded from config point to localhost:
- ✅ No SSRF risk
- ✅ No remote connections
- ✅ Localhost traffic only

### Authentication

Supports Bearer token authentication:
- ✅ Reads `LITELLM_MASTER_KEY` from environment
- ✅ Passes in `Authorization` header
- ✅ Uses auth-free endpoints where available (`/health/liveliness`)

### Input Validation

Environment variables validated:
- ✅ `PTUI_HTTP_TIMEOUT`: 0.5-120s range enforced
- ✅ `PTUI_REFRESH_SECONDS`: 1-60s range enforced
- ✅ Graceful fallback to defaults on invalid input

### No Shell Injection

Subprocess calls use list form (not string):
```python
subprocess.run([script_path], ...)  # Safe
```

## Known Limitations

1. **No resource metrics** (CPU/Memory/VRAM) - Use Textual dashboard for these
2. **No service controls** - Can't start/stop/restart services
3. **No state persistence** - Loses state on exit
4. **Read-only** - Can only monitor, not manage
5. **Single file** - All code in one 720-line file (harder to test)
6. **Basic UI** - No progress bars, no graphs

## Future Enhancements

- [ ] Add basic CPU/Memory metrics (optional psutil)
- [ ] Add service control actions (start/stop/restart)
- [ ] Save state to `~/.cache/ptui-dashboard/state.json`
- [ ] Add configuration file (`~/.ptui-dashboard.yaml`)
- [ ] Add color themes (dark, light, high-contrast)
- [ ] Add export metrics to JSON
- [ ] Add historical latency tracking

## Related Documentation

- [Main README](../README.md)
- [Textual Dashboard](ai-dashboard.md)
- [Dashboard Comparison](dashboards-comparison.md)
- [Architecture](architecture.md)
- [Troubleshooting](troubleshooting.md)

## License

Part of the LAB AI Backend Unified infrastructure project.
