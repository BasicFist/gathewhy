# Monitoring & Observability

Consolidated monitoring stack for AI Backend Unified Infrastructure, providing flexible observability options for both free and enterprise use cases.

## Architecture Overview

The monitoring stack supports two modes of operation:

### Mode 1: Free Monitoring (Recommended)
```
LiteLLM :4000
    ↓ (JSON logs)
/var/log/litellm/requests.log
    ↓ (analysis)
Debugging Tools
    ↓ (optional)
Grafana :3000 (visualization)
```

### Mode 2: Enterprise Monitoring
```
LiteLLM :4000
    ↓ (metrics endpoint)
Prometheus :9090
    ↓
Grafana :3000 (visualization)
```

## Components

| Component | Purpose | Port | Status |
|-----------|---------|------|--------|
| **LiteLLM** | Core gateway with JSON logging | 4000 | ✅ Active |
| **Prometheus** | Metrics collection (enterprise) | 9090 | ⚠️ Optional |
| **Grafana** | Visualization dashboards | 3000 | ✅ Available |
| **Debug Tools** | Log analysis & monitoring | N/A | ✅ Available |

## Quick Start

### Option 1: Free Monitoring (Default)

```bash
# 1. JSON logs are already configured in LiteLLM
# 2. View logs in real-time
./scripts/debugging/tail-requests.py

# 3. Analyze logs offline
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log

# 4. Start Grafana for manual visualization
cd monitoring
docker compose --profile grafana up -d
# Access: http://localhost:3000 (admin/admin)
```

### Option 2: Enterprise Monitoring

```bash
# 1. Set LiteLLM Enterprise license
export LITELLM_LICENSE="your-enterprise-key"

# 2. Start full monitoring stack
cd monitoring
docker compose --profile enterprise up -d
# Access: http://localhost:3000 (admin/admin)
# Access: http://localhost:9090 (Prometheus)
```

## Configuration Files

### LiteLLM Logging (config/litellm-unified.yaml)
```yaml
litellm_settings:
  logging:
    level: "INFO"
    log_format: "json"
    log_file: "/var/log/litellm/requests.log"
    log_requests: true
    log_responses: true
    log_slow_requests: true
    slow_request_threshold_ms: 5000

  tracing:
    enabled: true
    generate_request_id: true
    include_request_id_in_response: true
    sampling_rate: 1.0
```

### Prometheus Configuration (monitoring/prometheus/prometheus.yml)
```yaml
global:
  scrape_interval: 10s
  evaluation_interval: 10s

scrape_configs:
  - job_name: 'litellm'
    static_configs:
      - targets: ['localhost:4000']
    metrics_path: /metrics
    scrape_interval: 10s
    scrape_timeout: 5s
```

### Grafana Dashboards
Located in `monitoring/grafana/dashboards/`:
- `01-overview.json` - System health and request rates
- `02-tokens.json` - Token usage and cost tracking
- `03-performance.json` - Latency analysis and provider comparison
- `04-provider-health.json` - Provider reliability metrics
- `05-system-health.json` - Infrastructure health monitoring

## Available Tools

### Debugging Tools (scripts/debugging/)

#### tail-requests.py
Real-time log monitoring with filtering:
```bash
./scripts/debugging/tail-requests.py              # All requests
./scripts/debugging/tail-requests.py --model llama3.1:8b  # Filter by model
./scripts/debugging/tail-requests.py --level ERROR        # Errors only
```

#### analyze-logs.py
Offline log analysis for insights:
```bash
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log
./scripts/debugging/analyze-logs.py --errors            # Error patterns
./scripts/debugging/analyze-logs.py --performance       # Performance stats
```

#### test-request.py
Test requests with detailed debugging:
```bash
./scripts/debugging/test-request.py --model llama3.1:8b
./scripts/debugging/test-request.py --test-routing
```

### Performance Tools (scripts/profiling/)

#### profile-latency.py
Measure end-to-end latency:
```bash
./scripts/profiling/profile-latency.py --model llama3.1:8b
./scripts/profiling/profile-latency.py --export results.json
```

#### profile-throughput.py
Measure concurrent capacity:
```bash
./scripts/profiling/profile-throughput.py --sweep
./scripts/profiling/profile-throughput.py --requests 100 --concurrency 10
```

#### compare-providers.py
Side-by-side benchmarking:
```bash
./scripts/profiling/compare-providers.py
./scripts/profiling/compare-providers.py --models llama3.1:8b qwen-coder
```

### Load Testing (scripts/loadtesting/)

#### Locust (Python-based)
Interactive load testing:
```bash
cd scripts/loadtesting/locust
locust -f litellm_locustfile.py --host http://localhost:4000
# Open http://localhost:8089 for web interface
```

#### k6 (JavaScript-based)
High-performance load testing:
```bash
cd scripts/loadtesting/k6
k6 run smoke-test.js                    # Quick validation
k6 run litellm-load-test.js             # Full load test
```

## Usage Patterns

### Development Monitoring
```bash
# 1. Quick health check
curl http://localhost:4000/health

# 2. Monitor active requests
./scripts/debugging/tail-requests.py

# 3. Profile specific model
./scripts/profiling/profile-latency.py --model qwen-coder-vllm

# 4. Test with AI Dashboard
./scripts/ai-dashboard
```

### Production Monitoring
```bash
# 1. Continuous log analysis
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log --since "1 hour ago"

# 2. Performance comparison
./scripts/profiling/compare-providers.py --iterations 20

# 3. Load testing for capacity planning
cd scripts/loadtesting/k6
k6 run --vus 50 --duration 10m litellm-load-test.js

# 4. Monitor with AI Dashboard
./scripts/ai-dashboard
```

### Troubleshooting
```bash
# 1. Check all services
./scripts/validate-unified-backend.sh

# 2. Analyze recent errors
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log --errors

# 3. Test specific endpoint
./scripts/debugging/test-request.py --model problematic-model

# 4. Check configuration
./scripts/validate-config-schema.py
```

## Data Sources

### Free Monitoring Data
1. **LiteLLM JSON Logs**:
   - Request/response details
   - Token usage counts
   - Latency measurements
   - Error information
   - Provider routing

2. **Health Endpoints**:
   - LiteLLM: `http://localhost:4000/health`
   - Ollama: `http://localhost:11434/api/tags`
   - vLLM: `http://localhost:8001/v1/models`

### Enterprise Monitoring Data
1. **Prometheus Metrics**:
   - `litellm_requests_total` - Request count
   - `litellm_latency_seconds` - Response latency
   - `litellm_tokens_total` - Token usage
   - `litellm_cache_hits` - Cache performance

2. **Custom Callbacks**:
   - Request tracing
   - Custom metrics
   - Error tracking

## Decision Matrix

| Feature | Free Setup | Enterprise |
|---------|------------|------------|
| JSON Logs | ✅ Rich data | ✅ Rich data |
| Prometheus Metrics | ❌ Blocked | ✅ Available |
| Grafana Dashboards | ⚠️ Manual | ✅ Automated |
| Real-time Monitoring | ✅ Via tools | ✅ Both |
| Historical Analysis | ✅ Log parsing | ✅ Metrics |
| Custom Metrics | ❌ Custom code | ✅ Available |
| Cost | $0 | License fee |

## Migration Guide

### From Free to Enterprise
```bash
# 1. Backup current configuration
cp config/litellm-unified.yaml config/litellm-unified.yaml.backup

# 2. Set license
export LITELLM_LICENSE="your-enterprise-key"

# 3. Update LiteLLM config (add metrics)
# Add litellm_settings.callbacks: ["prometheus"]

# 4. Restart services
systemctl --user restart litellm.service
cd monitoring && docker compose --profile enterprise up -d
```

### From Enterprise to Free
```bash
# 1. Remove Prometheus callbacks from config
# Edit config/litellm-unified.yaml

# 2. Restart LiteLLM
systemctl --user restart litellm.service

# 3. Keep Grafana running for visualization
cd monitoring && docker compose --profile grafana up -d
```

## Best Practices

### Log Analysis
- Use structured JSON parsing with `jq`
- Filter by time ranges for trend analysis
- Correlate errors with request patterns
- Monitor token usage for cost optimization

### Performance Monitoring
- Profile under realistic load conditions
- Monitor P95 latency, not just averages
- Track error rates over time
- Compare provider performance regularly

### Production Deployment
- Use enterprise license for automated metrics
- Set up alerting based on metrics thresholds
- Implement log aggregation for long-term storage
- Regular backup of monitoring configuration

## Troubleshooting

### Grafana Not Showing Data
1. Check Prometheus: `curl http://localhost:9090/api/v1/targets`
2. Verify LiteLLM metrics: `curl http://localhost:4000/metrics`
3. Check Grafana datasource configuration
4. Review Grafana dashboard JSON structure

### Logs Not Appearing
1. Verify log file exists: `ls -la /var/log/litellm/`
2. Check LiteLLM logging configuration
3. Restart LiteLLM service
4. Review journalctl logs: `journalctl --user -u litellm.service -f`

### Performance Issues
1. Profile with latency script
2. Check provider health individually
3. Monitor resource usage
4. Review request patterns for bottlenecks

## Support

- **LiteLLM Documentation**: https://docs.litellm.ai/
- **Grafana Documentation**: https://grafana.com/docs/
- **Prometheus Documentation**: https://prometheus.io/docs/
- **Project Documentation**: See `docs/` directory

## File Structure

```
monitoring/
├── README.md                    # This file
├── docker-compose.yml            # Multi-profile container orchestration
├── prometheus.yml              # Prometheus scraping configuration
├── grafana/                    # Grafana configuration
│   ├── datasources/
│   │   └── prometheus.yml
│   └── dashboards/
│       ├── 01-overview.json
│       ├── 02-tokens.json
│       ├── 03-performance.json
│       ├── 04-provider-health.json
│       └── 05-system-health.json
├── systemd/                    # Service definitions (optional)
│   ├── grafana.service
│   ├── prometheus.service
│   └── promtail.service
└── PROMETHEUS-LIMITATION.md   # Enterprise license requirements
```
