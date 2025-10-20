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
cd ../CRUSHVLLM
./crush model load huggingface/model-path
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

## Runbook: Monitoring Setup

### Enable Prometheus Metrics

**Already configured** in `litellm-unified.yaml`:
```yaml
server_settings:
  prometheus:
    enabled: true
    port: 9090
```

### Add Grafana Dashboard

**Step 1: Import dashboard**
```bash
# Use monitoring/grafana/litellm-dashboard.json (Phase 4)
```

**Step 2: Configure data source**
- Add Prometheus at `http://localhost:9090`

**Step 3: Set up alerts**
- High latency: P95 > 2s
- High error rate: > 5%
- Provider unavailability

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
