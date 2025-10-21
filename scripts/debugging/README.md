# LiteLLM Debugging Utilities

Tools for debugging and monitoring LiteLLM unified backend requests.

## Prerequisites

```bash
pip install requests  # For test-request.py
```

## Available Tools

### 1. analyze-logs.py - Offline Log Analysis

Analyzes JSON-formatted LiteLLM logs for errors, performance issues, and usage patterns.

**Usage:**
```bash
# Analyze all aspects (errors + performance + usage)
./analyze-logs.py /var/log/litellm/requests.log

# Analyze specific aspects
./analyze-logs.py /var/log/litellm/requests.log --errors       # Errors only
./analyze-logs.py /var/log/litellm/requests.log --performance  # Performance only
./analyze-logs.py /var/log/litellm/requests.log --usage        # Usage only

# Trace specific request
./analyze-logs.py /var/log/litellm/requests.log --trace abc123def456
```

**Output:**
- Error patterns and frequencies
- Latency statistics (avg, p50, p95, p99)
- Token usage by model and provider
- Slow request identification (>5s)

**Example:**
```bash
./analyze-logs.py /var/log/litellm/requests.log

🚨 ERRORS (5 total)
Most common errors:
    3x Connection timeout to provider
    2x Rate limit exceeded

⚡ PERFORMANCE (127 requests)
Overall latency:
  Average: 1250 ms
  P50:     890 ms
  P95:     4500 ms
  P99:     8200 ms

📊 USAGE (127 total requests)
Total tokens: 45,230
Requests by model:
   45x     15,340 tokens (avg   341)  llama3.1:8b
   32x     18,900 tokens (avg   591)  qwen-coder-vllm
```

---

### 2. tail-requests.py - Real-time Request Monitoring

Live monitoring of LiteLLM requests with filtering and statistics.

**Usage:**
```bash
# Monitor all requests
./tail-requests.py

# Monitor specific log file
./tail-requests.py /path/to/requests.log

# Filter by model
./tail-requests.py --model llama3.1:8b

# Filter by provider
./tail-requests.py --provider ollama

# Show only errors
./tail-requests.py --level ERROR

# Show only slow requests (>5s)
./tail-requests.py --slow

# Show stats every 60 seconds
./tail-requests.py --stats-interval 60

# Combine filters
./tail-requests.py --provider vllm --slow
```

**Output:**
Real-time colored display of requests:
```
12:34:56 INFO    [a1b2c3d4] llama3.1:8b          ollama           850ms  200 Hello request
12:34:58 ERROR   [e5f6g7h8] qwen-coder-vllm     vllm            5240ms  500 Connection timeout
12:35:02 INFO    [i9j0k1l2] llama-3.1-8b-inst   llamacpp         620ms  200 Code generation

📊 Stats: 127 total | 🚨 5 errors | 🐌 3 slow (>5000ms)
```

**Tips:**
- Green = INFO, Yellow = WARNING, Red = ERROR
- Press Ctrl+C to show final stats and exit
- Use `--stats-interval 0` to disable periodic stats

---

### 3. test-request.py - Test Request Utility

Make test requests to LiteLLM with detailed debugging output.

**Usage:**
```bash
# Basic test (default model: llama3.1:8b)
./test-request.py

# Test specific model
./test-request.py --model qwen-coder-vllm --prompt "Write a Python hello world"

# Test with custom metadata (for tracking)
./test-request.py --metadata '{"project":"debug","environment":"dev"}'

# Test streaming response
./test-request.py --stream

# Test different LiteLLM instance
./test-request.py --url http://localhost:4000

# List available models
./test-request.py --list-models

# Test routing to all providers
./test-request.py --test-routing

# Verbose output (full request/response JSON)
./test-request.py -v

# Complex example
./test-request.py \
  --model llama3.1:8b \
  --prompt "Explain quantum computing in one sentence" \
  --max-tokens 50 \
  --metadata '{"project":"ai-backend","test":"latency"}' \
  -v
```

**Output:**
```
🔍 Testing LiteLLM health...
✅ LiteLLM is healthy

🚀 Testing completion request
   Model: llama3.1:8b
   Prompt: Explain quantum computing in one sentence
   Metadata: {"project":"ai-backend","test":"latency"}

📥 Response:
   Status: 200
   Time: 1250 ms
   Request ID: abc123def456

   Content: Quantum computing uses quantum mechanics principles...

   Usage:
     Prompt tokens: 12
     Completion tokens: 45
     Total tokens: 57

✅ Request successful
```

---

## Common Workflows

### Debug a slow request

1. **Identify slow requests:**
   ```bash
   ./analyze-logs.py /var/log/litellm/requests.log --performance
   ```

2. **Get request ID from slow requests list**

3. **Trace the request:**
   ```bash
   ./analyze-logs.py /var/log/litellm/requests.log --trace <request-id>
   ```

### Monitor production traffic

```bash
# Monitor errors in real-time
./tail-requests.py --level ERROR

# Monitor slow requests
./tail-requests.py --slow --stats-interval 30

# Monitor specific provider
./tail-requests.py --provider vllm
```

### Test routing configuration

```bash
# Test all provider routing
./test-request.py --test-routing

# Test specific model
./test-request.py --model qwen-coder-vllm --prompt "Test routing"
```

### Analyze daily logs

```bash
# Morning review
./analyze-logs.py /var/log/litellm/requests.log

# Focus on errors
./analyze-logs.py /var/log/litellm/requests.log --errors

# Check yesterday's performance
./analyze-logs.py /var/log/litellm/requests.log.1 --performance
```

---

## Log File Locations

Default LiteLLM log location (from config):
```
/var/log/litellm/requests.log
```

**Note:** Ensure the log directory exists and LiteLLM has write permissions:
```bash
sudo mkdir -p /var/log/litellm
sudo chown $USER:$USER /var/log/litellm
```

If you're using a different log path, update `config/litellm-unified.yaml`:
```yaml
litellm_settings:
  logging:
    log_file: "/your/custom/path/requests.log"
```

---

## Troubleshooting

### "Log file not found"
- Check if LiteLLM is running: `systemctl --user status litellm.service`
- Verify log path in config: `grep log_file config/litellm-unified.yaml`
- Check permissions: `ls -la /var/log/litellm/`

### "No log entries found"
- Ensure logging is enabled in `config/litellm-unified.yaml`
- Check log level: `logging.level` should be "INFO" or "DEBUG"
- Verify `log_requests: true` in config

### "Invalid JSON" errors
- Ensure `log_format: "json"` in config
- Check if log file has mixed formats (text + JSON)
- Look for application errors in systemd logs: `journalctl --user -u litellm.service`

---

## Integration with Prometheus/Grafana

These debugging tools complement the Prometheus/Grafana monitoring:

- **Prometheus/Grafana**: High-level metrics, dashboards, alerts
- **Log analysis**: Detailed request inspection, error patterns, specific traces
- **Real-time monitoring**: Live request flows, immediate issue detection
- **Test requests**: Validation, routing verification, integration testing

**Workflow:**
1. Grafana dashboard shows error rate spike
2. Use `tail-requests.py --level ERROR` to see errors live
3. Use `analyze-logs.py --errors` to find patterns
4. Use `analyze-logs.py --trace <request-id>` to debug specific request
5. Use `test-request.py` to reproduce and validate fix

---

## Advanced Usage

### Custom log parsing

```python
import json

with open('/var/log/litellm/requests.log') as f:
    for line in f:
        entry = json.loads(line)
        # Your custom analysis
        if entry.get('latency_ms', 0) > 10000:
            print(f"Very slow: {entry['request_id']}")
```

### Continuous monitoring script

```bash
#!/bin/bash
# monitor-loop.sh - Run continuous monitoring

while true; do
    echo "=== $(date) ==="
    ./analyze-logs.py /var/log/litellm/requests.log --errors
    sleep 300  # Every 5 minutes
done
```

### Alert on errors

```bash
#!/bin/bash
# alert-on-errors.sh

ERROR_COUNT=$(./analyze-logs.py /var/log/litellm/requests.log --errors 2>/dev/null | grep -c "ERROR")

if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "⚠️ High error count: $ERROR_COUNT errors detected!"
    # Send alert (email, Slack, etc.)
fi
```

---

## See Also

- Main documentation: `../../docs/`
- Configuration: `../../config/litellm-unified.yaml`
- Monitoring setup: `../../monitoring/`
- Validation scripts: `../validate-unified-backend.sh`
