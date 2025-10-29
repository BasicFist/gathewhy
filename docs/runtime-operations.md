# LiteLLM Runtime Operations

This document summarizes how to work with the consolidated LiteLLM runtime.

## Directory Structure
- `runtime/config/litellm.yaml` – symlinked to `config/litellm-unified.yaml`
- `runtime/config/backups/` – automatic backups kept via generator/reload scripts
- `runtime/scripts/` – includes `run_litellm.sh` and `update_and_reload.sh`
- `runtime/.venv/` – managed by OpenWebUI's `scripts/setup_backends.sh`
- `runtime/reports/` – log output (ignored, `.gitkeep` only)

## Common commands
```bash
# Regenerate config and restart service
./runtime/scripts/update_and_reload.sh

# Just restart systemd unit
systemctl --user restart litellm.service

# Tail logs
journalctl --user -u litellm.service -f

# Quick health check
curl -s http://localhost:4000/health | jq
```

## Warnings
- `run_litellm.sh` bails if the config symlink is missing; regenerate before running.
- If the venv is missing, the script warns and exits — run OpenWebUI `setup_backends.sh`.
- Health endpoint may show remote AWQ models as unhealthy until vLLM is running.
