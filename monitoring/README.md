# Monitoring & Observability

Comprehensive monitoring stack for the AI Backend Unified Infrastructure, providing metrics collection, visualization, log aggregation, and alerting.

## Stack Overview

| Component | Purpose | Port | Status |
|-----------|---------|------|--------|
| **Prometheus** | Metrics collection and storage | 9090 | ✓ Configured |
| **Grafana** | Visualization and dashboards | 3000 | ✓ Configured |
| **Loki** | Log aggregation and storage | 3100 | ✓ Configured |
| **Promtail** | Log shipping from journald | 9080 | ✓ Configured |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Prometheus :9090                    Loki :3100                 │
│  ├─ LiteLLM :4000/metrics           ├─ Promtail :9080          │
│  ├─ Ollama :11434/metrics           │   └─ journald            │
│  ├─ llama.cpp :8000/metrics         │     ├─ litellm.service   │
│  ├─ llama.cpp :8080/metrics         │     ├─ ollama.service    │
│  ├─ vLLM :8001/metrics              │     └─ system logs       │
│  ├─ Redis :9121/metrics             │                          │
│  └─ Node :9100/metrics              │                          │
│                                                                 │
│            ↓                                  ↓                 │
│                                                                 │
│                    Grafana :3000                                │
│                    ├─ Dashboards                                │
│                    ├─ Alerts                                    │
│                    └─ Query Interface                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Automated Setup

```bash
# Install monitoring stack (downloads binaries, configures services)
cd ai-backend-unified
./scripts/setup-monitoring.sh --install-binaries

# Start services
systemctl --user enable prometheus loki promtail grafana
systemctl --user start prometheus loki promtail grafana

# Verify services
systemctl --user status prometheus
systemctl --user status grafana
```

### 2. Manual Setup

If you prefer manual installation or already have the binaries installed:

```bash
# Create directories
./scripts/setup-monitoring.sh --skip-services

# Install systemd services
mkdir -p ~/.config/systemd/user
cp monitoring/systemd/*.service ~/.config/systemd/user/
systemctl --user daemon-reload

# Start services individually
systemctl --user start prometheus
systemctl --user start loki
systemctl --user start promtail
systemctl --user start grafana
```

### 3. Access Interfaces

| Interface | URL | Default Credentials |
|-----------|-----|---------------------|
| Prometheus | http://localhost:9090 | None |
| Grafana | http://localhost:3000 | admin / admin |
| Loki | http://localhost:3100 | None |

## Prometheus Configuration

### Scrape Targets

Prometheus is configured to scrape metrics from all infrastructure components:

| Target | Endpoint | Interval | Description |
|--------|----------|----------|-------------|
| **LiteLLM** | localhost:4000/metrics | 10s | Gateway metrics (requests, latency, errors) |
| **Ollama** | localhost:11434/metrics | 15s | Ollama provider metrics |
| **llama.cpp (Python)** | localhost:8000/metrics | 15s | Python bindings metrics |
| **llama.cpp (Native)** | localhost:8080/metrics | 15s | Native server metrics |
| **vLLM** | localhost:8001/metrics | 15s | vLLM inference metrics |
| **Redis** | localhost:9121/metrics | 30s | Cache performance (via redis_exporter) |
| **Node Exporter** | localhost:9100/metrics | 30s | System metrics (CPU, memory, disk) |

### Key Metrics

**LiteLLM Gateway**:
- `litellm_requests_total` - Total requests by model and status
- `litellm_request_duration_seconds` - Request latency histogram
- `litellm_fallback_triggered_total` - Fallback chain activations
- `litellm_rate_limit_exceeded_total` - Rate limit violations
- `litellm_current_requests_per_minute` - Current RPM usage

**Provider Metrics**:
- `up` - Provider availability (1 = up, 0 = down)
- `provider_requests_total` - Provider-specific request counts
- `provider_request_duration_seconds` - Provider latency

**System Metrics**:
- `node_cpu_seconds_total` - CPU usage by mode
- `node_memory_MemAvailable_bytes` - Available memory
- `node_filesystem_avail_bytes` - Disk space

**Cache Metrics**:
- `redis_keyspace_hits_total` - Cache hits
- `redis_keyspace_misses_total` - Cache misses
- `redis_memory_used_bytes` - Memory consumption

### Alert Rules

Located in `prometheus/alerts.yml`, organized into 8 alert groups:

1. **litellm_gateway**: Gateway health and performance
2. **provider_health**: Provider availability and errors
3. **cache_performance**: Redis health and efficiency
4. **rate_limiting**: Rate limit violations and thresholds
5. **system_resources**: CPU, memory, disk utilization
6. **fallback_behavior**: Fallback chain triggers
7. **configuration**: Config reload failures
8. **custom**: Project-specific alerts

**Alert Severity Levels**:
- **critical**: Immediate action required (page on-call)
- **warning**: Investigate within 1 hour
- **info**: Review during business hours

## Grafana Dashboards

### AI Backend Unified Infrastructure Dashboard

Located in `grafana/litellm-dashboard.json`, this dashboard provides comprehensive visibility into:

**Request Metrics** (Row 1):
- Request Rate: Real-time request volume by model and status
- Response Time (P95): 95th percentile latency by model
- Error Rate: Percentage of failed requests with alerting

**Provider Health** (Row 2):
- Provider Health: UP/DOWN status for all providers
- Cache Hit Rate: Redis cache efficiency
- Rate Limit Usage: Current usage vs. thresholds

**Fallback & System** (Row 3):
- Fallback Triggers: Fallback chain activation rate
- System CPU Usage: CPU utilization by instance
- System Memory Usage: Memory consumption

**Distribution & Alerts** (Row 4):
- Request Distribution by Model: Pie chart of traffic distribution
- Active Alerts: Table of currently firing alerts

### Dashboard Import

1. Login to Grafana (http://localhost:3000)
2. Navigate to Dashboards → Import
3. Upload `monitoring/grafana/litellm-dashboard.json`
4. Select Prometheus and Loki datasources
5. Click "Import"

### Custom Dashboards

Create custom dashboards using these data sources:
- **Prometheus**: Metrics and time-series data
- **Loki**: Log queries and aggregations

## Loki Log Aggregation

### Log Sources

Promtail ships logs from systemd journald to Loki:

| Service | Unit | Labels | Features |
|---------|------|--------|----------|
| **LiteLLM** | litellm.service | job=litellm, component=api | JSON parsing, level extraction |
| **Ollama** | ollama.service | job=ollama, provider=ollama | Regex level extraction |
| **llama.cpp** | llama-cpp.service | job=llama-cpp, component=inference | Basic scraping |
| **System** | PRIORITY<=3 | job=system, component=system | Critical logs only |
| **Redis** | redis.service | job=redis, component=cache | Notice/warning/error logs |

### Log Retention

- **Default**: 15 days (360 hours)
- **Storage**: Local filesystem at `loki/data/`
- **Compression**: BoltDB shipper with compaction

### Querying Logs

**Grafana Explore**:
1. Navigate to Explore in Grafana
2. Select Loki datasource
3. Use LogQL queries:

```logql
# All LiteLLM logs
{job="litellm"}

# Error logs from LiteLLM
{job="litellm"} |= "error"

# High latency requests
{job="litellm"} | json | latency_ms > 5000

# Logs from specific model
{job="litellm", model="llama3.1:8b"}

# Count errors by level
sum by (level) (count_over_time({job="litellm"}[5m]))
```

**Command Line**:
```bash
# Query via LogCLI
logcli query '{job="litellm"}' --limit=50 --since=1h

# Stream logs in real-time
logcli query '{job="litellm"}' --tail --since=1h
```

## Common Operations

### Check Service Health

```bash
# All services
systemctl --user status prometheus grafana loki promtail

# Individual service
systemctl --user status prometheus

# View logs
journalctl --user -u prometheus -f
```

### Verify Metrics Collection

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Check LiteLLM metrics endpoint
curl http://localhost:4000/metrics

# Check scrape status
curl http://localhost:9090/api/v1/query?query=up
```

### Query Metrics

**Prometheus Web UI**: http://localhost:9090/graph

```promql
# Request rate by model
rate(litellm_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(litellm_request_duration_seconds_bucket[5m]))

# Error rate
rate(litellm_requests_total{status=~"5.."}[5m]) / rate(litellm_requests_total[5m])

# Cache hit rate
rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
```

### Restart Services

```bash
# Restart all monitoring services
systemctl --user restart prometheus grafana loki promtail

# Reload Prometheus configuration (no downtime)
curl -X POST http://localhost:9090/-/reload

# Restart only LiteLLM (to apply config changes)
systemctl --user restart litellm.service
```

## Alerting Configuration

### Alert Routing

Prometheus alerts are configured but require Alertmanager for routing to notification channels.

**Optional Alertmanager Setup**:
```yaml
# alertmanager.yml
route:
  receiver: 'team-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'team-notifications'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#alerts'
```

### Alert Suppression

Temporarily suppress alerts during maintenance:

```bash
# Silence alerts via Prometheus API
curl -X POST http://localhost:9090/api/v1/alerts \
  -d '{"matchers":[{"name":"alertname","value":"LiteLLMDown"}],"startsAt":"2024-01-20T12:00:00Z","endsAt":"2024-01-20T14:00:00Z","comment":"Maintenance window"}'
```

## Troubleshooting

### Prometheus Not Scraping

**Symptom**: Targets show as DOWN in Prometheus

**Debug**:
```bash
# Check target endpoint directly
curl http://localhost:4000/metrics

# Check Prometheus logs
journalctl --user -u prometheus -n 100

# Verify network connectivity
nc -zv localhost 4000
```

**Common Fixes**:
- Ensure LiteLLM is running: `systemctl --user status litellm.service`
- Check firewall rules (should allow localhost)
- Verify metrics endpoint in prometheus.yml

### Grafana Shows No Data

**Symptom**: Dashboard panels show "No data"

**Debug**:
```bash
# Test Prometheus datasource
curl http://localhost:9090/api/v1/query?query=up

# Check Grafana logs
journalctl --user -u grafana -n 100

# Verify datasource in Grafana
# Navigate to Configuration > Data Sources
```

**Common Fixes**:
- Verify Prometheus datasource URL (http://localhost:9090)
- Check time range in dashboard (last 1 hour minimum)
- Ensure metrics are being collected (check Prometheus targets)

### Loki Not Receiving Logs

**Symptom**: No logs appear in Grafana Explore

**Debug**:
```bash
# Check Promtail status
systemctl --user status promtail
journalctl --user -u promtail -n 50

# Test Loki API directly
curl http://localhost:3100/loki/api/v1/labels

# Check if journals are accessible
journalctl --user -u litellm.service -n 10
```

**Common Fixes**:
- Ensure journald is accessible (user must be in systemd-journal group)
- Check Promtail configuration for correct journal matches
- Verify Loki storage directory permissions

### High Memory Usage

**Symptom**: Prometheus/Loki consuming excessive memory

**Solutions**:
```bash
# Reduce Prometheus retention
# Edit monitoring/systemd/prometheus.service
# Change: --storage.tsdb.retention.time=7d

# Reduce Loki retention
# Edit monitoring/loki/loki-config.yml
# Change: retention_period: 168h

# Restart services
systemctl --user restart prometheus loki
```

### Missing Metrics

**Symptom**: Expected metrics not appearing in Prometheus

**Debug**:
1. Check if endpoint is configured in prometheus.yml
2. Verify metric naming with `curl http://localhost:4000/metrics | grep <metric_name>`
3. Check relabel configs aren't filtering metrics

## Performance Tuning

### Prometheus

```yaml
# prometheus.yml adjustments for performance
global:
  scrape_interval: 30s       # Reduce from 15s if needed
  evaluation_interval: 30s

# Storage optimization
# In systemd service:
--storage.tsdb.retention.time=7d    # Shorter retention
--storage.tsdb.retention.size=5GB   # Size limit
```

### Loki

```yaml
# loki-config.yml optimizations
limits_config:
  ingestion_rate_mb: 5         # Reduce if logs are overwhelming
  ingestion_burst_size_mb: 10

chunk_store_config:
  max_look_back_period: 168h   # Reduce from 15 days to 7
```

### Resource Limits

Systemd services include resource limits:

| Service | Memory Limit | CPU Quota |
|---------|--------------|-----------|
| Prometheus | 2GB | 200% |
| Grafana | 1GB | 100% |
| Loki | 2GB | 150% |
| Promtail | 512MB | 50% |

Adjust in `monitoring/systemd/*.service` if needed.

## Backup and Restore

### Backup Prometheus Data

```bash
# Snapshot current data
cp -r monitoring/prometheus/data monitoring/prometheus/data.backup.$(date +%Y%m%d)

# Prometheus supports API-based snapshots
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
```

### Backup Grafana Dashboards

```bash
# Export all dashboards via API
for dash in $(curl -s http://admin:admin@localhost:3000/api/search | jq -r '.[].uid'); do
  curl -s "http://admin:admin@localhost:3000/api/dashboards/uid/$dash" | jq .dashboard > "grafana-backup-${dash}.json"
done
```

### Restore from Backup

```bash
# Stop services
systemctl --user stop prometheus loki promtail grafana

# Restore data directories
cp -r monitoring/prometheus/data.backup.20241020 monitoring/prometheus/data

# Start services
systemctl --user start prometheus loki promtail grafana
```

## Security Considerations

### Network Security

- All services bind to `127.0.0.1` (localhost only)
- No external network exposure by default
- Use reverse proxy (nginx) for external access with authentication

### Grafana Security

```bash
# Change default admin password immediately
curl -X PUT -H "Content-Type: application/json" \
  -d '{"oldPassword":"admin","newPassword":"NEW_SECURE_PASSWORD","confirmNew":"NEW_SECURE_PASSWORD"}' \
  http://admin:admin@localhost:3000/api/user/password
```

### Log Scrubbing

Promtail can scrub sensitive data from logs:

```yaml
# promtail-config.yml
pipeline_stages:
  - replace:
      expression: 'password=\S+'
      replace: 'password=***'
```

## Integration with External Systems

### Datadog

Export Prometheus metrics to Datadog:

```yaml
# Install Datadog agent and configure
# /etc/datadog-agent/conf.d/prometheus.d/conf.yaml
instances:
  - prometheus_url: http://localhost:9090/metrics
    namespace: ai_backend
    metrics:
      - litellm_*
      - provider_*
```

### Splunk

Forward Loki logs to Splunk via HTTP Event Collector.

### PagerDuty

Configure Alertmanager with PagerDuty integration for critical alerts.

## Production Checklist

- [ ] All services running and healthy
- [ ] Prometheus scraping all targets successfully
- [ ] Grafana dashboards imported and displaying data
- [ ] Alert rules configured and tested
- [ ] Alertmanager configured (if using external notifications)
- [ ] Grafana admin password changed from default
- [ ] Backup automation configured
- [ ] Resource limits appropriate for workload
- [ ] Log retention configured based on storage capacity
- [ ] Monitoring documented in runbooks

## Additional Resources

- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/
- Loki: https://grafana.com/docs/loki/
- Promtail: https://grafana.com/docs/loki/latest/clients/promtail/
- PromQL: https://prometheus.io/docs/prometheus/latest/querying/basics/
- LogQL: https://grafana.com/docs/loki/latest/logql/

## Support

For issues with the monitoring stack:

1. Check service logs: `journalctl --user -u <service> -n 100`
2. Verify configurations in `monitoring/`
3. Review troubleshooting section above
4. Check GitHub issues in the project repository
