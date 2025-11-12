# Model Mappings - Comprehensive Guide

## Overview

Model mappings define how model names in client requests are translated to specific provider endpoints. This memory documents all mapping patterns, best practices, and troubleshooting guidance.

## Model Naming Philosophy

### Three Naming Layers

**Layer 1: Client-Facing Model Names** (What users request)
- Simple, memorable names: `llama3.1:8b`, `qwen-coder`
- Hide implementation details from consumers
- Stable across provider changes

**Layer 2: LiteLLM Model Aliases** (Routing layer)
- Internal routing identifiers: `llama3.1-ollama`, `llama2-13b-vllm`
- Provider-specific variants for same logical model
- Enable A/B testing and gradual rollouts

**Layer 3: Provider Model Paths** (Backend implementation)
- Provider-native identifiers: `ollama/llama3.1:8b`, `vllm/meta-llama/Llama-2-13b-chat-hf`
- Direct mapping to provider APIs
- Include version and variant information

### Example: Three-Layer Mapping

```yaml
Client Request:
  model: "llama3.1:8b"

LiteLLM Routing:
  model_name: llama3.1-ollama
  model_alias: llama3.1:8b

Provider Call:
  litellm_params:
    model: ollama/llama3.1:8b
    api_base: http://127.0.0.1:11434
```

---

## Complete Model Registry

### Ollama Models

#### llama3.1:8b
```yaml
Client Name: "llama3.1:8b"
Aliases: ["llama3.1-ollama", "llama3.1"]
Provider: ollama
Backend Path: "ollama/llama3.1:8b"
API Base: http://127.0.0.1:11434

Capabilities:
  - general_chat
  - reasoning
  - summarization
  - question_answering

Tags: ["general", "chat", "8b"]
Context Window: 8192 tokens
Quantization: Q4_K_M
VRAM Required: ~5GB
```

**Usage Example**:
```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

#### qwen2.5-coder:7b
```yaml
Client Name: "qwen-coder"
Aliases: ["qwen2.5-coder:7b", "qwen-coder"]
Provider: ollama
Backend Path: "ollama/qwen2.5-coder:7b"
API Base: http://127.0.0.1:11434

Capabilities:
  - code_generation
  - code_completion
  - code_explanation
  - debugging

Tags: ["code", "specialized", "7b"]
Context Window: 32768 tokens (exceptional)
Quantization: Q4_K_M
VRAM Required: ~4.5GB
Specialty: Code generation and technical tasks
```

**Usage Example**:
```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "X-Capability: code_generation" \
  -d '{
    "model": "qwen-coder",
    "messages": [{
      "role": "user",
      "content": "Write a Python function to calculate Fibonacci"
    }]
  }'
```

### vLLM Models

#### llama2-13b-vllm
```yaml
Client Name: "llama2-13b-vllm"
Aliases: ["llama2-13b", "llama2-chat"]
Provider: vllm
Backend Path: "vllm/meta-llama/Llama-2-13b-chat-hf"
API Base: http://127.0.0.1:8001

Capabilities:
  - high_throughput
  - chat
  - batched_inference
  - production_workload

Tags: ["chat", "high-throughput", "13b", "vllm"]
Context Window: 4096 tokens
Precision: FP16
VRAM Required: ~26GB
Max Batch Size: Dynamic (depends on context)
```

**Usage Example**:
```bash
# Single request
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{
    "model": "llama2-13b-vllm",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Streaming request
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{
    "model": "llama2-13b-vllm",
    "stream": true,
    "messages": [{"role": "user", "content": "Tell me a story"}]
  }'
```

### llama.cpp Models

#### llama-cpp-default (llama_cpp_python)
```yaml
Client Name: "llama-cpp-default"
Aliases: ["llamacpp", "llama-cpp"]
Provider: llama_cpp_python
Backend Path: "openai/local-model"
API Base: http://127.0.0.1:8000

Capabilities:
  - low_latency
  - cuda_optimized
  - large_context
  - provider_diversity  # NEW: Integrated into fallback chains

Tags: ["gguf", "cuda", "high-performance"]
Context Window: 8192 tokens (configured)
Concurrency: 4 parallel requests
TTFB: ~80ms (CUDA-optimized)
Notes: "Python bindings, n_parallel=4, n_ctx=8192"

Fallback Chain (v1.7.1):
  - llama-cpp-native       # Same provider, faster C++ binding
```

**NEW in v1.7.1**: Now integrated into fallback chains for provider diversity!

#### llama-cpp-native
```yaml
Client Name: "llama-cpp-native"
Aliases: ["llamacpp-native"]
Provider: llama_cpp_native
Backend Path: "openai/local-model"
API Base: http://127.0.0.1:8080

Capabilities:
  - maximum_performance
  - low_latency
  - cuda_optimized
  - terminal_node  # NEW: Serves as fallback terminus

Tags: ["gguf", "cuda", "maximum-performance", "terminal"]
TTFB: ~50ms (Fastest local option - pure C++)
Notes: "Pure C++ server, no Python overhead, TERMINAL NODE"

Fallback Chain (v1.7.1):
  - []  # Terminal node - fastest local fallback terminus
```

**NEW in v1.7.1**: Serves as terminal node (fastest local option) for fallback chains!

---

## Mapping Patterns

### Pattern 1: Exact Name Match

**Use Case**: Production models with guaranteed routing

```yaml
exact_matches:
  "llama3.1:8b":
    provider: ollama
    priority: primary
    fallback: null
```

**Client Request**:
```json
{"model": "llama3.1:8b"}
```

**Routing Decision**:
- ✅ Exact match found
- Routes to: Ollama :11434
- No fallback needed
- Fastest routing decision

### Pattern 2: HuggingFace Model Paths

**Use Case**: Direct HuggingFace model references

```yaml
patterns:
  - pattern: "^meta-llama/.*"
    provider: vllm
    fallback: ollama
```

**Client Request**:
```json
{"model": "meta-llama/Llama-2-7b-chat-hf"}
```

**Routing Decision**:
- ❌ No exact match
- ✅ Pattern match: `^meta-llama/.*`
- Routes to: vLLM :8001
- Fallback: Ollama if vLLM unavailable

### Pattern 3: Ollama Naming Convention

**Use Case**: Auto-detect Ollama-style model names

```yaml
patterns:
  - pattern: ".*:\\d+[bB]$"  # Matches "model:7b", "model:13B"
    provider: ollama
```

**Client Request**:
```json
{"model": "mistral:7b"}
```

**Routing Decision**:
- ❌ No exact match
- ✅ Pattern match: `.*:\\d+[bB]$`
- Routes to: Ollama :11434
- Assumes model is pulled in Ollama

### Pattern 4: GGUF File Detection

**Use Case**: Route quantized GGUF models to llama.cpp

```yaml
patterns:
  - pattern: ".*\\.gguf$"
    provider: llama_cpp_python
    fallback: llama_cpp_native
```

**Client Request**:
```json
{"model": "llama-2-7b-chat.Q4_K_M.gguf"}
```

**Routing Decision**:
- ❌ No exact match
- ✅ Pattern match: `.*\\.gguf$`
- Routes to: llama.cpp Python :8000
- Fallback: llama.cpp Native :8080

### Pattern 5: Capability-Based

**Use Case**: Route by task type, not model name

```yaml
capabilities:
  code_generation:
    preferred_models:
      - qwen2.5-coder:7b
    provider: ollama
```

**Client Request**:
```bash
curl -H "X-Capability: code_generation" \
  -d '{"messages": [...]}'
```

**Routing Decision**:
- No model specified in request body
- X-Capability header detected
- Routes to: qwen2.5-coder:7b on Ollama
- Optimized for code generation tasks

---

## Model Groups and Aliases

### General Chat Group
```yaml
model_group_alias:
  general_chat:
    - llama3.1-ollama
    - llama2-13b-vllm
    - llama-cpp-python
```

**Behavior**:
- Client requests `general_chat` model group
- LiteLLM selects best available from group
- Selection based on: load, latency, success rate
- Automatic failover within group

**Usage**:
```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{
    "model": "general_chat",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Code Generation Group
```yaml
model_group_alias:
  code_generation:
    - qwen-coder
    - deepseek-coder  # If pulled
```

**Usage**:
```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{
    "model": "code_generation",
    "messages": [{
      "role": "user",
      "content": "Write a function to sort an array"
    }]
  }'
```

### High Throughput Group
```yaml
model_group_alias:
  high_throughput:
    - llama2-13b-vllm
```

**Usage**: Batched requests, high concurrency scenarios

---

## Fallback Mapping Strategies

### Primary-Backup Pattern
```yaml
exact_matches:
  "llama3.1:8b":
    provider: ollama
    priority: primary
    fallback: llama_cpp_python

fallbacks:
  - model: llama3.1:8b
    fallback_models:
      - llama3.1-backup  # llama.cpp version
```

**Flow**:
1. Try Ollama :11434
2. If fails → Try llama.cpp :8000
3. If fails → Return error

### Multi-Tier Fallback
```yaml
fallbacks:
  - model: llama2-13b-vllm
    fallback_models:
      - llama3.1-ollama  # Smaller model
      - llama-cpp-python  # Different backend
```

**Flow**:
1. Try vLLM :8001 (13B model)
2. If fails → Try Ollama :11434 (8B model, smaller but available)
3. If fails → Try llama.cpp :8000 (GGUF fallback)
4. If fails → Return error

### Provider Diversity Strategy
```yaml
fallbacks:
  - model: production-model
    fallback_models:
      - backup-model-provider-a
      - backup-model-provider-b
      - backup-model-provider-c
```

**Rationale**: Spread across different providers to avoid single point of failure

---

## Model Selection Decision Tree

```
Client Request: model="X"
│
├─ Exact match "X" exists?
│  ├─ Yes → Route to matched provider → DONE
│  └─ No ↓
│
├─ Pattern matches "X"?
│  ├─ Yes → Route to pattern provider → DONE
│  └─ No ↓
│
├─ "X" in model_group_alias?
│  ├─ Yes → Select from group (load balancing) → DONE
│  └─ No ↓
│
├─ X-Capability header present?
│  ├─ Yes → Route by capability → DONE
│  └─ No ↓
│
├─ Default provider available?
│  ├─ Yes → Route to default (Ollama) → DONE
│  └─ No ↓
│
└─ Return error: "Model not found"
```

---

## Adding New Model Mappings

### Step-by-Step Process

#### Step 1: Define in providers.yaml
```yaml
# config/providers.yaml
ollama:
  models:
    - name: new-model:7b
      size: "7B"
      quantization: Q4_K_M
      specialty: task_type
```

#### Step 2: Add routing in model-mappings.yaml
```yaml
# config/model-mappings.yaml
exact_matches:
  "new-model:7b":
    provider: ollama
    priority: primary
    fallback: llama_cpp_python
    description: "Description of model purpose"
```

#### Step 3: Configure in litellm-unified.yaml
```yaml
# config/litellm-unified.yaml
model_list:
  - model_name: new-model
    litellm_params:
      model: ollama/new-model:7b
      api_base: http://127.0.0.1:11434
    model_info:
      tags: ["relevant", "tags"]
      provider: ollama
```

#### Step 4: Add to capability group (optional)
```yaml
# config/model-mappings.yaml
capabilities:
  task_type:
    preferred_models:
      - new-model:7b
    provider: ollama
```

#### Step 5: Test mapping
```bash
# Test availability
curl http://localhost:4000/v1/models | jq '.data[] | select(.id=="new-model")'

# Test routing
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{
    "model": "new-model",
    "messages": [{"role": "user", "content": "Test"}]
  }'

# Verify logs
journalctl --user -u litellm.service | grep "new-model"
```

---

## Model Versioning Strategies

### Semantic Versioning in Model Names
```yaml
# Explicit version tagging
exact_matches:
  "llama3.1:8b-v1":
    provider: ollama
    backend_model: "llama3.1:8b"

  "llama3.1:8b-v2":
    provider: llama_cpp_python
    backend_model: "llama-3.1-8b-q4.gguf"
```

**Usage**: A/B testing, gradual rollouts

### Default Version Aliasing
```yaml
# "latest" points to current production version
exact_matches:
  "llama3.1:8b":
    provider: ollama
    version: "v1"

  "llama3.1:8b-latest":
    provider: ollama
    version: "v1"
```

**Benefits**: Users can specify version or get latest automatically

### Rollout Pattern
```yaml
# 90% traffic to stable, 10% to canary
redundant_models:
  "llama3.1:8b":
    providers:
      - provider: ollama
        weight: 0.9
        version: stable
      - provider: llama_cpp_python
        weight: 0.1
        version: canary
```

---

## Common Mapping Scenarios

### Scenario 1: Multi-Provider Same Model
```yaml
# llama3.1:8b available on both Ollama and llama.cpp
exact_matches:
  "llama3.1:8b":
    provider: ollama
    priority: primary
    fallback: llama_cpp_python

fallbacks:
  - model: llama3.1:8b
    fallback_models:
      - llama3.1-llamacpp
```

**Result**: Try Ollama first, fallback to llama.cpp

### Scenario 2: Task-Specific Routing
```yaml
# Code requests → specialized model
# Chat requests → general model
capabilities:
  code_generation:
    preferred_models: ["qwen-coder"]

  general_chat:
    preferred_models: ["llama3.1:8b"]
```

**Result**: Automatic model selection based on task

### Scenario 3: Size-Based Auto-Routing
```yaml
# 7B models → Ollama
# 13B+ models → vLLM
model_size_routing:
  - size: "< 8B"
    provider: ollama
  - size: "> 13B"
    provider: vllm
    fallback: ollama
```

**Result**: Optimal provider per model size

### Scenario 4: Streaming vs Non-Streaming
```yaml
# Streaming → Ollama (best streaming)
# Non-streaming → vLLM (best throughput)
request_metadata_routing:
  streaming_requests:
    provider: ollama
    condition: stream == true

  batch_requests:
    provider: vllm
    condition: stream == false
```

**Result**: Request-type optimized routing

---

## Model Mapping Best Practices

### 1. Naming Consistency
✅ **Good**: `llama3.1:8b`, `qwen-coder`, `llama2-13b-vllm`
❌ **Bad**: `llama_3_1_8b`, `QwenCoder`, `llama-2-13B-VLLM`

**Rule**: Use lowercase, hyphens for separators, consistent version format

### 2. Explicit Fallbacks
✅ **Good**: Define fallback for every production model
❌ **Bad**: Rely on default fallback only

**Rationale**: Explicit fallbacks prevent unexpected behavior

### 3. Capability Tagging
✅ **Good**: Tag models with capabilities (`code`, `chat`, `vision`)
❌ **Bad**: Generic model names with no metadata

**Benefit**: Enable capability-based routing

### 4. Provider Abstraction
✅ **Good**: `llama3.1:8b` → routes to best provider
❌ **Bad**: `ollama-llama3.1:8b` → locks to specific provider

**Benefit**: Change providers without client updates

### 5. Version Management
✅ **Good**: `model-v1`, `model-v2`, `model-latest`
❌ **Bad**: Overwrite production model definitions

**Benefit**: Safe rollouts and rollbacks

---

## Troubleshooting Model Mappings

### Issue: "Model not found"

**Symptoms**: 404 error when requesting model

**Debug Steps**:
```bash
# 1. Check model list
curl http://localhost:4000/v1/models | jq

# 2. Verify mapping exists
cat config/model-mappings.yaml | grep "model-name"

# 3. Check LiteLLM config
cat config/litellm-unified.yaml | grep "model-name"

# 4. View router logs
journalctl --user -u litellm.service | grep "model-name"
```

**Common Causes**:
- Model not defined in litellm-unified.yaml
- Typo in model name
- Provider not active

### Issue: Routing to wrong provider

**Symptoms**: Request goes to unexpected provider

**Debug Steps**:
```bash
# Enable debug mode
# Edit config/litellm-unified.yaml
debug_router: true

# Restart LiteLLM
systemctl --user restart litellm.service

# Make request and check logs
journalctl --user -u litellm.service -f | grep "ROUTER"
```

**Common Causes**:
- Pattern match conflict
- Load balancing selecting different provider
- Fallback triggered unexpectedly

### Issue: Fallback not working

**Symptoms**: Request fails instead of falling back

**Debug Steps**:
```bash
# Check fallback configuration
cat config/litellm-unified.yaml | grep -A 5 "fallbacks:"

# Verify secondary provider is healthy
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/v1/models  # llama.cpp

# Check fallback logs
journalctl --user -u litellm.service | grep "fallback"
```

**Common Causes**:
- Fallback provider also unavailable
- `allowed_fails` threshold not reached
- Timeout too short for fallback attempt

---

## Model Mapping Metrics

Track these for optimization:

```yaml
mapping_metrics:
  - model_request_distribution
  - routing_decision_latency
  - fallback_trigger_rate
  - provider_distribution_balance
  - capability_routing_accuracy
  - pattern_match_coverage
```

**Monitoring**:
```bash
# View model usage distribution
journalctl --user -u litellm.service | grep "model:" | sort | uniq -c

# Check fallback rate
journalctl --user -u litellm.service | grep "fallback" | wc -l
```

---

## Future Model Additions

### Planned Models

**Specialized Models** (when pulled):
- `deepseek-coder-v2:16b` - Advanced code generation
- `qwen2-math:7b` - Mathematical reasoning
- `llava:13b` - Vision + language multimodal

**Cloud Providers** (when enabled):
- `gpt-4` - OpenAI cutting-edge reasoning
- `claude-3-sonnet` - Anthropic long-context
- `gemini-pro` - Google multimodal

**Configuration Template**:
```yaml
# Add to model-mappings.yaml
exact_matches:
  "future-model":
    provider: provider_name
    priority: primary
    fallback: existing_model
```

**Version**: 1.7 (quality-preserving-fallbacks)
**Last Updated**: 2025-11-11
**Architecture**: Multi-tier cloud preservation with complexity-aware routing
**Deployed**: 2025-11-11 (10 models active, 9 healthy endpoints)
