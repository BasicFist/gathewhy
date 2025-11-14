# AI Backend Unified - Command Reference

> All commands assume you are in the repository root with dependencies installed.

## Dashboards & Visual Monitoring

### Textual dashboard (standard)
```bash
./scripts/ai-dashboard
# or
python3 scripts/ai-dashboard
```
- Real-time provider status, request log, routing insights.
- Key bindings documented inline (`r` refresh, `a` auto-refresh, `q` quit).

### Enhanced dashboard (multi-panel)
```bash
LITELLM_GATEWAY_URL=http://localhost:4000 \
  python3 scripts/ai-dashboard-enhanced.py
```
- Connects to live LiteLLM + providers.
- Adds request inspector, performance panel, and routing breakdown.

### PTUI dashboard
```bash
python3 scripts/ptui_dashboard.py
```
- Textual CLI focused on fast status checks.
- Ideal for SSH sessions or air-gapped hosts.

### Redis and routing monitors
```bash
./scripts/monitor-redis-cache.sh --watch
./scripts/monitor-routing-v1.7.1.sh
```
- Inspect cache hit rates / keys.
- Watch routing diversity and fallback execution.

---

## Health & Validation

### Full stack validation
```bash
./scripts/validate-unified-backend.sh
```
- Runs provider health checks, smoke tests, and routing probes.

### Configuration validation bundle
```bash
./scripts/validate-all-configs.sh
python3 scripts/validate-config-consistency.py
python3 scripts/validate-config-schema.py
```
- Ensures YAML syntax, schema conformance, and providers/models stay in sync.

### Observability stack validation
```bash
./scripts/validate-observability.sh
```
- Verifies Prometheus/Grafana containers, datasources, and dashboards.

### Port + service readiness
```bash
./scripts/check-port-conflicts.sh --required
./scripts/wait-for-service.sh "LiteLLM" http://localhost:4000/health 60
```
- Confirms gateway + providers have the ports they expect.

---

## Configuration & Deployment Workflow

### Generate + back up LiteLLM config
```bash
python3 scripts/generate-litellm-config.py
python3 scripts/generate-litellm-config.py --list-backups
python3 scripts/generate-litellm-config.py --rollback 20251030_153000
```
- Creates `config/litellm-unified.yaml`, keeps timestamped backups, supports restores.

### Deploy validated configuration
```bash
./scripts/reload-litellm-config.sh --validate-only
./scripts/reload-litellm-config.sh
```
- Dry-run validates diff; full run copies config into OpenWebUI and restarts LiteLLM with backups.

### Provider/model toggles
```bash
python3 scripts/manage-providers.py list
python3 scripts/manage-providers.py enable-model llama3.1:8b
python3 scripts/manage-providers.py disable-provider ollama
```
- Quickly toggle availability without hand-editing YAML.

### Configuration audits
```bash
python3 scripts/config-audit.py --quick
python3 scripts/schema_versioning.py --check-version
```
- Security/compliance checks plus schema evolution tracking.

---

## Routing, Debugging & Profiling

### Inspect routing graphically
```bash
python3 scripts/model-routing-visualizer.py --dot --output routing.dot
```
- Generates ASCII, DOT, or JSON summaries of router decisions.

### Debug individual requests
```bash
python3 scripts/debugging/test-request.py --model llama3.1:8b
python3 scripts/debugging/test-request.py --test-routing
./scripts/debugging/tail-requests.py --level ERROR
./scripts/debugging/analyze-logs.py --last 1h --model qwen
```
- Health check, routing validation, and live/error log streaming.

### Performance profiling
```bash
python3 scripts/profiling/profile-latency.py --model qwen2.5-coder:7b
python3 scripts/profiling/profile-throughput.py --sweep --model llama3.1:8b
python3 scripts/profiling/compare-providers.py --summary
```
- Measure latency, concurrency limits, and tokens/sec per provider.

### Load testing suites
```bash
k6 run scripts/loadtesting/k6/smoke-test.js
locust -f scripts/loadtesting/locust/litellm_locustfile.py
```
- Generate synthetic traffic to validate SLOs.

---

## Monitoring Stack
```bash
./scripts/setup-monitoring.sh
cd monitoring && docker compose up -d
./scripts/test-monitoring.sh
```
- Bootstraps Prometheus + Grafana, seeds datasources, and performs verification checks.

---

## Backup & Recovery
```bash
python3 scripts/generate-litellm-config.py --list-backups
python3 scripts/generate-litellm-config.py --rollback <timestamp>
./scripts/verify-backup.sh --all
./scripts/test-backup-rotation.sh
./scripts/test-rollback.sh
```
- Enumerate backups, restore specific versions, and dry-run the full rollback workflow.

---

## Testing & Quality Gates
```bash
pytest                 # Full test suite
pytest -m unit
pytest -m "integration and not slow"
./scripts/test-monitoring.sh
```
- Match CI filters locally before committing.

---

## Service Management & Logs
```bash
systemctl --user status litellm.service
systemctl --user restart litellm.service
systemctl --user restart ollama.service
journalctl --user -u litellm.service -n 50
```
- Control services managed by systemd user units and inspect logs.

---

## Security & Access Checks
```bash
python3 scripts/config-audit.py --focus security
python3 scripts/config-audit.py --focus compliance
```
- Validates authentication settings, secret handling, and compliance controls described in `docs/security-setup.md`.
