# PTUI - Provider TUI User Guide

**Version**: 2.0.0
**Command**: `ptui`, `pui`, or `providers`

## Overview

PTUI (Provider TUI) is a comprehensive command center for managing the AI Backend Unified infrastructure. It provides both an **interactive menu-driven interface** and **command-line tools** for monitoring and controlling all AI services.

## Quick Start

```bash
# Interactive mode (full TUI)
ptui        # or: pui

# Command-line mode (quick checks)
ptui status        # Show service status
ptui models        # List all models
ptui health        # Run health check
ptui vllm status   # Check vLLM status
ptui help          # Show help
```

## Installation (Optional)

You can run PTUI directly from the repository (`./scripts/ptui`). For convenience, either add the `scripts/` directory to your `PATH`, or create symlinks so `ptui`, `pui`, and `providers` are available globally.

### Option A: Add to PATH (recommended for dev)

```bash
# From the repo root
echo "export PATH=\"$PATH:$(pwd)/scripts\"" >> ~/.bashrc   # or ~/.zshrc
source ~/.bashrc  # reload shell config

# Verify
ptui help
providers help
```

### Option B: Create symlinks (system-wide)

```bash
sudo ln -sf "$(pwd)/scripts/ptui" /usr/local/bin/ptui
sudo ln -sf "$(pwd)/scripts/pui" /usr/local/bin/pui
sudo ln -sf "$(pwd)/scripts/providers" /usr/local/bin/providers

# Verify
ptui help
providers help
```

Set timeouts via environment variables (optional):

```bash
export PTUI_HTTP_TIMEOUT=3        # seconds (default 5)
export PTUI_REFRESH_SECONDS=5     # dashboard auto-refresh interval
```

## Features

### 🖥️  Service Monitoring
- Real-time status of all 5 services (LiteLLM, vLLM, Ollama, llama.cpp Python/Native)
- Health check with automatic endpoint testing
- GPU utilization monitoring
- Port usage tracking

### 🤖 Model Management
- List all available models across providers
- vLLM model switching (Qwen Coder ↔ Dolphin)
- Model information and statistics
- Provider-specific model details

### ⚙️  Configuration Management
- View LiteLLM unified config
- Browse model mappings
- Check provider registry
- Inspect vLLM model information

### 📊 Logging & Diagnostics
- View service logs (LiteLLM, vLLM, system)
- Real-time log tailing
- Error tracking and debugging
- System diagnostics

### 🚀 Quick Actions
- Restart services
- Run validation scripts
- Check GPU status
- Kill stuck processes
- Test endpoints

---

## Interactive Mode

Launch the full TUI with:

```bash
ptui
```

### Dashboard Layout

The curses dashboard now provides a two-pane command center with arrow-key navigation:

```
Sections                        Service Overview
➤ Service Overview              Service Health
  Model Catalog                 Required services: 2/2 healthy
  Operations                    Optional services: 3/3 online
                                ONLINE  LiteLLM Gateway
                                Latency: 87ms   URL: http://localhost:4000
                                ...
```

### Navigation Keys

- **↑ / ↓** – Move through the left-hand section list or quick actions.
- **→ / Tab** – Focus the actions list when "Operations" is selected.
- **← / Shift+Tab** – Return focus to the section list.
- **Enter** – Run the highlighted action (when the actions pane has focus).
- **r** – Manually refresh service and model data.
- **q** – Exit the dashboard (legacy menu appears only if curses cannot initialize).

### Sections

#### Service Overview
- Live health for required and optional services.
- Per-service latency and endpoint status.
- Inline error details when a service is offline or degraded.
- Auto-refresh every 5 seconds (configurable via `PTUI_REFRESH_SECONDS`).

#### Model Catalog
- Lists every LiteLLM model currently routable.
- Displays the time to fetch the model list.
- Indicates if the gateway is unreachable or the listing fails.

#### Operations
- Focus with **Tab** to highlight the actions list, then **Enter** to invoke:
  - **Refresh State** – Pulls fresh health/model data (same as pressing `r`).
  - **Health Probe** – Rechecks required services and reports failures.
  - **Run Validation** – Executes `scripts/validate-unified-backend.sh` and reports success/fail.
- The footer displays progress messages while actions run and reports results once complete.

> Tip: Advanced utilities (provider management, log viewers, endpoint tests, etc.) remain accessible through the command-line mode (`ptui status`, `ptui test`, `ptui vllm …`) or the legacy Bash menu that appears automatically if the curses dashboard cannot start.

---

## Command-Line Mode

For scripting and quick checks:

### Status Command

```bash
ptui status
```

Shows:
- Service health indicators (✅/❌)
- Running/stopped status
- Service URLs
- vLLM current model
- Quick stats

**Example Output**:
```
✅ LiteLLM Gateway (http://localhost:4000)
✅ Ollama (http://localhost:11434)
❌ llama.cpp (Python) (http://localhost:8000)
✅ vLLM (http://localhost:8001)
  └─ Model: Qwen/Qwen2.5-Coder-7B-Instruct-AWQ

🖥️  Services Running: 3/5
🤖 Models Available: 4
```

### Models Command

```bash
ptui models
```

Lists all available models with details:
```
LiteLLM Models:
  • llama3.1:latest
  • qwen2.5-coder:7b
  • qwen-coder-vllm
  • dolphin-uncensored-vllm

Ollama Models:
  • llama3.1:latest (4GB)
  • qwen2.5-coder:7b (4GB)

vLLM Current Model:
  • Qwen/Qwen2.5-Coder-7B-Instruct-AWQ
```

### Health Command

```bash
ptui health
```

Performs comprehensive health check:
```
Testing Endpoints:

[✓] LiteLLM health endpoint
[✓] LiteLLM completion test
[✓] Ollama API
[✓] vLLM API

💚 System Status: HEALTHY
```

### vLLM Commands

```bash
# Check vLLM status
ptui vllm status

# Switch to Qwen Coder
ptui vllm qwen

# Switch to Dolphin
ptui vllm dolphin

# Stop vLLM
ptui vllm stop
```

Delegates to `vllm-model-switch.sh` for full functionality.

### Test Command

```bash
ptui test
```

Opens interactive endpoint testing menu.

---

## Usage Examples

### Daily Workflow

```bash
# Morning: Check all services
ptui status

# Start work: Ensure everything is healthy
ptui health

# Need Dolphin model: Switch vLLM
ptui vllm dolphin

# End of day: Check what's running
ptui models
```

### Troubleshooting

```bash
# Service not responding
ptui status                    # Identify which service
ptui health                    # Run diagnostics

# vLLM issues
ptui vllm status              # Check vLLM
ptui                          # Interactive mode → view logs

# Port conflict
ptui                          # Interactive → Quick Actions → Check port usage
```

### Scripting

```bash
#!/bin/bash
# Auto-restart if unhealthy

if ! ptui health | grep -q "HEALTHY"; then
    echo "System unhealthy, restarting services..."
    systemctl --user restart litellm.service
    ptui vllm restart
    sleep 10
    ptui health
fi
```

### Monitoring

```bash
# Watch service status (every 5 seconds)
watch -n 5 "ptui status"

# Log health checks
while true; do
    echo "$(date): $(ptui health | grep 'System Status')" >> ~/health.log
    sleep 300  # Every 5 minutes
done
```

---

## Color-Coded Interface

PTUI uses colors for quick visual feedback:

- 🟢 **Green**: Service running / Test passed / Success
- 🔴 **Red**: Service stopped / Test failed / Error
- 🟡 **Yellow**: Warning / Optional service
- 🔵 **Blue**: Informational message
- **Gray**: Supplementary information
- **Bold White**: Important text / Headers

Icons:
- ✅ Running
- ❌ Stopped
- ⚠️  Warning
- ℹ️  Information
- 🚀 Action
- ⚙️  Configuration
- 📊 Statistics
- 🖥️  Server
- 🤖 Model
- 💚 Health

---

## Keyboard Shortcuts

In interactive mode:

- **1-8**: Select menu option
- **q/Q**: Quit / Go back
- **b/B**: Back to previous menu
- **Enter**: Confirm selection
- **Ctrl+C**: Force exit

---

## Integration with Other Tools

### vLLM Model Switch

PTUI integrates with `vllm-model-switch.sh`:

```bash
ptui vllm <command>
```

Equivalent to:

```bash
./scripts/vllm-model-switch.sh <command>
```

### Validation Script

Quick access to comprehensive validation:

```bash
ptui → Quick Actions → Run validation script
```

Runs:

```bash
./scripts/validate-unified-backend.sh
```

### Service Management

```bash
ptui → Quick Actions → Restart LiteLLM service
```

Executes:

```bash
systemctl --user restart litellm.service
```

---

## Configuration

PTUI reads configuration from:

- **Project root**: `$SCRIPT_DIR/..`
- **Config directory**: `$PROJECT_ROOT/config/`
- **Logs**: `/tmp/vllm-*.log`, `journalctl --user`

### Service Endpoints

Default endpoints (configurable in script):

```bash
LITELLM_URL="http://localhost:4000"
OLLAMA_URL="http://localhost:11434"
LLAMACPP_PYTHON_URL="http://localhost:8000"
LLAMACPP_NATIVE_URL="http://localhost:8080"
VLLM_URL="http://localhost:8001"
```

To change endpoints, edit `/scripts/ptui` lines 8-13.

---

## Troubleshooting

### "terminals database is inaccessible"

This is a warning from `clear` command. Safe to ignore. PTUI still works.

**Fix**:
```bash
export TERM=xterm-256color
```

### ptui command not found

Ensure the PTUI scripts are discoverable:

```bash
type ptui
type pui
```

Both should resolve to the repo scripts, for example:

```
ptui is /home/miko/LAB/ai/backend/ai-backend-unified/scripts/ptui
pui is /home/miko/LAB/ai/backend/ai-backend-unified/scripts/pui
```

If they do not, either invoke them directly (`./scripts/ptui`, `./scripts/pui`) or add the directory to your PATH:

```bash
export PATH="/home/miko/LAB/ai/backend/ai-backend-unified/scripts:$PATH"
```

Alternatively, add shell aliases pointing at the scripts:

```bash
# ~/.bashrc or ~/.zshrc
alias ptui='/home/miko/LAB/ai/backend/ai-backend-unified/scripts/ptui'
alias pui='/home/miko/LAB/ai/backend/ai-backend-unified/scripts/pui'
```

After updating your shell, reload it so the commands are immediately available:

```bash
source ~/.zshrc   # or ~/.bashrc
```

Once wired up, both `ptui` and `pui` launch the dashboard. If the curses UI cannot initialize (e.g. missing kitty terminfo), the tool automatically falls back to the legacy Bash menu, so the command still succeeds.

> ℹ️ The latest PTUI build also attempts to auto-install the kitty terminfo entry by running `tic` against the bundled `kitty.terminfo` file. If you still see a failure message after the automatic retry, double-check that `tic` is available (part of the `ncurses-bin` package) or compile the terminfo manually.

### Refreshing the Current Session

If you just added the alias (or switched branches), reload your current shell so the command becomes available without opening a new terminal:

```bash
source ~/.zshrc   # zsh
# or
source ~/.bashrc  # bash
```

You can confirm everything is wired up with:

```bash
type ptui
type pui
```

### Services show as stopped but are running

Check firewall or network issues:

```bash
# Test endpoints manually
curl http://localhost:4000/health
curl http://localhost:8001/v1/models
```

If these work but PTUI shows stopped, check timeout settings in script.

### vLLM commands not working

Ensure `vllm-model-switch.sh` exists and is executable:

```bash
ls -l /home/miko/LAB/ai/backend/ai-backend-unified/scripts/vllm-model-switch.sh
```

Should show: `-rwxr-xr-x` (executable)

---

## Advanced Usage

### Custom Health Checks

Add your own health check logic:

Edit `health_check()` function in `/scripts/ptui` around line 180.

### Additional Services

To monitor additional services:

1. Add endpoint URL at top of script
2. Add health check in `show_status()` function
3. Add to service count calculation

### Custom Menu Options

Add new menu items in `main_menu()` function around line 420.

Example:
```bash
echo "  ${CYAN}9${NC}. ${ICON_CUSTOM} My custom action"

# In case statement:
9)
    my_custom_function
    read -p "Press Enter to continue..."
    ;;
```

---

## FAQ

**Q: Can I run PTUI on a remote server?**
A: Yes, but interactive mode requires terminal support. Use command-line mode for scripting:
```bash
ssh server "ptui status"
```

**Q: Does PTUI modify any services?**
A: PTUI only reads status by default. Modifications (restart, stop) require explicit user action in Quick Actions menu.

**Q: Can I use PTUI in CI/CD?**
A: Yes! Use command-line mode:
```bash
ptui health && echo "PASS" || echo "FAIL"
```

**Q: How do I update PTUI?**
A: The script is version-controlled in git. Update via:
```bash
cd /home/miko/LAB/ai/backend/ai-backend-unified
git pull
```

**Q: Can PTUI auto-restart failed services?**
A: Not by default (safety). But you can create a wrapper script:
```bash
#!/bin/bash
ptui health || systemctl --user restart litellm.service
```

---

## Version History

### v2.0.0 (2025-10-24)
- Complete rewrite with interactive TUI
- Command-line mode support
- Integrated vLLM model management
- Color-coded status display
- Comprehensive health checks
- Service log viewing
- Configuration browser
- Quick actions menu

### v1.0.0 (Earlier)
- Initial basic status checker
- Simple service monitoring

---

## Support & Feedback

For issues or enhancements:

1. Check this documentation
2. Review `/scripts/ptui` source code
3. Test with `ptui status` for quick diagnostics
4. Check service logs via `ptui → View service logs`

---

**Last Updated**: 2025-10-24
**Maintained By**: AI Backend Unified Project
**License**: Part of ai-backend-unified (same license)
