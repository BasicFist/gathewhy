# LiteLLM Load Testing Suite

Comprehensive load testing for LiteLLM unified backend using Locust and k6.

## Tools Overview

| Tool | Best For | Language | UI | Distributed |
|------|----------|----------|-----|-------------|
| **Locust** | Complex scenarios, iterative development | Python | Web UI | Yes |
| **k6** | High performance, CI/CD integration | JavaScript | CLI | Yes |

**Use Locust for**: Interactive testing, complex user workflows, Python ecosystem
**Use k6 for**: Performance benchmarking, CI/CD pipelines, high load simulation

---

## Prerequisites

### Locust Installation

```bash
pip install locust
```

### k6 Installation

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
# Debian/Ubuntu
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Or via snap
sudo snap install k6
```

**Verify installations:**
```bash
locust --version
k6 version
```

---

## Locust Load Testing

### Quick Start

```bash
cd scripts/loadtesting/locust

# Basic test (web UI on http://localhost:8089)
locust -f litellm_locustfile.py --host http://localhost:4000

# Open browser to http://localhost:8089
# Configure: Users, Spawn rate, Duration
# Click "Start swarming"
```

### Command-Line Options

```bash
# Headless mode (no web UI)
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless

# Specific user class
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless \
  --only-summary

# Generate HTML report
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --html report.html

# Stress test with LiteLLMStressUser
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --users 200 \
  --spawn-rate 20 \
  --run-time 3m \
  --headless \
  --users-classes LiteLLMStressUser
```

### Distributed Load Testing (Locust)

For very high load, run Locust in distributed mode:

**Master node:**
```bash
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --master
```

**Worker nodes (on same or different machines):**
```bash
# Worker 1
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --worker --master-host=localhost

# Worker 2
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --worker --master-host=localhost

# Add more workers as needed
```

### Locust Features

**LiteLLMUser** (realistic load):
- 10x weight: Standard completions
- 3x weight: Streaming requests
- 1x weight: Model listing
- 1-5 second wait between requests
- Realistic model distribution (60% primary, 25% secondary, 15% specialized)

**LiteLLMStressUser** (stress testing):
- 0.1-0.5 second wait between requests
- Minimal token generation for maximum throughput
- Tests system under extreme load

**Custom Metrics:**
- Real-time success/failure rates
- Response time percentiles
- Request distribution by model
- Detailed error tracking

---

## k6 Load Testing

### Quick Start

```bash
cd scripts/loadtesting/k6

# Smoke test (quick validation)
k6 run smoke-test.js

# Full load test
k6 run litellm-load-test.js

# Different target
k6 run --env BASE_URL=http://production:4000 litellm-load-test.js
```

### Test Scenarios

**litellm-load-test.js** includes 3 scenarios:

1. **Gradual Load** (0-10m):
   - Ramp 0→10 users (1m)
   - Hold 10 users (3m)
   - Ramp 10→50 users (1m)
   - Hold 50 users (3m)
   - Ramp 50→0 (1m)

2. **Spike Test** (10-15m):
   - Baseline 10 users (30s)
   - Spike to 100 users (10s)
   - Hold 100 users (1m)
   - Back to 10 users (30s)
   - Ramp down (30s)

3. **Constant Load** (15-20m):
   - 30 constant users for 5 minutes

**Total duration**: ~20 minutes

### Custom k6 Runs

```bash
# Quick 1-minute test
k6 run --vus 10 --duration 1m litellm-load-test.js

# Spike test only
k6 run litellm-load-test.js --scenario spike_test

# Override duration
k6 run --vus 50 --duration 5m --scenario constant_load litellm-load-test.js

# Generate JSON report
k6 run litellm-load-test.js --out json=results.json

# Cloud execution (requires k6 Cloud account)
k6 cloud litellm-load-test.js
```

### k6 Thresholds

Built-in success criteria:
- `http_req_failed < 5%` - Less than 5% failures
- `http_req_duration p(95) < 5000ms` - 95% under 5 seconds
- `errors < 5%` - Less than 5% error rate
- `completion_duration p(95) < 6000ms` - 95% completions under 6s

Test fails if ANY threshold is exceeded.

### k6 Output Formats

```bash
# JSON output (programmatic analysis)
k6 run litellm-load-test.js --out json=results.json

# InfluxDB (real-time monitoring)
k6 run litellm-load-test.js --out influxdb=http://localhost:8086/k6db

# CSV output
k6 run litellm-load-test.js --out csv=results.csv

# Multiple outputs
k6 run litellm-load-test.js \
  --out json=results.json \
  --out influxdb=http://localhost:8086/k6db
```

---

## Comparison: Locust vs k6

### When to Use Locust

✅ **Best for:**
- Interactive testing with web UI
- Complex user workflows and scenarios
- Python-based test logic
- Team members familiar with Python
- Iterative test development

**Example:**
```bash
# Start Locust web UI
locust -f litellm_locustfile.py --host http://localhost:4000

# Adjust parameters in browser, observe real-time graphs
# Export results as HTML report
```

### When to Use k6

✅ **Best for:**
- CI/CD pipeline integration
- High-performance load generation
- Scripted/automated testing
- Performance regression testing
- JavaScript/TypeScript ecosystem

**Example:**
```bash
# Automated performance gate in CI
k6 run litellm-load-test.js || exit 1

# If thresholds fail, build fails
```

### Side-by-Side Comparison

| Feature | Locust | k6 |
|---------|--------|-----|
| **Web UI** | ✅ Yes | ❌ No (CLI only) |
| **Distributed** | ✅ Master/Worker | ✅ Cloud execution |
| **Real-time graphs** | ✅ Live in browser | ⚠️ Via external tools |
| **Scripting language** | Python | JavaScript |
| **Performance** | Good (100-1000 VUs) | Excellent (10k+ VUs) |
| **CI/CD integration** | Good | Excellent |
| **Learning curve** | Low (if Python familiar) | Medium |
| **Custom metrics** | ✅ Easy | ✅ Easy |

---

## Load Testing Workflows

### 1. Pre-deployment Validation

```bash
# Step 1: Smoke test (quick validation)
k6 run smoke-test.js

# Step 2: Gradual load test
k6 run litellm-load-test.js --scenario gradual_load

# Step 3: Full test suite
k6 run litellm-load-test.js

# All must pass thresholds
```

### 2. Capacity Planning

```bash
# Use Locust for interactive exploration
locust -f litellm_locustfile.py --host http://localhost:4000

# In browser:
# - Start with 10 users
# - Gradually increase to find breaking point
# - Note when response times degrade
# - Document optimal user count
```

### 3. Performance Regression Testing

```bash
#!/bin/bash
# regression-test.sh

echo "Running baseline test..."
k6 run litellm-load-test.js --out json=baseline.json

# After code changes...
echo "Running current test..."
k6 run litellm-load-test.js --out json=current.json

# Compare (requires analysis script)
python compare-results.py baseline.json current.json
```

### 4. Stress Testing

```bash
# Locust stress test
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --users 500 \
  --spawn-rate 50 \
  --run-time 10m \
  --headless \
  --only-summary
```

### 5. Spike Testing

```bash
# k6 spike scenario
k6 run litellm-load-test.js --scenario spike_test

# Validates system handles sudden traffic surges
```

---

## Analyzing Results

### Locust Results

**Web UI** (during test):
- Real-time RPS, response times, failure rates
- Charts: Total requests, response times, users
- Download data as CSV

**HTML Report** (after test):
```bash
locust -f litellm_locustfile.py \
  --host http://localhost:4000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html report.html

# Open report.html in browser
```

**CSV Analysis**:
```python
import pandas as pd

# Load stats
stats = pd.read_csv('locust_stats.csv')

# Analyze
print(stats.groupby('Name')['Average Response Time'].mean())
print(stats.groupby('Name')['Requests/s'].sum())
```

### k6 Results

**Console output** (automatic):
- Real-time progress bar
- Final summary with all metrics
- Threshold pass/fail status

**JSON analysis**:
```javascript
// results.json contains full test data
const results = require('./results.json');

// Extract metrics
const p95 = results.metrics.http_req_duration.values['p(95)'];
const rps = results.metrics.http_reqs.values.rate;
const failRate = results.metrics.http_req_failed.values.rate;

console.log(`P95: ${p95}ms, RPS: ${rps}, Failures: ${failRate * 100}%`);
```

**InfluxDB + Grafana** (advanced):
```bash
# Send metrics to InfluxDB
k6 run litellm-load-test.js --out influxdb=http://localhost:8086/k6db

# Visualize in Grafana (import k6 dashboard)
# Real-time graphs during test execution
```

---

## Best Practices

### Test Design

1. **Start small**: Begin with smoke tests, gradually increase load
2. **Realistic scenarios**: Use actual prompts and model distributions
3. **Warmup period**: Allow system to warm up before measuring
4. **Think time**: Include realistic delays between requests
5. **Mixed workload**: Test streaming and non-streaming requests

### Load Patterns

- **Smoke test**: 5 users, 30s (validation)
- **Load test**: 10-50 users, 5-10m (typical usage)
- **Stress test**: 100-500 users, 10-30m (find limits)
- **Spike test**: Sudden 10x increase (resilience)
- **Soak test**: Constant load, hours (memory leaks)

### Monitoring During Tests

```bash
# Terminal 1: Run load test
k6 run litellm-load-test.js

# Terminal 2: Monitor logs
./scripts/debugging/tail-requests.py

# Terminal 3: System resources
htop

# Terminal 4: Grafana dashboards
# Open http://localhost:3000
```

### Success Criteria

Define clear thresholds:
- **P95 latency < 5s** (user experience)
- **Error rate < 1%** (reliability)
- **RPS > X** (capacity requirement)
- **No crashes** (stability)

---

## Troubleshooting

### High Failure Rate

```bash
# Check LiteLLM logs
journalctl --user -u litellm.service -f

# Check provider health
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/v1/models  # llama.cpp
curl http://localhost:8001/v1/models  # vLLM

# Reduce concurrency
locust --users 10  # Instead of 100
```

### Connection Timeouts

```bash
# Increase timeout in test scripts
# Locust: timeout parameter in requests
# k6: http.setResponseCallback() for custom handling

# Check connection limits
ulimit -n  # File descriptor limit
```

### Inconsistent Results

```bash
# Increase iterations for statistical significance
# Ensure no background processes
# Run warmup phase
# Check for thermal throttling (long tests)
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Load Test

on:
  push:
    branches: [main]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6

      - name: Run smoke test
        run: cd scripts/loadtesting/k6 && k6 run smoke-test.js

      - name: Run load test
        run: cd scripts/loadtesting/k6 && k6 run litellm-load-test.js

      - name: Upload results
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: load-test-results
          path: scripts/loadtesting/k6/summary.json
```

---

## See Also

- **Profiling**: `../profiling/` - Detailed performance analysis
- **Debugging**: `../debugging/` - Request tracing and logs
- **Monitoring**: `../../monitoring/` - Prometheus + Grafana
- **Configuration**: `../../config/litellm-unified.yaml`
