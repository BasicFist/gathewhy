# Local vs Cloud Model Routing Strategy

## Architecture Overview

You **cannot** route cloud models through vLLM because:

```
❌ IMPOSSIBLE:
Cloud Model (https://ollama.com) → Download → vLLM → Inference
                                      ↑
                              Doesn't exist locally!

✅ ACTUAL ARCHITECTURE:
Request → LiteLLM :4000 → Routes to:
                         ├─ Local vLLM :8001 (7B models, your GPU)
                         ├─ Local Ollama :11434 (8B-13B models, your GPU)
                         └─ Remote Ollama Cloud (671B-1T models, Ollama's servers)
```

## What "Cloud Models" Actually Are

| Model | Where It Runs | Can Run Locally? |
|-------|---------------|------------------|
| `deepseek-v3.1:671b-cloud` | Ollama's data centers | ❌ No (needs ~335GB VRAM) |
| `qwen3-coder:480b-cloud` | Ollama's data centers | ❌ No (needs ~240GB VRAM) |
| `kimi-k2:1t-cloud` | Ollama's data centers | ❌ No (needs ~500GB VRAM) |
| **Your GPU** | **Quadro RTX 5000** | **16GB VRAM available** |

These are **remote API calls**, not local inference. You can't "route them through vLLM" any more than you can route a Google search through your local web server.

---

## Current Routing Strategy (Already Configured)

### Strategy 1: Local First, Cloud Fallback ✅

**Code generation requests:**
```
qwen2.5-coder:7b (Ollama, local)
  ↓ if busy/down
qwen-coder-vllm (vLLM, local)
  ↓ if busy/down
qwen3-coder:480b-cloud (Ollama Cloud, remote)
  ↓ if rate limited
dolphin-uncensored-vllm (vLLM, local)
```

**General chat requests:**
```
llama3.1:latest (Ollama, local)
  ↓ if busy/down
qwen2.5-coder:7b (Ollama, local)
  ↓ if busy/down
qwen-coder-vllm (vLLM, local)
  ↓ if busy/down
dolphin-uncensored-vllm (vLLM, local)
  ↓ if busy/down
gpt-oss:120b-cloud (Ollama Cloud, remote)
```

This is **already configured** in `config/model-mappings.yaml`.

### Strategy 2: Cloud First, Local Fallback ✅

**When cloud model fails:**
```
deepseek-v3.1:671b-cloud (Ollama Cloud, remote)
  ↓ if rate limited/down
llama3.1:latest (Ollama, local)
  ↓ if busy/down
qwen-coder-vllm (vLLM, local)
```

This is **already configured** for all cloud models.

---

## What You CAN Do

### Option 1: Add Smaller Versions of Cloud Models to vLLM

Run **local alternatives** to the massive cloud models.

#### DeepSeek Local Alternative

**Cloud**: `deepseek-v3.1:671b-cloud` (671B parameters, remote)
**Local**: `deepseek-ai/DeepSeek-Coder-6.7B-Instruct-AWQ` (6.7B, ~3.5GB VRAM)

```bash
# 1. Download model
cd ~/venvs/vllm
source bin/activate
huggingface-cli download TheBloke/deepseek-coder-6.7B-instruct-AWQ

# 2. Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model TheBloke/deepseek-coder-6.7B-instruct-AWQ \
  --quantization awq \
  --dtype half \
  --gpu-memory-utilization 0.45 \
  --port 8003 \
  --host 0.0.0.0

# 3. Add to providers.yaml
```

Add this to `config/providers.yaml`:
```yaml
  vllm-deepseek:
    type: vllm
    base_url: http://127.0.0.1:8003
    status: active
    description: vLLM DeepSeek local alternative to 671B cloud model
    models:
      - name: deepseek-coder-6.7b-vllm
        size: "6.7B"
        quantization: AWQ
        specialty: code_generation
        model_size_gb: 3.5
```

Add to `config/model-mappings.yaml`:
```yaml
exact_matches:
  "deepseek-coder-6.7b-vllm":
    provider: vllm-deepseek
    priority: primary
    fallback: deepseek-v3.1:671b-cloud
    description: "Local DeepSeek, falls back to 671B cloud"

fallback_chains:
  "deepseek-coder-6.7b-vllm":
    chain:
      - deepseek-v3.1:671b-cloud  # Upgrade to cloud if needed
      - qwen2.5-coder:7b
```

#### Qwen Local Upgrade

**Current**: `Qwen2.5-Coder-7B-AWQ` (5.2GB, port 8001)
**Cloud**: `qwen3-coder:480b-cloud` (480B, remote)
**Upgrade**: `Qwen2.5-Coder-14B-AWQ` (~7GB VRAM)

```bash
# Download 14B model
huggingface-cli download TheBloke/Qwen2.5-Coder-14B-Instruct-AWQ

# Stop 7B vLLM, start 14B (same port 8001)
# OR run both on different ports
```

---

### Option 2: Configure Priority-Based Routing

**Prefer local for development, cloud for complex tasks:**

Add to `config/model-mappings.yaml`:
```yaml
capabilities:
  code_generation:
    preferred_models:
      - qwen2.5-coder:7b
      - qwen3-coder:480b-cloud
    provider: ollama
    routing_strategy: load_balance
```

---

## Summary

- Local models run on your GPU (fast, free).
- Cloud models run on Ollama's servers (huge context, higher cost).
- Routing rules already prefer local, with automatic fallback to cloud.
- Adding local alternatives or tuning capabilities lets you control costs and throughput.
