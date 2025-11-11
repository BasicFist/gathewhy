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

1. **llama3.1:latest**
   - Size: 8B parameters
   - Quantization: Q4_K_M (4-bit medium quality)
   - Use Case: General-purpose chat, reasoning
   - Context Window: 8192 tokens
   - Pulled: 2025-10-19
   - **Note**: Canonical name changed from `:8b` to `:latest` for version flexibility

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

**Purpose**: Production-grade high-throughput batched inference with AWQ quantization

**Connection**:
- Base URL: `http://127.0.0.1:8001`
- Health Endpoint: `/v1/models`
- API Format: OpenAI-compatible
- Status: **Active** ✅ (restored 2025-10-23)

**Features**:
- Continuous batching for high throughput
- PagedAttention for efficient KV cache management
- AWQ 4-bit quantization for memory efficiency
- Optimized for code generation workloads
- Production-grade performance and reliability
- OpenAI API compliant (chat/completions, streaming)

**Models Deployed**:

1. **Qwen/Qwen2.5-Coder-7B-Instruct-AWQ**
   - Size: 7B parameters (AWQ 4-bit quantized)
   - Model Size: 5.2GB (vs 14.2GB unquantized)
   - Context: 4096 tokens
   - Specialty: Code generation, technical tasks
   - VRAM Required: 16GB (Quadro RTX 5000)
   - KV Cache Available: 7.36GB
   - Max Concurrency: 33.63x for 4096-token requests
   - Cache Capacity: 137,744 tokens

**Performance Characteristics** (Validated 2025-10-21):
- Latency: 100-200ms TTFT (first token)
- Throughput: Real-time streaming
- Memory: GPU 90% utilization (14.0GB/15.5GB)
- Concurrency: Excellent (33.63x for 4096-token requests)
- Code Quality: Production-ready, Pythonic solutions

**Hardware Requirements**:
- GPU: NVIDIA with 16GB+ VRAM
- Compute Capability: 7.5+ (Turing architecture or newer)
- CUDA: 12.x
- System RAM: 16GB+ recommended

**Deployment Configuration**:
```bash
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \
  --port 8001 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096
```

**Integration Location**:
- Installation: `~/venvs/vllm` (Python virtual environment)
- vLLM Version: 0.11.0
- Model Cache: `~/.cache/huggingface/hub/`
- Logs: `~/vllm_awq.log`

**Tested Capabilities** (Phase 3 Integration Tests - 2025-10-21):
- ✅ Health endpoint (`/health`)
- ✅ Model availability (`/v1/models`)
- ✅ Chat completions (`/v1/chat/completions`)
- ✅ Streaming responses (SSE format)
- ✅ Token usage reporting
- ✅ Code generation quality (prime numbers, fibonacci, etc.)

**Known Limitations**:
- Context window: 4096 tokens (hardware constraint)
- Model specialty: Code generation (not general chat)
- Quantization: AWQ 4-bit (minimal quality loss vs FP16)
- GPU dependency: Requires NVIDIA GPU with CUDA support

**Best For**:
- Code generation and technical tasks
- High concurrency code completion requests
- Production workloads on 16GB VRAM GPUs
- Memory-efficient inference with AWQ quantization
- Real-time streaming code suggestions

**Configuration Status**: ✅ Restored 2025-10-23 after accidental removal

---

### 5. Ollama Cloud (ollama_cloud)

**Purpose**: Managed cloud API for massive models without local GPU requirements

**Connection**:
- Base URL: `https://ollama.com`
- Health Endpoint: `/api/tags`
- API Format: Ollama-compatible (ollama_chat prefix for LiteLLM)
- Status: **Active** ✅ (added 2025-10-30)
- Requires: API Key (`OLLAMA_API_KEY` environment variable)

**Features**:
- Cloud-hosted massive models (no local GPU required)
- Data-center-grade hardware and infrastructure
- Same API as local Ollama (seamless integration)
- Automatic offloading for cloud-only models
- Free preview tier with generous rate limits
- Models up to 1 trillion parameters

**Models Deployed**:

1. **deepseek-v3.1:671b-cloud**
   - Size: 671B parameters
   - Specialty: Advanced reasoning, analysis
   - Use Case: Complex research, multi-step problem solving
   - Fallback Chain: kimi-k2:1t → gpt-oss:120b → llama3.1:8b

2. **qwen3-coder:480b-cloud**
   - Size: 480B parameters
   - Specialty: Code generation, technical tasks
   - Use Case: Complex code, architectural design
   - Fallback Chain: gpt-oss:120b → qwen-coder-vllm → qwen2.5-coder:7b

3. **kimi-k2:1t-cloud**
   - Size: 1 Trillion parameters (largest available)
   - Specialty: Advanced reasoning, research
   - Use Case: Extreme complexity tasks, academic research
   - Fallback Chain: None (fail if unavailable - quality preservation)

4. **gpt-oss:120b-cloud**
   - Size: 120B parameters
   - Specialty: General chat, analysis
   - Use Case: General-purpose with cloud scale
   - Fallback Chain: gpt-oss:20b → glm-4.6 → llama3.1:8b

5. **gpt-oss:20b-cloud**
   - Size: 20B parameters
   - Specialty: General chat
   - Use Case: Mid-tier cloud inference
   - Fallback Chain: glm-4.6 → llama3.1:8b

6. **glm-4.6:cloud**
   - Size: 4.6B parameters
   - Specialty: General chat, lightweight
   - Use Case: Fast cloud inference for simple tasks
   - Fallback Chain: llama3.1:8b

**Performance Characteristics**:
- Latency: 150-1200ms TTFT (varies by model size)
  - glm-4.6: ~150ms
  - gpt-oss:20b: ~250ms
  - gpt-oss:120b: ~400ms
  - qwen3-coder:480b: ~600ms
  - deepseek-v3.1:671b: ~800ms
  - kimi-k2:1t: ~1200ms
- Throughput: Data-center grade (high concurrency)
- Quality: Superior to local models due to parameter count
- Cost: Free preview (rate limits apply)

**Rate Limits**:
- Hourly limits: Yes (generous for free tier)
- Daily limits: Yes
- Details: "Free preview with generous limits"
- Behavior: Returns 429 on rate limit → triggers fallback chain

**Integration**:
- API Key: Loaded from SOPS-encrypted secrets (`$OLLAMA_API_KEY`)
- Authentication: Bearer token in Authorization header
- Model Prefix: `ollama_chat/` for LiteLLM routing
- Health Checks: Same as local Ollama (`/api/tags`)

**Use Cases**:
- **Complex Reasoning**: Tasks requiring 100B+ parameter models
- **Code Architecture**: Large-scale system design, refactoring
- **Research**: Academic analysis, literature review
- **Fallback**: When local GPUs insufficient for task complexity
- **Development**: Testing with massive models before local deployment

**Routing Strategy** (v1.7):
- **Cloud-first routing**: Certain tasks route directly to cloud (capability: reasoning + complexity: high)
- **Local-first with cloud fallback**: Most tasks try local first, fall back to cloud
- **Cloud-only**: Kimi K2 (1T) has no fallback - returns error if unavailable
- **Quality preservation**: Cloud models fall back to other cloud models before local

**Best For**:
- Tasks requiring >13B models
- Complex multi-step reasoning
- Advanced code generation and architecture
- Research and academic analysis
- Fallback when local VRAM exhausted

**Not Recommended For**:
- Simple chat (use local llama3.1:8b)
- Quick code snippets (use local qwen2.5-coder)
- Privacy-sensitive data (cloud API)
- Offline environments

**Configuration Status**: ✅ Active since 2025-10-30

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

## OpenWebUI Integration (Relocated)

**Status**: Services relocated to OpenWebUI project (../openwebui)

**Note**: As of 2025-10-23, OpenWebUI pipelines, toolsrv, and frontend are managed within the OpenWebUI project, not this coordination project. These services run independently:

- **Pipelines**: Port 9099 (academic_search, market_snapshot, smart_router, hybrid_search, consensus, code_analyzer, comfyui_generator)
- **Toolsrv**: Port 8600 (arXiv, PubMed, market data APIs)
- **Frontend**: Port 5000 (Web UI with RAG)

**Integration**: These services are available but documented separately in the OpenWebUI project.

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
✅ Code generation workloads
✅ Production-grade reliability needed
✅ AWQ quantization for memory efficiency
❌ Not for low-latency single requests
❌ Requires 16GB+ VRAM

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

**Total Providers**: 5 active (Ollama, llama.cpp Python, llama.cpp Native, vLLM, Ollama Cloud)
**Total Models Available**: 13 (3 local Ollama, 1 vLLM, 6 Ollama Cloud, 3 llama.cpp generic)
**Total Capacity**: ~70+ concurrent requests (local) + unlimited (cloud with rate limits)
**Combined VRAM**: ~20GB required for all local providers active (with AWQ quantization)
**API Compatibility**: 100% OpenAI-compatible

**Provider Types**:
- **ollama**: Simple local server (3 models: llama3.1, qwen2.5-coder, mythomax-l2-13b)
- **ollama_cloud**: Managed cloud API for massive models (6 models: up to 1T parameters)
- **llama_cpp**: High-performance C++ inference (GGUF support)
- **vllm**: Production-grade batched inference with AWQ quantization
- **openai**: Cloud API providers (disabled template)
- **openai_compatible**: Generic compatible servers (template)

**Deployment Status** (2025-11-11):
- ✅ Ollama: Active with llama3.1:latest, qwen2.5-coder:7b, mythomax-l2-13b-q5_k_m
- ✅ llama.cpp Python: Active on port 8000
- ✅ llama.cpp Native: Active on port 8080
- ✅ vLLM: Active with Qwen2.5-Coder-7B-Instruct-AWQ on port 8001
- ✅ Ollama Cloud: Active with 6 models (deepseek-v3.1:671b, qwen3-coder:480b, kimi-k2:1t, gpt-oss:120b/20b, glm-4.6)

**Model Distribution**:
- Local <10B: 3 models (llama3.1:8b, qwen2.5-coder:7b, qwen-coder-vllm:7b-awq)
- Local 10-15B: 1 model (mythomax-l2-13b-q5_k_m)
- Cloud 1-100B: 3 models (glm-4.6, gpt-oss:20b, gpt-oss:120b)
- Cloud 100B+: 3 models (qwen3-coder:480b, deepseek-v3.1:671b, kimi-k2:1t)

**Routing Architecture**: v1.7 (quality-preserving-fallbacks)
- Cloud fallback chains: Cloud → Cloud → Local (tier preservation)
- Capability-based routing: 8 clear categories (code, analytical, reasoning, creative, chat, high_throughput, low_latency, large_context)
- Load balancing: 4 strategies (weighted, complexity-based, quality-based)
- vLLM single-instance pattern: Qwen Coder active on :8001, Dolphin disabled

**Recent Changes**:
- 2025-11-11: Added Ollama Cloud provider (6 massive cloud models)
- 2025-11-11: Routing v1.7 - Fixed cloud fallback chains (quality-preserving)
- 2025-11-11: Consolidated capabilities (10 → 8, eliminated overlaps)
- 2025-11-11: Added intelligent load balancing for code generation
- 2025-11-11: Documented vLLM single-instance pattern
- 2025-10-30: Added mythomax-l2-13b-q5_k_m for creative writing
- 2025-10-23: Restored vLLM provider after accidental removal
- 2025-10-23: Standardized llama3.1 model name to `:latest`

**Version**: 1.4
**Last Updated**: 2025-11-11
