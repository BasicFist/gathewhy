# WTH Dashboard (Beta)

The WTH dashboard is a next-generation terminal UI that uses sticker-based layouts and plugin modules to provide a responsive command center for LiteLLM. This document explains how to install, customize, and operate the bundled widgets found under `wth-widgets/`.

## Why WTH?

- **Responsive layout**: stickers automatically resize when the terminal changes dimensions.
- **Modular architecture**: widgets are standalone shell scripts (or shared objects) you can version independently.
- **Gum-powered styling**: rich text, tables, and highlights without having to write Go.

## Requirements

- WTH ≥ 0.11 (`brew install wth`, `nix profile install github:mrusme/wth`, or build from source)
- Charm’s [Gum](https://github.com/charmbracelet/gum) (optional but recommended for styling)
- `curl`, `jq`, `bc`, and `systemctl --user`
- LiteLLM/Ollama services running locally (the widgets assume default ports from `config/ports.yaml`)

## Installation

```bash
# From repo root
./scripts/install-wth-dashboard.sh

# Export widget path (if you changed WTH_WIDGET_DEST)
export WTH_WIDGET_DIR="$HOME/.local/share/wth-widgets"

# Launch WTH (or use the alias added to ~/.bashrc / ~/.zshrc)
wth run --config $HOME/.config/wth/wth.yaml
wth-lite  # default alias created by the installer
```

The install script copies:

- Widgets → `$HOME/.local/share/wth-widgets/`
- Config → `$HOME/.config/wth/wth.yaml` (only if a file does not already exist)

If you already maintain a WTH config, merge `wth-widgets/litellm/config/wth-lite-dashboard.yaml` into it manually.

## Widgets

| Sticker | Script | Description |
| --- | --- | --- |
| `litellm-status` | `litellm-status.sh` | Checks `systemctl --user` for LiteLLM, Ollama, llama.cpp Python, and vLLM. Hits `/health/liveliness` for router status. |
| `providers-overview` | `providers-overview.sh` | Counts models per provider using `/v1/models`. |
| `health-status` | `health-status.sh` | Lists healthy/unhealthy deployments using `/health?details=true` (falls back to `/health`). |
| `provider-score` | `provider-score.sh` | Builds a scorecard (requests, latency, error %) per provider via Prometheus metrics. |
| `litellm-metrics` | `litellm-metrics.sh` | Pulls Prometheus metrics from `/metrics` and highlights request volume, cache hits, and latency. |
| `cache-performance` | `cache-performance.sh` | Summarizes Redis cache hit/miss metrics and estimated savings. |
| `litellm-logs` | `litellm-logs.sh` | Streams recent LiteLLM logs via `journalctl --user -u litellm.service`. |

All scripts degrade gracefully if Gum is unavailable by emitting plain text.

### Environment Variables

| Variable | Default | Effect |
| --- | --- | --- |
| `LITELLM_HOST` | `http://127.0.0.1:4000` | Router base URL |
| `LITELLM_HEALTH_ENDPOINT` | `/health/liveliness` | Health endpoint path |
| `LITELLM_METRICS_ENDPOINT` | `/metrics` | Prometheus metrics path |
| `LITELLM_LOG_SOURCE` | `journalctl --user -u litellm.service -n 40 --no-pager` | Command used by logs widget |
| `LITELLM_API_KEY` | (unset) | If set, widgets hit LiteLLM endpoints with `Authorization: Bearer` headers |
| `PROM_HOST` | `http://127.0.0.1:9090` | Prometheus base URL |
| `WTH_WIDGET_DIR` | `$HOME/.local/share/wth-widgets` | Base path referenced in the config file |
| `WTH_ALIAS_NAME` | `wth-lite` | Alias name appended to `~/.zshrc` or `~/.bashrc` |
| `WTH_ALIAS_FILE` | Auto-detected (`~/.zshrc` or `~/.bashrc`) | Target file that receives the alias |

## Custom Widgets

1. Drop a shell script into `wth-widgets/<component>/bin/my-widget.sh`.
2. Update `common.sh` (if you need shared helpers).
3. Reference the script in the YAML layout with a unique sticker name, e.g.:

   ```yaml
   - name: redis-status
     top: 14
     left: 0
     width: 50%
     height: 4
     module: command
     command: ${WTH_WIDGET_DIR}/litellm/bin/redis-status.sh
     refresh: 15s
   ```

4. Re-run `./scripts/install-wth-dashboard.sh` or copy files manually.

For full Bubble Tea modules, compile Go code with `-buildmode=plugin` and place the resulting `.so` files under `~/.config/wth/plugins`.

## Roadmap

- Service control widget (start/stop LiteLLM) implemented as a Go plugin for better UX
- Redis/GPU monitoring stickers
- Optional remote auth integration once LiteLLM master-key support is required

Feedback and contributions are welcome—open an issue or PR with your widget ideas.
