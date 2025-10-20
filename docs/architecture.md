# AI Unified Backend - Architecture Overview

## Introduction

The AI Unified Backend provides a single API endpoint that routes requests to multiple LLM inference providers (Ollama, llama.cpp, vLLM), enabling LAB projects to consume AI services through a consistent OpenAI-compatible interface.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAB Projects Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐        │
│  │   KANNA     │  │  ComfyUI    │  │ Custom Apps  │        │
│  │  (Research) │  │ (Workflows) │  │              │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘        │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           │ OpenAI-Compatible API
                           │ http://localhost:4000
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Gateway Layer (LiteLLM)                        │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │         Intelligent Router                         │   │
│  │  • Model name matching                             │   │
│  │  • Pattern-based routing                           │   │
│  │  • Capability-based routing                        │   │
│  │  • Load balancing                                  │   │
│  │  • Fallback chains                                 │   │
│  │  • Redis caching                                   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
└─────────┬─────────┬─────────┬─────────┬────────────────────┘
          │         │         │         │
          ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────────────────┐
│              Provider Layer                                  │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Ollama  │  │ llama.cpp│  │   vLLM   │  │  Future   │ │
│  │  :11434  │  │:8000/8080│  │  :8001   │  │ Providers │ │
│  │          │  │          │  │          │  │           │ │
│  │ • llama  │  │ • GGUF   │  │ • Llama2 │  │ • OpenAI  │ │
│  │   3.1:8b │  │   models │  │   13B    │  │ • Anthrop │ │
│  │ • qwen   │  │ • CUDA   │  │ • High   │  │ • Custom  │ │
│  │   coder  │  │   opt    │  │   thru   │  │           │ │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### LAB Projects Layer

**Role**: Consumers of AI services

**Projects**:
- **KANNA**: Research assistant with code generation
- **ComfyUI**: Visual workflow automation with AI text nodes
- **Custom Apps**: Any LAB project needing AI capabilities

**Communication**: Standard OpenAI API calls to `http://localhost:4000`

**Benefits**:
- Provider-agnostic code
- Automatic failover
- No provider-specific logic needed
- Simple integration using OpenAI SDK

### Gateway Layer (LiteLLM)

**Role**: Central routing and orchestration

**Location**: `../openwebui/` (LiteLLM service)

**Port**: 4000

**Key Functions**:
- Request routing based on model name/patterns
- Load balancing across providers
- Fallback chain execution
- Response caching (Redis)
- Health monitoring
- Metrics collection

**Configuration**: This project's `config/litellm-unified.yaml`

### Provider Layer

**Role**: Actual LLM inference execution

#### 1. Ollama (Port 11434)
- **Type**: General-purpose local server
- **Models**: llama3.1:8b, qwen2.5-coder:7b
- **Best For**: Quick prototyping, easy model management
- **Performance**: 50-200ms TTFT, ~30-40 tokens/sec

#### 2. llama.cpp (Ports 8000, 8080)
- **Type**: High-performance CUDA-optimized inference
- **Models**: GGUF quantized models
- **Best For**: Maximum single-request performance
- **Performance**: 20-150ms TTFT, ~40-60 tokens/sec

#### 3. vLLM (Port 8001)
- **Type**: Production-grade batched inference
- **Models**: meta-llama/Llama-2-13b-chat-hf
- **Best For**: High concurrency, large models (13B+)
- **Performance**: 100-300ms TTFT, ~80-120 tokens/sec (batched)
- **Special**: MCP integration for advanced features

## Request Flow

### Standard Chat Completion

```
1. Client Request
   POST http://localhost:4000/v1/chat/completions
   {
     "model": "llama3.1:8b",
     "messages": [{"role": "user", "content": "Hello"}]
   }

2. LiteLLM Router
   - Matches model name "llama3.1:8b" → Ollama provider
   - Checks provider health
   - Checks Redis cache for identical request

3. Provider Execution (Ollama)
   - Routes to http://localhost:11434/api/chat
   - Executes inference
   - Returns response

4. LiteLLM Response
   - Caches result in Redis (1 hour TTL)
   - Returns OpenAI-compatible response
   - Updates metrics

5. Client Receives
   Standard OpenAI format response
```

### Streaming Response

```
Client → LiteLLM → Provider
   ↑                   ↓
   └─ Stream Chunks ───┘

Timeline: TTFT ~50-200ms, streaming thereafter
Use Case: Real-time chat, long-form generation
```

### Cached Response (Redis)

```
Client → LiteLLM → Redis Cache → Client

Timeline: ~5-10ms
Use Case: Repeated queries, common prompts
Cache TTL: 1 hour (configurable)
```

## Routing Decision Logic

```python
def route_request(model_name, request_params):
    # 1. Check exact model name match
    if model_name in exact_matches:
        return exact_matches[model_name].provider

    # 2. Check pattern matching
    for pattern in routing_patterns:
        if pattern.matches(model_name):
            return pattern.provider

    # 3. Check capability-based routing
    if request_params.get('capability'):
        return capability_routing[capability].provider

    # 4. Apply load balancing if multiple providers
    if len(available_providers) > 1:
        return load_balancer.select(available_providers)

    # 5. Use default provider
    return default_provider
```

## Fault Tolerance

### Fallback Chains

**Example: High Availability Chain**
```yaml
Model: llama3.1:8b
Primary: Ollama (:11434)
   ↓ (if fails or timeout)
Secondary: llama.cpp Python (:8000)
   ↓ (if fails or timeout)
Tertiary: llama.cpp Native (:8080)
   ↓ (if all fail)
Error Response to Client
```

### Health Checking

**Continuous Monitoring**:
- Interval: Every 60 seconds
- Timeout: 5 seconds per check
- Retry: 3 attempts before marking unhealthy

**Provider States**:
- `active`: Healthy, accepting requests
- `degraded`: High latency but functional
- `unavailable`: Health check failed
- `cooldown`: Recently failed, in recovery period

### Circuit Breaker Pattern

```
Error Threshold: 3 failures in 60 seconds
Action: Mark provider as unavailable
Cooldown: 300 seconds (5 minutes)
Recovery: Gradual traffic increase
```

## Performance Optimization

### Caching Strategy (Redis)

**Benefits**:
- 50-80% latency reduction for repeated queries
- Reduced provider load
- Cost savings for cloud providers

**Configuration**:
- Cache Keys: Hash of (model, messages, temperature, max_tokens)
- TTL: 3600 seconds (1 hour)
- Hit Rate Target: >30%

### Load Balancing Strategies

**Usage-Based Routing** (Default):
- Tracks: Latency, success rate, throughput
- Weight Factors: latency=0.4, success_rate=0.4, cost=0.2
- Updates: Every 10 requests

**Least-Loaded Routing**:
- Metric: Active concurrent requests
- Best For: High-throughput scenarios (vLLM)

**Round-Robin**:
- Distribution: Even across all healthy providers
- Best For: General chat workloads

## Security Considerations

### Network Access
- **Internal Only**: All providers listen on localhost
- **No External Exposure**: LiteLLM on 0.0.0.0 for LAB network only
- **Future**: Add reverse proxy + authentication for external access

### API Keys
- **Current**: No authentication (local development)
- **Production**: Set `master_key` in litellm.yaml
- **Cloud Providers**: Store API keys in environment variables

## Monitoring & Observability

### Metrics (Prometheus)

**Provider Metrics**:
- `provider_requests_total{provider="ollama"}`
- `provider_latency_seconds{provider="vllm", quantile="0.95"}`
- `provider_errors_total{provider="llama_cpp"}`

**Router Metrics**:
- `router_routing_decisions{strategy="pattern_match"}`
- `router_fallback_triggered{original_provider="vllm"}`
- `cache_hit_rate{}`

**System Metrics**:
- `active_connections`
- `request_queue_size`
- `total_throughput_tokens_per_second`

### Logging

**Structured JSON Logs**:
```json
{
  "timestamp": "2025-10-19T09:00:00Z",
  "level": "INFO",
  "event": "request_routed",
  "model": "llama3.1:8b",
  "provider": "ollama",
  "latency_ms": 127,
  "cache_hit": false
}
```

**Log Levels**:
- `DEBUG`: Routing decisions, cache lookups
- `INFO`: Successful requests, provider switches
- `WARN`: Fallback triggers, high latency
- `ERROR`: Provider failures, timeout errors

## Extensibility

### Adding New Provider

**Steps**:
1. Add entry to `config/providers.yaml`
2. Define routing rules in `config/model-mappings.yaml`
3. Add model definition to `config/litellm-unified.yaml`
4. Run validation script

See [Adding Providers Guide](adding-providers.md) for detailed instructions.

## Key Ports Reference

| Service | Port | Purpose |
|---------|------|---------|
| OpenWebUI | 5000 | Web interface |
| **LiteLLM** | **4000** | **Unified gateway** |
| Ollama | 11434 | Local model server |
| llama.cpp (Python) | 8000 | Python bindings server |
| llama.cpp (Native) | 8080 | C++ native server |
| vLLM | 8001 | High-performance inference |

## Design Philosophy

**Non-Invasive**: Extends existing systems without modifying working code

**Additive**: New providers added via configuration

**Reversible**: Easy rollback through version-controlled configs

**Provider-Agnostic**: LAB projects don't know which provider serves them

## Next Steps

- **Integration**: See [Consuming the API](consuming-api.md)
- **Provider Management**: See [Adding Providers](adding-providers.md)
- **Troubleshooting**: See [Troubleshooting Guide](troubleshooting.md)
