# WTH LiteLLM Dashboard Widgets

Modular widgets and configuration for running the [WTH](https://github.com/mrusme/wth) terminal dashboard against the AI Backend Unified stack. The goal is to offer a responsive, sticker-based command center that mirrors the visibility provided by the Textual/PTUI dashboards while staying entirely shell/script driven.

## Layout

```
wth-widgets/
  README.md
  litellm/
    bin/
      common.sh               # Helper functions shared by widgets
      litellm-status.sh       # Service health overview
      litellm-metrics.sh      # Prometheus-style metrics sampler
      litellm-logs.sh         # Recent LiteLLM proxy logs
    config/
      wth-lite-dashboard.yaml # Sticker layout referencing the widgets
```

## Requirements

- WTH ≥ 0.11 installed locally (`wth` binary on PATH)
- [Gum](https://github.com/charmbracelet/gum) (optional, enables styled output)
- LiteLLM + supporting services running on localhost per this repository’s defaults
- `curl`, `jq`, and `systemctl --user` access for status checks

Each widget degrades gracefully if Gum is missing by falling back to plain text output.

## Usage

1. Copy or symlink the widgets into a location on your PATH (see `scripts/install-wth-dashboard.sh`).
2. Copy `wth-widgets/litellm/config/wth-lite-dashboard.yaml` to `~/.config/wth/wth.yaml` (or merge into an existing WTH config).
3. Start WTH: `wth run --config ~/.config/wth/wth.yaml`.

Set the following environment variables to customize behavior:

| Variable | Default | Description |
| --- | --- | --- |
| `LITELLM_HOST` | `http://127.0.0.1:4000` | Base URL for LiteLLM router |
| `LITELLM_LOG_SOURCE` | `journalctl --user -u litellm.service -n 40` | Command used by the logs widget |
| `WTH_WIDGET_REFRESH` | widget-specific | Override refresh intervals defined in the config |

## Extending

- Drop additional shell scripts into `litellm/bin/` and reference them from the YAML layout.
- For advanced use-cases, compile Go/Bubble Tea modules into shared objects (`.so`) and place them on WTH’s plugin path (`~/.config/wth/plugins`).
- Keep widgets stateless; every run should print a complete view so WTH can simply render the captured output.

## Licensing

These widgets inherit the repository’s license. Gum and WTH retain their respective upstream licenses.
