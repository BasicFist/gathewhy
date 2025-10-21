# Prometheus Metrics Limitation

**Status**: ⚠️ **Enterprise Feature Required**

## Issue Discovery

During Phase 2 observability setup (2025-10-21), we discovered that **Prometheus metrics are an enterprise-only feature** in LiteLLM.

### Error Message
```
WARNING: Prometheus metrics are only available for premium users.
You must be a LiteLLM Enterprise user to use this feature.
If you have a license please set `LITELLM_LICENSE` in your env.
```

### Technical Details

- **Feature**: `callbacks: ["prometheus"]` and `/metrics` endpoint
- **Requirement**: Paid LiteLLM Enterprise license
- **Free Version**: Metrics callbacks fail silently, no `/metrics` endpoint exposed
- **License Info**: https://www.litellm.ai/#pricing
- **Free Trial**: 7-day trial available at https://www.litellm.ai/enterprise#trial

## Impact on Phase 2 Observability

### ✅ Working Components
- Docker Compose stack (Prometheus + Grafana + Redis)
- Grafana web UI accessible at http://localhost:3001
- Dashboard JSON files structurally valid
- Redis caching operational
- LiteLLM health checks functional

### ❌ Blocked Components
- Prometheus scraping (no `/metrics` endpoint without license)
- Grafana dashboards (no data source)
- All 5 pre-built dashboards (require Prometheus metrics):
  - 01-overview.json
  - 02-tokens.json
  - 03-performance.json
  - 04-provider-health.json
  - 05-system-health.json

## Configuration Issues Discovered

Beyond the license requirement, the unified config had several issues:

### 1. Invalid Metric Names
Config referenced metrics that don't exist in LiteLLM:
```yaml
litellm_redis_latency  # ❌ Invalid
litellm_redis_fails    # ❌ Invalid
litellm_self_latency   # ❌ Invalid
```

Valid metric names are documented in LiteLLM logs on startup.

### 2. Invalid Metric Labels
Config used labels not supported by LiteLLM metrics:
```yaml
# ❌ Invalid for token metrics
- "api_provider"

# ❌ Invalid for request metrics
- "model_group"
- "status_code"
```

Valid labels are metric-specific. See startup logs for authoritative list.

### 3. Duplicate `litellm_settings:` Sections
The unified config had two `litellm_settings:` blocks:
- First block: Cache, timeout, basic settings
- Second block: Prometheus callbacks

In YAML, duplicate keys cause the second to override the first, losing critical settings.

## Alternative Monitoring Approaches

Since Prometheus metrics require enterprise license, consider these alternatives:

### Option 1: Structured JSON Logs
**Status**: ✅ Already enabled

LiteLLM already produces JSON-structured logs with:
- Request/response details
- Token usage
- Latency timings
- Provider information

**Access**:
```bash
journalctl --user -u litellm.service -f --output=json-pretty
```

**Advantages**:
- Free, no license required
- Rich structured data
- Can be parsed and aggregated with tools like jq, Loki, or ELK stack

**Example log entry**:
```json
{
  "timestamp": "2025-10-21T12:26:24.123",
  "level": "INFO",
  "model": "llama3.1:8b",
  "provider": "ollama",
  "latency_ms": 5184,
  "tokens": {"prompt": 21, "completion": 20, "total": 41}
}
```

### Option 2: LiteLLM Database Analytics
**Status**: ⚠️ Requires setup

LiteLLM supports logging to PostgreSQL for analytics:
```yaml
litellm_settings:
  database_url: "postgresql://user:pass@localhost/litellm"
  store_model_in_db: true
```

**Advantages**:
- SQL-queryable request history
- Built-in analytics tables
- No external dependencies

**Query Example**:
```sql
SELECT model, COUNT(*), AVG(response_time_ms)
FROM litellm_requests
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY model;
```

### Option 3: Custom Callback for Metrics Export
**Status**: 💡 Possible workaround

Write a custom LiteLLM callback to export metrics:
```python
# custom_prometheus_callback.py
from litellm.integrations.custom_logger import CustomLogger
from prometheus_client import Counter, Histogram, start_http_server

class CustomPrometheusLogger(CustomLogger):
    def __init__(self):
        self.requests = Counter('litellm_requests_total', 'Total requests', ['model', 'provider'])
        self.latency = Histogram('litellm_latency_seconds', 'Request latency', ['model'])
        start_http_server(9090)  # Expose metrics on :9090

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        model = kwargs.get('model')
        provider = kwargs.get('litellm_params', {}).get('custom_llm_provider', 'unknown')
        latency = end_time - start_time

        self.requests.labels(model=model, provider=provider).inc()
        self.latency.labels(model=model).observe(latency)
```

**Enable in config**:
```yaml
litellm_settings:
  success_callback: ["custom_prometheus_callback"]
```

**Advantages**:
- Free, open-source
- Full control over metrics
- Works with existing Grafana/Prometheus stack

**Disadvantages**:
- Requires custom code maintenance
- May not match LiteLLM enterprise metrics exactly

### Option 4: Health Check Monitoring
**Status**: ✅ Already working

LiteLLM exposes `/health` endpoint with provider status:
```bash
curl http://localhost:4000/health | jq
```

**Prometheus scrape config**:
```yaml
- job_name: 'litellm-health'
  metrics_path: /health
  scheme: http
  static_configs:
    - targets: ['localhost:4000']
  metric_relabel_configs:
    - source_labels: [healthy_count]
      target_label: __name__
      replacement: litellm_healthy_endpoints
```

This gives basic up/down monitoring without enterprise license.

## Recommendations

### Immediate Actions (No License)
1. ✅ **Use JSON logs** for debugging and manual analysis
2. ✅ **Monitor `/health` endpoint** for basic uptime tracking
3. 📋 **Document metrics requirements** in project README
4. 💡 **Consider custom callback** if metrics are critical

### With Enterprise Trial (7 days)
1. Get trial license from https://www.litellm.ai/enterprise#trial
2. Set `LITELLM_LICENSE` environment variable
3. Fix metric names and labels in unified config
4. Merge duplicate `litellm_settings:` sections
5. Test Prometheus scraping and Grafana dashboards
6. Evaluate if enterprise features justify cost

### Long-term Strategy
- **Solo dev / small scale**: JSON logs + health checks sufficient
- **Team / production**: Consider enterprise license or custom callback
- **Hybrid approach**: Basic free monitoring + enterprise trial for peak periods

## Config Restoration

Due to the enterprise requirement, the original working config was restored:
```bash
# Backup unified config
cp config/litellm-unified.yaml config/litellm-unified.yaml.enterprise-required

# Restore original
cp ../openwebui/config/litellm.yaml.backup-20251021-122303 ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

**Service status**: ✅ Running successfully with original config

## Files Status

### Created/Modified
- ✅ `monitoring/docker-compose.yml` - Prometheus + Grafana stack
- ✅ `monitoring/prometheus/prometheus.yml` - Scrape configuration
- ✅ `monitoring/grafana/provisioning/` - Datasources and dashboards
- ✅ `monitoring/grafana/dashboards/*.json` - 5 dashboard JSON files (fixed structure)
- ⚠️ `config/litellm-unified.yaml` - Has Prometheus config (requires license)

### Documentation
- ✅ `monitoring/README.md` - Setup and usage instructions
- ✅ `monitoring/PROMETHEUS-LIMITATION.md` - This file

## Testing Done

### ✅ Successful Tests
1. Docker Compose stack starts all containers
2. Grafana UI accessible and functional (automated Playwright test)
3. Dashboard JSON files structurally valid after fix
4. LiteLLM service healthy with original config
5. Redis cache operational
6. Provider health checks functional

### ❌ Blocked Tests
1. Prometheus scraping (no metrics endpoint)
2. Grafana dashboards (no data)
3. Alert rules (no metrics to alert on)

## Next Steps

1. **Decision required**: Get enterprise trial or use alternative monitoring?
2. If trial: Follow "With Enterprise Trial" recommendations above
3. If alternatives: Choose from Options 1-4 above
4. Update project README with chosen approach
5. Document observability architecture in `.serena/memories/`

## References

- LiteLLM Pricing: https://www.litellm.ai/#pricing
- Enterprise Trial: https://www.litellm.ai/enterprise#trial
- Prometheus Docs: https://prometheus.io/docs/prometheus/latest/configuration/configuration/
- Grafana Provisioning: https://grafana.com/docs/grafana/latest/administration/provisioning/
- LiteLLM Callbacks: https://docs.litellm.ai/docs/observability/custom_callback
