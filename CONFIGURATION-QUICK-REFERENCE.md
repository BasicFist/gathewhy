# Configuration Quick Reference

**Fast lookup for common configuration tasks**

---

## File Locations

```
config/
├── providers.yaml         # SOURCE OF TRUTH - Provider definitions
├── model-mappings.yaml    # SOURCE OF TRUTH - Routing rules
└── litellm-unified.yaml   # AUTO-GENERATED - Do not edit directly
```

---

## Adding a New Model to Existing Provider

### 1. Ollama Model

**Pull the model:**
```bash
ollama pull model-name:version
```

**Add to `config/providers.yaml`:**
```yaml
providers:
  ollama:
    models:
      - name: model-name:version
        size: "7B"
        quantization: Q4_K_M
        pulled_at: "2025-10-30"
        specialty: code_generation  # or general_chat, creative_writing, etc.
```

**Add routing in `config/model-mappings.yaml`:**
```yaml
exact_matches:
  "model-name:version":
    provider: ollama
    priority: primary
    fallback: null
    description: "Description of model"
```

**Regenerate and apply:**
```bash
python3 scripts/generate-litellm-config.py
systemctl --user restart litellm.service
```

**Verify:**
```bash
curl http://localhost:4000/v1/models | jq '.data[] | select(.id == "model-name:version")'
```

---

## Adding Ollama Cloud Model

**Add to `config/providers.yaml`:**
```yaml
providers:
  ollama_cloud:
    models:
      - name: new-model:cloud
        size: "XXB"
        specialty: code_generation
```

**Add routing in `config/model-mappings.yaml`:**
```yaml
exact_matches:
  "new-model:cloud":
    provider: ollama_cloud
    priority: primary
    fallback: ollama
    description: "Cloud model for X"
```

**Ensure `OLLAMA_API_KEY` is set:**
```bash
echo ${OLLAMA_API_KEY:0:10}...  # Check it's set
# If not, see docs/ollama-cloud-setup.md
```

**Regenerate and test:**
```bash
python3 scripts/generate-litellm-config.py
systemctl --user restart litellm.service
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "new-model:cloud", "messages": [{"role": "user", "content": "test"}], "max_tokens": 10}'
```

---

## Adding a New Provider

**1. Add to `config/providers.yaml`:**
```yaml
providers:
  new_provider:
    type: openai_compatible  # or ollama, llama_cpp, vllm
    base_url: http://127.0.0.1:8002
    status: active
    description: "Description"
    models:
      - name: model-name
        size: "7B"
        specialty: general_chat
    health_endpoint: /v1/models
```

**2. Add routing rules to `config/model-mappings.yaml`:**
```yaml
exact_matches:
  "model-name":
    provider: new_provider
    priority: primary
    fallback: ollama
    description: "New provider model"
```

**3. Generate config:**
```bash
python3 scripts/generate-litellm-config.py
```

**4. Validate:**
```bash
python3 scripts/validate-config-schema.py
```

**5. Apply:**
```bash
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

**6. Verify:**
```bash
scripts/validate-unified-backend.sh
curl http://localhost:4000/v1/models | jq '.data[] | select(.provider == "new_provider")'
```

---

## Changing Model Routing

### Make Model Use Different Provider

**Edit `config/model-mappings.yaml`:**
```yaml
exact_matches:
  "llama3.1:latest":
    provider: llama_cpp_python  # Changed from ollama
    priority: primary
    fallback: ollama
```

### Add Fallback Chain

**Edit `config/model-mappings.yaml`:**
```yaml
fallback_chains:
  "qwen2.5-coder:7b":
    chain:
      - qwen-coder-vllm      # Try vLLM first
      - llama3.1:latest      # Then Llama
      - qwen3-coder:480b-cloud  # Finally cloud
```

### Load Balance Across Providers

**Edit `config/model-mappings.yaml`:**
```yaml
load_balancing:
  "llama3.1:latest":
    providers:
      - provider: ollama
        weight: 0.7  # 70% of requests
      - provider: llama_cpp_python
        weight: 0.3  # 30% of requests
    strategy: weighted_round_robin
```

**After any routing change:**
```bash
python3 scripts/generate-litellm-config.py
systemctl --user restart litellm.service
```

---

## Common Provider Configurations

### Ollama
```yaml
ollama:
  type: ollama
  base_url: http://127.0.0.1:11434
  status: active
  health_endpoint: /api/tags
```

### llama.cpp (Python)
```yaml
llama_cpp_python:
  type: llama_cpp
  base_url: http://127.0.0.1:8000
  status: active
  configuration:
    n_gpu_layers: -1
    n_ctx: 8192
    n_parallel: 4
  health_endpoint: /v1/models
```

### vLLM
```yaml
vllm-qwen:
  type: vllm
  base_url: http://127.0.0.1:8001
  status: active
  gpu_memory_utilization: 0.45
  max_model_len: 4096
  health_endpoint: /v1/models
```

### Ollama Cloud
```yaml
ollama_cloud:
  type: ollama
  base_url: https://ollama.com
  status: active
  requires_api_key: true
  env_var: OLLAMA_API_KEY
  health_endpoint: /api/tags
```

---

## Troubleshooting

### Model Not Appearing

**Check:**
```bash
# 1. Is it in providers.yaml?
grep "model-name" config/providers.yaml

# 2. Is it in model-mappings.yaml?
grep "model-name" config/model-mappings.yaml

# 3. Was config regenerated?
ls -lh config/litellm-unified.yaml  # Check timestamp

# 4. Was LiteLLM restarted?
systemctl --user status litellm.service
```

**Fix:**
```bash
python3 scripts/generate-litellm-config.py
systemctl --user restart litellm.service
curl http://localhost:4000/v1/models | jq '.data[] | .id'
```

### Provider Not Healthy

**Check health:**
```bash
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8001/v1/models  # vLLM
```

**Check logs:**
```bash
journalctl --user -u litellm.service -f
```

**Restart provider:**
```bash
systemctl --user restart ollama.service  # If using systemd
systemctl --user restart vllm-qwen.service
```

### Routing Not Working

**Test routing:**
```bash
./scripts/debugging/test-routing.sh model-name
```

**Check routing config:**
```bash
jq '.model_list[] | select(.model_name == "model-name")' config/litellm-unified.yaml
```

**Verify in model-mappings.yaml:**
```bash
yq '.exact_matches."model-name"' config/model-mappings.yaml
```

---

## Environment Variables

### Required for Cloud Models
```bash
export OLLAMA_API_KEY="your-api-key"  # For Ollama Cloud models
```

### Optional
```bash
export LITELLM_MASTER_KEY="sk-..."  # For authentication (production)
export REDIS_HOST="localhost"        # Redis cache
export REDIS_PORT="6379"
```

---

## Service Management

### LiteLLM Gateway
```bash
systemctl --user status litellm.service
systemctl --user start litellm.service
systemctl --user stop litellm.service
systemctl --user restart litellm.service
journalctl --user -u litellm.service -f  # Logs
```

### Providers
```bash
# Ollama
systemctl --user status ollama.service
systemctl --user restart ollama.service

# vLLM
systemctl --user status vllm-qwen.service
systemctl --user status vllm-dolphin.service
systemctl --user restart vllm-qwen.service
```

---

## Configuration Validation

### Validate All Configs
```bash
./scripts/validate-all-configs.sh
```

### Validate Individual Files
```bash
# YAML syntax
yamllint config/providers.yaml
yamllint config/model-mappings.yaml

# Schema validation
python3 scripts/validate-config-schema.py
```

### Test Configuration
```bash
# Test all providers
./scripts/validate-unified-backend.sh

# Test specific model
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "test-model",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'
```

---

## Backup & Rollback

### Backup Configuration
```bash
# Automatic (on restart)
cp config/litellm-unified.yaml config/litellm-unified.yaml.backup_$(date +%Y%m%d_%H%M%S)

# Manual
./scripts/backup-config.sh
```

### Rollback
```bash
# Stop service
systemctl --user stop litellm.service

# Restore from backup
cp config/litellm-unified.yaml.backup_TIMESTAMP config/litellm-unified.yaml

# Restart
systemctl --user start litellm.service
```

---

## Monitoring

### Quick Health Check
```bash
curl http://localhost:4000/health
```

### Real-time Request Monitoring
```bash
./scripts/debugging/tail-requests.py
```

### Analyze Recent Logs
```bash
./scripts/debugging/analyze-logs.py --last 1h
```

### Check Model Usage
```bash
./scripts/profiling/analyze-token-usage.py
```

---

## Common Patterns

### Test New Model
```bash
# 1. Pull (if Ollama)
ollama pull new-model:7b

# 2. Add to providers.yaml
# 3. Add to model-mappings.yaml
# 4. Regenerate
python3 scripts/generate-litellm-config.py

# 5. Restart
systemctl --user restart litellm.service

# 6. Test
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "new-model:7b", "messages": [{"role": "user", "content": "test"}], "max_tokens": 10}'
```

### Switch Default Model
```bash
# Edit model-mappings.yaml
# Change routing_rules.default_provider

python3 scripts/generate-litellm-config.py
systemctl --user restart litellm.service
```

### Disable Provider
```bash
# Edit providers.yaml
# Set status: disabled

python3 scripts/generate-litellm-config.py
systemctl --user restart litellm.service
```

---

## Quick Links

- **Full Docs**: [DOCUMENTATION-INDEX.md](DOCUMENTATION-INDEX.md)
- **API Reference**: [docs/API-REFERENCE.md](docs/API-REFERENCE.md)
- **Adding Providers**: [docs/adding-providers.md](docs/adding-providers.md)
- **Troubleshooting**: [docs/troubleshooting.md](docs/troubleshooting.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)

---

**Last Updated**: 2025-10-30
**Config Version**: 1.3
