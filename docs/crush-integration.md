# CrushVLLM Integration Guide

## Overview

CrushVLLM can access all models in the unified backend through the LiteLLM gateway on port 4000, including **Ollama Cloud** models with up to 1 trillion parameters.

## Quick Start

### 1. Configure CrushVLLM Endpoint

Point CrushVLLM to the unified gateway:

```bash
export OPENAI_BASE_URL=http://localhost:4000/v1
```

Or in your CrushVLLM configuration file:

```yaml
api:
  base_url: http://localhost:4000/v1
  provider: litellm_unified
```

### 2. Available Models

All models are accessible through a single endpoint:

**Local Models** (free, no API key):
- `llama3.1:latest` - 8B general chat
- `qwen2.5-coder:7b` - 7.6B code generation
- `mythomax-l2-13b-q5_k_m` - 13B creative writing
- `qwen-coder-vllm` - 7B code via vLLM (high throughput)
- `dolphin-uncensored-vllm` - 7B uncensored via vLLM

**Cloud Models** (requires `OLLAMA_API_KEY`):
- `deepseek-v3.1:671b-cloud` - 671B advanced reasoning
- `qwen3-coder:480b-cloud` - 480B code generation
- `kimi-k2:1t-cloud` - 1 trillion parameter reasoning
- `gpt-oss:120b-cloud` - 120B general chat
- `gpt-oss:20b-cloud` - 20B general chat
- `glm-4.6:cloud` - 4.6B general chat

### 3. Example Usage

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="not-needed"  # Local models don't need key
)

# Use local model
response = client.chat.completions.create(
    model="qwen2.5-coder:7b",
    messages=[
        {"role": "user", "content": "Write a Python sorting algorithm"}
    ]
)

# Use massive cloud model (if OLLAMA_API_KEY is set)
response = client.chat.completions.create(
    model="deepseek-v3.1:671b-cloud",
    messages=[
        {"role": "user", "content": "Explain quantum entanglement"}
    ]
)
```

## Automatic Fallback

The gateway provides automatic failover:

```
Request: qwen2.5-coder:7b
  ↓
1. Try local Ollama (qwen2.5-coder:7b)
   ↓ (if fails)
2. Try vLLM (qwen-coder-vllm)
   ↓ (if fails)
3. Try Ollama Cloud (qwen3-coder:480b-cloud)
   ↓ (if fails)
4. Try other local models
```

You get **high availability** without changing your code!

## Enabling Ollama Cloud

### Step 1: Get API Key

1. Visit https://ollama.com/settings/keys
2. Create an API key
3. Copy the key

### Step 2: Set Environment Variable

```bash
# In your terminal
export OLLAMA_API_KEY="your-api-key-here"

# Make it permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export OLLAMA_API_KEY="your-api-key-here"' >> ~/.bashrc
```

### Step 3: Enable Provider

```bash
cd ~/LAB/ai/backend/ai-backend-unified

# Edit providers config
vim config/providers.yaml
# Change: ollama_cloud status: disabled → status: active

# Regenerate configuration
python3 scripts/generate-litellm-config.py

# Apply to OpenWebUI
cp config/litellm-unified.yaml runtime/config/litellm.yaml

# Restart LiteLLM
systemctl --user restart litellm.service
```

### Step 4: Verify

```bash
# Check available models
curl http://localhost:4000/v1/models | jq '.data[] | .id'
```

You should see the cloud models listed.

## Model Selection Guide

### When to use local models

✅ **Development and testing** - Free, fast, always available
✅ **Privacy-sensitive data** - Stays on your machine
✅ **High-volume requests** - No rate limits
✅ **Offline work** - No internet required

### When to use cloud models

✅ **Complex reasoning** - 671B model for hard problems
✅ **Large code generation** - 480B model for complex code
✅ **Fallback availability** - When local GPU is busy
✅ **Model exploration** - Try trillion-parameter models

## Performance Tips

### 1. Use Capability-Based Routing

Instead of specifying models, use capabilities:

```python
response = client.chat.completions.create(
    model="code_generation",
    messages=[...]
)
```

Capabilities automatically route between local and cloud models as needed.

### 2. Control Fallbacks

Configure fallback chains in `config/model-mappings.yaml` to prioritize local, then cloud.

### 3. Monitor Usage

Use the included Prometheus/Grafana dashboards (once metrics enabled) or structured logs to track cloud usage.

## Troubleshooting

- **401 Unauthorized**: Ensure `OLLAMA_API_KEY` is exported for the environment running LiteLLM
- **Models missing**: Regenerate config and restart LiteLLM (`python3 scripts/generate-litellm-config.py` → `systemctl --user restart litellm.service`)
- **High latency**: Cloud models are remote; use local models for smaller tasks

## References

- `CLOUD_MODELS_READY.md` – Integration change log
- `CRUSH-CONFIG-AUDIT.md` / `CRUSH-CONFIG-FIX.json` – Crush CLI adjustments
- `docs/ollama-cloud-setup.md` – Step-by-step setup and operations guide
- `docs/local-vs-cloud-routing.md` – Architecture rationale and routing details
