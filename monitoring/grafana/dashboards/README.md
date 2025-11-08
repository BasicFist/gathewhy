# Grafana Dashboards

Pre-configured Grafana dashboards for monitoring the AI Backend Infrastructure.

## Available Dashboards

### 1. Overview (`overview.json`)
**Purpose:** High-level health and performance metrics

**Panels:**
- Total Requests (requests/sec)
- Request Success Rate (%)
- Active Providers count
- P95 Latency
- Requests by Provider (timeseries)
- Error Rate by Provider
- Cache Hit Rate
- Model Usage Distribution
- Provider Health Status

**Best for:** Quick system health check, executive dashboards

---

### 2. Provider Performance (`provider-performance.json`)
**Purpose:** Detailed provider comparison and performance analysis

**Panels:**
- Latency Comparison (P50, P95, P99)
- Throughput by Provider
- Token Usage Rate
- Individual Provider Stats (Ollama, vLLM, llama.cpp, Ollama Cloud)
- Errors by Provider
- Fallback Activations

**Best for:** Performance tuning, identifying slow providers

---

### 3. Cache Efficiency (`cache-efficiency.json`)
**Purpose:** Redis cache monitoring and optimization

**Panels:**
- Cache Hit Rate (Overall)
- Cache Operations count
- Memory Usage
- Cache Keys Count
- Evicted Keys rate
- Cache Hit vs Miss Rate (timeseries)
- Cache Latency (P95, P99)
- Cache Size Growth
- Keys by Database
- LiteLLM Cache Savings

**Best for:** Cache tuning, cost optimization

---

## Installation

### Method 1: Manual Import

1. Open Grafana UI (http://localhost:3000)
2. Navigate to **Dashboards** → **Import**
3. Upload the JSON file or paste JSON content
4. Select Prometheus datasource
5. Click **Import**

### Method 2: Automated Provisioning

1. Copy dashboards to Grafana provisioning directory:
   ```bash
   cp monitoring/grafana/dashboards/*.json /etc/grafana/provisioning/dashboards/
   ```

2. Create provisioning config:
   ```yaml
   # /etc/grafana/provisioning/dashboards/ai-backend.yaml
   apiVersion: 1
   providers:
     - name: 'AI Backend'
       orgId: 1
       folder: 'AI Backend'
       type: file
       disableDeletion: false
       updateIntervalSeconds: 10
       options:
         path: /etc/grafana/provisioning/dashboards
   ```

3. Restart Grafana:
   ```bash
   sudo systemctl restart grafana-server
   ```

### Method 3: Docker Compose (Recommended for Development)

Already configured in `monitoring/docker-compose.yml`:
```yaml
services:
  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
```

Just run:
```bash
cd monitoring && docker compose up -d
```

---

## Required Metrics

These dashboards expect the following Prometheus metrics to be available:

### LiteLLM Metrics
- `litellm_requests_total{provider, status, model}` - Total requests counter
- `litellm_request_duration_seconds_bucket` - Request latency histogram
- `litellm_tokens_total{provider, type}` - Token usage (input/output)
- `litellm_cache_hits_total` - Cache hits
- `litellm_cache_misses_total` - Cache misses
- `litellm_fallback_activations_total{from_provider, to_provider}` - Fallback events

### Redis Metrics
- `redis_keyspace_hits_total` - Cache hits
- `redis_keyspace_misses_total` - Cache misses
- `redis_memory_used_bytes` - Memory usage
- `redis_memory_max_bytes` - Max memory
- `redis_db_keys{db}` - Keys per database
- `redis_evicted_keys_total` - Evicted keys
- `redis_commands_processed_total` - Total commands
- `redis_command_duration_seconds_bucket` - Command latency

### Provider Health
- `up{job="ai-providers"}` - Provider availability (0 or 1)

---

## Customization

### Adding New Panels

1. Edit dashboard JSON
2. Add new panel object to `panels` array
3. Specify query, visualization type, and grid position
4. Reimport dashboard

### Changing Thresholds

Edit `fieldConfig.defaults.thresholds.steps` in panel JSON:
```json
{
  "thresholds": {
    "steps": [
      {"value": 0, "color": "red"},
      {"value": 90, "color": "yellow"},
      {"value": 95, "color": "green"}
    ]
  }
}
```

### Adding Alerts

1. Open panel
2. Click **Alert** tab
3. Configure alert rule with thresholds
4. Set notification channels

---

## Troubleshooting

### Dashboard Shows "No Data"

**Possible causes:**
1. Prometheus not scraping metrics
2. LiteLLM not exposing metrics
3. Wrong datasource selected
4. Metric names don't match

**Solutions:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check available metrics
curl http://localhost:9090/api/v1/label/__name__/values

# Test LiteLLM metrics endpoint
curl http://localhost:4000/metrics
```

### Queries Showing Errors

- Verify PromQL syntax: https://prometheus.io/docs/prometheus/latest/querying/basics/
- Check metric labels match your setup
- Test query directly in Prometheus UI

### Missing Panels

- Ensure Grafana version >= 8.0
- Check browser console for errors
- Verify JSON structure is valid

---

## Dashboard Versions

- **v1.0** (2025-11-08): Initial dashboards (Overview, Provider Performance, Cache Efficiency)

---

## Contributing

To add new dashboards:

1. Create dashboard in Grafana UI
2. Export to JSON (Share → Export → Save to file)
3. Clean up JSON (remove datasource IDs, use variables)
4. Add to this directory
5. Update this README
6. Submit PR

---

## Metrics Collection Setup

If metrics aren't being collected, ensure:

1. **LiteLLM** has Prometheus enabled:
   ```yaml
   # config/litellm-unified.yaml
   server_settings:
     prometheus:
       enabled: true
       port: 4000
   ```

2. **Prometheus** is scraping LiteLLM:
   ```yaml
   # monitoring/prometheus.yml
   scrape_configs:
     - job_name: 'litellm'
       static_configs:
         - targets: ['localhost:4000']
   ```

3. **Redis Exporter** is running (if monitoring Redis):
   ```bash
   docker run -d --name redis_exporter \
     -p 9121:9121 \
     oliver006/redis_exporter \
     --redis.addr=redis://localhost:6379
   ```

---

**Last Updated:** 2025-11-08
**Maintained By:** AI Backend Infrastructure Team
