# Adding New Providers - Complete Guide

This guide walks through adding a new LLM provider to the unified backend infrastructure.

## Overview

Adding a provider involves 4 configuration files:
1. `config/providers.yaml` - Provider registry
2. `config/model-mappings.yaml` - Routing rules
3. `config/litellm-unified.yaml` - LiteLLM integration
4. `.serena/memories/02-provider-registry.md` - Documentation

## Prerequisites

- Provider's API endpoint accessible from LAB network
- Provider supports OpenAI-compatible API (or LiteLLM has native support)
- Health check endpoint available
- Model identifiers known

## Step-by-Step Process

### Step 1: Add to Provider Registry

Edit `config/providers.yaml`:

```yaml
providers:
  # ... existing providers ...

  new_provider:
    type: provider_type  # openai_compatible, anthropic, custom, etc.
    base_url: http://host:port
    status: active
    description: "Brief description of provider purpose"

    features:
      - feature_1
      - feature_2
      - feature_3

    models:
      - name: model-name
        size: "7B"  # or "13B", "70B", etc.
        context_length: 4096
        specialty: task_type  # code, chat, vision, etc.

    health_endpoint: /health
    api_format: openai_compatible
    docs: https://provider.docs.url
    location: ../path/to/provider  # If local
```

**Example: Adding a Text Generation WebUI Instance**

```yaml
providers:
  text_gen_webui:
    type: openai_compatible
    base_url: http://127.0.0.1:5001
    status: active
    description: "Text Generation WebUI server for additional models"

    features:
      - GPU acceleration
      - Multiple model support
      - Web interface
      - LoRA support

    models:
      - name: mistral-7b-instruct
        size: "7B"
        context_length: 8192
        specialty: instruction_following

    health_endpoint: /v1/models
    api_format: openai_compatible
    docs: https://github.com/oobabooga/text-generation-webui
    location: ~/text-generation-webui
```

### Step 2: Define Routing Rules

Edit `config/model-mappings.yaml`:

```yaml
exact_matches:
  # Add exact model name mapping
  "new-model-name":
    provider: new_provider
    priority: primary
    fallback: existing_provider  # Optional
    description: "Model description"

# OR add pattern-based routing
patterns:
  - pattern: "^new-provider/.*"
    provider: new_provider
    fallback: ollama
    description: "Route all new-provider models"

# AND/OR add to capability routing
capabilities:
  task_type:
    preferred_models:
      - new-model-name
    provider: new_provider
    routing_strategy: load_balance
```

**Example: Text Generation WebUI Routing**

```yaml
exact_matches:
  "mistral-7b":
    provider: text_gen_webui
    priority: primary
    fallback: ollama
    description: "Mistral 7B Instruct via Text Gen WebUI"

capabilities:
  instruction_following:
    preferred_models:
      - mistral-7b
    provider: text_gen_webui
    routing_strategy: usage_based
```

### Step 3: Configure LiteLLM Integration

Edit `config/litellm-unified.yaml`:

```yaml
model_list:
  # Add model entry
  - model_name: new-model-alias
    litellm_params:
      model: provider_prefix/model-path
      api_base: http://host:port
      stream: true  # If streaming supported
    model_info:
      tags: ["tag1", "tag2", "tag3"]
      provider: new_provider
      context_length: 4096
      notes: "Additional notes"

# Update router settings if needed
router_settings:
  model_group_alias:
    task_group:
      - new-model-alias
      - existing-model

  fallbacks:
    - model: new-model-alias
      fallback_models:
        - existing-fallback-model
```

**Example: Text Generation WebUI in LiteLLM**

```yaml
model_list:
  - model_name: mistral-7b-webui
    litellm_params:
      model: openai/mistral-7b-instruct  # Generic OpenAI format
      api_base: http://127.0.0.1:5001/v1
      stream: true
    model_info:
      tags: ["instruct", "7b", "webui"]
      provider: text_gen_webui
      context_length: 8192
      notes: "Mistral 7B via Text Gen WebUI"

router_settings:
  model_group_alias:
    instruction_tasks:
      - mistral-7b-webui
      - llama3.1-ollama

  fallbacks:
    - model: mistral-7b-webui
      fallback_models:
        - llama3.1-ollama
```

### Step 4: Update Serena Memory

Edit `.serena/memories/02-provider-registry.md`:

Add comprehensive documentation for the new provider, including:
- Connection details
- Features and capabilities
- Models available
- Performance characteristics
- Best use cases
- Integration notes

### Step 5: Test the Integration

```bash
# 1. Backup existing configuration
cp ../openwebui/config/litellm.yaml ../openwebui/config/litellm.yaml.backup

# 2. Apply new configuration
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml

# 3. Restart LiteLLM service
systemctl --user restart litellm.service

# 4. Verify service started
systemctl --user status litellm.service

# 5. Check new provider appears in model list
curl http://localhost:4000/v1/models | jq '.data[] | select(.id | contains("new-model"))'

# 6. Test health endpoint
curl http://host:port/health

# 7. Test routing to new provider
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "new-model-name",
    "messages": [{"role": "user", "content": "Hello"}]
  }' | jq

# 8. Check logs for routing decision
journalctl --user -u litellm.service | grep "new-model-name"
```

### Step 6: Validation Script

Run the validation script to ensure everything works:

```bash
./scripts/validate-unified-backend.sh
```

Expected output:
```
Testing unified AI backend...
✅ All providers healthy
✅ LiteLLM routing functional
✅ New provider reachable
✅ Model routing working
✅ Fallback chains operational
```

## Provider Type Examples

### OpenAI-Compatible Provider

```yaml
openai_compatible_provider:
  type: openai_compatible
  base_url: http://host:port
  health_endpoint: /v1/models
  # Uses standard OpenAI API format
```

### Anthropic

```yaml
anthropic:
  type: anthropic
  base_url: https://api.anthropic.com/v1
  requires_api_key: true
  env_var: ANTHROPIC_API_KEY
  models:
    - claude-3-opus-20240229
    - claude-3-sonnet-20240229
```

### OpenAI

```yaml
openai:
  type: openai
  base_url: https://api.openai.com/v1
  requires_api_key: true
  env_var: OPENAI_API_KEY
  models:
    - gpt-4
    - gpt-3.5-turbo
```

### Custom Self-Hosted

```yaml
custom_provider:
  type: custom
  base_url: http://custom-host:port
  status: active
  custom_config:
    auth_method: bearer_token
    headers:
      Authorization: "Bearer ${CUSTOM_API_KEY}"
```

## Advanced Configuration

### Load Balancing Between Providers

```yaml
# Distribute same model across multiple providers
redundant_models:
  "popular-model":
    providers:
      - provider: new_provider
        weight: 0.5  # 50% traffic
      - provider: existing_provider
        weight: 0.5  # 50% traffic
```

### Provider-Specific Fallback

```yaml
fallback_chains:
  new_provider_fallback:
    description: "Fallback for new provider failures"
    chain:
      - primary: new_provider
      - secondary: ollama
      - tertiary: llama_cpp_python
    retry_attempts: 3
    retry_delay_ms: 500
```

### Health Check Customization

```yaml
health_checks:
  new_provider:
    endpoint: http://host:port/custom/health
    interval_seconds: 30
    timeout_seconds: 10
    retry_attempts: 2
```

### Rate Limiting

```yaml
rate_limit_settings:
  enabled: true
  limits:
    new_provider:
      rpm: 60  # requests per minute
      tpm: 100000  # tokens per minute
```

## Common Integration Scenarios

### Scenario 1: Adding Cloud Provider (OpenAI)

**Requirements**:
- API key
- Budget management
- Rate limiting

**Configuration**:

```yaml
# providers.yaml
openai:
  type: openai
  base_url: https://api.openai.com/v1
  status: active
  requires_api_key: true
  env_var: OPENAI_API_KEY

# model-mappings.yaml
exact_matches:
  "gpt-4":
    provider: openai
    priority: primary
    fallback: llama2-13b-vllm  # Local fallback

# litellm-unified.yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}

# Set environment variable
export OPENAI_API_KEY="sk-..."
```

### Scenario 2: Adding Local GPU Server

**Requirements**:
- Local network access
- CUDA-enabled inference
- High performance

**Configuration**:

```yaml
# providers.yaml
local_gpu_server:
  type: openai_compatible
  base_url: http://192.168.1.100:8080
  status: active
  gpu_memory_utilization: 0.95
  features:
    - CUDA acceleration
    - FP16 inference

# model-mappings.yaml
capabilities:
  high_performance:
    provider: local_gpu_server
    routing_strategy: fastest_response
```

### Scenario 3: Adding Multiple Model Sizes

**Configuration**:

```yaml
# model-mappings.yaml
model_size_routing:
  - size: "< 8B"
    provider: ollama

  - size: "8B - 13B"
    provider: new_provider

  - size: "> 13B"
    provider: vllm
```

## Troubleshooting New Provider Integration

### Issue: Provider not appearing in model list

**Debug**:
```bash
# Check LiteLLM config syntax
python -m yaml config/litellm-unified.yaml

# Verify provider is active
cat config/providers.yaml | grep -A 10 "new_provider"

# Check LiteLLM logs
journalctl --user -u litellm.service -f
```

### Issue: Routing to wrong provider

**Debug**:
```bash
# Enable debug mode
# Edit config/litellm-unified.yaml
debug_router: true

# Restart and test
systemctl --user restart litellm.service
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "new-model", "messages": [...]}' | jq

# Check routing decision
journalctl --user -u litellm.service | grep "ROUTER"
```

### Issue: Provider health check failing

**Debug**:
```bash
# Test health endpoint directly
curl http://provider:port/health

# Check network connectivity
ping provider-host

# Verify port is open
nc -zv provider-host port

# Check firewall rules
sudo ufw status
```

### Issue: Authentication errors

**Debug**:
```bash
# Verify environment variable
echo $PROVIDER_API_KEY

# Check LiteLLM sees the variable
systemctl --user show litellm.service | grep Environment

# Test API key directly
curl -H "Authorization: Bearer $API_KEY" http://provider:port/v1/models
```

## Best Practices

### 1. Start with Test Configuration
- Add provider with `status: testing`
- Test thoroughly before setting to `active`
- Use small traffic percentage initially

### 2. Always Define Fallbacks
- Every production model should have fallback
- Test fallback by stopping primary provider
- Document fallback behavior

### 3. Monitor Performance
- Track latency metrics for new provider
- Compare with existing providers
- Adjust routing weights based on performance

### 4. Document Everything
- Update Serena memories
- Add usage examples
- Document specific configurations

### 5. Version Control
- Commit configuration changes
- Use descriptive commit messages
- Tag stable configurations

## Rollback Procedure

If new provider causes issues:

```bash
# 1. Stop LiteLLM
systemctl --user stop litellm.service

# 2. Restore backup configuration
cp ../openwebui/config/litellm.yaml.backup ../openwebui/config/litellm.yaml

# 3. Restart LiteLLM
systemctl --user start litellm.service

# 4. Verify recovery
curl http://localhost:4000/v1/models | jq

# 5. Investigate issue before re-attempting
journalctl --user -u litellm.service | tail -100
```

## Validation Checklist

Before marking provider integration complete:

- [ ] Provider added to `config/providers.yaml`
- [ ] Routing rules defined in `config/model-mappings.yaml`
- [ ] LiteLLM configuration updated in `config/litellm-unified.yaml`
- [ ] Serena memory documentation updated
- [ ] Health check endpoint verified
- [ ] Model list includes new provider models
- [ ] Routing test successful
- [ ] Fallback chain tested
- [ ] Performance metrics acceptable
- [ ] Documentation complete
- [ ] Configuration committed to git

## Getting Help

If you encounter issues:

1. Check logs: `journalctl --user -u litellm.service`
2. Review configuration syntax
3. Test provider endpoint directly
4. Consult LiteLLM documentation: https://docs.litellm.ai/
5. Check provider-specific documentation

## Next Steps

- [Test your integration](consuming-api.md)
- [Configure monitoring](troubleshooting.md#monitoring)
- [Optimize performance](troubleshooting.md#performance-tuning)
