# Error Troubleshooting Guide

Comprehensive guide to diagnosing, debugging, and resolving common errors in the AI Backend Unified Infrastructure.

## Table of Contents

1. [Diagnostic Tools](#diagnostic-tools)
2. [Configuration Errors](#configuration-errors)
3. [Provider Connection Errors](#provider-connection-errors)
4. [Routing Errors](#routing-errors)
5. [LiteLLM Gateway Errors](#litellm-gateway-errors)
6. [Cache/Redis Errors](#cacheredis-errors)
7. [Performance Issues](#performance-issues)
8. [Migration Errors](#migration-errors)
9. [Common Solutions](#common-solutions)

---

## Diagnostic Tools

### Quick Diagnostic Script

```bash
#!/bin/bash
# Run comprehensive diagnostics

echo "=== AI Backend Unified - Diagnostic Report ==="
echo "Generated: $(date)"
echo

# 1. Check configurations
echo "1. Configuration Status:"
python3 scripts/validate-config-schema.py && echo "  ✅ Schema valid" || echo "  ❌ Schema invalid"
python3 scripts/validate-config-consistency.py && echo "  ✅ Consistency OK" || echo "  ❌ Consistency issues"

# 2. Check services
echo
echo "2. Service Status:"
systemctl --user is-active litellm.service && echo "  ✅ LiteLLM running" || echo "  ❌ LiteLLM stopped"

# 3. Check providers
echo
echo "3. Provider Health:"
curl -s http://localhost:11434/api/tags >/dev/null && echo "  ✅ Ollama responsive" || echo "  ❌ Ollama unresponsive"
curl -s http://localhost:8001/v1/models >/dev/null && echo "  ✅ vLLM responsive" || echo "  ❌ vLLM unresponsive"

# 4. Check gateway
echo
echo "4. Gateway Status:"
curl -s http://localhost:4000/v1/models >/dev/null && echo "  ✅ Gateway responding" || echo "  ❌ Gateway not responding"

# 5. Check Redis (if used)
echo
echo "5. Redis Status:"
redis-cli ping >/dev/null 2>&1 && echo "  ✅ Redis responding" || echo "  ⚠️  Redis not responding (optional)"
```

### Schema Validation

```bash
# Full schema validation with details
python3 scripts/validate-config-schema.py

# Configuration consistency check
python3 scripts/validate-config-consistency.py

# Health check
python3 scripts/schema_versioning.py --health-check

# Check schema version
python3 scripts/schema_versioning.py --check-version
```

---

## Configuration Errors

### Error: YAML Parsing Error

**Symptoms:**
```
❌ providers.yaml validation failed: mapping values are not allowed here
```

**Causes:**
- Invalid YAML syntax (misaligned indentation, missing colons, incorrect quotes)
- Tabs instead of spaces (YAML requires spaces)
- Special characters not properly quoted

**Solution:**
```bash
# 1. Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config/providers.yaml'))"

# 2. Check indentation
cat -A config/providers.yaml | head -20  # Should show spaces, not tabs

# 3. Use YAML linter
yamllint config/providers.yaml

# 4. Fix common issues
# - Replace tabs with spaces: sed -i 's/\t/  /g' config/providers.yaml
# - Check quotes around special characters: "value:with:colons"
```

### Error: Schema Validation Failed

**Symptoms:**
```
❌ Model entry X missing required field 'model_name'
❌ Provider type 'unknown' not in allowed values
```

**Causes:**
- Missing required fields in configuration
- Invalid enumeration values
- Type mismatches (string vs number)

**Solution:**
```bash
# 1. Check what's required
grep -A 5 "class ModelDefinition" scripts/validate-config-schema.py

# 2. Validate specific config
python3 << 'EOF'
from scripts.validate_config_schema import LiteLLMUnifiedYAML
import yaml
with open('config/litellm-unified.yaml') as f:
    try:
        LiteLLMUnifiedYAML(**yaml.safe_load(f))
        print("✅ Valid")
    except Exception as e:
        print(f"❌ Error: {e}")
EOF

# 3. Check allowed values
grep -E "(Literal\[|enum)" scripts/validate-config-schema.py
```

### Error: Provider Not Found

**Symptoms:**
```
❌ Model 'gpt-4' routes to non-existent provider 'openai-prod'
```

**Causes:**
- Typo in provider name
- Provider not defined in providers.yaml
- Provider status is not 'active'

**Solution:**
```bash
# 1. List all providers
grep "^  [a-z].*:" config/providers.yaml

# 2. Check if provider is active
grep -A 3 "provider_name:" config/providers.yaml | grep "status:"

# 3. Fix typo in model-mappings.yaml
# Find: provider: openai-prod
# Replace: provider: openai

# 4. Revalidate
python3 scripts/validate-config-schema.py
```

---

## Provider Connection Errors

### Error: Connection Refused

**Symptoms:**
```
curl: (7) Failed to connect to localhost port 11434: Connection refused
Ollama provider health check failed
```

**Causes:**
- Provider service not running
- Wrong port number
- Network interface binding issue
- Firewall blocking connection

**Solution:**
```bash
# 1. Check if provider is running
systemctl --user status ollama.service
ps aux | grep ollama

# 2. Check port is listening
lsof -i :11434
netstat -tlnp | grep 11434

# 3. Verify correct port in config
grep "base_url" config/providers.yaml | grep 11434

# 4. Start provider
systemctl --user start ollama.service

# 5. Test connectivity
curl http://localhost:11434/api/tags
```

### Error: Timeout Connecting to Provider

**Symptoms:**
```
curl: (28) Operation timeout. Timeout was 5000 milliseconds
request timeout after 30 seconds
```

**Causes:**
- Provider overloaded or hanging
- Network latency
- Firewall rules blocking traffic
- DNS resolution issues

**Solution:**
```bash
# 1. Check provider responsiveness
time curl -s http://localhost:11434/api/tags > /dev/null

# 2. Check provider CPU/memory
ps aux | grep ollama
top -p $(pgrep ollama)

# 3. Restart provider
systemctl --user restart ollama.service

# 4. Check network latency
ping -c 3 localhost
mtr -c 5 localhost:11434

# 5. Increase timeout in litellm-unified.yaml
# router_settings:
#   timeout: 60  # Increase from 30
```

### Error: SSL Certificate Verification Failed

**Symptoms:**
```
urllib3.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
CERTIFICATE_VERIFY_FAILED certificate verify failed
```

**Causes:**
- HTTPS provider with self-signed certificate
- Certificate expired
- Certificate chain incomplete

**Solution:**
```bash
# 1. Check certificate
openssl s_client -connect localhost:8443 </dev/null

# 2. Disable SSL verification (dev only)
# litellm-unified.yaml:
# litellm_settings:
#   api_request_params:
#     verify: false

# 3. Add certificate to trusted store
cp provider-cert.pem /usr/local/share/ca-certificates/
update-ca-certificates

# 4. Use HTTP instead of HTTPS (if available)
# Change base_url: https://... to http://...
```

---

## Routing Errors

### Error: Model Not Found in Gateway

**Symptoms:**
```
curl: Model 'llama3.1:8b' not found
/v1/models response missing expected model
```

**Causes:**
- Model name mismatch in configuration
- Model not loaded in provider
- Provider not responding
- Routing configuration incomplete

**Solution:**
```bash
# 1. Check model availability in provider
curl http://localhost:11434/api/tags | jq '.models[].name'

# 2. Check model mapping
grep "llama3.1:8b" config/model-mappings.yaml

# 3. Check LiteLLM model list
python3 << 'EOF'
import yaml
with open('config/litellm-unified.yaml') as f:
    models = yaml.safe_load(f)['model_list']
    for m in models:
        if 'llama' in m['model_name']:
            print(m['model_name'])
EOF

# 4. Reload configuration
./scripts/reload-litellm-config.sh

# 5. Test through gateway
curl http://localhost:4000/v1/models | jq '.data[] | select(.id == "llama3.1:8b")'
```

### Error: Wrong Provider Selected

**Symptoms:**
```
Request to 'model-x' routed to ollama (expected vllm)
Model latency unexpectedly high
```

**Causes:**
- Model priority/routing order incorrect
- Fallback chain triggered unexpectedly
- Load balancing weights misconfigured

**Solution:**
```bash
# 1. Check exact match priority
grep -A 5 "model-x:" config/model-mappings.yaml

# 2. Check load balancing weights
grep -A 5 "load_balancing:" config/model-mappings.yaml | grep -A 3 "model-x"

# 3. Verify weights sum to 1.0
python3 << 'EOF'
import yaml
with open('config/model-mappings.yaml') as f:
    cfg = yaml.safe_load(f)
    for model, config in cfg.get('load_balancing', {}).items():
        total = sum(p.get('weight', 0) for p in config['providers'])
        print(f"{model}: {total}")
EOF

# 4. Check fallback chain
grep -B 2 -A 5 "fallback_chain:" config/model-mappings.yaml
```

### Error: Circular Fallback Chain

**Symptoms:**
```
❌ Circular fallback chain detected starting at 'model-x'
Infinite loop detected in fallback routing
```

**Causes:**
- Fallback chain references itself
- Circular references in fallback configuration
- Self-referential routing rules

**Solution:**
```bash
# 1. Identify circular reference
python3 scripts/validate-config-consistency.py

# 2. Visualize fallback chains
python3 << 'EOF'
import yaml
with open('config/model-mappings.yaml') as f:
    cfg = yaml.safe_load(f)
    for model, config in cfg.get('fallback_chains', {}).items():
        chain = config.get('chain', [])
        print(f"{model} -> {' -> '.join(chain)}")
        # Check for self-reference
        if model in chain:
            print(f"  ❌ CIRCULAR: {model} references itself")
EOF

# 3. Fix configuration
# Remove self-references from fallback chains
# Ensure chain is linear: A -> B -> C (not A -> B -> A)

# 4. Revalidate
python3 scripts/validate-config-consistency.py
```

---

## LiteLLM Gateway Errors

### Error: Gateway Not Starting

**Symptoms:**
```
systemctl status litellm.service
● litellm.service - LiteLLM Proxy Server
   Loaded: loaded (/home/user/.config/systemd/user/litellm.service)
   Active: failed (Result: exit-code) ...
```

**Causes:**
- Configuration error in litellm-unified.yaml
- Port already in use
- Missing dependencies
- Insufficient permissions

**Solution:**
```bash
# 1. Check service logs
journalctl --user -u litellm.service -n 50
journalctl --user -u litellm.service -f  # Follow mode

# 2. Validate configuration
python3 scripts/validate-config-schema.py

# 3. Check if port is available
lsof -i :4000
ss -tlnp | grep 4000

# 4. Free port if needed
sudo lsof -i :4000 -s TCP:LISTEN | awk 'NR!=1 {print $2}' | xargs kill -9

# 5. Restart service
systemctl --user restart litellm.service

# 6. Manual start for debugging
litellm --config config/litellm-unified.yaml --debug
```

### Error: Gateway Hanging/Slow Response

**Symptoms:**
```
curl http://localhost:4000/v1/models
# Takes 30+ seconds to respond
request timeout after 30 seconds
```

**Causes:**
- Provider unavailable or slow
- High memory usage
- CPU throttling
- Stuck request handler

**Solution:**
```bash
# 1. Check resource usage
ps aux | grep litellm
top -p $(pgrep -f "litellm")

# 2. Check provider responsiveness
for port in 11434 8001 8000; do
    echo "Testing port $port:"
    time curl -s http://localhost:$port/api/tags > /dev/null
done

# 3. Restart gateway
systemctl --user restart litellm.service

# 4. Check for stuck connections
netstat -tp | grep litellm
ss -tap | grep litellm

# 5. Increase timeout
# litellm_settings:
#   timeout: 60
```

### Error: Provider API Key Issues

**Symptoms:**
```
401 Unauthorized
"error": "invalid_request_error", "message": "Invalid API Key"
```

**Causes:**
- `OLLAMA_API_KEY` not exported for the service
- Provider key expired or revoked
- Direnv/systemd not loading the `.env` file
- Key rotation performed but LiteLLM not restarted

**Solution:**
```bash
# 1. Check provider secrets
echo ${OLLAMA_API_KEY:0:6}...
systemctl --user show litellm.service | grep OLLAMA

# 2. Confirm LiteLLM config references the provider key
rg "env_var: OLLAMA_API_KEY" -n config/providers.yaml

# 3. Reload environment if direnv/systemd missed it
direnv reload
systemctl --user restart litellm.service

# 4. Rotate the upstream key in your secrets store if compromised
```

---

## Cache/Redis Errors

### Error: Redis Connection Failed

**Symptoms:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
Cache disabled - Redis unavailable
```

**Causes:**
- Redis not running
- Redis port not open
- Wrong Redis configuration
- Authentication failure

**Solution:**
```bash
# 1. Check if Redis is running
redis-cli ping
ps aux | grep redis

# 2. Start Redis
systemctl start redis-server
redis-server /etc/redis/redis.conf

# 3. Check port
redis-cli -p 6379 ping

# 4. Verify configuration in litellm-unified.yaml
grep -A 5 "cache_params:" config/litellm-unified.yaml

# 5. Test connection directly
python3 << 'EOF'
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    print("✅ Redis connected:", r.ping())
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

### Error: Cache Invalidation Issues

**Symptoms:**
```
Model configuration changed but cache not updated
Old model responses returned after config change
```

**Causes:**
- Cache TTL too long
- Manual cache key mismatch
- Cache not cleared on config update
- Stale cache entries

**Solution:**
```bash
# 1. Check cache status
./scripts/monitor-redis-cache.sh

# 2. View cache keys
redis-cli KEYS "*"
redis-cli KEYS "litellm:*"

# 3. Clear specific cache
redis-cli DEL litellm:models
redis-cli FLUSHDB  # Clear all (careful!)

# 4. Monitor cache operations
redis-cli MONITOR

# 5. Reduce cache TTL
# litellm_settings:
#   cache_params:
#     ttl: 300  # 5 minutes instead of 1 hour
```

---

## Performance Issues

### Issue: High Latency

**Symptoms:**
```
TTFB (Time to First Byte): 5+ seconds
P95 latency: 10+ seconds
```

**Causes:**
- Provider is slow/overloaded
- Network latency
- Inefficient query planning
- Cache misses
- Model too large for hardware

**Solution:**
```bash
# 1. Measure baseline
curl -w "time_connect: %{time_connect}\ntime_total: %{time_total}\n" \
  http://localhost:4000/v1/models

# 2. Profile provider performance
python3 scripts/profiling/profile-latency.py

# 3. Identify bottleneck
# Gateway -> Provider: use gateway logs
# Provider processing: check provider logs
# Network: use mtr/ping

# 4. Optimize
# - Use smaller models
# - Enable caching
# - Reduce batch size
# - Allocate more GPU memory
```

### Issue: High Memory Usage

**Symptoms:**
```
top: Memory usage 80%+
OOM killer triggered
```

**Causes:**
- Large model loaded
- Memory leak in provider
- Insufficient swap
- Too many concurrent requests

**Solution:**
```bash
# 1. Check memory usage
free -h
ps aux --sort=-%mem | head

# 2. Check model size
ollama list | grep model-name
vllm stats  # if available

# 3. Reduce model size
# Use quantized version (4-bit instead of 8-bit)
# Use smaller model

# 4. Enable swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 5. Limit concurrent requests
# litellm_settings:
#   max_concurrent_requests: 2
```

### Issue: High CPU Usage

**Symptoms:**
```
top: CPU usage 90%+
top: Load average very high
```

**Causes:**
- Provider processing intensive task
- CPU throttling due to temperature
- Inefficient algorithms
- Too many concurrent requests

**Solution:**
```bash
# 1. Identify process
top -p $(pgrep ollama)
ps aux | grep -E "ollama|vllm" | grep -v grep

# 2. Check CPU frequency
cat /proc/cpuinfo | grep MHz

# 3. Monitor temperature
sensors
vcgencmd measure_temp  # Raspberry Pi

# 4. Reduce concurrency
# Set max workers/threads in provider config

# 5. Use CPU affinity
# taskset -c 0-3 ollama serve
```

---

## Migration Errors

### Error: Schema Compatibility Issue

**Symptoms:**
```
❌ Cannot migrate from v1.0 to v2.0: breaking changes detected
Migration incompatible
```

**Causes:**
- Version mismatch
- Breaking changes in schema
- Missing required fields for new version

**Solution:**
```bash
# 1. Check migration path
python3 scripts/schema_versioning.py --plan-migration v1.0 v2.0

# 2. Review migration guide
python3 scripts/schema_versioning.py --plan-migration v1.0 v2.0 | grep -A 20 "Migration Guide"

# 3. Backup current configuration
cp config/providers.yaml config/providers.yaml.backup.v1.0
cp config/model-mappings.yaml config/model-mappings.yaml.backup.v1.0

# 4. Validate before migration
python3 scripts/schema_versioning.py --validate-migration

# 5. Execute migration manually following guide
```

### Error: Migration Rollback Failed

**Symptoms:**
```
Migration failed, cannot rollback
Configuration corrupted after failed migration
```

**Causes:**
- Backup corrupted
- Incomplete backup
- Permissions issue

**Solution:**
```bash
# 1. Check backup files
ls -la config/backups/

# 2. Verify backup integrity
python3 -c "import yaml; yaml.safe_load(open('config/backups/providers.yaml.v1.0'))"

# 3. Restore from backup
cp config/backups/providers.yaml.v1.0 config/providers.yaml
cp config/backups/model-mappings.yaml.v1.0 config/model-mappings.yaml

# 4. Revalidate
python3 scripts/validate-config-schema.py

# 5. Restart services
./scripts/reload-litellm-config.sh
```

---

## Common Solutions

### Solution: Comprehensive Restart

```bash
# Full restart of all services
echo "Stopping services..."
systemctl --user stop litellm.service

echo "Restarting providers..."
systemctl --user restart ollama.service
systemctl --user restart vllm.service

echo "Clearing cache..."
redis-cli FLUSHDB

echo "Reloading configuration..."
./scripts/reload-litellm-config.sh

echo "Starting gateway..."
systemctl --user start litellm.service

echo "Running diagnostics..."
python3 scripts/validate-config-schema.py
python3 scripts/validate-config-consistency.py

echo "✅ Restart complete"
```

### Solution: Emergency Reset

```bash
# Reset to known good state
echo "WARNING: This will reset all configurations to defaults"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Restore from git
    git checkout config/providers.yaml
    git checkout config/model-mappings.yaml

    # Regenerate LiteLLM config
    python3 scripts/generate-litellm-config.py

    # Validate
    python3 scripts/validate-config-schema.py

    # Restart
    ./scripts/reload-litellm-config.sh
fi
```

### Solution: Get Help

If these solutions don't work:

1. **Gather diagnostic information:**
```bash
python3 scripts/schema_versioning.py --health-check
python3 scripts/validate-config-schema.py
python3 scripts/validate-config-consistency.py
journalctl --user -u litellm.service -n 100
```

2. **Check logs:**
```bash
cat ~/.local/share/litellm/litellm.log
tail -f /var/log/syslog | grep litellm
```

3. **Create issue report with:**
- Error message (exact text)
- Steps to reproduce
- Configuration (redacted)
- Diagnostic output
- System info (OS, CPU, memory, GPU)

---

## Quick Reference Table

| Error | Quick Fix |
|-------|-----------|
| YAML syntax error | `yamllint config/*.yaml` |
| Provider not found | Check `config/providers.yaml` for typo |
| Connection refused | `systemctl --user start ollama.service` |
| Gateway not responding | `systemctl --user restart litellm.service` |
| Model not in gateway | `./scripts/reload-litellm-config.sh` |
| High latency | Run `python3 scripts/profiling/profile-latency.py` |
| High memory | Check model size, use quantized version |
| Cache issues | `redis-cli FLUSHDB` |
| Migration failed | Restore backup: `cp config/backups/*.v1.0 config/` |

---

**For more help:** See `docs/troubleshooting.md` for operational procedures
