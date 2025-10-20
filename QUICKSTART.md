# Quick Start Guide - AI Backend Unified Infrastructure

## 🚀 Getting Started in 5 Minutes

This guide will help you get the AI Backend Unified Infrastructure up and running with monitoring.

## Prerequisites

All dependencies are now installed:
- ✅ Python packages (pytest, playwright, etc.)
- ✅ Playwright Chromium browser
- ✅ User-friendly monitor script

## The New User-Friendly Interface

All monitoring operations are now available through a single command:

```bash
./scripts/monitor [command]
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `setup` | Run interactive setup wizard | `./scripts/monitor setup` |
| `test` | Run dashboard validation tests | `./scripts/monitor test` |
| `status` | Check all services status | `./scripts/monitor status` |
| `start` | Start monitoring services | `./scripts/monitor start` |
| `stop` | Stop monitoring services | `./scripts/monitor stop` |
| `restart` | Restart monitoring services | `./scripts/monitor restart` |
| `logs` | View service logs | `./scripts/monitor logs` |
| `open` | Open dashboards in browser | `./scripts/monitor open` |
| `help` | Show help message | `./scripts/monitor help` |

## Step-by-Step Setup

### Step 1: Run the Setup Wizard

```bash
cd ~/LAB/ai/backend/ai-backend-unified
./scripts/monitor setup
```

The wizard will guide you through:
1. ✅ Checking Python dependencies (already installed)
2. ✅ Installing Playwright browsers (already installed)
3. 📁 Creating necessary directories
4. 🔧 Checking monitoring services
5. 📊 Checking Grafana dashboard

### Step 2: Start Monitoring Services

If services aren't running, start them:

```bash
./scripts/monitor start
```

This starts:
- Prometheus (metrics collection) on port 9090
- Grafana (dashboards) on port 3000
- Loki (log aggregation) on port 3100
- Promtail (log shipping) on port 9080

### Step 3: Verify Everything Works

Check service status:

```bash
./scripts/monitor status
```

You should see all green checkmarks ✓

### Step 4: Open Dashboards

Open Grafana in your browser:

```bash
./scripts/monitor open
```

Or manually visit: http://localhost:3000
- Username: `admin`
- Password: `admin`

### Step 5: Run Dashboard Tests

Validate the dashboard is correctly configured:

```bash
./scripts/monitor test
```

Choose from:
1. **Quick test** (headless) - Fast validation without opening browser
2. **Watch browser** (headed mode) - See the tests running in real browser
3. **Specific test only** - Run individual test scenarios

## Daily Usage

### Check System Health

```bash
./scripts/monitor status
```

Shows:
- ✓/✗ Status of each service
- Request rate metrics
- Quick stats

### View Logs

```bash
./scripts/monitor logs
```

Interactive menu to select which service logs to view:
1. Prometheus
2. Grafana
3. Loki
4. Promtail
5. LiteLLM

### Restart Services

After configuration changes:

```bash
./scripts/monitor restart
```

## Testing the Infrastructure

### Run All Tests

```bash
# Unit tests only
pytest -m unit -v

# Integration tests (requires services running)
pytest -m integration -v

# Monitoring dashboard tests
./scripts/monitor test

# All tests
pytest -v
```

### Run Specific Test Suites

```bash
# Routing logic tests
pytest tests/unit/test_routing.py -v

# Provider contract tests
./tests/contract/test_provider_contracts.sh

# Integration tests
pytest tests/integration/test_integration.py -v

# Rollback tests
./scripts/test-rollback.sh
```

### Check Coverage

```bash
pytest --cov=. --cov-report=html
firefox htmlcov/index.html  # View coverage report
```

## Using the AI Gateway

### From Python

```python
from openai import OpenAI

# Point to local LiteLLM gateway
client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="dummy-key"  # Not required for local
)

# Make a request
response = client.chat.completions.create(
    model="llama3.1:8b",  # Routes to Ollama
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=50
)

print(response.choices[0].message.content)
```

### From Command Line

```bash
# Chat completion
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'

# List available models
curl http://localhost:4000/v1/models | jq
```

### Streaming Responses

```python
response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Tell me a story"}],
    max_tokens=200,
    stream=True  # Enable streaming
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='', flush=True)
```

## Monitoring Your Requests

### View Real-Time Metrics

1. Open Grafana: `./scripts/monitor open`
2. Navigate to "AI Backend Unified Infrastructure" dashboard
3. Watch metrics update in real-time:
   - Request rate per model
   - Response time (P95)
   - Error rate
   - Provider health
   - Cache hit rate

### Query Prometheus Directly

```bash
# Request rate
curl 'http://localhost:9090/api/v1/query?query=rate(litellm_requests_total[5m])'

# Error rate
curl 'http://localhost:9090/api/v1/query?query=rate(litellm_requests_total{status="error"}[5m])'

# Cache hit rate
curl 'http://localhost:9090/api/v1/query?query=rate(litellm_cache_hits[5m])/rate(litellm_requests_total[5m])'
```

### Search Logs with Loki

```bash
# Recent LiteLLM logs
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="litellm"}' \
  --data-urlencode "start=$(date -u -d '1 hour ago' '+%s')000000000" \
  --data-urlencode "end=$(date -u '+%s')000000000" | jq

# Errors only
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="litellm"} |= "error"' \
  --data-urlencode "start=$(date -u -d '1 hour ago' '+%s')000000000" \
  --data-urlencode "end=$(date -u '+%s')000000000" | jq
```

## Troubleshooting

### Services Won't Start

```bash
# Check service status
systemctl --user status prometheus
systemctl --user status grafana

# View logs
journalctl --user -u prometheus -n 50
journalctl --user -u grafana -n 50

# Try manual restart
./scripts/monitor restart
```

### Dashboard Not Showing Data

1. **Wait 30 seconds** - Prometheus needs time to scrape metrics
2. **Generate some traffic** - Make a few test requests
3. **Check Prometheus targets**: http://localhost:9090/targets
4. **Check Grafana datasources**: http://localhost:3000/datasources

### Tests Failing

```bash
# Ensure services are running
./scripts/monitor status

# Re-run setup wizard
./scripts/monitor setup

# Try headed mode to see what's happening
./scripts/monitor test
# Select option 2 (Watch browser)
```

### Port Conflicts

If ports 3000, 4000, 9090, etc. are already in use:

```bash
# Check what's using a port
sudo lsof -i :3000
sudo lsof -i :4000

# Stop conflicting services or edit configs
# to use different ports
```

## Configuration Files

All configuration lives in version control:

```
ai-backend-unified/
├── config/
│   ├── providers.yaml           # Provider registry
│   ├── model-mappings.yaml      # Routing rules
│   └── litellm-unified.yaml     # LiteLLM config
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml       # Metrics scraping
│   │   └── alerts.yml           # Alert rules
│   ├── grafana/
│   │   └── litellm-dashboard.json  # Dashboard definition
│   └── loki/
│       ├── loki-config.yml      # Log aggregation
│       └── promtail-config.yml  # Log shipping
└── tests/
    ├── unit/                    # Unit tests
    ├── integration/             # Integration tests
    ├── contract/                # Contract tests
    └── monitoring/              # Dashboard tests
```

## What's Next?

1. **Explore the Dashboard**: Open Grafana and explore all 11 panels
2. **Make Test Requests**: Generate traffic and watch metrics update
3. **Review Alerts**: Check configured alerts in Prometheus
4. **Add New Models**: Follow `docs/adding-providers.md`
5. **Production Deployment**: Follow `DEPLOYMENT.md` checklist

## Getting Help

### Documentation

- **Main README**: `README.md` - Project overview
- **Architecture**: `docs/architecture.md` - System design
- **Testing**: `tests/README.md` - Testing guide
- **Monitoring**: `monitoring/README.md` - Monitoring details
- **Deployment**: `DEPLOYMENT.md` - Production checklist

### Commands

```bash
./scripts/monitor help          # Monitor script help
pytest --help                   # Test runner help
./scripts/validate-unified-backend.sh --help  # Validation help
```

### Check Logs

```bash
./scripts/monitor logs          # Interactive log viewer
journalctl --user -u litellm.service -f  # Follow LiteLLM logs
tail -f monitoring/prometheus/data/wal/*  # Raw Prometheus data
```

## Key Features Summary

✅ **User-Friendly Interface**: Single `./scripts/monitor` command for everything
✅ **Interactive Setup**: Guided wizard for first-time setup
✅ **Comprehensive Testing**: 75+ automated tests across all layers
✅ **Real-Time Monitoring**: 11-panel Grafana dashboard with live metrics
✅ **Automated Alerts**: 30+ alert rules for proactive monitoring
✅ **Log Aggregation**: 15-day retention with powerful search
✅ **Version Control**: All configuration in git
✅ **Production Ready**: Complete deployment checklist

---

**Happy monitoring!** 🎉

For detailed documentation, see the `docs/` directory or run `./scripts/monitor help`.
