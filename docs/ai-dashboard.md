# AI Dashboard (Bubble Tea / WTH)

The AI Dashboard now runs on top of [WTH](https://github.com/mrusme/wth), a Bubble Tea–powered terminal UI that renders configurable "stickers" backed by shell/Gum widgets. The dashboard replaces the previous Textual application with a lightweight command center that can be extended with standard shell tooling.

## Requirements

| Component | Version / Notes |
| --- | --- |
| WTH | v0.11 or newer (provides the Bubble Tea runtime) |
| Gum | Optional, enables styled tables/highlights |
| curl, jq, bc | Used by the bundled LiteLLM widgets |
| LiteLLM stack | Should be running locally on default ports |

## Quick Start

```bash
# Install WTH + Gum per your OS (brew/nix/apt).

# Copy widgets + config to $HOME (one-time)
./scripts/install-wth-dashboard.sh

# Launch the dashboard (auto-detects installed config)
./ai-dashboard
```

To run directly from the repo without installing assets:

```bash
python3 scripts/ai-dashboard --use-repo
```

## Launcher Options (`scripts/ai-dashboard`)

| Option | Description |
| --- | --- |
| `--install` | Executes `scripts/install-wth-dashboard.sh` before launching. |
| `--config PATH` | Explicit WTH config file. Defaults to the installed config if present, otherwise the in-repo layout. |
| `--widgets PATH` | Directory that contains the widget scripts. Useful when testing modified copies. |
| `--use-repo` | Force usage of the in-repo widgets/config even if installed copies are available. |
| `--wth-binary PATH` | Override the WTH binary (`wth` by default). |
| `-- ...` | Any arguments after `--` are forwarded to `wth run`. |

Examples:

```bash
# Run with installed config but custom widget directory
python3 scripts/ai-dashboard --widgets /tmp/new-widgets

# Force in-repo assets even if ~/.config/wth/wth.yaml exists
python3 scripts/ai-dashboard --use-repo

# Install assets and launch in one command
python3 scripts/ai-dashboard --install
```

## Sticker Layout & Features

The default layout lives at `wth-widgets/litellm/config/wth-lite-dashboard.yaml` and references the shell widgets under `wth-widgets/litellm/bin/`. The stickers refresh independently, giving you real-time visibility without a Python event loop.

Key features:

- **Provider status summary** (systemd + LiteLLM health checks)
- **Model catalog** sourced from `/v1/models`
- **Deployment health matrix** via `/health?details=true`
- **Provider scorecard** built from Prometheus metrics
- **Router metrics** covering request volume, cache hit rates, and latency
- **Redis cache performance** summary
- **Live LiteLLM logs** using `journalctl --user`

## Widget Reference

| Sticker | Script | Description |
| --- | --- | --- |
| `litellm-status` | `litellm/bin/litellm-status.sh` | Summarizes systemd health for LiteLLM, Ollama, vLLM, llama.cpp, and prints router liveliness. |
| `providers-overview` | `litellm/bin/providers-overview.sh` | Counts providers/models via the LiteLLM model catalog. |
| `health-status` | `litellm/bin/health-status.sh` | Lists healthy/degraded deployments using `/health?details=true`. |
| `provider-score` | `litellm/bin/provider-score.sh` | Builds a per-provider scorecard (requests, error rate, P95 latency) via Prometheus. |
| `litellm-metrics` | `litellm/bin/litellm-metrics.sh` | Highlights throughput, cache hit rate, and request mix from `/metrics`. |
| `cache-performance` | `litellm/bin/cache-performance.sh` | Computes Redis cache hit/miss ratios and estimated savings. |
| `litellm-logs` | `litellm/bin/litellm-logs.sh` | Streams recent LiteLLM journal entries. |

All widgets rely on standard shell commands (`curl`, `jq`, `gum`). They are stateless: each invocation prints a full view so that WTH can simply render the captured output.

## Customization

1. Edit `wth-widgets/litellm/config/wth-lite-dashboard.yaml` to rearrange stickers (width/height/top/left) or change refresh intervals.
2. Modify or add scripts under `wth-widgets/litellm/bin/`. Make sure they are executable.
3. Set `WTH_WIDGET_DIR` to point at your custom directory before launching `./ai-dashboard`.
4. Re-run `./scripts/install-wth-dashboard.sh` to copy the updated widgets to `$HOME`.

For advanced scenarios you can write Bubble Tea plugins in Go (`-buildmode=plugin`) and drop the resulting `.so` files into `~/.config/wth/plugins`.

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `LITELLM_HOST` | `http://127.0.0.1:4000` | Base URL used by the widgets. |
| `LITELLM_METRICS_ENDPOINT` | `/metrics` | Prometheus scrape path. |
| `LITELLM_HEALTH_ENDPOINT` | `/health/liveliness` | Health endpoint for system checks. |
| `LITELLM_LOG_SOURCE` | `journalctl --user -u litellm.service -n 40 --no-pager` | Command executed by the logs widget. |
| `PROM_HOST` | `http://127.0.0.1:9090` | Prometheus base URL for scorecard widgets. |
| `WTH_WIDGET_DIR` | `$HOME/.local/share/wth-widgets` | Directory that contains the widget scripts referenced in the YAML layout. |
| `WTH_ALIAS_NAME` | `wth-lite` | Alias name added to your shell profile by the installer. |

## Troubleshooting

| Symptom | Resolution |
| --- | --- |
| `wth: command not found` | Install WTH from GitHub releases or package manager, or pass `--wth-binary /path/to/wth`. |
| Widgets show `command not found` for Gum | Install Gum or set `USE_GUM=false` in the scripts to fall back to plain text. |
| `litellm-logs` is empty | Ensure `LITELLM_LOG_SOURCE` points to a readable command (e.g., `journalctl --user`). |
| Custom config not picked up | Launch with `python3 scripts/ai-dashboard --config /path/to/wth.yaml --widgets /path/to/widgets`. |
| Need to refresh assets | Re-run `./scripts/install-wth-dashboard.sh` and relaunch. |

## Migration Notes

- The Textual-based dashboard has been retired in favor of the Bubble Tea approach described here.
- Service-control buttons are planned as future WTH plugins; the current dashboard focuses on observability (status, metrics, logs).
- Existing documentation that references the Textual UI now points here or to the PTUI/Grafana alternatives.
