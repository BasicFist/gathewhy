# Production Deployment Checklist

Comprehensive checklist for deploying the AI Backend Unified Infrastructure to production.

## Pre-Deployment Validation

### Configuration

- [ ] All configuration files validated with Pydantic schemas
  ```bash
  python3 scripts/validate-config-schema.py
  ```

- [ ] LiteLLM configuration generated from source of truth
  ```bash
  python3 scripts/generate-litellm-config.py
  cat config/litellm-unified.yaml | head -50  # Verify generation
  ```

- [ ] Provider registry accurate and up-to-date
  ```bash
  cat config/providers.yaml | grep -A 5 "status: active"
  ```

- [ ] Model mappings tested for all active models
  ```bash
  # Verify exact matches exist for all production models
  cat config/model-mappings.yaml | grep -A 10 "exact_matches"
  ```

- [ ] Fallback chains configured and non-circular
  ```bash
  pytest -m unit tests/unit/test_routing.py::TestFallbackChains
  ```

### Testing

- [ ] All unit tests passing (>90% coverage)
  ```bash
  pytest -m unit --cov=config --cov-report=term-missing
  ```

- [ ] All contract tests passing (provider API compliance)
  ```bash
  tests/contract/test_provider_contracts.sh
  ```

- [ ] All integration tests passing (end-to-end routing)
  ```bash
  pytest -m integration
  ```

- [ ] Rollback procedures tested and validated
  ```bash
  ./scripts/test-rollback.sh
  ```

- [ ] Load testing completed (if applicable)
  ```bash
  # Example with locust or similar tool
  # locust -f tests/load/locustfile.py --host http://localhost:4000
  ```

### Security

- [ ] CORS configuration restricted appropriately
  ```bash
  # For production: ONLY allow specific origins
  grep -A 5 "cors" config/litellm-unified.yaml
  ```

- [ ] Rate limits configured per model
  ```bash
  grep -A 5 "rpm\|tpm" config/litellm-unified.yaml
  ```

- [ ] Authentication configured (optional, only for shared deployments)
  ```bash
  # Defaults rely on localhost-only exposure; front with a reverse proxy if you need authentication
  ```

- [ ] Redis password configured (if applicable)
  ```bash
  grep "redis_password" config/litellm-unified.yaml
  ```

- [ ] Sensitive data not committed to git
  ```bash
  git log --all --pretty=format: --name-only | grep -i "secret\|password\|key" | sort -u
  ```

### Infrastructure

- [ ] All provider services running and healthy
  ```bash
  ./scripts/validate-unified-backend.sh
  ```

- [ ] LiteLLM gateway accessible and responding
  ```bash
  curl http://localhost:4000/health
  curl http://localhost:4000/v1/models | jq '.data[].id'
  ```

- [ ] Redis cache running (if enabled)
  ```bash
  redis-cli ping
  redis-cli info stats | grep keyspace
  ```

- [ ] System resources sufficient for workload
  ```bash
  # Check CPU, memory, disk
  htop
  df -h
  free -h
  ```

- [ ] Network connectivity between all components verified
  ```bash
  # Test provider endpoints
  curl http://localhost:11434/api/tags
  curl http://localhost:8000/v1/models
  curl http://localhost:8001/v1/models
  ```

## Deployment Steps

### 1. Backup Current Configuration

```bash
# Create backup directory with timestamp
BACKUP_DIR="backups/pre-deployment-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup current configs
cp config/*.yaml "$BACKUP_DIR/"
cp -r .serena/memories "$BACKUP_DIR/memories"

# Backup current LiteLLM config from OpenWebUI
cp ../openwebui/config/litellm.yaml "$BACKUP_DIR/litellm-openwebui.yaml"

# Document current state
./scripts/validate-unified-backend.sh > "$BACKUP_DIR/pre-deployment-status.txt"
```

- [ ] Backup directory created: _______________
- [ ] All configurations backed up
- [ ] Current state documented

### 2. Deploy Configuration

```bash
# Generate latest configuration
python3 scripts/generate-litellm-config.py

# Copy to OpenWebUI (actual LiteLLM location)
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml

# Verify file copied correctly
diff config/litellm-unified.yaml ../openwebui/config/litellm.yaml
```

- [ ] Configuration generated successfully
- [ ] Configuration copied to OpenWebUI
- [ ] File integrity verified

### 3. Restart Services

```bash
# Restart LiteLLM gateway
systemctl --user restart litellm.service

# Wait for service to start
sleep 5

# Check service status
systemctl --user status litellm.service
```

- [ ] LiteLLM service restarted
- [ ] Service status is active (running)
- [ ] No error messages in logs

### 4. Smoke Testing

```bash
# Test health endpoint
curl http://localhost:4000/health

# List available models
curl http://localhost:4000/v1/models | jq '.data[].id'

# Test routing to Ollama
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }' | jq .

# Test routing to vLLM (if active)
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2-13b-vllm",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }' | jq .

# Test cache behavior (second request should be faster)
time curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Cache test 123"}],
    "max_tokens": 5,
    "temperature": 0
  }'

# Test fallback behavior (use invalid model with fallback chain)
# Verify fallback to secondary model occurs
```

- [ ] Health endpoint responds OK
- [ ] All expected models listed
- [ ] Routing to Ollama successful
- [ ] Routing to vLLM successful (if active)
- [ ] Cache behavior working correctly
- [ ] Fallback chain working correctly

### 5. Deploy Monitoring Stack (Optional but Recommended)

```bash
# Install monitoring stack
./scripts/setup-monitoring.sh --install-binaries

# Start monitoring services
systemctl --user enable prometheus grafana loki promtail
systemctl --user start prometheus grafana loki promtail

# Verify monitoring services
systemctl --user status prometheus
systemctl --user status grafana
systemctl --user status loki
systemctl --user status promtail

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Access Grafana
# http://localhost:3000 (admin/admin)
# Import dashboard: monitoring/grafana/litellm-dashboard.json
```

- [ ] Monitoring stack installed
- [ ] All monitoring services running
- [ ] Prometheus targets healthy
- [ ] Grafana accessible
- [ ] Dashboard imported

### Optional: WTH Terminal Dashboard

Set up the sticker-based dashboard for operators who prefer WTH/Gum:

```bash
./scripts/install-wth-dashboard.sh
export WTH_WIDGET_DIR=$HOME/.local/share/wth-widgets
wth run --config $HOME/.config/wth/wth.yaml
```

- [ ] WTH installed on jump hosts
- [ ] Widgets copied via `install-wth-dashboard.sh`
- [ ] Operators briefed on [docs/wth-dashboard.md](docs/wth-dashboard.md)

## Post-Deployment Verification

### Functional Testing

- [ ] Run comprehensive validation
  ```bash
  ./scripts/validate-unified-backend.sh
  ```

- [ ] Test all production models
  ```bash
  # Create test script for each model
  for model in $(curl -s http://localhost:4000/v1/models | jq -r '.data[].id'); do
    echo "Testing $model..."
    curl -X POST http://localhost:4000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"Test\"}], \"max_tokens\": 5}" | jq .
  done
  ```

- [ ] Verify fallback chains execute correctly
  ```bash
  # Stop secondary provider temporarily, verify fallback
  # systemctl --user stop ollama.service
  # Test request that should fallback
  # systemctl --user start ollama.service
  ```

- [ ] Test rate limiting (if configured)
  ```bash
  # Send rapid requests to trigger rate limit
  # for i in {1..100}; do curl -X POST ...; done
  ```

### Performance Validation

- [ ] Measure baseline latency (P50, P95, P99)
  ```bash
  # Use Prometheus queries or custom script
  # histogram_quantile(0.95, rate(litellm_request_duration_seconds_bucket[5m]))
  ```

- [ ] Verify cache hit rate >50% after warmup
  ```bash
  # Redis cache stats
  redis-cli info stats | grep keyspace_hits

  # Prometheus query
  # rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
  ```

- [ ] Check error rate <1%
  ```bash
  # Prometheus query
  # rate(litellm_requests_total{status=~"5.."}[5m]) / rate(litellm_requests_total[5m])
  ```

- [ ] Verify system resource utilization is acceptable
  ```bash
  # CPU <80%, Memory <85%, Disk <85%
  top -b -n 1 | head -20
  free -h
  df -h
  ```

### Monitoring & Alerting

- [ ] Prometheus scraping all targets successfully
  ```bash
  curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'
  ```

- [ ] Grafana dashboard displaying metrics correctly
  - Navigate to http://localhost:3000
  - Open "AI Backend Unified Infrastructure" dashboard
  - Verify all panels showing data

- [ ] Alert rules loaded and evaluating
  ```bash
  curl http://localhost:9090/api/v1/rules | jq '.data.groups[].name'
  ```

- [ ] Loki receiving logs from all services
  ```bash
  # Query logs via Grafana Explore or LogCLI
  # {job="litellm"} | count_over_time([5m])
  ```

- [ ] Test alert firing (optional)
  ```bash
  # Temporarily stop a provider to trigger alert
  # systemctl --user stop ollama.service
  # Wait 2 minutes, check Prometheus alerts
  # curl http://localhost:9090/api/v1/alerts
  # systemctl --user start ollama.service
  ```

### Documentation

- [ ] Update deployment notes with timestamp and changes
- [ ] Document any configuration changes made
- [ ] Update Serena memories if routing patterns changed
- [ ] Update runbook with any new procedures discovered
- [ ] Record baseline metrics for future comparison

## Rollback Procedure

If deployment fails validation:

### 1. Stop Services

```bash
systemctl --user stop litellm.service
```

### 2. Restore Configuration

```bash
# Identify backup directory
ls -ltr backups/

# Restore from backup
BACKUP_DIR="backups/pre-deployment-20241020-120000"  # Use actual backup
cp "$BACKUP_DIR/litellm-openwebui.yaml" ../openwebui/config/litellm.yaml

# Or use automated rollback
python3 scripts/generate-litellm-config.py --rollback <version>
```

### 3. Restart Services

```bash
systemctl --user start litellm.service
```

### 4. Verify Rollback

```bash
./scripts/validate-unified-backend.sh
curl http://localhost:4000/health
```

### 5. Document Failure

- [ ] Document what failed: _______________
- [ ] Root cause identified: _______________
- [ ] Corrective actions planned: _______________

## Production Monitoring

After deployment, monitor these metrics for 24-48 hours:

### Critical Metrics

- **Request Rate**: Baseline and trends
- **Error Rate**: Should be <1%
- **P95 Latency**: Should be <2s for most models
- **Provider Health**: All providers should stay UP
- **Cache Hit Rate**: Should stabilize >50%
- **System Resources**: CPU <80%, Memory <85%

### Alert Responses

**Critical Alerts**:
- LiteLLMDown → Check service status, restart if needed
- AllProvidersDown → Investigate infrastructure, check network
- FallbackChainExhausted → All providers failing, critical issue

**Warning Alerts**:
- HighErrorRate → Check provider logs, investigate specific models
- HighLatency → Check provider performance, system resources
- RateLimitViolations → Review rate limit thresholds

**Info Alerts**:
- RateLimitNearThreshold → Monitor for capacity planning
- FallbacksFrequent → Check primary provider health

## Sign-Off

Deployment completed by: _______________
Date: _______________
Version deployed: _______________

Verified by: _______________
Date: _______________

Issues encountered: _______________

Resolution: _______________

Production-ready: ☐ Yes  ☐ No  ☐ With caveats: _______________
