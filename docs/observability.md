# LiteLLM Unified Backend Observability Guide

Complete guide to monitoring, debugging, and performance optimization for the LiteLLM unified backend.

---

## Table of Contents

1. [Overview](#overview)
2. [Monitoring Stack](#monitoring-stack)
3. [Debugging Tools](#debugging-tools)
4. [Performance Profiling](#performance-profiling)
5. [Load Testing](#load-testing)
6. [Complete Workflow Examples](#complete-workflow-examples)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The observability stack for LiteLLM unified backend consists of four integrated layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY STACK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. MONITORING (Real-time Metrics)                             │
│     • Prometheus: Metrics collection                            │
│     • Grafana: Visualization & Dashboards                       │
│     • Redis: Caching & performance metrics                      │
│                                                                  │
│  2. DEBUGGING (Request Tracing)                                │
│     • JSON logging: Structured request/response logs            │
│     • Request IDs: Distributed tracing                          │
│     • Debug utilities: Log analysis & live monitoring           │
│                                                                  │
│  3. PROFILING (Performance Analysis)                            │
│     • Latency profiling: TTFB, network, generation speed        │
│     • Throughput testing: Concurrency optimization              │
│     • Provider comparison: Performance benchmarking             │
│                                                                  │
│  4. LOAD TESTING (Capacity Planning)                            │
│     • Locust: Interactive web-based testing                     │
│     • k6: High-performance scripted testing                     │
│     • Scenarios: Gradual, spike, stress, soak tests            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Capabilities:**
- ✅ Real-time request monitoring
- ✅ Historical performance trends
- ✅ Error pattern analysis
- ✅ Provider health tracking
- ✅ Capacity planning and optimization
- ✅ Performance regression detection

---

## Monitoring Stack

### Architecture

```
LiteLLM :4000
    ↓
    └─→ /metrics endpoint (Prometheus format)
           ↓
        Prometheus :9090 (scrapes every 10s)
           ↓
        Grafana :3000 (visualizes + alerts)
```

### Quick Start

```bash
# 1. Start monitoring stack
cd monitoring
docker-compose up -d

# 2. Verify services
docker-compose ps

# 3. Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### Grafana Dashboards

Five purpose-built dashboards for comprehensive monitoring:

#### 1. Overview Dashboard
**Purpose**: At-a-glance system health
**Location**: monitoring/grafana/dashboards/01-overview.json

**Panels:**
- Request rate (req/sec)
- Error rate (%)
- Response time (P50, P95, P99)
- Active models
- Provider distribution
- Redis health
- System self-latency

**Use for**: Quick health checks, incident response

#### 2. Token Usage Dashboard
**Purpose**: Cost tracking and optimization
**Location**: monitoring/grafana/dashboards/02-tokens.json

**Panels:**
- Token rate by model
- Total tokens consumed
- Input vs output tokens
- Tokens by provider
- Cost estimation (if configured)

**Use for**: Cost monitoring, usage analytics

#### 3. Performance Dashboard
**Purpose**: Latency analysis
**Location**: monitoring/grafana/dashboards/03-performance.json

**Panels:**
- Latency comparison by provider
- P95 latency trends
- Latency heatmap
- Performance comparison table

**Use for**: Performance optimization, SLA monitoring

#### 4. Provider Health Dashboard
**Purpose**: Provider reliability
**Location**: monitoring/grafana/dashboards/04-provider-health.json

**Panels:**
- Success rate by provider (%)
- Failure rate
- Provider status summary
- Traffic distribution

**Use for**: Provider selection, failure investigation

#### 5. System Health Dashboard
**Purpose**: Infrastructure monitoring
**Location**: monitoring/grafana/dashboards/05-system-health.json

**Panels:**
- Redis latency
- Redis failures (with alerts)
- LiteLLM self-latency
- System health score
- Cache hit rate

**Use for**: Infrastructure troubleshooting, capacity planning

### Prometheus Configuration

**Metrics collected** (config/litellm-unified.yaml):

```yaml
litellm_settings:
  callbacks: ["prometheus"]
  service_callback: ["prometheus_system"]

  # 5 metric groups for organized collection:
  prometheus_metrics_config:
    - group: "token_usage"        # Token consumption
    - group: "requests"           # Request tracking
    - group: "performance"        # Latency metrics
    - group: "health"             # Deployment health
    - group: "system"             # Redis & infrastructure
```

**Scraping**: Every 10 seconds from http://localhost:4000/metrics
**Retention**: 30 days
**Storage**: Persistent volume

### Alerts (Optional Enhancement)

To add alerting, configure Grafana alert rules:

```yaml
# Example: High error rate alert
- alert: HighErrorRate
  expr: rate(litellm_proxy_failed_requests_metric[5m]) > 0.05
  for: 5m
  annotations:
    summary: "Error rate above 5% for 5 minutes"
```

---

## Debugging Tools

### Request Tracing Configuration

**Logging settings** (config/litellm-unified.yaml):

```yaml
litellm_settings:
  tracing:
    enabled: true
    generate_request_id: true
    include_request_id_in_response: true
    sampling_rate: 1.0  # 100% in dev, reduce in prod

  logging:
    level: "INFO"  # DEBUG for troubleshooting
    log_file: "/var/log/litellm/requests.log"
    log_format: "json"
    log_requests: true
    log_responses: true
    log_slow_requests: true
    slow_request_threshold_ms: 5000
```

### Debugging Utilities

Located in `scripts/debugging/`:

#### 1. analyze-logs.py

**Purpose**: Offline log analysis for errors, performance, usage

**Usage:**
```bash
# Full analysis
./analyze-logs.py /var/log/litellm/requests.log

# Errors only
./analyze-logs.py /var/log/litellm/requests.log --errors

# Performance analysis
./analyze-logs.py /var/log/litellm/requests.log --performance

# Trace specific request
./analyze-logs.py /var/log/litellm/requests.log --trace abc123def456
```

**Output**: Error patterns, latency stats, token usage, slow requests

#### 2. tail-requests.py

**Purpose**: Real-time request monitoring with filtering

**Usage:**
```bash
# Monitor all requests
./tail-requests.py

# Filter by model
./tail-requests.py --model llama3.1:8b

# Show only errors
./tail-requests.py --level ERROR

# Show slow requests only
./tail-requests.py --slow
```

**Output**: Live colored display with automatic statistics

#### 3. test-request.py

**Purpose**: Make test requests with detailed debugging

**Usage:**
```bash
# Basic test
./test-request.py

# Test specific model
./test-request.py --model qwen-coder-vllm

# Test with metadata
./test-request.py --metadata '{"project":"debug","env":"dev"}'

# Test routing to all providers
./test-request.py --test-routing

# List available models
./test-request.py --list-models
```

**Output**: Health check, request/response details, timing data

### Debugging Workflow

```bash
# Step 1: Identify issue in Grafana
# See error rate spike in Overview dashboard

# Step 2: Monitor errors live
./scripts/debugging/tail-requests.py --level ERROR

# Step 3: Analyze historical patterns
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log --errors

# Step 4: Trace specific failing request
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log --trace <request-id>

# Step 5: Test fix
./scripts/debugging/test-request.py --model <failing-model>
```

---

## Performance Profiling

### Profiling Utilities

Located in `scripts/profiling/`:

#### 1. profile-latency.py

**Purpose**: Measure end-to-end latency with breakdown

**Usage:**
```bash
# Basic latency profiling
./profile-latency.py --model llama3.1:8b

# More iterations for accuracy
./profile-latency.py --model llama3.1:8b --iterations 20 --warmup 5

# Export results
./profile-latency.py --model llama3.1:8b --export results.json
```

**Metrics:**
- Total latency (P50, P95, P99)
- Time to first byte (TTFB)
- Network time
- Token generation speed (tokens/sec)

**Use for**: Identifying latency bottlenecks, provider comparison

#### 2. profile-throughput.py

**Purpose**: Measure concurrent request capacity

**Usage:**
```bash
# Basic throughput test
./profile-throughput.py --requests 100 --concurrency 10

# Find optimal concurrency
./profile-throughput.py --sweep

# Test specific model
./profile-throughput.py --model qwen-coder-vllm --sweep
```

**Metrics:**
- Requests per second (RPS)
- Success rate at different concurrency levels
- Latency under load
- Optimal concurrency recommendation

**Use for**: Capacity planning, finding performance limits

#### 3. compare-providers.py

**Purpose**: Compare performance across providers/models

**Usage:**
```bash
# Compare default models
./compare-providers.py

# Compare specific models
./compare-providers.py --models llama3.1:8b qwen-coder-vllm

# More iterations for statistical confidence
./compare-providers.py --iterations 20 --export comparison.json
```

**Metrics:**
- Median latency by provider
- Token generation speed
- Success rates
- Speedup factors

**Use for**: Provider selection, performance optimization

### Profiling Workflow

```bash
# Step 1: Baseline latency
./scripts/profiling/profile-latency.py --export baseline-latency.json

# Step 2: Find optimal concurrency
./scripts/profiling/profile-throughput.py --sweep

# Step 3: Compare providers
./scripts/profiling/compare-providers.py --export provider-comparison.json

# Step 4: Review results
cat provider-comparison.json | jq '.results[] | {provider, model, median_latency_ms}'
```

---

## Load Testing

### Load Testing Tools

Located in `scripts/loadtesting/`:

#### Locust (Python-based, Web UI)

**Best for**: Interactive testing, complex scenarios

**Quick start:**
```bash
cd scripts/loadtesting/locust
locust -f litellm_locustfile.py --host http://localhost:4000

# Open browser: http://localhost:8089
# Configure users, spawn rate, duration
# Click "Start swarming"
```

**Headless mode:**
```bash
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --html report.html
```

**Features:**
- LiteLLMUser: Realistic traffic (60% primary model, 25% secondary, 15% specialized)
- LiteLLMStressUser: High-intensity stress testing
- Real-time web UI with graphs
- HTML reports

#### k6 (JavaScript-based, CLI)

**Best for**: CI/CD integration, high-performance testing

**Smoke test** (quick validation):
```bash
cd scripts/loadtesting/k6
k6 run smoke-test.js
```

**Full load test** (3 scenarios: gradual, spike, constant):
```bash
k6 run litellm-load-test.js
```

**Custom scenarios:**
```bash
# Only gradual load
k6 run litellm-load-test.js --scenario gradual_load

# Only spike test
k6 run litellm-load-test.js --scenario spike_test

# Custom parameters
k6 run --vus 100 --duration 5m litellm-load-test.js
```

**Features:**
- 3 built-in scenarios (gradual, spike, constant)
- Automatic threshold checking
- JSON export for CI/CD
- Detailed summary statistics

### Load Testing Scenarios

**Smoke test** (validation):
- 5 users, 30 seconds
- Verifies basic functionality

**Load test** (normal operation):
- 10-50 users, 5-10 minutes
- Simulates typical usage

**Stress test** (find limits):
- 100-500 users, 10-30 minutes
- Identifies breaking points

**Spike test** (resilience):
- Sudden 10x increase
- Tests autoscaling and recovery

**Soak test** (stability):
- Constant moderate load, hours
- Detects memory leaks

### Load Testing Workflow

```bash
# Step 1: Smoke test
k6 run scripts/loadtesting/k6/smoke-test.js

# Step 2: Gradual load test
k6 run scripts/loadtesting/k6/litellm-load-test.js --scenario gradual_load

# Step 3: Monitor in Grafana
# Open http://localhost:3000, watch dashboards during test

# Step 4: Spike test
k6 run scripts/loadtesting/k6/litellm-load-test.js --scenario spike_test

# Step 5: Analyze results
# Review console output and Grafana dashboards
```

---

## Complete Workflow Examples

### Scenario 1: New Model Performance Validation

```bash
# 1. Baseline profiling
./scripts/profiling/profile-latency.py --model new-model:latest --export baseline.json

# 2. Compare with existing models
./scripts/profiling/compare-providers.py \
  --models llama3.1:8b new-model:latest \
  --iterations 20 \
  --export comparison.json

# 3. Find optimal concurrency
./scripts/profiling/profile-throughput.py --model new-model:latest --sweep

# 4. Load test at optimal concurrency
k6 run --vus <optimal> --duration 10m scripts/loadtesting/k6/litellm-load-test.js

# 5. Review Grafana dashboards
# Check Performance and Provider Health dashboards
```

### Scenario 2: Production Issue Investigation

```bash
# 1. Check Grafana Overview dashboard
# Identify: Error rate spike at 14:30

# 2. Monitor current errors
./scripts/debugging/tail-requests.py --level ERROR

# 3. Analyze logs from incident time
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log --errors

# 4. Trace specific failing requests
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log --trace <request-id>

# 5. Test reproduction
./scripts/debugging/test-request.py --model <failing-model> -v

# 6. Verify fix with profiling
./scripts/profiling/profile-latency.py --model <failing-model>
```

### Scenario 3: Capacity Planning

```bash
# 1. Baseline current capacity
./scripts/profiling/profile-throughput.py --sweep --export current-capacity.json

# 2. Load test at target capacity
k6 run --vus <target-users> --duration 30m scripts/loadtesting/k6/litellm-load-test.js

# 3. Monitor resource usage
# Terminal 1: htop (CPU, RAM)
# Terminal 2: nvidia-smi (GPU if applicable)
# Terminal 3: Grafana dashboards

# 4. Identify bottlenecks
# Check System Health dashboard for Redis latency
# Check Performance dashboard for provider latency

# 5. Optimize configuration
# Adjust Redis settings, connection pools, concurrency limits
```

### Scenario 4: Performance Regression Detection

```bash
#!/bin/bash
# regression-test.sh (run in CI/CD)

# Run baseline profiling
./scripts/profiling/profile-latency.py --export baseline-latency.json

# Extract P95 latency
BASELINE_P95=$(jq '.summary.p95_latency_ms' baseline-latency.json)

# Compare with previous baseline
PREVIOUS_P95=$(jq '.summary.p95_latency_ms' previous-baseline.json)

# Calculate regression
CHANGE=$(echo "scale=2; ($BASELINE_P95 - $PREVIOUS_P95) / $PREVIOUS_P95 * 100" | bc)

if (( $(echo "$CHANGE > 15" | bc -l) )); then
    echo "⚠️ PERFORMANCE REGRESSION: P95 latency increased by $CHANGE%"
    exit 1
fi

echo "✅ No performance regression detected"
```

---

## Troubleshooting

### High Error Rate

**Symptoms**: Error rate > 5% in Grafana Overview dashboard

**Investigation:**
```bash
# 1. Check live errors
./scripts/debugging/tail-requests.py --level ERROR

# 2. Analyze error patterns
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log --errors

# 3. Check provider health
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/v1/models  # llama.cpp
curl http://localhost:8001/v1/models  # vLLM

# 4. Test routing
./scripts/debugging/test-request.py --test-routing
```

**Common causes**:
- Provider offline
- Model not loaded
- Network issues
- Rate limiting

### High Latency

**Symptoms**: P95 > 5s in Performance dashboard

**Investigation:**
```bash
# 1. Profile detailed latency breakdown
./scripts/profiling/profile-latency.py --model <slow-model>

# 2. Compare providers
./scripts/profiling/compare-providers.py

# 3. Check system resources
htop
nvidia-smi  # If using GPU

# 4. Review slow requests
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log --performance
```

**Common causes**:
- High TTFB: Model loading, prompt processing overhead
- High network time: Connection issues, data transfer bottleneck
- Low tokens/sec: Provider overloaded, hardware limits

### Low Throughput

**Symptoms**: Can't sustain target RPS

**Investigation:**
```bash
# 1. Find optimal concurrency
./scripts/profiling/profile-throughput.py --sweep

# 2. Load test at limits
k6 run --vus <max> --duration 5m scripts/loadtesting/k6/litellm-load-test.js

# 3. Monitor resource utilization
# CPU, RAM, GPU during peak load

# 4. Check Redis performance
# System Health dashboard → Redis latency
```

**Common causes**:
- Connection pool exhausted
- Redis bottleneck
- Provider capacity limits
- Hardware constraints

### Monitoring Stack Issues

**Prometheus not scraping:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Check LiteLLM metrics endpoint
curl http://localhost:4000/metrics

# Restart Prometheus
docker-compose restart prometheus
```

**Grafana dashboards empty:**
```bash
# Check datasource
curl http://localhost:3000/api/datasources

# Re-provision dashboards
docker-compose restart grafana

# Check dashboard files
ls -l monitoring/grafana/dashboards/
```

---

## Best Practices

### Monitoring

- ✅ Review Overview dashboard daily
- ✅ Set up alerts for error rate, latency, Redis health
- ✅ Monitor token usage for cost optimization
- ✅ Track provider health trends
- ✅ Export Grafana snapshots for incident reports

### Debugging

- ✅ Use request IDs for distributed tracing
- ✅ Keep log retention at 30+ days for trend analysis
- ✅ Use DEBUG level logging only when troubleshooting
- ✅ Tail logs during deployments
- ✅ Archive logs for major incidents

### Profiling

- ✅ Profile before and after optimizations
- ✅ Use warmup iterations to eliminate cold-start effects
- ✅ Run multiple iterations for statistical confidence
- ✅ Export results for regression tracking
- ✅ Compare providers periodically (monthly)

### Load Testing

- ✅ Always start with smoke tests
- ✅ Use gradual ramp-up, not instant load
- ✅ Monitor resources during tests
- ✅ Run soak tests before major releases
- ✅ Integrate k6 into CI/CD for regression gates

---

## Quick Reference

### Ports

| Service | Port | URL |
|---------|------|-----|
| LiteLLM | 4000 | http://localhost:4000 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |
| Locust | 8089 | http://localhost:8089 |

### Key Files

| Component | Location |
|-----------|----------|
| Prometheus config | `config/litellm-unified.yaml` (litellm_settings) |
| Grafana dashboards | `monitoring/grafana/dashboards/` |
| Debug tools | `scripts/debugging/` |
| Profiling tools | `scripts/profiling/` |
| Load testing | `scripts/loadtesting/` |
| Logs | `/var/log/litellm/requests.log` |

### Commands Summary

```bash
# Monitoring
docker-compose -f monitoring/docker-compose.yml up -d

# Debugging
./scripts/debugging/tail-requests.py
./scripts/debugging/analyze-logs.py /var/log/litellm/requests.log

# Profiling
./scripts/profiling/profile-latency.py
./scripts/profiling/profile-throughput.py --sweep
./scripts/profiling/compare-providers.py

# Load Testing
k6 run scripts/loadtesting/k6/smoke-test.js
k6 run scripts/loadtesting/k6/litellm-load-test.js
locust -f scripts/loadtesting/locust/litellm_locustfile.py
```

---

## See Also

- [Architecture Documentation](./architecture.md)
- [Adding Providers Guide](./adding-providers.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [API Integration Guide](./consuming-api.md)
