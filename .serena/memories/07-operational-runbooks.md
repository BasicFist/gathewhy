# AI Backend Unified Infrastructure - Operational Runbooks

**Memory Type**: Operational Procedures
**Created**: 2025-10-20
**Last Updated**: 2025-10-20

## Runbook: Adding a New Provider

### Prerequisites
- Provider service accessible via HTTP
- Provider implements OpenAI-compatible API or known format
- Port assignment doesn't conflict with existing services

### Procedure

**Step 1: Add to providers.yaml**
```yaml
providers:
  new_provider:
    type: openai_compatible  # or ollama, llama_cpp, vllm
    base_url: http://127.0.0.1:8002
    status: active
    description: "Description of new provider"
    models:
      - name: model-name
        size: "7B"
        specialty: general
    health_endpoint: /v1/models
```

**Step 2: Add routing rules to model-mappings.yaml**
```yaml
exact_matches:
  "model-name":
    provider: new_provider
    priority: primary
    fallback: ollama
    description: "New provider model"
```

**Step 3: Generate LiteLLM configuration**
```bash
python3 scripts/generate-litellm-config.py
```

**Step 4: Validate configuration**
```bash
python3 scripts/validate-config-schema.py
```

**Step 5: Apply configuration**
```bash
# Backup current config
cp ../openwebui/config/litellm.yaml ../openwebui/config/litellm.yaml.backup

# Apply new config
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml

# Restart LiteLLM
systemctl --user restart litellm.service
```

**Step 6: Verify**
```bash
# Check model appears
curl http://localhost:4000/v1/models | jq '.data[] | select(.provider == "new_provider")'

# Test completion
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "model-name", "messages": [{"role": "user", "content": "Test"}]}'
```

**Step 7: Update Serena memory**
```bash
# Update 02-provider-registry.md with new provider info
```

---

## Runbook: Adding a New Model to Existing Provider

### For Ollama

**Step 1: Pull model**
```bash
ollama pull model-name:version
```

**Step 2: Verify model available**
```bash
ollama list
```

**Step 3: Add to providers.yaml**
```yaml
providers:
  ollama:
    models:
      - name: model-name:version
        size: "7B"
        quantization: Q4_K_M
        pulled_at: "2025-10-20"
```

**Step 4: Add routing entry**
```yaml
# In model-mappings.yaml
exact_matches:
  "model-name:version":
    provider: ollama
    priority: primary
    description: "New Ollama model"
```

**Step 5: Regenerate and apply**
```bash
python3 scripts/generate-litellm-config.py
python3 scripts/validate-config-schema.py
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

### For vLLM

**Step 1: Update vLLM server**
```bash
# Update vLLM systemd service with new model path
systemctl --user edit vllm-qwen.service
# Or use vllm-model-switch.sh script if available
```

**Step 2: Follow same config steps as Ollama** (steps 3-5)

---

## Runbook: Updating Model Routing Strategy

### Scenario: Change from round-robin to usage-based routing

**Step 1: Update litellm-unified.yaml**
```yaml
router_settings:
  routing_strategy: usage-based-routing-v2  # Changed from simple-shuffle
```

**Step 2: Apply configuration**
```bash
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

**Step 3: Monitor behavior**
```bash
# Watch routing decisions
journalctl --user -u litellm.service -f | grep "routing"

# Check which providers get requests
journalctl --user -u litellm.service --since "10 minutes ago" | \
  grep '"provider":' | \
  awk -F'"provider": "' '{print $2}' | \
  awk -F'"' '{print $1}' | \
  sort | uniq -c
```

**Step 4: Validate performance**
```bash
# Compare latency before/after
scripts/compare-routing-performance.sh  # If created in Phase 3
```

---

## Runbook: Enabling/Disabling Provider

### Disable Provider (Maintenance)

**Step 1: Update status in providers.yaml**
```yaml
providers:
  provider_name:
    status: disabled  # Changed from active
```

**Step 2: Regenerate configuration**
```bash
python3 scripts/generate-litellm-config.py
```

**Step 3: Apply (provider routes removed)**
```bash
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

**Step 4: Verify fallbacks work**
```bash
# Requests to disabled provider models should use fallbacks
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "disabled-provider-model", ...}'
```

### Re-enable Provider

**Reverse process**: Set `status: active`, regenerate, apply

---

## Runbook: Configuration Rollback

### When to Use
- Configuration change causes errors
- Performance degradation detected
- Provider incompatibility discovered

### Procedure

**Step 1: Identify rollback target**
```bash
# List recent git commits
cd ai-backend-unified
git log --oneline -5 config/

# Or use backup
ls -lt ../openwebui/config/litellm.yaml.backup*
```

**Step 2: Stop LiteLLM**
```bash
systemctl --user stop litellm.service
```

**Step 3: Restore configuration**
```bash
# From git
git checkout <commit-hash> config/litellm-unified.yaml

# Or from backup
cp ../openwebui/config/litellm.yaml.backup ../openwebui/config/litellm.yaml
```

**Step 4: Restart and verify**
```bash
systemctl --user start litellm.service
curl http://localhost:4000/v1/models | jq
scripts/validate-unified-backend.sh
```

**Step 5: Document rollback**
```bash
# Create incident log
echo "Rollback performed: $(date)" >> logs/rollback-$(date +%Y%m%d).log
echo "Reason: <reason>" >> logs/rollback-$(date +%Y%m%d).log
```

---

## Runbook: Performance Tuning

### Optimize for Latency

**Step 1: Use fastest providers**
```yaml
# Route critical requests to llama-cpp-native
exact_matches:
  "fast-model":
    provider: llama_cpp_native
    priority: primary
```

**Step 2: Enable caching**
```yaml
litellm_settings:
  cache: true
  cache_params:
    ttl: 3600
```

**Step 3: Disable pre-call checks**
```yaml
router_settings:
  enable_pre_call_checks: false  # Skip health checks for speed
```

### Optimize for Throughput

**Step 1: Use vLLM for high concurrency**
```yaml
capabilities:
  high_throughput:
    provider: vllm
    routing_strategy: least_loaded
```

**Step 2: Increase cache TTL**
```yaml
litellm_settings:
  cache_params:
    ttl: 7200  # 2 hours for batch workloads
```

---

## Runbook: Security Hardening

### Enable Authentication

**Step 1: Generate master key**
```bash
LITELLM_MASTER_KEY="sk-$(openssl rand -hex 16)"
echo "export LITELLM_MASTER_KEY='$LITELLM_MASTER_KEY'" >> ~/.bashrc
```

**Step 2: Update systemd service**
```bash
systemctl --user edit litellm.service

# Add:
[Service]
Environment="LITELLM_MASTER_KEY=sk-..."
```

**Step 3: Restart**
```bash
systemctl --user daemon-reload
systemctl --user restart litellm.service
```

**Step 4: Test**
```bash
# Without key - should fail
curl http://localhost:4000/v1/models

# With key - should work
curl -H "Authorization: Bearer sk-..." http://localhost:4000/v1/models
```

### Restrict CORS

**Step 1: Update litellm-unified.yaml**
```yaml
server_settings:
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:*"
      - "http://127.0.0.1:*"
```

**Step 2: Apply and restart**

### Enable Rate Limiting

**Step 1: Configure limits**
```yaml
rate_limit_settings:
  enabled: true
  limits:
    llama3.1:8b:
      rpm: 100
      tpm: 50000
```

**Step 2: Apply and monitor**
```bash
# Watch for rate limit triggers
journalctl --user -u litellm.service -f | grep "rate_limit"
```

---

## Runbook: Dashboard and Monitoring

### Available Dashboard Implementations

The project provides two complementary dashboard solutions:

1. **Enhanced Textual Dashboard (PTUI)** - Interactive TUI with real-time monitoring
2. **WTH Dashboard Widgets** - Lightweight shell-based monitoring

### Enhanced Textual Dashboard

**Location**: `scripts/ai-dashboard-enhanced.py`

**Features**:
- Real-time provider health monitoring with visual indicators
- Performance comparison widgets for latency analysis
- Configuration editor integration
- Request inspector with live updates
- Auto-refreshing metrics display

**Installation**:
```bash
# Install dependencies
./scripts/install-wth-dashboard.sh

# Or manually
pip install textual requests psutil
```

**Usage**:
```bash
# Launch dashboard
python3 scripts/ai-dashboard-enhanced.py

# Keyboard shortcuts
# q - Quit
# r - Refresh
# c - Toggle configuration editor
```

**Requirements**:
- Python 3.8+
- Textual >= 0.40.0
- psutil, requests
- LiteLLM running on localhost:4000

**Troubleshooting**:
```bash
# If dashboard fails to connect
curl http://localhost:4000/health

# Check LiteLLM service
systemctl --user status litellm.service

# Enable debug mode
python3 scripts/ai-dashboard-enhanced.py --debug  # If implemented
```

---

### WTH Dashboard Widgets

**Location**: `wth-widgets/litellm/`

**Architecture**:
- Modular shell-based widgets (9 specialized scripts)
- Sticker-based layout via WTH configuration
- Graceful degradation without optional dependencies

**Available Widgets**:
1. **health-status.sh** - Service health overview
2. **providers-overview.sh** - Provider status matrix
3. **litellm-metrics.sh** - Prometheus-style metrics sampler
4. **cache-performance.sh** - Redis cache hit rates
5. **provider-score.sh** - Provider performance scoring
6. **litellm-logs.sh** - Recent LiteLLM proxy logs
7. **litellm-status.sh** - Detailed service status
8. **common.sh** - Shared helper functions

**Installation**:
```bash
# Method 1: Using install script
./scripts/install-wth-dashboard.sh

# Method 2: Manual installation
# Install WTH (https://github.com/mrusme/wth)
go install github.com/mrusme/wth@latest

# Install Gum (optional, for styled output)
brew install gum  # macOS
# or
sudo apt install gum  # Ubuntu/Debian

# Copy widgets to PATH
sudo cp wth-widgets/litellm/bin/* /usr/local/bin/
sudo chmod +x /usr/local/bin/litellm-*.sh /usr/local/bin/health-status.sh

# Copy WTH config
mkdir -p ~/.config/wth
cp wth-widgets/litellm/config/wth-lite-dashboard.yaml ~/.config/wth/wth.yaml
```

**Usage**:
```bash
# Start WTH dashboard
wth run --config ~/.config/wth/wth.yaml

# Run individual widgets
litellm-status.sh
providers-overview.sh
cache-performance.sh
```

**Configuration**:
```bash
# Environment variables
export LITELLM_HOST="http://127.0.0.1:4000"  # LiteLLM base URL
export LITELLM_LOG_SOURCE="journalctl --user -u litellm.service -n 40"
export WTH_WIDGET_REFRESH=5  # Refresh interval in seconds
```

**Extending**:
```bash
# Add custom widget
vim wth-widgets/litellm/bin/custom-widget.sh

# Source common helpers
source "$(dirname "$0")/common.sh"

# Use helper functions
check_litellm_health
get_prometheus_metric "litellm_requests_total"

# Reference from WTH config
# In wth-lite-dashboard.yaml:
stickers:
  - command: custom-widget.sh
    refresh: 10s
```

---

### Monitoring Stack Setup

**Prometheus Metrics**

Already configured in `litellm-unified.yaml`:
```yaml
server_settings:
  prometheus:
    enabled: true
    port: 9090
```

**Grafana Dashboard**

**Step 1: Start monitoring stack** (if using Docker Compose)
```bash
cd monitoring
docker compose up -d
```

**Step 2: Access Grafana**
- URL: http://localhost:3000
- Default credentials: admin/admin

**Step 3: Configure data source**
- Add Prometheus at `http://localhost:9090`

**Step 4: Import dashboard**
```bash
# Use monitoring/grafana/litellm-dashboard.json
# Or create custom dashboard
```

**Step 5: Set up alerts**
- High latency: P95 > 2s
- High error rate: > 5%
- Provider unavailability

---

### Testing Dashboard Integration

**Test Kimi K2 Routing** (validates load balancing):

**Location**: `test_kimi_routing.sh`

**Usage**:
```bash
# Test direct Kimi K2 requests
./test_kimi_routing.sh

# Expected output:
# Test 1: Direct request to kimi-k2:1t-cloud
# [Response content]
#
# Test 2: Reasoning capability request (load balanced)
# [Response content]
```

**What it tests**:
- Direct model routing to Ollama Cloud
- Capability-based routing (reasoning → model pool)
- Load balancing across multiple providers
- Fallback chain integrity

**Troubleshooting**:
```bash
# If FAILED - Check OLLAMA_API_KEY
echo $OLLAMA_API_KEY  # Should be set in environment

# Check Ollama Cloud connectivity
curl https://ollama.com/api/tags \
  -H "Authorization: Bearer $OLLAMA_API_KEY"

# Verify routing configuration
grep -A 5 "kimi-k2:1t-cloud" config/model-mappings.yaml
```

---

### Dashboard Selection Guide

**Use Enhanced Textual Dashboard when**:
- Interactive exploration needed
- Real-time visual feedback required
- Debugging provider issues
- Learning system behavior

**Use WTH Dashboard when**:
- Lightweight monitoring preferred
- Shell-based workflow
- Terminal multiplexer integration (tmux/screen)
- Low resource overhead critical
- Scripting/automation needed

**Use Both**:
- WTH for persistent monitoring in tmux pane
- Textual for deep-dive troubleshooting sessions

---

### Monitoring Checklist

**Initial Setup**:
- [ ] Install dashboard dependencies
- [ ] Configure environment variables
- [ ] Verify LiteLLM accessibility
- [ ] Test dashboard launch
- [ ] Validate metrics collection

**Daily Operations**:
- [ ] Check provider health indicators
- [ ] Review cache performance
- [ ] Monitor request latency (P95/P99)
- [ ] Verify fallback chains active
- [ ] Check for error spikes

**Performance Analysis**:
- [ ] Compare provider latencies
- [ ] Analyze routing distribution
- [ ] Review cache hit rates
- [ ] Identify slow models
- [ ] Validate load balancing

**Incident Response**:
- [ ] Launch dashboard for real-time view
- [ ] Check provider health status
- [ ] Review recent logs
- [ ] Verify fallback activation
- [ ] Document anomalies

---

## Checklist Templates

### New Provider Checklist
- [ ] Provider accessible via HTTP
- [ ] Added to providers.yaml
- [ ] Routing rules in model-mappings.yaml
- [ ] Configuration validated
- [ ] Config applied and LiteLLM restarted
- [ ] Model availability verified
- [ ] Completion test successful
- [ ] Serena memory updated
- [ ] Documentation updated

### Configuration Change Checklist
- [ ] Backup current configuration
- [ ] Changes made to config files
- [ ] Validation passed (`validate-config-schema.py`)
- [ ] Configuration applied
- [ ] Service restarted successfully
- [ ] Verification tests passed
- [ ] Performance monitored for 30 minutes
- [ ] Rollback plan documented
- [ ] Changes committed to git

### Rollback Checklist
- [ ] Issue documented with timestamp and reason
- [ ] Service stopped
- [ ] Configuration restored from backup/git
- [ ] Service restarted
- [ ] Basic functionality verified
- [ ] Full validation run
- [ ] Incident log updated
- [ ] Root cause analysis scheduled
