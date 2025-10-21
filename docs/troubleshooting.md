# Troubleshooting Guide

Common issues and solutions for the unified AI backend infrastructure.

## Quick Diagnostics

Run this quick check script:

```bash
#!/bin/bash
# quick-check.sh

echo "=== Unified AI Backend Health Check ==="

# Check LiteLLM service
echo -e "\n1. LiteLLM Service:"
systemctl --user is-active litellm.service && echo "✅ Running" || echo "❌ Not running"

# Check providers
echo -e "\n2. Provider Health:"
curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama" || echo "❌ Ollama"
curl -s http://localhost:8000/v1/models > /dev/null && echo "✅ llama.cpp Python" || echo "❌ llama.cpp Python"
curl -s http://localhost:8080/v1/models > /dev/null && echo "✅ llama.cpp Native" || echo "❌ llama.cpp Native"
curl -s http://localhost:8001/v1/models > /dev/null && echo "✅ vLLM" || echo "❌ vLLM"

# Check LiteLLM endpoint
echo -e "\n3. LiteLLM Endpoint:"
curl -s http://localhost:4000/v1/models > /dev/null && echo "✅ Accessible" || echo "❌ Not accessible"

# Check model count
echo -e "\n4. Available Models:"
model_count=$(curl -s http://localhost:4000/v1/models | jq '.data | length')
echo "   $model_count models available"

echo -e "\n=== End Health Check ==="
```

## Common Issues

### Issue: LiteLLM Service Not Running

**Symptoms**:
- `curl http://localhost:4000/v1/models` fails
- "Connection refused" errors

**Diagnosis**:
```bash
systemctl --user status litellm.service
```

**Solutions**:

1. **Service not started**:
```bash
systemctl --user start litellm.service
```

2. **Service failed to start**:
```bash
# Check logs
journalctl --user -u litellm.service -n 50

# Common causes:
# - Configuration syntax error
# - Port 4000 already in use
# - Missing dependencies
```

3. **Configuration error**:
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('../openwebui/config/litellm.yaml'))"

# If errors, restore backup
cp ../openwebui/config/litellm.yaml.backup ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

4. **Port conflict**:
```bash
# Check what's using port 4000
sudo lsof -i :4000

# If needed, change port in config
# Edit: ../openwebui/config/litellm.yaml
# server_settings:
#   port: 4001  # Changed from 4000

systemctl --user restart litellm.service
```

---

### Issue: "Model Not Found" Error

**Symptoms**:
- API returns 404 for model request
- Model not in `/v1/models` list

**Diagnosis**:
```bash
# List available models
curl http://localhost:4000/v1/models | jq '.data[].id'

# Check LiteLLM config
cat ../openwebui/config/litellm.yaml | grep -A 5 "model_name: your-model"
```

**Solutions**:

1. **Model not configured**:
```bash
# Add model to config/litellm-unified.yaml
# Then apply:
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

2. **Typo in model name**:
```bash
# Check exact spelling
curl http://localhost:4000/v1/models | jq '.data[].id' | grep -i "partial-name"
```

3. **Provider not running**:
```bash
# Check provider health
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/v1/models  # llama.cpp
curl http://localhost:8001/v1/models  # vLLM

# Start if needed
systemctl --user start ollama.service
```

---

### Issue: Slow Response Times

**Symptoms**:
- Requests take >5 seconds
- First token delay >1 second

**Diagnosis**:
```bash
# Test response time
time curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "llama3.1:8b", "messages": [{"role": "user", "content": "Hi"}]}' \
  > /dev/null

# Check provider directly
time curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "llama3.1:8b", "prompt": "Hi"}' > /dev/null
```

**Solutions**:

1. **Wrong model for use case**:
```python
# For speed, use llama-cpp-native
response = client.chat.completions.create(
    model="llama-cpp-native",  # Fastest
    messages=[...]
)

# For batching, use vLLM
response = client.chat.completions.create(
    model="llama2-13b-vllm",  # Best throughput
    messages=[...]
)
```

2. **Provider under load**:
```bash
# Check concurrent requests
journalctl --user -u litellm.service | grep "concurrent" | tail -20

# Check provider resource usage
htop -p $(pgrep -f "ollama|llama|vllm")
```

3. **Cold start**:
```bash
# Warm up providers with test request
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "llama3.1:8b", "messages": [{"role": "user", "content": "Test"}]}'
```

4. **Enable caching**:
```yaml
# In litellm.yaml
litellm_settings:
  cache: true
  cache_params:
    type: redis
    host: 127.0.0.1
    port: 6379
    ttl: 3600
```

---

### Issue: Ollama Provider Unavailable

**Symptoms**:
- Ollama models return errors
- Health check fails for Ollama

**Diagnosis**:
```bash
# Check Ollama service
systemctl --user status ollama.service

# Test Ollama directly
curl http://localhost:11434/api/tags

# Check logs
journalctl --user -u ollama.service -n 50
```

**Solutions**:

1. **Service not running**:
```bash
systemctl --user start ollama.service
systemctl --user enable ollama.service  # Auto-start
```

2. **Models not pulled**:
```bash
# List pulled models
ollama list

# Pull missing model
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

3. **GPU not available**:
```bash
# Check GPU status
nvidia-smi

# If GPU unavailable, Ollama falls back to CPU (slower)
# Check Ollama config for gpu_layers setting
```

---

### Issue: vLLM Integration Not Working

**Current Deployment** (2025-10-21):
- Model: `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ`
- Port: 8001
- Installation: Manual (vLLM 0.11.0 in `~/venvs/vllm`)

**Symptoms**:
- vLLM models return errors
- "qwen-coder-7b-vllm" not found
- CUDA out of memory errors
- vLLM server not responding

**Diagnosis**:
```bash
# Check vLLM service
curl http://localhost:8001/v1/models

# Check if vLLM process is running
ps aux | grep vllm

# Check GPU memory
nvidia-smi

# Check vLLM logs
tail -50 ~/vllm_awq.log
```

**Solutions**:

1. **vLLM not started**:
```bash
# Activate venv and start server
source ~/venvs/vllm/bin/activate
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \
  --port 8001 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096
```

2. **CUDA Out of Memory errors**:
```bash
# Symptoms: "Available KV cache memory: -X.XX GiB" (negative!)
# Root cause: Model too large for available VRAM

# Solution 1: Use AWQ quantized model (recommended)
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \  # AWQ quantized
  --port 8001 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096

# Solution 2: Reduce memory settings (if still using unquantized)
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct \
  --port 8001 \
  --gpu-memory-utilization 0.7 \  # Reduced from 0.9
  --max-model-len 2048 \            # Reduced from 4096
  --max-num-seqs 32                 # Limit concurrent requests

# Solution 3: Use smaller model
vllm serve Qwen/Qwen2.5-Coder-3B-Instruct \  # 3B instead of 7B
  --port 8001 \
  --gpu-memory-utilization 0.9
```

**Memory Requirements**:
- **Qwen-7B unquantized**: ~14GB model + KV cache = 19GB+ VRAM (won't fit on 16GB GPU)
- **Qwen-7B AWQ**: ~5.2GB model + 7.36GB KV cache = 12.5GB VRAM (fits comfortably)
- **Llama-2-13B**: ~26GB VRAM required (use AWQ or smaller GPU)

3. **Configuration not applied to LiteLLM**:
```bash
# Apply vLLM integration config
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service

# Verify vLLM model appears
curl http://localhost:4000/v1/models | jq '.data[] | select(.id | contains("qwen"))'
```

4. **Wrong model name in requests**:
```bash
# Use exact model name from config
# Correct: "qwen-coder-7b-vllm" or "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"
# Incorrect: "llama2-13b-vllm" (outdated, no longer deployed)

# Test with correct model name
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'
```

5. **CRUSHVLLM quick-setup fails**:
```bash
# Symptoms: "Failed to build vllm==0.2.5"
# Root cause: CRUSHVLLM uses outdated vLLM version

# Solution: Use manual installation instead
python3 -m venv ~/venvs/vllm
source ~/venvs/vllm/bin/activate
pip install --upgrade pip
pip install vllm  # Installs latest version (0.11.0+)
```

**Performance Validation**:
```bash
# Check if vLLM is healthy
curl http://localhost:8001/health

# List available models
curl http://localhost:8001/v1/models | jq

# Test inference
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Write a Python hello world"}],
    "max_tokens": 50
  }' | jq '.choices[0].message.content'

# Test streaming
curl -N -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Count to 3"}],
    "max_tokens": 20,
    "stream": true
  }'
```

**AWQ Quantization Benefits**:
- 65% memory reduction (14.2GB → 5.2GB)
- Minimal quality loss (4-bit weights)
- Enables deployment on 16GB VRAM GPUs
- Same API compatibility
- Faster inference (less data movement)

---

### Issue: Fallback Not Triggering

**Symptoms**:
- Request fails instead of falling back
- Primary provider down but no fallback

**Diagnosis**:
```bash
# Check fallback configuration
cat config/litellm-unified.yaml | grep -A 10 "fallbacks:"

# Check error threshold
cat config/litellm-unified.yaml | grep "allowed_fails"
```

**Solutions**:

1. **Fallback not configured**:
```yaml
# Add to litellm-unified.yaml
router_settings:
  fallbacks:
    - model: llama3.1:8b
      fallback_models:
        - llama-cpp-python
```

2. **Error threshold not reached**:
```yaml
# Lower threshold for faster fallback
router_settings:
  allowed_fails: 1  # Fallback after 1 failure
```

3. **Test fallback manually**:
```bash
# Stop primary provider
systemctl --user stop ollama.service

# Request should fallback
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "llama3.1:8b", "messages": [...]}'

# Check logs for fallback
journalctl --user -u litellm.service | grep "fallback"

# Restart primary
systemctl --user start ollama.service
```

---

### Issue: Redis Caching Not Working

**Symptoms**:
- No performance improvement on repeated queries
- Low cache hit rate

**Diagnosis**:
```bash
# Check Redis service
systemctl status redis

# Test Redis connection
redis-cli ping

# Check cache hits
redis-cli INFO stats | grep keyspace_hits
```

**Solutions**:

1. **Redis not running**:
```bash
sudo systemctl start redis
sudo systemctl enable redis
```

2. **Cache not enabled in config**:
```yaml
# In litellm-unified.yaml
litellm_settings:
  cache: true
  cache_params:
    type: redis
    host: 127.0.0.1
    port: 6379
    ttl: 3600
```

3. **Cache keys changing**:
```bash
# Check cache key pattern
redis-cli KEYS "litellm:*"

# If empty, requests might have different parameters
# (temperature, max_tokens) affecting cache key
```

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

# Check which models are loaded
ollama list
curl http://localhost:8001/v1/models | jq
```

**Solutions**:

1. **Too many models loaded**:
```bash
# Unload unused Ollama models
# (Ollama loads on-demand, but keeps in memory)

# For vLLM, restart with single model
cd ../CRUSHVLLM
./crush stop
./crush start --model meta-llama/Llama-2-13b-chat-hf
```

2. **Reduce vLLM GPU memory**:
```bash
# Edit vLLM config
# Set gpu_memory_utilization to 0.8 (from 0.9)
```

3. **Use smaller models**:
```bash
# Prefer 7B models over 13B
# Use quantized models (Q4_K_M vs full precision)
```

---

### Issue: Authentication Errors with Cloud Providers

**Symptoms**:
- "Invalid API key" errors
- 401/403 responses from cloud providers

**Diagnosis**:
```bash
# Check environment variable
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Check systemd service environment
systemctl --user show litellm.service | grep Environment
```

**Solutions**:

1. **Environment variable not set**:
```bash
# Set in systemd service
systemctl --user edit litellm.service

# Add:
[Service]
Environment="OPENAI_API_KEY=sk-..."
Environment="ANTHROPIC_API_KEY=sk-ant-..."

systemctl --user daemon-reload
systemctl --user restart litellm.service
```

2. **API key in config file**:
```yaml
# Use environment variable reference
model_list:
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}  # Reference, not literal
```

3. **Test API key directly**:
```bash
# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

---

## Monitoring

### Real-Time Monitoring

```bash
# Watch LiteLLM logs
journalctl --user -u litellm.service -f

# Watch with filtering
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
  awk '{count++; sum+=$1; if(NR==1) min=$1; max=$1} END {print "Count:", count, "Min:", min, "Max:", max, "Avg:", sum/count}'
```

### Cache Hit Rate

```bash
# Calculate cache hit rate
journalctl --user -u litellm.service --since "1 hour ago" | \
  grep "cache_hit" | \
  awk -F'cache_hit.: ' '{print $2}' | \
  awk '{print $1}' | \
  awk '{total++; if($1=="true") hits++} END {print "Hit rate:", hits/total*100 "%"}'
```

### Provider Distribution

```bash
# See which providers are being used
journalctl --user -u litellm.service --since "1 hour ago" | \
  grep '"provider":' | \
  awk -F'"provider": "' '{print $2}' | \
  awk -F'"' '{print $1}' | \
  sort | uniq -c | sort -rn
```

## Performance Tuning

### Optimize for Latency

```yaml
# config/litellm-unified.yaml
router_settings:
  routing_strategy: latency-based-routing
  enable_pre_call_checks: false  # Skip health checks for speed

litellm_settings:
  request_timeout: 30  # Reasonable timeout
  cache: true  # Enable caching
```

### Optimize for Throughput

```yaml
router_settings:
  routing_strategy: usage-based-routing-v2
  model_group_alias:
    high_throughput:
      - llama2-13b-vllm  # vLLM excels at batching

litellm_settings:
  cache: true
  cache_params:
    ttl: 7200  # Longer cache for batch workloads
```

### Optimize for Reliability

```yaml
router_settings:
  allowed_fails: 1  # Quick fallback
  num_retries: 3
  cooldown_time: 30  # Quick recovery

  fallbacks:
    - model: production-model
      fallback_models:
        - backup-provider-1
        - backup-provider-2
        - backup-provider-3
```

## Debugging Tips

### Enable Debug Logging

```yaml
# config/litellm-unified.yaml
debug: true
debug_router: true
set_verbose: true
```

### Trace Individual Request

```bash
# Make request and capture details
curl -v -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Test"}]
  }' 2>&1 | tee request.log

# Check routing in logs
journalctl --user -u litellm.service | grep "llama3.1:8b" | tail -20
```

### Compare Provider Performance

```bash
#!/bin/bash
# compare_providers.sh

models=("llama3.1:8b" "llama-cpp-python" "llama2-13b-vllm")

for model in "${models[@]}"; do
  echo "Testing $model..."
  time curl -s -X POST http://localhost:4000/v1/chat/completions \
    -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}" \
    > /dev/null
done
```

## Getting Help

If issues persist:

1. **Check logs**:
   ```bash
   journalctl --user -u litellm.service -n 100 --no-pager
   ```

2. **Verify configuration**:
   ```bash
   python3 -c "import yaml; print(yaml.safe_load(open('../openwebui/config/litellm.yaml')))"
   ```

3. **Test providers individually**:
   ```bash
   curl http://localhost:11434/api/tags
   curl http://localhost:8000/v1/models
   curl http://localhost:8001/v1/models
   ```

4. **Run validation script**:
   ```bash
   ./scripts/validate-unified-backend.sh
   ```

5. **Check documentation**:
   - [Architecture](architecture.md)
   - [API Guide](consuming-api.md)
   - [Provider Guide](adding-providers.md)

6. **Consult resources**:
   - LiteLLM Docs: https://docs.litellm.ai/
   - Ollama Docs: https://ollama.ai/docs
   - vLLM Docs: https://docs.vllm.ai/

## Emergency Rollback

If the unified backend is completely broken:

```bash
# 1. Stop LiteLLM
systemctl --user stop litellm.service

# 2. Restore backup configuration
cp ../openwebui/config/litellm.yaml.backup ../openwebui/config/litellm.yaml

# 3. Restart with backup config
systemctl --user start litellm.service

# 4. Verify restoration
curl http://localhost:4000/v1/models | jq

# 5. Investigate issue before re-attempting
journalctl --user -u litellm.service -n 200 > debug.log
```
