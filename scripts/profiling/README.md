# LiteLLM Performance Profiling Utilities

Tools for measuring and analyzing LiteLLM unified backend performance.

## Prerequisites

```bash
pip install requests
```

## Available Tools

### 1. profile-latency.py - Latency Analysis

Measures end-to-end request latency with detailed breakdown (TTFB, network time, token generation speed).

**Usage:**
```bash
# Basic latency profiling (default: 10 iterations + 2 warmup)
./profile-latency.py

# Profile specific model
./profile-latency.py --model qwen-coder-vllm

# Custom iterations and warmup
./profile-latency.py --model llama3.1:8b --iterations 20 --warmup 5

# Custom prompt
./profile-latency.py --prompt "Write a Python hello world"

# Export results to JSON
./profile-latency.py --export results-latency.json

# Profile different LiteLLM instance
./profile-latency.py --url http://production:4000
```

**Output:**
```
🔥 Latency Profiler
   Model: llama3.1:8b
   Prompt: Count from 1 to 10.
   Iterations: 10 (+ 2 warmup)

🏃 Warmup phase (2 requests)...
   Warmup 1: 1450ms ✅
   Warmup 2: 890ms ✅

📊 Profiling (10 requests)...
   Request  1/10:   920ms (TTFB:  250ms, Tokens:  45, Speed:  48.9 t/s) ✅
   Request  2/10:   850ms (TTFB:  230ms, Tokens:  42, Speed:  49.4 t/s) ✅
   ...

================================================================================
📈 STATISTICS
================================================================================

Success rate: 10/10 (100.0%)

⏱️  Total Latency:
   Mean    :   875.50
   Median  :   870.00
   Std Dev :    45.20
   Min     :   820.00
   Max     :   950.00
   P50     :   870.00
   P90     :   930.00
   P95     :   945.00
   P99     :   950.00

⚡ Time to First Byte (TTFB):
   Mean    :   240.30
   Median  :   235.00
   ...

🚀 Generation Speed (tokens/second):
   Mean    :    48.50
   Median  :    48.90
   ...
```

**Key Metrics:**
- **Total Latency**: End-to-end request time
- **TTFB**: Time until first response byte (includes model loading, prompt processing)
- **Network Time**: Data transfer time
- **Tokens/second**: Generation speed

---

### 2. profile-throughput.py - Throughput Testing

Measures concurrent request handling capacity and requests per second.

**Usage:**
```bash
# Basic throughput test (100 requests, 10 concurrent)
./profile-throughput.py

# Custom concurrency
./profile-throughput.py --concurrency 20

# More requests
./profile-throughput.py --requests 500 --concurrency 50

# Concurrency sweep (automatically test 1, 2, 5, 10, 20, 50 concurrent)
./profile-throughput.py --sweep --requests 50

# Profile specific model
./profile-throughput.py --model qwen-coder-vllm --sweep
```

**Output (single test):**
```
🚀 Throughput Test
   Model: llama3.1:8b
   Total requests: 100
   Concurrency: 10

   Progress:   20/100 ( 98.0% success,  12.34 req/s)
   Progress:   40/100 ( 97.5% success,  13.21 req/s)
   Progress:   60/100 ( 98.3% success,  13.85 req/s)
   Progress:   80/100 ( 98.8% success,  14.12 req/s)
   Progress:  100/100 ( 99.0% success,  14.28 req/s)

================================================================================
📊 THROUGHPUT RESULTS
================================================================================

Requests:
   Total:      100
   Successful: 99 (99.0%)
   Failed:     1 (1.0%)

Throughput:
   Duration:   7.00 seconds
   RPS:        14.29 requests/second

Latency:
   Mean:       680 ms
   Median:     650 ms
   P95:        890 ms
```

**Output (concurrency sweep):**
```
🔬 Concurrency Sweep
   Model: llama3.1:8b
   Requests per level: 50
   Concurrency levels: [1, 2, 5, 10, 20, 50]

[... individual test outputs ...]

================================================================================
📈 CONCURRENCY SWEEP SUMMARY
================================================================================

 Concurrency |      RPS |  Median Latency |  Success Rate
--------------------------------------------------------------------------------
           1 |     5.23 |          190 ms |       100.0%
           2 |    10.15 |          195 ms |       100.0%
           5 |    22.45 |          220 ms |       100.0%
          10 |    38.20 |          260 ms |        98.0%
          20 |    45.30 |          440 ms |        94.0%
          50 |    42.10 |          980 ms |        88.0%

🎯 Optimal concurrency: ~20 (45.30 req/s)
```

**Use Cases:**
- Find optimal concurrency for your hardware
- Identify performance degradation points
- Measure maximum throughput capacity
- Load testing before production deployment

---

### 3. compare-providers.py - Provider Comparison

Compare performance across different providers and models side-by-side.

**Usage:**
```bash
# Compare default models (Ollama, llama.cpp, vLLM)
./compare-providers.py

# Compare specific models
./compare-providers.py --models llama3.1:8b llama-3.1-8b-instruct qwen-coder-vllm

# Custom test prompt
./compare-providers.py --prompt "Explain Python decorators"

# More iterations for statistical confidence
./compare-providers.py --iterations 20

# Export comparison results
./compare-providers.py --export comparison-results.json

# Full example
./compare-providers.py \
  --models llama3.1:8b llama3.2:3b qwen-coder-vllm \
  --prompt "Write a quicksort function" \
  --iterations 15 \
  --export quicksort-comparison.json
```

**Output:**
```
🏁 Provider Comparison
   Models: llama3.1:8b, llama-3.1-8b-instruct, qwen-coder-vllm
   Prompt: Write a Python function to calculate factorial.
   Iterations per model: 10

🔬 Benchmarking: llama3.1:8b
   Request  1:   920ms (45 tokens, 48.9 t/s) ✅
   Request  2:   850ms (42 tokens, 49.4 t/s) ✅
   ...

🔬 Benchmarking: llama-3.1-8b-instruct
   Request  1:   650ms (48 tokens, 73.8 t/s) ✅
   Request  2:   620ms (45 tokens, 72.6 t/s) ✅
   ...

🔬 Benchmarking: qwen-coder-vllm
   Request  1:   580ms (52 tokens, 89.7 t/s) ✅
   Request  2:   560ms (50 tokens, 89.3 t/s) ✅
   ...

========================================================================================================================
📊 PROVIDER COMPARISON
========================================================================================================================

Provider     | Model                     | Success | Median (ms) | P95 (ms) | Tokens/s | Total Tokens
------------------------------------------------------------------------------------------------------------------------
vLLM         | qwen-coder-vllm          |  100.0% |         570 |      620 |     88.5 |          510
llama.cpp    | llama-3.1-8b-instruct    |  100.0% |         635 |      710 |     72.3 |          465
Ollama       | llama3.1:8b              |  100.0% |         885 |      950 |     48.9 |          430

========================================================================================================================
📈 SUMMARY
========================================================================================================================

🏆 Fastest (median latency): qwen-coder-vllm (570ms)
🐌 Slowest (median latency): llama3.1:8b (885ms)
🚀 Fastest generation: qwen-coder-vllm (88.5 tokens/s)

📊 Speedup (fastest vs slowest): 1.55x

📋 Provider Averages:
   Ollama      :    885 ms (median)
   llama.cpp   :    635 ms (median)
   vLLM        :    570 ms (median)
```

**Key Insights:**
- Which provider is fastest for your use case
- Token generation speed differences
- Success rate comparisons
- Latency variance across providers

---

## Common Workflows

### Benchmark a new model

```bash
# 1. Test latency characteristics
./profile-latency.py --model new-model:latest --iterations 20 --export latency-new-model.json

# 2. Find optimal concurrency
./profile-throughput.py --model new-model:latest --sweep

# 3. Compare with existing models
./compare-providers.py --models llama3.1:8b new-model:latest --iterations 15
```

### Performance regression testing

```bash
#!/bin/bash
# regression-test.sh

echo "=== Latency Regression Test ==="
./profile-latency.py --model llama3.1:8b --export baseline-latency.json

echo -e "\n=== Throughput Regression Test ==="
./profile-throughput.py --model llama3.1:8b --requests 200 --concurrency 10

# Compare with previous baseline (manual review)
```

### Provider selection for production

```bash
# Compare all providers with production-like prompts
./compare-providers.py \
  --models llama3.1:8b llama-3.1-8b-instruct qwen-coder-vllm \
  --prompt "Summarize this product review: [long text]" \
  --iterations 20 \
  --export production-comparison.json

# Test optimal concurrency for selected provider
./profile-throughput.py --model selected-model --sweep
```

### Continuous performance monitoring

```bash
#!/bin/bash
# monitor-performance.sh - Run daily

DATE=$(date +%Y-%m-%d)

echo "Running daily performance benchmark: $DATE"

# Latency benchmark
./profile-latency.py --export "benchmarks/latency-$DATE.json"

# Throughput benchmark
./profile-throughput.py --requests 100 --concurrency 10

# Compare trend over time (requires analysis script)
python analyze-trend.py benchmarks/
```

---

## Performance Optimization Tips

### If latency is high:
1. Check TTFB - if high, model loading or prompt processing is slow
2. Profile with different `max_tokens` to isolate generation vs processing
3. Compare providers - vLLM often has lowest latency for larger models
4. Check system resources during profiling

### If throughput is low:
1. Run concurrency sweep to find optimal level
2. Monitor resource usage (CPU, RAM, GPU) during peak concurrency
3. Check for connection pooling issues
4. Consider horizontal scaling if single instance is maxed

### For provider selection:
1. **Ollama**: Best for quick prototyping, moderate throughput
2. **llama.cpp**: Best for single-request latency on CPU
3. **vLLM**: Best for high concurrency, production workloads

---

## Output Files

All tools support `--export <file.json>` for programmatic analysis:

```python
import json

# Analyze latency results
with open('results-latency.json') as f:
    data = json.load(f)
    measurements = data['measurements']
    summary = data['summary']

    print(f"Mean latency: {summary['mean_latency_ms']:.0f}ms")
    print(f"P95 latency: {summary['p95_latency_ms']:.0f}ms")

# Compare with baseline
baseline_p95 = 850  # ms
current_p95 = summary['p95_latency_ms']
regression = (current_p95 - baseline_p95) / baseline_p95 * 100

if regression > 10:
    print(f"⚠️ Performance regression: {regression:.1f}% slower")
```

---

## Integration with Monitoring

These profiling tools complement real-time monitoring:

**Prometheus/Grafana**: Live metrics, historical trends, alerting
**Profiling scripts**: Detailed analysis, comparisons, benchmarking

**Workflow:**
1. Grafana shows latency increase
2. Run `profile-latency.py` to measure current performance
3. Run `compare-providers.py` to check if provider-specific
4. Review Grafana dashboards for correlation with traffic patterns
5. Use profiling data to set realistic alert thresholds

---

## Troubleshooting

### "Connection refused"
- Check if LiteLLM is running: `curl http://localhost:4000/health`
- Verify URL: `./profile-latency.py --url http://localhost:4000`

### High variance in results
- Increase warmup iterations: `--warmup 5`
- Increase test iterations: `--iterations 20`
- Check for background processes consuming resources

### Timeouts during profiling
- Reduce concurrency: `--concurrency 5`
- Reduce max_tokens (in script)
- Check provider health: `curl http://localhost:11434/api/tags` (Ollama)

### Different results than production
- Match production prompt patterns
- Match production concurrency levels
- Consider caching effects (disable Redis for true cold-start measurements)

---

## Advanced Usage

### Custom latency analysis

```python
#!/usr/bin/env python3
import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)

measurements = data['measurements']

# Find slowest requests
slow_requests = [m for m in measurements if m['total_ms'] > 2000]
print(f"Slow requests (>2s): {len(slow_requests)}")

# Analyze TTFB correlation
ttfb_values = [m['ttfb_ms'] for m in measurements if m['success']]
total_values = [m['total_ms'] for m in measurements if m['success']]

import statistics
correlation = statistics.correlation(ttfb_values, total_values)
print(f"TTFB correlation with total latency: {correlation:.2f}")
```

### Automated regression detection

```bash
#!/bin/bash
# detect-regression.sh

BASELINE="baseline-latency.json"
CURRENT="current-latency.json"

# Run current benchmark
./profile-latency.py --export "$CURRENT"

# Compare (requires jq)
BASELINE_P95=$(jq '.summary.p95_latency_ms' "$BASELINE")
CURRENT_P95=$(jq '.summary.p95_latency_ms' "$CURRENT")

CHANGE=$(echo "scale=2; ($CURRENT_P95 - $BASELINE_P95) / $BASELINE_P95 * 100" | bc)

echo "P95 latency change: $CHANGE%"

if (( $(echo "$CHANGE > 15" | bc -l) )); then
    echo "⚠️ REGRESSION DETECTED"
    exit 1
fi
```

---

## See Also

- Debugging tools: `../debugging/`
- Load testing: `../loadtesting/` (locust + k6 suites)
- Configuration: `../../config/litellm-unified.yaml`
- Monitoring: `../../monitoring/` (Prometheus + Grafana)
- Documentation: `../../docs/`
