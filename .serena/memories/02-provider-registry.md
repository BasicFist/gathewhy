# Provider Registry - Complete Reference

## Overview

The provider registry (`config/providers.yaml`) is the master catalog of all LLM inference providers available in the LAB ecosystem. Each provider entry defines connection details, capabilities, models, health endpoints, and integration status.

## Active Providers

### 1. Ollama (ollama)

**Purpose**: General-purpose local model server with easy management

**Connection**:
- Base URL: `http://127.0.0.1:11434`
- Health Endpoint: `/api/tags`
- Status: **Active**

**Features**:
- Easy model management (`ollama pull`, `ollama list`)
- CPU and GPU support with automatic detection
- Quantized GGUF format for efficient memory usage
- Fast model switching without server restart
- Native chat and completion endpoints

**Models Available**:

1. **llama3.1:8b**
   - Size: 8B parameters
   - Quantization: Q4_K_M (4-bit medium quality)
   - Use Case: General-purpose chat, reasoning
   - Context Window: 8192 tokens
   - Pulled: 2025-10-19

2. **qwen2.5-coder:7b**
   - Size: 7.6B parameters
   - Quantization: Q4_K_M
   - Specialty: Code generation, technical tasks
   - Context Window: 32768 tokens (exceptional)
   - Pulled: 2025-10-19

**Performance Characteristics**:
- Latency: 50-200ms TTFT for 8B models
- Throughput: ~30-40 tokens/sec on GPU
- Memory: ~5-6GB VRAM per 8B Q4 model
- Concurrency: Moderate (2-4 concurrent requests)

**Integration Location**:
- Physical: Integrated within OpenWebUI container
- Config: OpenWebUI manages Ollama lifecycle
- Port: 11434 exposed to localhost only

**Best For**:
- Quick prototyping and experimentation
- Model comparison and testing
- Development workflows
- Small to medium workloads

---

### 2. llama.cpp Python Bindings (llama_cpp_python)

**Purpose**: High-performance CUDA-optimized inference via Python bindings

**Connection**:
- Base URL: `http://127.0.0.1:8000`
- Health Endpoint: `/v1/models`
- API Format: OpenAI-compatible
- Status: **Active**

**Features**:
- Full or partial GPU offloading (configurable layers)
- Extended context windows (up to 8192 tokens configured)
- Parallel request handling (4 concurrent)
- OpenAI-compatible `/v1/chat/completions` endpoint
- Efficient memory management

**Configuration**:
```yaml
n_gpu_layers: -1          # -1 = full GPU offload
n_ctx: 8192               # context window size
n_parallel: 4             # concurrent requests
threads: 6                # CPU threads for non-GPU ops
```

**Performance Characteristics**:
- Latency: 30-150ms TTFT (faster than Ollama)
- Throughput: ~40-50 tokens/sec
- Memory: Efficient KV cache management
- Concurrency: Good (4 parallel requests)

**Service Management**:
- systemd Service: `~/.config/systemd/user/llamacpp-python.service`
- Auto-start: Enabled
- Logs: `journalctl --user -u llamacpp-python`

**Integration Location**:
- Physical: `../openwebui/backends/llama.cpp`
- Model Storage: `../openwebui/backends/llama.cpp/models/`
- Binaries: Python package `llama-cpp-python`

**Best For**:
- Single-request performance optimization
- CUDA-accelerated inference
- Extended context window requirements
- Production workloads with moderate concurrency

---

### 3. llama.cpp Native C++ Server (llama_cpp_native)

**Purpose**: Maximum performance pure C++ inference server

**Connection**:
- Base URL: `http://127.0.0.1:8080`
- Health Endpoint: `/v1/models`
- API Format: OpenAI-compatible
- Status: **Active**

**Features**:
- Pure C/C++ implementation (no Python overhead)
- Maximum throughput for single requests
- CUDA-optimized kernels
- Minimal memory footprint
- Direct hardware access

**Performance Characteristics**:
- Latency: 20-120ms TTFT (fastest available)
- Throughput: ~50-60 tokens/sec
- Memory: Most efficient KV cache
- Concurrency: Limited (best for single high-priority requests)

**Integration Location**:
- Physical: `../openwebui/backends/llama.cpp`
- Binary: Native compiled `server` executable
- Build: CUDA-enabled compilation

**Best For**:
- Maximum single-request speed
- Low-latency requirements
- Resource-constrained environments
- Backup/failover provider

---

### 4. vLLM (vllm)

**Purpose**: Production-grade high-throughput batched inference

**Connection**:
- Base URL: `http://127.0.0.1:8001`
- Health Endpoint: `/v1/models`
- API Format: OpenAI-compatible
- Status: **Pending Integration** (will be active after Phase 3)

**Features**:
- Continuous batching for high throughput
- PagedAttention for efficient KV cache management
- Optimized for 13B-70B parameter models
- Superior concurrent request handling
- Production-grade performance and reliability

**Models Configured**:

1. **meta-llama/Llama-2-13b-chat-hf**
   - Size: 13B parameters
   - Context: 4096 tokens
   - Specialty: Chat, conversational AI
   - VRAM: ~26GB (FP16)
   - Batch Size: Dynamic (depends on context length)

**Performance Characteristics**:
- Latency: 100-300ms TTFT (higher due to batching)
- Throughput: ~80-120 tokens/sec (batched)
- Memory: High VRAM usage, efficient for concurrent
- Concurrency: Excellent (10+ concurrent requests)

**Advanced Features**:
- GPU Memory Utilization: 0.9 (90% VRAM usage)
- Tensor Parallelism: Supported for multi-GPU
- Speculative Decoding: Available
- Beam Search: Supported

**MCP Integration**:
- MCP Server: Available in CrushVLLM
- MCP Tools:
  - `generate_text`: Text completion
  - `chat_completion`: Chat interface
  - `stream_completion`: Streaming generation
  - `server_status`: Health and metrics
  - `server_metrics`: Performance data

**Integration Location**:
- Physical: `../CRUSHVLLM`
- Language: Go (TUI) + Python (vLLM server)
- Config: `../CRUSHVLLM/configs/`

**Best For**:
- High concurrency production workloads
- Large models (13B+)
- Batched inference scenarios
- Enterprise-grade reliability requirements

---

## Template Providers (Disabled)

### OpenAI (openai)

**Status**: Disabled (template for reference)

**Connection**:
- Base URL: `https://api.openai.com/v1`
- Requires: API Key (`OPENAI_API_KEY` environment variable)

**Models**:
- gpt-4
- gpt-3.5-turbo

**Rate Limits**:
- Requests per minute: 3500
- Tokens per minute: 90000

**Cost**:
- GPT-4: $0.03 per 1K tokens
- GPT-3.5-turbo: $0.0015 per 1K tokens

**When to Enable**:
- Need cutting-edge capabilities beyond local models
- Budget available for cloud API costs
- Require GPT-4 level reasoning
- Fallback for when local providers unavailable

---

### Anthropic (anthropic)

**Status**: Disabled (template for reference)

**Connection**:
- Base URL: `https://api.anthropic.com/v1`
- Requires: API Key (`ANTHROPIC_API_KEY` environment variable)

**Models**:
- claude-3-opus-20240229
- claude-3-sonnet-20240229

**When to Enable**:
- Long-context requirements (100K+ tokens)
- Complex reasoning tasks
- Production-grade reliability from cloud
- Specific Claude capabilities needed

---

### Custom OpenAI-Compatible (custom_openai_compatible)

**Status**: Template

**Purpose**: Add any OpenAI-compatible API server

**Use Cases**:
- LocalAI servers
- Text Generation WebUI
- FastChat servers
- Custom inference endpoints
- Third-party LLM providers

**Configuration Template**:
```yaml
custom_provider:
  type: openai_compatible
  base_url: http://localhost:CUSTOM_PORT
  status: active
  models:
    - custom-model-name
  health_endpoint: /v1/models
```

---

## Provider Selection Criteria

### When to Use Ollama
✅ Quick prototyping and testing
✅ Easy model management
✅ General development work
✅ Resource-efficient operation
❌ Not for maximum performance
❌ Limited concurrent capacity

### When to Use llama.cpp (Python or Native)
✅ Maximum single-request performance
✅ CUDA optimization critical
✅ Extended context windows needed
✅ Production single-user scenarios
❌ Not for high concurrency
❌ More complex setup than Ollama

### When to Use vLLM
✅ High concurrency requirements (10+ concurrent)
✅ Large models (13B+ parameters)
✅ Production-grade reliability needed
✅ Batched inference scenarios
❌ Not for low-latency single requests
❌ Requires significant VRAM

### When to Use Cloud Providers (OpenAI/Anthropic)
✅ Cutting-edge capabilities required
✅ Budget available for API costs
✅ Fallback for local unavailability
✅ Specific model features needed
❌ Higher latency than local
❌ Privacy/data concerns
❌ Ongoing costs

---

## Health Check Configuration

### Health Check System
- **Interval**: 60 seconds
- **Timeout**: 5 seconds per check
- **Retries**: 3 attempts before marking unhealthy
- **Cooldown**: 300 seconds (5 minutes) after failure

### Health Endpoints
```yaml
ollama: http://127.0.0.1:11434/api/tags
llama_cpp_python: http://127.0.0.1:8000/v1/models
llama_cpp_native: http://127.0.0.1:8080/v1/models
vllm: http://127.0.0.1:8001/v1/models
```

### Provider States
- `active`: Healthy, accepting requests
- `degraded`: High latency but functional
- `unavailable`: Health check failed
- `cooldown`: Recently failed, in recovery period

---

## Adding New Providers

### Step-by-Step Process

1. **Add Entry to `config/providers.yaml`**
```yaml
new_provider:
  type: provider_type
  base_url: http://host:port
  status: active
  description: "Provider description"
  features: [list, of, features]
  models: [model definitions]
  health_endpoint: /health
```

2. **Define Routing in `config/model-mappings.yaml`**
```yaml
exact_matches:
  "new-model-name":
    provider: new_provider
    priority: primary
    fallback: existing_provider
```

3. **Add to `config/litellm-unified.yaml`**
```yaml
model_list:
  - model_name: new-model-alias
    litellm_params:
      model: provider/model-path
      api_base: http://host:port
    model_info:
      tags: [relevant, tags]
      provider: new_provider
```

4. **Update Documentation**
- Update this memory file
- Add to `docs/adding-providers.md`
- Update architecture diagram if new provider type

5. **Test Integration**
```bash
./scripts/validate-unified-backend.sh
curl http://localhost:4000/v1/models | jq
```

---

## Provider Metadata Summary

**Total Providers**: 4 active (Ollama, llama.cpp Python, llama.cpp Native, vLLM)
**Total Models Available**: 5 (2 Ollama, 1 vLLM, 2 llama.cpp endpoints)
**Total Capacity**: ~50+ concurrent requests across all providers
**Combined VRAM**: ~35GB required for all providers active
**API Compatibility**: 100% OpenAI-compatible

**Provider Types**:
- **ollama**: Simple local server
- **llama_cpp**: High-performance C++ inference
- **vllm**: Production-grade batched inference
- **openai**: Cloud API providers (disabled)
- **openai_compatible**: Generic compatible servers (template)

**Version**: 1.0
**Last Updated**: 2025-10-19
