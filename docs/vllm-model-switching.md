# vLLM Model Switching Guide

## Overview

The ai-backend-unified project uses a **single-instance vLLM strategy** due to hardware constraints (16GB VRAM). Only one vLLM model can run at a time, but both models are available through manual switching.

## Hardware Constraints

| Resource | Available | Per Model Requirement | Max Concurrent |
|----------|-----------|----------------------|----------------|
| **VRAM** | 16GB | ~12-13GB | **1 model** |
| GPU | Quadro RTX 5000 | Full utilization | 1 instance |

**Why single-instance?**
- Qwen Coder: ~5.2GB model + ~7.4GB KV cache = 12.6GB
- Dolphin: ~5-6GB model + ~7GB KV cache = 12-13GB
- **Both together: ~25GB > 16GB available ❌**

## Available Models

### Qwen2.5-Coder-7B-Instruct-AWQ (Default)
- **Model**: `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ`
- **Port**: 8001
- **Specialty**: Code generation and technical tasks
- **Quantization**: AWQ (4-bit)
- **VRAM**: ~12.6GB
- **Context**: 4096 tokens
- **Tool Calling**: Enabled (Hermes parser)
- **API name**: `qwen-coder-vllm`

### Dolphin-2.8-Mistral-7B-v02-AWQ
- **Model**: `solidrust/dolphin-2.8-mistral-7b-v02-AWQ`
- **Port**: 8001 (same as Qwen)
- **Specialty**: Uncensored conversational AI
- **Quantization**: AWQ (4-bit)
- **VRAM**: ~12-13GB
- **Context**: 8192 tokens
- **Tool Calling**: Enabled (Hermes parser)
- **API name**: `dolphin-uncensored-vllm`

## Model Switching Script

### Quick Commands

```bash
# Check current status
./scripts/vllm-model-switch.sh status

# Switch to Qwen Coder (code generation)
./scripts/vllm-model-switch.sh qwen

# Switch to Dolphin (uncensored conversational)
./scripts/vllm-model-switch.sh dolphin

# Stop vLLM server
./scripts/vllm-model-switch.sh stop

# Restart current model
./scripts/vllm-model-switch.sh restart
```

### Script Features

- **Graceful shutdown**: Stops current model cleanly
- **Health checks**: Waits for new model to be fully loaded
- **Logging**: Separate logs for each model in `/tmp/`
- **Color-coded output**: Clear status indicators
- **Auto-recovery**: Falls back to force kill if needed

## Manual Model Switching

If you prefer manual control:

### Step 1: Stop Current Model

```bash
pkill -f "vllm serve"
```

### Step 2: Start Qwen Coder

```bash
cd /home/miko
nohup /home/miko/venvs/vllm/bin/vllm serve Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \
  --host 0.0.0.0 \
  --port 8001 \
  --gpu-memory-utilization 0.85 \
  --dtype auto \
  --enforce-eager \
  --trust-remote-code \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  > /tmp/vllm-qwen-coder.log 2>&1 &
```

### Step 2 (Alternative): Start Dolphin

```bash
cd /home/miko
nohup /home/miko/venvs/vllm/bin/vllm serve solidrust/dolphin-2.8-mistral-7b-v02-AWQ \
  --host 0.0.0.0 \
  --port 8001 \
  --quantization awq \
  --gpu-memory-utilization 0.8 \
  --dtype auto \
  --trust-remote-code \
  --max-model-len 8192 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  > /tmp/vllm-dolphin.log 2>&1 &
```

### Step 3: Verify Model is Running

```bash
# Check process
ps aux | grep vllm

# Check API availability
curl http://localhost:8001/v1/models | jq

# Test completion
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }' | jq
```

## LiteLLM Integration

Both models are configured in `config/litellm-unified.yaml`:

```yaml
# Only ONE can run at a time
- model_name: qwen-coder-vllm          # Default
- model_name: dolphin-uncensored-vllm  # Requires manual switch
```

### Using Through LiteLLM Gateway

```bash
# Qwen Coder (if running)
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-coder-vllm",
    "messages": [{"role": "user", "content": "Write a Python function"}],
    "max_tokens": 200
  }'

# Dolphin (if running)
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "dolphin-uncensored-vllm",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "max_tokens": 300
  }'
```

## Fallback Behavior

LiteLLM is configured with automatic fallbacks:

- **qwen-coder-vllm** → `qwen2.5-coder:7b` (Ollama)
- **dolphin-uncensored-vllm** → `llama3.1:latest` (Ollama)

**During model switching:**
1. Client requests `qwen-coder-vllm` or `dolphin-uncensored-vllm`
2. If vLLM is down (switching), LiteLLM automatically retries with fallback
3. Request completes using Ollama backend (brief performance impact)
4. Once vLLM is back, future requests route to vLLM again

## Best Practices

### When to Use Each Model

**Qwen Coder** (Default):
- Code generation and review
- Technical documentation
- API design and implementation
- Debugging assistance
- Code explanation

**Dolphin** (Alternate):
- Creative writing
- Uncensored conversations
- Role-playing scenarios
- Long-form content generation
- General chat without content filters

### Recommended Workflow

1. **Default**: Keep Qwen Coder running for daily development work
2. **Switch**: Use `./scripts/vllm-model-switch.sh dolphin` when needed
3. **Revert**: Switch back to Qwen when done with conversational tasks
4. **Monitor**: Check logs if performance degrades

### Performance Considerations

- **Switching time**: ~30-60 seconds (model download + loading)
- **GPU memory release**: ~2-3 seconds after shutdown
- **First request latency**: ~1-2 seconds (KV cache warmup)
- **Steady-state**: <100ms for short prompts

## Troubleshooting

### Model Won't Start

```bash
# Check logs
tail -f /tmp/vllm-qwen-coder.log
tail -f /tmp/vllm-dolphin.log

# Check GPU memory
nvidia-smi

# Force cleanup
pkill -9 -f "vllm serve"
```

### Port Already in Use

```bash
# Find what's using port 8001
lsof -i :8001

# Kill specific process
kill -9 <PID>
```

### Out of Memory Errors

```bash
# Reduce GPU memory utilization
# Edit script and change --gpu-memory-utilization to 0.7 or 0.75
```

### Model Loads But Requests Fail

```bash
# Check vLLM is responding
curl http://localhost:8001/v1/models

# Check LiteLLM can reach vLLM
curl http://localhost:4000/v1/models

# Verify model name matches
grep model_name config/litellm-unified.yaml
```

## Future Considerations

### If You Upgrade to 32GB+ VRAM

With more VRAM, you can run both models simultaneously on different ports:

1. **Update config/litellm-unified.yaml**:
   ```yaml
   - model_name: qwen-coder-vllm
     litellm_params:
       api_base: http://127.0.0.1:8001/v1

   - model_name: dolphin-uncensored-vllm
     litellm_params:
       api_base: http://127.0.0.1:8002/v1
   ```

2. **Start both models**:
   ```bash
   vllm serve Qwen/... --port 8001 &
   vllm serve solidrust/dolphin... --port 8002 &
   ```

3. **No switching needed**: Both models available 24/7

### Alternative: Smaller Models

If you need both models running simultaneously on 16GB:
- Use smaller quantizations (GPTQ/GGUF)
- Reduce context window (--max-model-len 2048)
- Lower KV cache reservation (--gpu-memory-utilization 0.5)

**Trade-off**: Lower quality and shorter context windows

## References

- [vLLM Documentation](https://docs.vllm.ai/)
- [LiteLLM Multi-Provider Setup](https://docs.litellm.ai/)
- [AWQ Quantization](https://github.com/mit-han-lab/llm-awq)
- [Project Configuration](../config/litellm-unified.yaml)
