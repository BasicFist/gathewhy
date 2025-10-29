# CrushVLLM Cloud Models Configuration ✅

**Date**: October 27, 2025, 14:20 CET
**Issue**: Cloud models were available through LiteLLM gateway but not visible in CrushVLLM
**Root Cause**: CrushVLLM configuration file only listed local models
**Solution**: Added 6 Ollama Cloud models to `~/.config/crush/crush.json`

---

## What Was Fixed

### Problem
- Cloud models accessible via API: `curl http://localhost:4000/v1/models` showed all 6 cloud models
- CrushVLLM provider list: Only showed 5 local models (llama3.1, qwen2.5-coder, mythomax, qwen-vllm, dolphin-vllm)
- Configuration gap: `~/.config/crush/crush.json` didn't include cloud models in the `workspace-backend` provider

### Solution
Added 6 Ollama Cloud models to the `workspace-backend` provider configuration:

```json
{
  "id": "deepseek-v3.1:671b-cloud",
  "name": "DeepSeek V3.1 671B (Cloud)",
  "context_window": 64000,
  "default_max_tokens": 4000
},
{
  "id": "qwen3-coder:480b-cloud",
  "name": "Qwen3 Coder 480B (Cloud)",
  "context_window": 32768,
  "default_max_tokens": 4000
},
{
  "id": "kimi-k2:1t-cloud",
  "name": "Kimi K2 1T (Cloud)",
  "context_window": 128000,
  "default_max_tokens": 4000
},
{
  "id": "gpt-oss:120b-cloud",
  "name": "GPT-OSS 120B (Cloud)",
  "context_window": 32768,
  "default_max_tokens": 4000
},
{
  "id": "gpt-oss:20b-cloud",
  "name": "GPT-OSS 20B (Cloud)",
  "context_window": 32768,
  "default_max_tokens": 2000
},
{
  "id": "glm-4.6:cloud",
  "name": "GLM 4.6 (Cloud)",
  "context_window": 128000,
  "default_max_tokens": 2000
}
```

---

## How to See Cloud Models in CrushVLLM

### Step 1: Restart CrushVLLM

```bash
pkill crush
crush
```

Or, if running as systemd service:

```bash
systemctl --user restart crush.service
```

### Step 2: Verify Models Are Visible

1. Open CrushVLLM
2. Press `/` or click the model selector
3. You should now see the local and cloud models listed with suffixes.

---

## Model Selection Guide

### Local Models
✅ Fast, free, privacy-preserving. Recommended for development/testing.

### Cloud Models
✅ Use for complex reasoning, large context, or when local GPU is saturated.

---

## Automatic Fallback

Cloud models are integrated into LiteLLM fallback chains, so requests automatically escalate to cloud if local infrastructure is overloaded or unavailable.

---

**Summary**: Added cloud models to Crush configuration so they are selectable alongside local models. Restart Crush to pick up the changes.
