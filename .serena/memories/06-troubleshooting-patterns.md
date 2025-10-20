# AI Backend Unified Infrastructure - Troubleshooting Patterns

**Memory Type**: Operational Knowledge
**Created**: 2025-10-20
**Last Updated**: 2025-10-20

## Common Issues and Solutions

### Issue: Provider Not Responding

**Symptoms**:
- Health check fails
- Timeout errors
- "Connection refused"

**Diagnosis**:
```bash
# Check provider directly
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/v1/models  # llama.cpp
curl http://localhost:8001/v1/models  # vLLM

# Check service status
systemctl --user status ollama.service
systemctl --user status litellm.service
```

**Solutions**:
1. Start/restart provider service
2. Check if port is already in use: `lsof -i :<port>`
3. Review provider logs: `journalctl --user -u <service> -n 50`

---

### Issue: Model Not Found

**Symptoms**:
- 404 error for model request
- Model not in `/v1/models` list

**Diagnosis**:
```bash
# List available models
curl http://localhost:4000/v1/models | jq '.data[].id'

# Check provider has model
ollama list  # For Ollama models
```

**Solutions**:
1. Pull model if missing: `ollama pull llama3.1:8b`
2. Add model to `config/litellm-unified.yaml`
3. Restart LiteLLM: `systemctl --user restart litellm.service`

---

### Issue: Slow Response Times

**Symptoms**:
- Requests take >5 seconds
- High TTFT (Time To First Token)

**Diagnosis**:
```bash
# Test response time
time curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "llama3.1:8b", "messages": [{"role": "user", "content": "Hi"}]}'

# Check provider resource usage
htop -p $(pgrep -f "ollama|llama|vllm")
```

**Solutions**:
1. Use faster provider: llama-cpp-native for speed
2. Enable Redis caching in config
3. Reduce model size (7B instead of 13B)
4. Check GPU availability: `nvidia-smi`

---

### Issue: Fallback Not Triggering

**Symptoms**:
- Request fails instead of using fallback
- No fallback chain execution in logs

**Diagnosis**:
```bash
# Check fallback configuration
cat config/litellm-unified.yaml | grep -A 10 "fallbacks:"

# Test with primary provider down
systemctl --user stop ollama.service
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "llama3.1:8b", ...}'
```

**Solutions**:
1. Verify fallback chain is configured
2. Lower `allowed_fails` threshold
3. Check logs for routing decisions
4. Ensure fallback models are available

---

### Issue: Configuration Validation Fails

**Symptoms**:
- Pydantic validation errors
- YAML syntax errors
- Pre-commit hook failures

**Diagnosis**:
```bash
# Run validation manually
python3 scripts/validate-config-schema.py

# Check YAML syntax
yamllint config/*.yaml

# Validate specific file
python3 -c "import yaml; yaml.safe_load(open('config/providers.yaml'))"
```

**Solutions**:
1. Fix syntax errors reported by yamllint
2. Ensure required fields are present
3. Validate URL formats (must start with http:// or https://)
4. Check provider references are consistent
5. Verify port numbers are 1-65535

---

### Issue: Redis Caching Not Working

**Symptoms**:
- No performance improvement on repeated queries
- Cache hit rate = 0

**Diagnosis**:
```bash
# Check Redis service
systemctl status redis
redis-cli ping

# Check cache configuration
grep -A 5 "cache:" config/litellm-unified.yaml

# Monitor cache hits
redis-cli INFO stats | grep keyspace_hits
```

**Solutions**:
1. Start Redis: `sudo systemctl start redis`
2. Enable caching in config: `cache: true`
3. Verify Redis connection settings
4. Check cache keys: `redis-cli KEYS "litellm:*"`

---

### Issue: High Memory Usage

**Symptoms**:
- System running out of RAM
- OOM killer terminating processes

**Diagnosis**:
```bash
# Check memory usage
free -h

# Check process memory
ps aux --sort=-%mem | head -10

# Check loaded models
ollama list
curl http://localhost:8001/v1/models | jq
```

**Solutions**:
1. Unload unused models
2. Use smaller/quantized models (Q4_K_M)
3. Reduce vLLM `gpu_memory_utilization`
4. Restart providers to clear memory

---

## Debugging Patterns

### Enable Debug Logging
```yaml
# In litellm-unified.yaml
debug: true
debug_router: true
set_verbose: true
```

### Trace Request Flow
```bash
# Watch logs in real-time
journalctl --user -u litellm.service -f

# Filter for specific model
journalctl --user -u litellm.service | grep "llama3.1:8b"

# Check routing decisions
journalctl --user -u litellm.service | grep "routing"
```

### Compare Provider Performance
```bash
# Test each provider
for model in "llama3.1:8b" "llama-cpp-python" "llama2-13b-vllm"; do
  echo "Testing $model..."
  time curl -s -X POST http://localhost:4000/v1/chat/completions \
    -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}" \
    > /dev/null
done
```

---

## Emergency Procedures

### Rollback Configuration
```bash
# Stop LiteLLM
systemctl --user stop litellm.service

# Restore backup
cp ../openwebui/config/litellm.yaml.backup ../openwebui/config/litellm.yaml

# Restart
systemctl --user start litellm.service

# Verify
curl http://localhost:4000/v1/models | jq
```

### Reset to Known Good State
```bash
# Restore from git
cd ai-backend-unified
git checkout config/litellm-unified.yaml

# Reapply
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

---

## Monitoring Commands

### Real-Time Monitoring
```bash
# Watch logs
journalctl --user -u litellm.service -f | grep "ERROR\|fallback\|cache"

# Monitor request rate
watch -n 1 'journalctl --user -u litellm.service --since "1 minute ago" | grep "request_routed" | wc -l'
```

### Performance Metrics
```bash
# Response time distribution
journalctl --user -u litellm.service --since "1 hour ago" | \
  grep "latency_ms" | \
  awk -F'latency_ms.: ' '{print $2}' | \
  awk '{print $1}' | \
  sort -n | \
  awk '{count++; sum+=$1} END {print "Avg:", sum/count, "ms"}'

# Cache hit rate
journalctl --user -u litellm.service --since "1 hour ago" | \
  grep "cache_hit" | \
  awk -F'cache_hit.: ' '{print $2}' | \
  awk '{print $1}' | \
  awk '{total++; if($1=="true") hits++} END {print "Hit rate:", hits/total*100 "%"}'
```

---

## Prevention Strategies

1. **Regular Health Checks**: Run `scripts/validate-unified-backend.sh` weekly
2. **Configuration Testing**: Always validate before applying: `python3 scripts/validate-config-schema.py`
3. **Gradual Rollouts**: Test routing changes with single model first
4. **Backup Before Changes**: Always create config backups
5. **Monitor Logs**: Watch for warning patterns indicating degradation
