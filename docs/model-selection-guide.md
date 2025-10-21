# Model Selection Guide

Choose the right model and provider for your use case.

## Quick Decision Tree

```
What's your primary use case?
│
├─ Code Generation & Programming Tasks
│  │
│  ├─ High concurrency needed (>10 simultaneous requests)
│  │  → vLLM: qwen-coder-vllm (33.63x concurrency)
│  │
│  └─ Simple tasks, prototyping
│     → Ollama: qwen2.5-coder:7b
│
├─ General Chat & Conversation
│  │
│  ├─ Quick prototyping, development
│  │  → Ollama: llama3.1:8b
│  │
│  ├─ Production workloads with high concurrency
│  │  → vLLM: llama2-13b-vllm
│  │
│  └─ Maximum single-request performance
│     → llama.cpp: GGUF models (ports 8000/8080)
│
└─ Research, Analysis, Long-form Content
   │
   ├─ Need high throughput
   │  → vLLM: llama2-13b-vllm
   │
   └─ Occasional use, simple deployment
      → Ollama: llama3.1:8b
```

## Provider Comparison

| Feature | Ollama | llama.cpp | vLLM |
|---------|--------|-----------|------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Performance (Single)** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Performance (Concurrent)** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Model Management** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Memory Efficiency** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Production Ready** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Detailed Provider Characteristics

### Ollama (Port 11434)

**Strengths**:
- ✅ Dead simple setup and model management (`ollama pull model-name`)
- ✅ Great for development and prototyping
- ✅ Auto model downloading and caching
- ✅ Good for 8B parameter models

**Limitations**:
- ⚠️ Lower concurrency compared to vLLM
- ⚠️ Not optimized for production scale

**Best For**:
- Development and testing
- Quick prototyping
- Educational projects
- Low-concurrency applications

**Available Models**:
- `llama3.1:8b` - General chat and conversation
- `qwen2.5-coder:7b` - Code generation and programming

**Performance**:
- Time to First Token (TTFT): 50-200ms
- Tokens per Second: 30-40
- Concurrency: Moderate

### llama.cpp (Ports 8000, 8080)

**Strengths**:
- ✅ Maximum single-request performance
- ✅ CUDA optimized for NVIDIA GPUs
- ✅ Supports GGUF quantized models
- ✅ Low memory footprint with quantization

**Limitations**:
- ⚠️ More complex setup than Ollama
- ⚠️ Manual model conversion to GGUF required
- ⚠️ Lower concurrency than vLLM

**Best For**:
- Single-user applications
- Real-time interactive chat
- Resource-constrained environments
- Maximum per-request speed

**Available Models**:
- Any GGUF format model
- Quantization levels: Q2_K to Q8_0

**Performance**:
- Time to First Token (TTFT): 20-150ms
- Tokens per Second: 40-60
- Concurrency: Low to Moderate

**Ports**:
- 8000: Python bindings server
- 8080: Native C++ server

### vLLM (Port 8001) ✅ Production

**Strengths**:
- ✅ **Exceptional concurrency** (33.63x for 4096-token requests)
- ✅ Production-grade batched inference
- ✅ PagedAttention for memory efficiency
- ✅ AWQ quantization support (65% memory reduction)
- ✅ Real-time streaming performance

**Limitations**:
- ⚠️ More complex deployment than Ollama
- ⚠️ Requires GPU (optimal on A100, works on RTX)
- ⚠️ Higher resource requirements

**Best For**:
- **Production applications with high traffic**
- **API services with concurrent users**
- **Code generation at scale**
- **Applications requiring consistent low latency**

**Deployed Models**:
- `qwen-coder-vllm` (Qwen/Qwen2.5-Coder-7B-Instruct-AWQ)
  - 7B parameters, AWQ 4-bit quantized
  - Specialized for code generation
  - Memory: 5.2GB VRAM (down from 14.2GB)

- `llama2-13b-vllm` (meta-llama/Llama-2-13b-chat-hf)
  - 13B parameters for better reasoning
  - General conversation and tasks

**Performance**:
- Time to First Token (TTFT): 100-200ms
- Tokens per Second: Real-time streaming
- Concurrency: **33.63x** (64 concurrent sequences)
- GPU Utilization: 90% on Quadro RTX 5000
- Context Window: 4096 tokens

## Use Case Recommendations

### Code Generation

**Scenario**: Building a code assistant, IDE plugin, or developer tool

**Recommended**: vLLM (`qwen-coder-vllm`)

**Why**:
- Specialized Qwen model trained for code
- High concurrency supports multiple users/sessions
- Fast response times for interactive coding
- Production-ready reliability

**Example**:
```python
response = client.chat.completions.create(
    model="qwen-coder-vllm",
    messages=[
        {"role": "system", "content": "You are an expert Python programmer."},
        {"role": "user", "content": "Write a function to validate email addresses."}
    ],
    temperature=0.3  # Lower temperature for code accuracy
)
```

### Interactive Chat Application

**Scenario**: Building a chatbot or conversational AI

**Low Traffic (Development)**:
- Provider: Ollama
- Model: `llama3.1:8b`
- Why: Easy setup, good enough for development

**High Traffic (Production)**:
- Provider: vLLM
- Model: `llama2-13b-vllm`
- Why: Handles concurrent users, consistent latency

### Content Generation

**Scenario**: Generating articles, summaries, or creative writing

**Recommended**: vLLM (`llama2-13b-vllm`)

**Why**:
- Larger 13B model for better coherence
- Batch processing for multiple requests
- Streaming for progressive content display

### Rapid Prototyping

**Scenario**: Experimenting with prompts, testing ideas

**Recommended**: Ollama (any model)

**Why**:
- Instant model switching (`ollama run model-name`)
- No complex configuration
- Easy to try different models

### Research & Analysis

**Scenario**: Document analysis, summarization, question answering

**Single Documents**:
- Provider: llama.cpp
- Why: Maximum speed for one-off tasks

**Batch Processing**:
- Provider: vLLM
- Model: `llama2-13b-vllm`
- Why: Process multiple documents concurrently

## Performance Comparison

| Use Case | Ollama | llama.cpp | vLLM |
|----------|--------|-----------|------|
| **Single Request Speed** | Good | Excellent | Very Good |
| **10 Concurrent Requests** | Slow | Moderate | Excellent |
| **100 Concurrent Requests** | N/A | N/A | Excellent |
| **Code Generation Quality** | Good | Good | Excellent* |
| **Memory Usage (8B model)** | ~8GB | ~4GB† | ~5GB‡ |

*Using Qwen specialist model
†With Q4 quantization
‡With AWQ 4-bit quantization

## Model Selection by Workload

### Development Workload
```
Personal project, <5 users, flexibility needed
→ Ollama: llama3.1:8b or qwen2.5-coder:7b
```

### Small Team Workload
```
Team of 5-20 developers, shared resource
→ vLLM: qwen-coder-vllm (code) or llama2-13b-vllm (chat)
```

### Production API Workload
```
Public API, >100 requests/minute, SLA requirements
→ vLLM: llama2-13b-vllm (with multiple instances if needed)
```

### Batch Processing Workload
```
Process 1000s of documents overnight
→ vLLM: llama2-13b-vllm (leverage concurrency)
```

## Special Considerations

### When to Use Multiple Providers

You can use multiple providers simultaneously for different use cases:

```python
# Code generation: vLLM (best quality + concurrency)
code_client = OpenAI(base_url="http://localhost:4000/v1")
code_response = code_client.chat.completions.create(
    model="qwen-coder-vllm",
    messages=[{"role": "user", "content": "Write Python code..."}]
)

# Quick chat: Ollama (simple, reliable)
chat_client = OpenAI(base_url="http://localhost:4000/v1")
chat_response = chat_client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "What's the weather?"}]
)

# The unified gateway routes each to the appropriate provider
```

### Cost Considerations

All providers in this setup are **self-hosted and free**:
- ✅ No API usage fees
- ✅ Pay only for hardware/electricity
- ✅ Unlimited requests
- ✅ Complete data privacy

**Hardware Requirements**:
- **Ollama**: CPU OK, GPU recommended for 8B models
- **llama.cpp**: GPU recommended (CUDA), CPU fallback available
- **vLLM**: **GPU required** (NVIDIA, 16GB+ VRAM for 7B-13B models)

### Context Window Limits

| Provider | Model | Context Limit |
|----------|-------|---------------|
| Ollama | llama3.1:8b | 8192 tokens |
| Ollama | qwen2.5-coder:7b | 4096 tokens |
| vLLM | qwen-coder-vllm | 4096 tokens |
| vLLM | llama2-13b-vllm | 4096 tokens |
| llama.cpp | Varies by model | Configurable |

**Note**: 1 token ≈ 0.75 words (English)

## Migration Paths

### From Ollama to vLLM (Scaling Up)

**When**: Your application grows and needs better concurrency

**Steps**:
1. No code changes needed - just change model name
2. Test with small traffic first
3. Gradually shift more requests to vLLM
4. Monitor GPU memory and adjust `--gpu-memory-utilization`

**Example**:
```python
# Before (Ollama)
model="llama3.1:8b"

# After (vLLM) - no other code changes
model="llama2-13b-vllm"
```

### From vLLM to Ollama (Simplifying)

**When**: Downsizing, reducing complexity, or prototyping

**Steps**:
1. Change model name in requests
2. Ollama automatically handles single-user workloads
3. Keep vLLM configuration for easy scale-back

## Quick Reference Table

| Scenario | Model Name | Provider | Why |
|----------|------------|----------|-----|
| Code assistance | `qwen-coder-vllm` | vLLM | Specialist model + concurrency |
| General chat (dev) | `llama3.1:8b` | Ollama | Easy, reliable |
| General chat (prod) | `llama2-13b-vllm` | vLLM | Production scale |
| Single fast request | GGUF model | llama.cpp | Minimum latency |
| Batch processing | `llama2-13b-vllm` | vLLM | High throughput |
| Learning/experimenting | Any Ollama model | Ollama | Simplest setup |

## Need Help Deciding?

Ask yourself:

1. **How many concurrent users?**
   - 1-5: Ollama or llama.cpp
   - 5-50: vLLM
   - 50+: vLLM (consider multiple instances)

2. **What's the primary task?**
   - Code: `qwen-coder-vllm`
   - Chat: `llama3.1:8b` (dev) or `llama2-13b-vllm` (prod)
   - Mixed: Use multiple models via unified gateway

3. **What's your deployment stage?**
   - Prototype: Ollama
   - Testing: Ollama or vLLM
   - Production: vLLM

4. **What hardware do you have?**
   - CPU only: Ollama (small models)
   - GPU <16GB: Ollama, llama.cpp
   - GPU ≥16GB: vLLM recommended

---

**Still unsure?** Start with Ollama for prototyping, then migrate to vLLM for production. The unified gateway makes switching seamless - just change the model name!

See [Quick Start Guide](quick-start.md) to begin testing different providers.
