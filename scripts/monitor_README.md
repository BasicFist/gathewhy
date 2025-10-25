# AI Backend Provider Command Center

A terminal-based dashboard for monitoring and managing AI backend providers.

## Features

- **Real-time monitoring**: View provider status, response times, and model counts
- **Service control**: Start, stop, and restart providers directly from the dashboard
- **System metrics**: Monitor CPU and memory usage with sparkline graphs
- **Quick actions**: One-click controls for common operations
- **Keyboard navigation**: Full keyboard support for power users

## Requirements

- Python 3.7+
- Textual
- Rich
- psutil
- requests

## Usage

```bash
./scripts/monitor
```

## Keyboard Shortcuts

- `R` - Refresh all data
- `Q` - Quit the application
- `T` - Toggle tabs
- `C` - Show control panel
- `M` - Show metrics
- `Tab` - Navigate to next element
- `Shift+Tab` - Navigate to previous element

## Control Elements

- **Provider Status Table**: Shows current status of all AI providers
- **Quick Actions**: Buttons to refresh all data or restart LiteLLM
- **Provider Controls**: Individual start/stop/restart buttons for each provider
- **System Metrics**: Real-time CPU and memory usage graphs

## Provider Support

Currently supports monitoring and control of:
- Ollama
- vLLM (Qwen model)
- vLLM (Dolphin model)
- llama.cpp Python bindings
- llama.cpp native server

## Troubleshooting

If you encounter issues with service controls not working, ensure that:
1. You have the necessary permissions to run systemctl commands
2. The systemd service files exist for each provider
3. The provider endpoints are accessible
