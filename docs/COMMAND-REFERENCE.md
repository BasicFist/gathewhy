# Command Reference - AI Backend Unified Infrastructure

Quick reference card for the most common commands.

## Monitor Script (User-Friendly Interface)

All monitoring operations through a single command:

```bash
./scripts/monitor [command]
```

### Commands

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `setup` | Interactive setup wizard | First time setup |
| `status` | Check all services | Daily health check |
| `start` | Start monitoring stack | After system reboot |
| `stop` | Stop monitoring stack | Before system shutdown |
| `restart` | Restart all services | After config changes |
| `test` | Run dashboard tests | Validate configuration |
| `logs` | View service logs | Troubleshooting |
| `open` | Open Grafana in browser | View dashboards |
| `help` | Show help message | Reference |

### Examples

```bash
# First time setup (runs through 5-step wizard)
./scripts/monitor setup

# Check if everything is running
./scripts/monitor status

# Start services if they're stopped
./scripts/monitor start

# Open dashboard in browser
./scripts/monitor open

# Run validation tests (headless)
./scripts/monitor test
```

## PTUI - Provider TUI Command Center

Comprehensive command center for managing all AI backend services.

**Version**: 2.0.0 | **Command**: `ptui`, `pui`, or `providers`

### Installation (Optional)

Make PTUI available globally by adding the repo `scripts/` folder to your `PATH` or symlinking the commands:

```bash
# Add to PATH (recommended for development)
echo "export PATH=\"$PATH:$(pwd)/scripts\"" >> ~/.bashrc && source ~/.bashrc

# Or symlink (system-wide)
sudo ln -sf "$(pwd)/scripts/ptui" /usr/local/bin/ptui
sudo ln -sf "$(pwd)/scripts/pui" /usr/local/bin/pui
sudo ln -sf "$(pwd)/scripts/providers" /usr/local/bin/providers
```

### Quick Start

```bash
# Interactive mode (full TUI)
ptui        # or: pui, providers

# Command-line mode (quick checks)
ptui status        # Show service status
ptui models        # List all models
ptui health        # Run health check
ptui vllm status   # Check vLLM status
ptui help          # Show help
```

### Interactive Mode Features

| Menu Option | Description | When to Use |
|-------------|-------------|-------------|
| Detailed Status | Comprehensive service health | Daily health check |
| List Models | All models across providers | Check model availability |
| Health Check | Endpoint testing + inference | Troubleshooting connectivity |
| vLLM Management | Model switching, logs, status | Switch between Qwen/Dolphin |
| View Configuration | Browse config files | Review settings |
| Service Logs | LiteLLM, vLLM, system logs | Debug issues |
| Test Endpoints | Interactive API testing | Validate routing |
| Quick Actions | Restart, GPU check, port check | Fast operations |

### Command-Line Mode

```bash
# Service monitoring
ptui status                    # Check all 5 services
ptui models                    # List models by provider

# Health validation
ptui health                    # Comprehensive health check

# vLLM operations
ptui vllm status              # Current vLLM model
ptui vllm qwen                # Switch to Qwen Coder
ptui vllm dolphin             # Switch to Dolphin
ptui vllm stop                # Stop vLLM

# Interactive testing
ptui test                     # Open endpoint testing menu
```

### Integration with Other Tools

```bash
# vLLM Model Switching
ptui vllm qwen                # Calls vllm-model-switch.sh qwen
ptui vllm dolphin             # Calls vllm-model-switch.sh dolphin

# Service Restart
ptui                          # Interactive → Quick Actions → Restart LiteLLM
# Executes: systemctl --user restart litellm.service

# Validation
ptui                          # Interactive → Quick Actions → Run validation
# Executes: ./scripts/validate-unified-backend.sh
```

### Service Status Indicators

```
✅ LiteLLM Gateway (http://localhost:4000)         # Running
✅ Ollama (http://localhost:11434)                 # Running
✅ llama.cpp (Python) (http://localhost:8000)      # Running
✅ llama.cpp (Native) (http://localhost:8080)      # Running
✅ vLLM (http://localhost:8001)                    # Running
  └─ Model: Qwen/Qwen2.5-Coder-7B-Instruct-AWQ

🖥️  Services Running: 5/5
🤖 Models Available: 4
```

### Examples

```bash
# Morning workflow: Check everything
ptui status

# Need to switch vLLM model for creative writing
ptui vllm dolphin

# Test LiteLLM routing after config change
ptui health

# Interactive debugging session
ptui                          # Opens full TUI
# Navigate: Menu → View service logs → LiteLLM

# Scripting example: Auto-restart if unhealthy
if ! ptui health | grep -q "HEALTHY"; then
    systemctl --user restart litellm.service
    ptui vllm restart
fi

# Watch service status (updates every 5 seconds)
watch -n 5 "ptui status"
```

### Troubleshooting

```bash
# Service not responding
ptui status                   # Identify which service
ptui health                   # Run diagnostics
ptui                          # Interactive → View logs

# vLLM issues
ptui vllm status             # Check current model
ptui                         # Interactive → vLLM management → View logs

# Port conflicts
ptui                         # Interactive → Quick Actions → Check port usage
```

**Full Documentation**: See `docs/ptui-user-guide.md`

## Testing Commands

### Quick Tests

```bash
# Unit tests only (fast, no external dependencies)
pytest -m unit -v

# Integration tests (requires services running)
pytest -m integration -v

# Monitoring dashboard tests
./scripts/monitor test

# All tests
pytest -v
```

### Specific Test Files

```bash
# Routing logic tests
pytest tests/unit/test_routing.py -v

# Provider contract tests (bash script)
./tests/contract/test_provider_contracts.sh

# Integration tests
pytest tests/integration/test_integration.py -v

# Rollback tests (bash script)
./scripts/test-rollback.sh
```

### Coverage

```bash
# Run tests with coverage report
pytest --cov=. --cov-report=html

# View coverage in browser
firefox htmlcov/index.html
```

### Test Markers

```bash
# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m contract       # Contract tests only
pytest -m monitoring     # Monitoring tests only
pytest -m slow           # Slow tests only

# Combine markers
pytest -m "unit or integration" -v
pytest -m "not slow" -v
```

## Service Management

### systemd Commands

```bash
# Start services
systemctl --user start prometheus
systemctl --user start grafana
systemctl --user start loki
systemctl --user start promtail
systemctl --user start litellm.service

# Stop services
systemctl --user stop prometheus grafana loki promtail

# Restart services
systemctl --user restart litellm.service

# Check status
systemctl --user status prometheus
systemctl --user status grafana

# View logs
journalctl --user -u prometheus -f
journalctl --user -u grafana -f
journalctl --user -u litellm.service -f
```

### Quick Service Checks

```bash
# Check if services are responding
curl http://localhost:9090/-/healthy    # Prometheus
curl http://localhost:3000/api/health   # Grafana
curl http://localhost:3100/ready        # Loki
curl http://localhost:9080/ready        # Promtail
curl http://localhost:4000/health       # LiteLLM
```

## API Usage

### List Available Models

```bash
curl http://localhost:4000/v1/models | jq
```

### Test Routing

```bash
# Route to Ollama
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'

# Route to vLLM
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2-13b-vllm",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

### Python Client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="dummy-key"  # pragma: allowlist secret
)

response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=50
)

print(response.choices[0].message.content)
```

## Configuration Management

### Validate Configuration

```bash
# Validate configuration files
./scripts/validate-unified-backend.sh

# Check Pydantic schema
python3 scripts/validate-config-schema.py

# Check generated configs
./scripts/check-generated-configs.sh
```

### Update Configuration

```bash
# Edit configuration files
nano config/providers.yaml
nano config/model-mappings.yaml

# Regenerate LiteLLM config
python3 scripts/generate-litellm-config.py

# Restart LiteLLM to apply changes
systemctl --user restart litellm.service
```

## Monitoring & Metrics

### Prometheus Queries

```bash
# Request rate
curl 'http://localhost:9090/api/v1/query?query=rate(litellm_requests_total[5m])' | jq

# Error rate
curl 'http://localhost:9090/api/v1/query?query=rate(litellm_requests_total{status="error"}[5m])' | jq

# P95 latency
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(litellm_request_duration_seconds_bucket[5m]))' | jq
```

### Loki Log Queries

```bash
# Recent logs
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="litellm"}' \
  --data-urlencode "start=$(date -u -d '1 hour ago' '+%s')000000000" \
  --data-urlencode "end=$(date -u '+%s')000000000" | jq

# Error logs only
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="litellm"} |= "error"' \
  --data-urlencode "start=$(date -u -d '1 hour ago' '+%s')000000000" \
  --data-urlencode "end=$(date -u '+%s')000000000" | jq
```

### Dashboard Access

```bash
# Grafana
firefox http://localhost:3000
# Login: admin/admin

# Prometheus
firefox http://localhost:9090

# Or use the monitor script
./scripts/monitor open
```

## Troubleshooting

### Check Everything

```bash
# Single command to check all services
./scripts/monitor status

# Detailed validation
./scripts/validate-unified-backend.sh
```

### View Logs

```bash
# Interactive log viewer
./scripts/monitor logs

# Direct journalctl access
journalctl --user -u prometheus -n 50
journalctl --user -u grafana -n 50
journalctl --user -u litellm.service -n 50 -f
```

### Port Conflicts

```bash
# Check what's using a port
sudo lsof -i :3000
sudo lsof -i :4000
sudo lsof -i :9090
```

### Reset Services

```bash
# Stop everything
./scripts/monitor stop

# Clear data directories (if needed)
rm -rf monitoring/prometheus/data/*
rm -rf monitoring/grafana/data/*
rm -rf monitoring/loki/data/*

# Start fresh
./scripts/monitor start
```

## Git Commands

### Common Operations

```bash
# Check status
git status

# View changes
git diff

# Commit changes
git add .
git commit -m "feat: description of changes"

# View history
git log --oneline --graph
```

### Branching

```bash
# Create feature branch
git checkout -b feature/new-provider

# Switch branches
git checkout main

# Merge feature
git merge feature/new-provider
```

## Documentation

### Quick Access

```bash
# Main documentation files
cat README.md
cat QUICKSTART.md
cat DEPLOYMENT.md

# Specific guides
cat docs/architecture.md
cat docs/adding-providers.md
cat docs/consuming-api.md

# Testing docs
cat tests/README.md
cat monitoring/README.md
```

### Man-Style Help

```bash
# Monitor script help
./scripts/monitor help

# Pytest help
pytest --help

# Script help messages
./scripts/validate-unified-backend.sh --help
```

## One-Liners

### Status Check

```bash
./scripts/monitor status
```

### Quick Test

```bash
pytest -m unit -v && echo "✓ All unit tests passed"
```

### Restart After Config Change

```bash
systemctl --user restart litellm.service && sleep 2 && ./scripts/monitor status
```

### Generate Traffic for Testing

```bash
for i in {1..10}; do curl -s -X POST http://localhost:4000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"llama3.1:8b","messages":[{"role":"user","content":"Test"}],"max_tokens":5}' > /dev/null && echo "✓ Request $i"; sleep 1; done
```

### Watch Metrics Update

```bash
watch -n 1 'curl -s http://localhost:9090/api/v1/query?query=rate\(litellm_requests_total\[1m\]\) | jq .data.result[].value[1]'
```

## Key Ports Reference

| Service | Port | Purpose |
|---------|------|---------|
| **LiteLLM** | **4000** | **Main API gateway** |
| Ollama | 11434 | Local model server |
| llama.cpp (Python) | 8000 | Python bindings |
| llama.cpp (Native) | 8080 | C++ native |
| vLLM | 8001 | High-performance inference |
| OpenWebUI | 5000 | Web interface |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards |
| Loki | 3100 | Log aggregation |
| Promtail | 9080 | Log shipping |

## Environment Variables

```bash
# Playwright test modes
export PLAYWRIGHT_HEADED=1     # Show browser during tests
export PLAYWRIGHT_SLOWMO=500   # Slow down automation (ms)

# Test configuration
export PYTEST_TIMEOUT=30       # Test timeout (seconds)
export COVERAGE_MIN=80         # Minimum coverage percentage
```

## Quick Cheat Sheet

```bash
# Daily workflow
./scripts/monitor status           # Check health
./scripts/monitor test            # Validate config
./scripts/monitor logs            # View logs if issues

# After changes
systemctl --user restart litellm.service
./scripts/monitor status

# Troubleshooting
./scripts/monitor status          # What's wrong?
./scripts/monitor logs           # Why is it wrong?
./scripts/monitor restart        # Fix it

# Testing
pytest -m unit                   # Quick validation
pytest -m integration            # Full validation
./scripts/monitor test           # Dashboard validation
```

---

**Pro tip**: Bookmark this file for quick reference!

For detailed documentation, see `QUICKSTART.md` or run `./scripts/monitor help`.
