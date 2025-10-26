# vLLM Single-Instance Management

## Hardware Constraint

**VRAM Available**: 16GB (Quadro RTX 5000)
**vLLM Memory Requirements**:
- Qwen2.5-Coder-7B-AWQ: ~12.6GB (model + KV cache)
- Dolphin-2.8-Mistral-7B-AWQ: ~12-13GB (model + KV cache)
- **Both models together**: ~25GB > 16GB available ❌

## Current State

**Active Model**: Qwen2.5-Coder-7B-Instruct-AWQ (port 8001)
- **Process ID**: 607676
- **Status**: Running and healthy
- **LiteLLM Name**: `qwen-coder-vllm`
- **Internal Model**: `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ`

**Inactive Model**: Dolphin-2.8-Mistral-7B-AWQ
- **Configured for**: Port 8001 (same as Qwen)
- **Status**: Cannot run simultaneously due to VRAM constraints

## Model Switching

### Quick Switch Commands

```bash
# Switch to Qwen Coder (default)
./scripts/vllm-model-switch.sh qwen

# Switch to Dolphin (replaces Qwen)
./scripts/vllm-model-switch.sh dolphin

# Check current status
./scripts/vllm-model-switch.sh status

# Stop vLLM entirely
./scripts/vllm-model-switch.sh stop
```

### Current vLLM Process Details

```bash
# Current running command:
/home/miko/venvs/vllm/bin/python3.12 /home/miko/venvs/vllm/bin/vllm serve \
  Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \
  --host 127.0.0.1 \
  --port 8001 \
  --gpu-memory-utilization 0.85 \
  --dtype auto \
  --enforce-eager \
  --trust-remote-code \
  --enable-prefix-caching \
  --max-model-len 32768 \
  --max-num-seqs 16 \
  --max-num-batched-tokens 8192 \
  --served-model-name workspace-coder \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

## Configuration Impact

### LiteLLM Configuration

Both models are configured in `config/litellm-unified.yaml` but only the active model will work:

```yaml
# Currently WORKING (Qwen is loaded)
- model_name: qwen-coder-vllm
  litellm_params:
    model: Qwen/Qwen2.5-Coder-7B-Instruct-AWQ  # Matches loaded model
    api_base: http://127.0.0.1:8001/v1

# Currently NOT WORKING (Dolphin not loaded)
- model_name: dolphin-uncensored-vllm
  litellm_params:
    model: solidrust/dolphin-2.8-mistral-7b-v02-AWQ  # Different model
    api_base: http://127.0.0.1:8001/v1  # Same port, wrong model
```

### Fallback Behavior

When Dolphin is requested but Qwen is loaded:

1. **LiteLLM tries**: Dolphin model on port 8001
2. **vLLM responds**: With Qwen model (model name mismatch)
3. **LiteLLM detects**: Wrong model/service error
4. **Fallback triggered**: To Ollama models (llama3.1, qwen2.5-coder)

## Resolution Options

### Option 1: Model Switching (Recommended)

Use the single-instance strategy with manual switching:

```bash
# When you need Dolphin:
./scripts/vllm-model-switch.sh dolphin

# When you need Qwen:
./scripts/vllm-model-switch.sh qwen

# LiteLLM automatically routes to the active model
```

**Pros**:
- Fits within 16GB VRAM constraint
- Simple to manage
- Both models available on-demand

**Cons**:
- Manual switching required
- ~30-60 seconds switch time
- Only one model available at a time

### Option 2: Disable Dolphin Model (Not Recommended)

Remove Dolphin from LiteLLM configuration:

```yaml
# Comment out or remove:
# - model_name: dolphin-uncensored-vllm
#   litellm_params:
#     model: solidrust/dolphin-2.8-mistral-7b-v02-AWQ
```

**Pros**:
- No confusion about model availability
- Cleaner configuration

**Cons**:
- Loses Dolphin functionality
- Reduces system capability

### Option 3: Hardware Upgrade (Future)

Upgrade to 32GB+ VRAM GPU to run both models simultaneously:

```yaml
# Future configuration for multi-instance:
- model_name: qwen-coder-vllm
  litellm_params:
    api_base: http://127.0.0.1:8001/v1

- model_name: dolphin-uncensored-vllm
  litellm_params:
    api_base: http://127.0.0.1:8002/v1  # Different port
```

## Recommended Implementation

### Step 1: Clear Documentation

Update model descriptions to clarify single-instance constraint:

```yaml
model_info:
  notes: "Single instance - use vllm-model-switch.sh to change models"
```

### Step 2: Update Fallback Chains

Make fallbacks aware of active model:

```yaml
fallbacks:
  - qwen-coder-vllm:
      fallback_models:
        - llama3.1:latest      # Always available
        - qwen2.5-coder:7b    # Always available

  - dolphin-uncensored-vllm:
      fallback_models:
        - llama3.1:latest      # Always available
        - qwen2.5-coder:7b    # Always available
```

### Step 3: Improve Switching Script

Enhance `vllm-model-switch.sh` to:
- ✅ Update LiteLLM configuration automatically
- ✅ Notify when model switch is complete
- ✅ Verify model is responding before returning
- ✅ Handle errors gracefully

## Current Recommendations

### For Development Use

**Keep Qwen as default** - Better for code generation and technical tasks
- Switch to Dolphin only when specifically needed
- Use fallback Ollama models for general chat

### For Production Use

**Implement model switching API endpoint**:
```bash
# Future enhancement: HTTP endpoint for model switching
POST http://localhost:8001/admin/switch-model
{
  "model": "dolphin"  # or "qwen"
}
```

### Monitoring

**Track model availability**:
```bash
# Check which model is currently active
curl http://localhost:8001/v1/models | jq '.data[0].id'

# Should return:
# "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"  # When Qwen is active
# "solidrust/dolphin-2.8-mistral-7b-v02-AWQ"  # When Dolphin is active
```

## Summary

The AI Backend Unified Infrastructure is working correctly with the hardware constraints. The "Dolphin not working" issue is expected behavior - only one vLLM model can run at a time on 16GB VRAM.

**Next Steps**:
1. Use `./scripts/vllm-model-switch.sh` to change models when needed
2. Document the single-instance constraint for users
3. Consider hardware upgrade for simultaneous model availability
4. Implement automatic LiteLLM config updates when switching models
