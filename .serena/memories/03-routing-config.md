# Routing Configuration - LiteLLM Strategies

## Overview

The routing configuration defines how LiteLLM routes incoming requests to the appropriate provider based on model names, patterns, capabilities, and load conditions. This memory documents all routing strategies, decision logic, and configuration patterns.

## Routing Decision Hierarchy

LiteLLM evaluates routing in this priority order:

```
1. Exact Model Name Match
   ↓ (if no match)
2. Pattern Matching (regex)
   ↓ (if no match)
3. Capability-Based Routing
   ↓ (if no match)
4. Load Balancing (if multiple providers)
   ↓ (if no providers)
5. Default Provider
   ↓ (if default fails)
6. Fallback Chain
   ↓ (if all fail)
7. Error Response
```

---

## 1. Exact Model Name Routing

### Definition
Direct mapping from specific model name to provider endpoint.

### Configuration Pattern
```yaml
# In config/model-mappings.yaml
exact_matches:
  "llama3.1:8b":
    provider: ollama
    priority: primary
    fallback: null
    description: "General-purpose chat model"
```

### LiteLLM Implementation
```yaml
# In config/litellm-unified.yaml
model_list:
  - model_name: llama3.1:8b
    litellm_params:
      model: ollama/llama3.1:8b
      api_base: http://127.0.0.1:11434
```

### Example Request Flow
```bash
# Client Request
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "llama3.1:8b", "messages": [...]}'

# LiteLLM Decision
1. Check exact_matches: "llama3.1:8b" found
2. Route to: ollama provider at :11434
3. Transform: model → "ollama/llama3.1:8b"
4. Forward request to Ollama
5. Return response to client
```

### Current Exact Matches

**Ollama Models**:
- `llama3.1:8b` → Ollama :11434
- `qwen2.5-coder:7b` → Ollama :11434

**vLLM Models**:
- `llama2-13b-vllm` → vLLM :8001 (meta-llama/Llama-2-13b-chat-hf)

**llama.cpp Models**:
- `llama-cpp-default` → llama.cpp Python :8000

---

## 2. Pattern-Based Routing

### Definition
Regex pattern matching against model names for dynamic routing.

### Configuration Pattern
```yaml
# In config/model-mappings.yaml
patterns:
  - pattern: "^meta-llama/.*"
    provider: vllm
    fallback: ollama
    description: "HuggingFace Llama models prefer vLLM"
```

### Example Patterns

**HuggingFace Model Paths → vLLM**:
```yaml
- pattern: "^meta-llama/.*"
  provider: vllm
  fallback: ollama

- pattern: "^mistralai/.*"
  provider: vllm
  fallback: ollama
```

**Ollama Naming Convention**:
```yaml
- pattern: ".*:\\d+[bB]$"  # Matches "model:7b", "model:13B"
  provider: ollama
  description: "Ollama naming (model:size)"
```

**GGUF Files → llama.cpp**:
```yaml
- pattern: ".*\\.gguf$"
  provider: llama_cpp_python
  fallback: llama_cpp_native
  description: "Quantized GGUF models"
```

### Example Request Flow
```bash
# Client Request
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "meta-llama/Llama-2-7b-chat-hf", "messages": [...]}'

# LiteLLM Decision
1. Check exact_matches: No match for "meta-llama/Llama-2-7b-chat-hf"
2. Check patterns: Matches "^meta-llama/.*"
3. Route to: vllm provider
4. Fallback configured: ollama
5. Forward to vLLM :8001
```

---

## 3. Capability-Based Routing

### Definition
Route based on task requirements rather than model names.

### Configuration Pattern
```yaml
# In config/model-mappings.yaml
capabilities:
  code_generation:
    description: "Models specialized for code"
    preferred_models:
      - qwen2.5-coder:7b
      - deepseek-coder-v2
    provider: ollama
    routing_strategy: load_balance
```

### Defined Capabilities

**Code Generation**:
```yaml
code_generation:
  preferred_models:
    - qwen2.5-coder:7b
    - deepseek-coder-v2
  provider: ollama
  routing_strategy: load_balance
```

**High Throughput**:
```yaml
high_throughput:
  description: "Many concurrent requests"
  min_model_size: "13B"
  provider: vllm
  routing_strategy: least_loaded
```

**Low Latency**:
```yaml
low_latency:
  description: "Single-request speed priority"
  provider: llama_cpp_native
  fallback: llama_cpp_python
  routing_strategy: fastest_response
```

**General Chat**:
```yaml
general_chat:
  description: "General conversational AI"
  preferred_models:
    - llama3.1:8b
    - llama2-13b-vllm
  routing_strategy: usage_based
```

**Large Context**:
```yaml
large_context:
  description: "Large context windows"
  min_context: 8192
  providers:
    - llama_cpp_python  # 8192 configured
    - vllm              # 4096 default
  routing_strategy: most_capacity
```

### Usage Pattern
```bash
# Client Request with capability hint
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "X-Capability: code_generation" \
  -d '{"messages": [{"role": "user", "content": "Write a Python function"}]}'

# LiteLLM uses capability hint to select appropriate model
```

---

## 4. Load Balancing Strategies

### Enabled Strategies

#### Round Robin
```yaml
round_robin:
  description: "Distribute requests evenly"
  applicable_to:
    - general_chat
    - code_generation
```

**Algorithm**:
1. Maintain counter for each provider
2. Increment counter on each request
3. Route to provider with lowest counter
4. Reset counters periodically

#### Least Loaded
```yaml
least_loaded:
  description: "Route to fewest active requests"
  applicable_to:
    - high_throughput
```

**Algorithm**:
1. Track active requests per provider
2. Query provider metrics
3. Route to provider with lowest active count
4. Real-time adjustment

#### Usage-Based Routing (Default)
```yaml
usage_based:
  description: "Route based on historical performance"
  weight_factors:
    - latency: 0.4
    - success_rate: 0.4
    - cost: 0.2
```

**Algorithm**:
1. Track: latency, success rate, cost per provider
2. Calculate weighted score for each provider
3. Route to highest-scoring provider
4. Update metrics every 10 requests

**Score Calculation**:
```
score = (1/latency * 0.4) + (success_rate * 0.4) + (1/cost * 0.2)
```

#### Fastest Response
```yaml
fastest_response:
  description: "Always use fastest provider"
  measure: time_to_first_token
  applicable_to:
    - low_latency
```

**Algorithm**:
1. Measure TTFT for each provider
2. Track 95th percentile latency
3. Route to provider with lowest p95 TTFT
4. Re-evaluate every hour

### Redundant Model Configuration

Same model available on multiple providers:

```yaml
redundant_models:
  "llama3.1:8b":
    providers:
      - provider: ollama
        weight: 0.7  # Primary (70% of requests)
      - provider: llama_cpp_python
        weight: 0.3  # Backup (30% of requests)
```

---

## 5. Fallback Chains

### Definition
Ordered sequence of providers to try if primary fails.

### Default Fallback Chain
```yaml
fallback_chains:
  default:
    description: "Standard fallback for most requests"
    chain:
      - primary: vllm
        condition: model_size >= "13B"
      - secondary: ollama
        condition: always
      - tertiary: llama_cpp_python
        condition: always
```

### Code Generation Fallback
```yaml
code_generation:
  description: "Fallback for code tasks"
  chain:
    - primary: ollama
      preferred_model: qwen2.5-coder:7b
    - secondary: llama_cpp_python
      condition: ollama_unavailable
```

### High Availability Chain
```yaml
high_availability:
  description: "Maximum uptime priority"
  chain:
    - primary: ollama
    - secondary: llama_cpp_python
    - tertiary: llama_cpp_native
  retry_attempts: 3
  retry_delay_ms: 500
```

### Execution Flow
```
1. Attempt primary provider
   ↓ (if fails)
2. Check failure type (timeout, error, rate limit)
   ↓
3. Mark primary as degraded/unavailable
   ↓
4. Attempt secondary provider
   ↓ (if fails)
5. Attempt tertiary provider
   ↓ (if fails)
6. Return error to client
   ↓
7. Trigger cooldown for failed providers
```

---

## 6. Model Size-Based Routing

### Configuration
```yaml
model_size_routing:
  - size: "< 8B"
    provider: ollama
    reason: "Small models work well with Ollama"

  - size: "8B - 13B"
    provider: ollama
    fallback: llama_cpp_python
    reason: "Medium models, Ollama preferred"

  - size: "> 13B"
    provider: vllm
    fallback: ollama
    reason: "Large models benefit from vLLM batching"
```

### Detection Logic
LiteLLM extracts size from:
1. Model name pattern (e.g., "llama-7b", "qwen:13b")
2. Model info metadata in configuration
3. Provider model list response

---

## 7. Request Metadata Routing

### Header-Based Routing
```yaml
request_metadata_routing:
  high_priority_requests:
    provider: vllm
    condition: header.x-priority == "high"

  batch_requests:
    provider: vllm
    condition: batch_size > 1

  streaming_requests:
    provider: ollama
    condition: stream == true
```

### Usage Example
```bash
# High priority request
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "X-Priority: high" \
  -d '{"model": "llama3.1:8b", "messages": [...]}'
# Routes to vLLM instead of default Ollama

# Streaming request
curl -X POST http://localhost:4000/v1/chat/completions \
  -d '{"model": "llama3.1:8b", "stream": true, "messages": [...]}'
# Routes to Ollama (best streaming support)
```

---

## 8. Special Routing Cases

### First Request Routing (Cold Start Optimization)
```yaml
first_request_routing:
  description: "Cold start optimization"
  strategy: prefer_warm_providers
  warm_check_timeout_ms: 100
```

**Logic**:
1. Check which providers have warm instances
2. Route to warm provider even if not optimal
3. Avoid cold start latency penalty
4. Normal routing after first request

### Rate-Limited Fallback
```yaml
rate_limited_fallback:
  description: "Automatic fallback on rate limits"
  enabled: true
  fallback_duration_seconds: 60
```

**Flow**:
1. Detect rate limit error (429)
2. Mark provider as rate-limited
3. Activate fallback chain immediately
4. Resume after cooldown period

### Error-Based Routing
```yaml
error_based_routing:
  description: "Avoid providers with recent errors"
  enabled: true
  error_threshold: 3
  cooldown_seconds: 300
```

**Logic**:
1. Track errors per provider
2. If errors > threshold in time window
3. Mark provider as degraded
4. Reduce routing weight by 50%
5. Resume after cooldown

---

## Router Settings in LiteLLM

### Complete Configuration
```yaml
# In config/litellm-unified.yaml
router_settings:
  # Strategy
  routing_strategy: usage-based-routing-v2
  # Options: simple-shuffle, least-busy, usage-based-routing, latency-based-routing

  # Model aliases for fallback
  model_group_alias:
    general_chat:
      - llama3.1-ollama
      - llama2-13b-vllm
      - llama-cpp-python
    code_generation:
      - qwen-coder
      - deepseek-coder
    high_throughput:
      - llama2-13b-vllm

  # Reliability
  allowed_fails: 3
  num_retries: 2
  timeout: 30  # seconds
  cooldown_time: 60  # seconds before retry

  # Load balancing
  enable_pre_call_checks: true  # Health check before routing
  redis_host: 127.0.0.1
  redis_port: 6379

  # Fallback chains
  fallbacks:
    - model: llama3.1:8b
      fallback_models:
        - llama3.1-backup
        - llama-cpp-python

    - model: llama2-13b-vllm
      fallback_models:
        - llama3.1-ollama
```

---

## Routing Debugging

### Enable Debug Mode
```yaml
# In config/litellm-unified.yaml
debug: false
debug_router: false  # Set to true for routing diagnostics
```

### Router Logs
```bash
# View routing decisions
journalctl --user -u litellm.service | grep "ROUTER"

# Example log output:
[ROUTER] Model: llama3.1:8b -> Provider: ollama (exact match)
[ROUTER] Model: meta-llama/Llama-2-7b -> Provider: vllm (pattern match)
[ROUTER] Fallback triggered: ollama -> llama_cpp_python
```

### Test Routing
```bash
# Test specific model routing
curl http://localhost:4000/v1/models | jq '.data[] | {id, object}'

# Test with different models
for model in "llama3.1:8b" "llama2-13b-vllm" "qwen-coder"; do
  echo "Testing: $model"
  curl -X POST http://localhost:4000/v1/chat/completions \
    -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}]}" \
    | jq '.model'
done
```

---

## Best Practices

### Routing Strategy Selection
- **Development**: Use `simple-shuffle` for even distribution
- **Production**: Use `usage-based-routing-v2` for optimal performance
- **High Availability**: Enable all fallback chains
- **Cost Optimization**: Weight by cost in usage-based routing

### Model Naming
- **Exact matches**: Use for critical production models
- **Patterns**: Use for HuggingFace models, versions
- **Avoid conflicts**: Ensure patterns don't overlap unintentionally

### Fallback Design
- **Always define fallback**: Never rely on single provider
- **Test fallback chains**: Simulate provider failures
- **Monitor fallback rate**: High rate indicates primary issues

### Performance Tuning
- **Pre-call health checks**: Enable for reliability, disable for speed
- **Timeout configuration**: Balance latency vs success rate
- **Redis caching**: Essential for repeated queries

---

## Routing Metrics

Track these metrics for optimization:

```yaml
routing_metrics:
  - routing_decision_time_ms
  - exact_match_rate
  - pattern_match_rate
  - fallback_trigger_rate
  - provider_distribution
  - load_balance_effectiveness
  - cache_hit_rate
```

**Version**: 1.0
**Last Updated**: 2025-10-19
