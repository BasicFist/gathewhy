# AI Backend Monitoring Dashboard

Professional terminal-based monitoring for AI backend providers with real-time VRAM monitoring.

## Features

### Enhanced Dashboard (`ai-monitor-enhanced`)
- **Real-time Provider Status**: Monitor all AI providers (Ollama, vLLM, llama.cpp)
- **VRAM Monitoring**: Real-time GPU memory usage tracking with process correlation
- **Actionable Controls**: Start/Stop/Restart buttons for each provider
- **System Metrics**: CPU, memory, and GPU utilization with visual indicators
- **Professional Layout**: Three-panel dashboard with responsive design
- **Color-coded Status**: Visual feedback for provider health and resource usage

### Lite Dashboard (`ai-monitor-lite`)
- **Lightweight Monitoring**: Essential information with minimal overhead
- **Fast Performance**: Optimized for systems with limited resources
- **Information Dense**: Maximum data in minimal screen space
- **Quick Actions**: Rapid refresh and restart capabilities

## Usage

### Enhanced Dashboard
```bash
# Launch the enhanced dashboard with full VRAM monitoring
ai-monitor-enhanced
```

### Lite Dashboard
```bash
# Launch the lightweight dashboard
ai-monitor-lite
```

## Keyboard Shortcuts

### Enhanced Dashboard
- `R` - Refresh all data
- `Q` - Quit application
- `Ctrl+D` - Toggle dark mode
- `F1` - Show help
- Click provider buttons to control services

### Lite Dashboard
- `R` - Refresh all data
- `Q` - Quit application
- `Ctrl+D` - Toggle dark mode
- `F1` - Show help

## Provider Controls

Each provider in the enhanced dashboard has individual controls:
- **Start**: Launch the provider service
- **Stop**: Shutdown the provider service
- **Restart**: Restart the provider service

## VRAM Monitoring

The enhanced dashboard provides detailed GPU resource monitoring:
- Real-time VRAM usage for each provider
- GPU utilization percentages
- Temperature and power draw metrics
- Visual progress bars for memory usage
- Color-coded warnings for high resource usage

## System Requirements

### GPU Monitoring
- NVIDIA GPU with NVML support
- `nvidia-ml-py3` Python package installed
- Compatible drivers (tested with CUDA 11.8+)

### CPU/Memory Monitoring
- `psutil` Python package
- Standard Linux system metrics access

## Installation

The monitoring dashboards are automatically installed with the AI Backend Unified Infrastructure. Required dependencies are:

```bash
pip install textual rich psutil requests nvidia-ml-py3
```

## Configuration

### Service Names
The dashboards use systemd user services for provider control:
- Ollama: `ollama.service`
- vLLM Qwen: `vllm.service`
- vLLM Dolphin: `vllm-dolphin.service`
- llama.cpp Python: `llamacpp-python.service`
- llama.cpp Native: `llama-cpp-native.service`

### Provider Endpoints
Monitoring endpoints are configured in the dashboard code:
- Ollama: `http://127.0.0.1:11434/api/tags`
- llama.cpp Python: `http://127.0.0.1:8000/v1/models`
- llama.cpp Native: `http://127.0.0.1:8080/v1/models`
- vLLM Qwen: `http://127.0.0.1:8001/v1/models`
- vLLM Dolphin: `http://127.0.0.1:8002/v1/models`

## Troubleshooting

### No GPU Information
If GPU information is not displayed:
1. Ensure NVIDIA drivers are properly installed
2. Verify `nvidia-ml-py3` is installed in the correct Python environment
3. Check that the user has access to GPU resources

### Provider Controls Not Working
If provider control buttons don't respond:
1. Verify systemd user services exist for each provider
2. Ensure the user has permissions to run `systemctl --user` commands
3. Check service status with `systemctl --user status <service-name>`

### Dashboard Not Updating
If dashboard information appears stale:
1. Check network connectivity to provider endpoints
2. Verify providers are running and accessible
3. Restart the dashboard to reset connections

## Performance Considerations

### Resource Usage
- Enhanced dashboard: ~50-100MB RAM, minimal CPU usage
- Lite dashboard: ~30-50MB RAM, minimal CPU usage
- Both dashboards use efficient threading for non-blocking operations

### Update Intervals
- Provider status: Every 5 seconds
- System metrics: Every 2 seconds
- GPU information: Every 2 seconds

## Customization

### Adding New Providers
To add new providers to monitoring:
1. Add endpoint to `PROVIDER_ENDPOINTS` dictionary
2. Add service mapping for control buttons
3. Update UI layout if needed

### Modifying Layout
The dashboard uses Textual's CSS-like styling system:
- Modify CSS in the `CSS` class variable
- Adjust grid layouts with `grid-size` and `column-span` properties
- Customize colors with Textual's theme variables

## Integration

### Prometheus Export
For integration with monitoring stacks:
- Dashboard metrics can be exported via REST API
- Add Prometheus exporter endpoint for scraping
- Configure Grafana dashboards to visualize data

### Alerting
- Color-coded status indicators provide visual alerts
- High VRAM usage triggers warning states
- Provider downtime is immediately visible

## Best Practices

### Monitoring Strategy
1. Use enhanced dashboard for detailed analysis and troubleshooting
2. Use lite dashboard for routine monitoring with minimal overhead
3. Set up alerts for critical provider downtime
4. Monitor VRAM usage to prevent out-of-memory conditions

### Resource Management
1. Regularly check for leaked provider processes
2. Monitor VRAM usage to optimize model loading
3. Use provider controls to manage resource allocation
4. Schedule maintenance during low-usage periods

## Security

### Access Control
- Dashboard runs with user privileges
- Provider control uses `systemctl --user` commands
- No elevated privileges required for normal operation

### Data Privacy
- All monitoring data stays local
- No external connections except to configured providers
- Provider API keys are not exposed through dashboard
