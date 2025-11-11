# Unified Backend Enhancements v2.0

**Major Update: November 9, 2025**

This document describes the major enhancements added to the AI Unified Backend Infrastructure in version 2.0.

## Overview

Version 2.0 introduces significant improvements in provider support and advanced features:

1. **New Cloud Providers**: OpenAI and Anthropic integration
2. **Semantic Caching**: Intelligent caching based on prompt similarity
3. **Request Queuing**: Priority-based request management
4. **Multi-Region Support**: Geographic distribution and compliance
5. **Advanced Load Balancing**: Intelligent provider selection algorithms

## 1. OpenAI and Anthropic Providers

### OpenAI Integration

**Status**: Active
**Models**: 7 models including GPT-4o, o1, GPT-3.5-turbo

#### Available Models

| Model | Specialty | Context | Features |
|-------|-----------|---------|----------|
| gpt-4o | Advanced reasoning | 128K | Vision, function calling |
| gpt-4o-mini | General chat | 128K | Cost-effective, fast |
| gpt-4-turbo | Advanced reasoning | 128K | Vision, function calling |
| gpt-4 | Advanced reasoning | 8K | Function calling |
| gpt-3.5-turbo | General chat | 16K | Cost-effective |
| o1 | Advanced reasoning | 200K | Extended thinking |
| o1-mini | Code generation | 128K | STEM-optimized |

#### Configuration

```yaml
# config/providers.yaml
openai:
  type: openai
  base_url: https://api.openai.com/v1
  status: active
  requires_api_key: true
  env_var: OPENAI_API_KEY
```

#### Usage Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000",  # LiteLLM gateway
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="gpt-4o",  # Routes to OpenAI
    messages=[{"role": "user", "content": "Analyze this code"}]
)
```

### Anthropic Integration

**Status**: Active
**Models**: 5 models including Claude 3.5 Sonnet, Opus, Haiku

#### Available Models

| Model | Specialty | Context | Features |
|-------|-----------|---------|----------|
| claude-3-5-sonnet-20241022 | Advanced reasoning | 200K | Vision, tool use, superior coding |
| claude-3-5-haiku-20241022 | General chat | 200K | Fast, cost-effective |
| claude-3-opus-20240229 | Advanced reasoning | 200K | Most capable, vision, tool use |
| claude-3-sonnet-20240229 | General chat | 200K | Vision, tool use |
| claude-3-haiku-20240307 | General chat | 200K | Fast, cost-effective |

#### Configuration

```yaml
# config/providers.yaml
anthropic:
  type: anthropic
  base_url: https://api.anthropic.com/v1
  status: active
  requires_api_key: true
  env_var: ANTHROPIC_API_KEY
```

### Cross-Provider Fallback

The system implements intelligent fallback chains between providers:

```yaml
# Example: GPT-4o with Anthropic fallback
"gpt-4o":
  chain:
    - claude-3-5-sonnet-20241022  # Primary fallback
    - gpt-4-turbo                  # Secondary fallback
    - claude-3-opus-20240229       # Tertiary fallback
```

## 2. Semantic Caching

**Location**: `scripts/semantic_cache.py`
**Purpose**: Intelligent caching based on semantic similarity rather than exact text matching

### Features

- **Embedding-Based Matching**: Uses sentence transformers for semantic similarity
- **Configurable Threshold**: Adjust similarity threshold (default: 0.85)
- **Redis Backend**: Distributed caching with TTL support
- **Cost Savings**: Cache hits for similar queries even with different wording

### Usage Example

```python
from semantic_cache import SemanticCache

cache = SemanticCache(similarity_threshold=0.85)

# Check cache before API call
cached = cache.get("What is the capital of France?", model="gpt-4o")
if cached:
    print(f"Cache HIT (similarity: {cached['similarity']:.3f})")
    return cached['response']

# After API call, store in cache
cache.set(
    prompt="What is the capital of France?",
    response=api_response,
    model="gpt-4o",
    ttl=3600
)
```

### Configuration

```bash
# Environment variables
export SEMANTIC_CACHE_THRESHOLD=0.85  # Similarity threshold (0.0-1.0)
export SEMANTIC_CACHE_EMBEDDING_MODEL=all-MiniLM-L6-v2  # Embedding model
```

### CLI Management

```bash
# View cache statistics
python3 scripts/semantic_cache.py --stats

# Clear cache for specific model
python3 scripts/semantic_cache.py --invalidate gpt-4o

# Test semantic similarity
python3 scripts/semantic_cache.py --test
```

## 3. Request Queuing and Prioritization

**Location**: `scripts/request_queue.py`
**Purpose**: Manage request flow with priority levels and deadline enforcement

### Priority Levels

| Priority | Use Case | Value |
|----------|----------|-------|
| CRITICAL | System-critical, emergency | 4 |
| HIGH | Business-critical, interactive | 3 |
| NORMAL | Standard requests | 2 |
| LOW | Background processing | 1 |
| BULK | Non-time-sensitive | 0 |

### Features

- **Priority Queuing**: Higher priority requests processed first
- **Deadline Enforcement**: Automatic expiration of aged requests
- **Priority Boosting**: Age-based priority increases
- **Provider-Specific Queues**: Separate queues per model/provider
- **Queue Analytics**: Real-time monitoring and statistics

### Usage Example

```python
from request_queue import RequestQueue, Priority

queue = RequestQueue()

# Enqueue high-priority request
request_id = queue.enqueue(
    prompt="Critical analysis needed",
    model="gpt-4o",
    priority=Priority.HIGH,
    deadline=30.0  # Expire after 30 seconds
)

# Dequeue for processing (gets highest priority first)
request = queue.dequeue(model="gpt-4o")
if request:
    process_request(request)
```

### Queue Management

```bash
# View queue statistics
python3 scripts/request_queue.py --stats

# Clear expired requests
python3 scripts/request_queue.py --clear-expired

# Test queue operations
python3 scripts/request_queue.py --test
```

## 4. Multi-Region Support

**Location**: `config/multi-region.yaml`
**Purpose**: Geographic distribution, data residency compliance, and latency optimization

### Supported Regions

| Region | Location | Timezone | Providers |
|--------|----------|----------|-----------|
| us-east | N. Virginia | America/New_York | OpenAI, Anthropic, Ollama Cloud |
| us-west | Oregon | America/Los_Angeles | OpenAI, Anthropic, Ollama Cloud |
| eu-west | Ireland | Europe/Dublin | OpenAI, Anthropic, Ollama Cloud |
| ap-southeast | Singapore | Asia/Singapore | OpenAI, Ollama Cloud |
| local | On-Premises | UTC | All local providers |

### Data Residency Compliance

The system supports strict data residency requirements:

```yaml
# EU users: Stay within EU for GDPR compliance
data_residency_rules:
  eu_users:
    regions:
      - eu-west
      - local  # Allow local if in EU
    strict: true  # Never route outside specified regions
    compliant_providers:
      - anthropic  # GDPR-compliant
      - ollama_cloud
      - ollama  # Local control
```

### Failover Strategies

```yaml
# Cross-region failover for high availability
regional_failover:
  strategies:
    - name: "EU Compliant"
      description: "Stay within EU for data residency"
      sequence:
        - local  # If in EU
        - eu-west
        # No cross-region failover outside EU
```

### Configuration

See `config/multi-region.yaml` for full configuration options including:
- Regional endpoints
- Latency-based routing
- Cost optimization per region
- Health monitoring by region

## 5. Advanced Load Balancing

**Location**: `scripts/advanced_load_balancer.py`
**Purpose**: Intelligent provider selection using multiple factors

### Routing Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| HEALTH_WEIGHTED | Weight by provider health scores | Maximize reliability |
| LATENCY_BASED | Route to fastest provider | Minimize response time |
| COST_OPTIMIZED | Select cheapest provider | Budget optimization |
| CAPACITY_AWARE | Consider rate limits and quotas | Avoid throttling |
| LEAST_LOADED | Route to least busy provider | Load distribution |
| TOKEN_AWARE | Consider context window requirements | Large context handling |
| HYBRID | Combine multiple factors | Balanced optimization |

### Usage Example

```python
from advanced_load_balancer import LoadBalancer, RoutingStrategy

lb = LoadBalancer()

# Select provider using cost-optimized strategy
provider = lb.select_provider(
    providers=["openai", "anthropic", "ollama"],
    strategy=RoutingStrategy.COST_OPTIMIZED,
    context_tokens=5000
)

# Hybrid strategy (combines health, latency, cost, capacity)
provider = lb.select_provider(
    providers=["openai", "anthropic"],
    strategy=RoutingStrategy.HYBRID,
    context_tokens=10000,
    health_weight=0.4,
    latency_weight=0.3,
    cost_weight=0.2,
    capacity_weight=0.1
)
```

### Metrics Tracking

The load balancer tracks real-time metrics:

```python
# Update metrics after request
lb.update_metrics(
    provider="openai",
    health_score=0.95,
    latency_ms=250.0,
    error=False,
    rate_limit_remaining=450,
    cost_per_1k_tokens=0.005
)

# View current metrics
metrics = lb.get_metrics("openai")
print(f"Health: {metrics.health_score}")
print(f"Avg Latency: {metrics.avg_latency_ms}ms")
print(f"Error Rate: {metrics.error_rate}")
```

## Integration Guide

### Environment Setup

```bash
# Required API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export OLLAMA_API_KEY="..."  # If using Ollama Cloud

# Redis configuration (for caching, queuing, load balancing)
export REDIS_HOST="127.0.0.1"
export REDIS_PORT="6379"

# Optional feature configuration
export SEMANTIC_CACHE_THRESHOLD="0.85"
export MAX_QUEUE_SIZE="1000"
export PRIORITY_AGE_BOOST_SECONDS="30"
```

### LiteLLM Gateway Configuration

The enhancements integrate seamlessly with LiteLLM:

```yaml
# config/litellm-unified.yaml (AUTO-GENERATED)
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: gpt-4o
      api_key: os.environ/OPENAI_API_KEY
    model_info:
      provider: openai

  - model_name: claude-3-5-sonnet-20241022
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY
    model_info:
      provider: anthropic
```

### Capability-Based Routing

Use capability aliases for automatic model selection:

```python
# Code generation: Routes to o1-mini (best for code)
response = client.chat.completions.create(
    model="code_generation",  # Capability alias
    messages=[{"role": "user", "content": "Write a Python function"}]
)

# Analysis: Routes to Claude 3.5 Sonnet (best for analysis)
response = client.chat.completions.create(
    model="analysis",
    messages=[{"role": "user", "content": "Analyze this data"}]
)

# Vision: Routes to GPT-4o (vision specialist)
response = client.chat.completions.create(
    model="vision",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": "..."}}
        ]
    }]
)
```

## Performance and Cost Optimization

### Cost Savings with Semantic Caching

- **Traditional caching**: Only exact matches hit cache
- **Semantic caching**: Similar queries hit cache, reducing API calls by 30-60%

Example:
- "What is the capital of France?" (cache miss, API call)
- "Tell me France's capital city" (cache HIT, no API call, similarity: 0.92)
- "Which city is the capital of France?" (cache HIT, no API call, similarity: 0.89)

### Intelligent Fallback Chains

Minimize costs by configuring cloud → local fallback:

```yaml
fallback_chains:
  "gpt-4o":
    chain:
      - claude-3-5-sonnet-20241022  # Try Anthropic if OpenAI fails
      - qwen2.5-coder:7b             # Fallback to local (free)
      - llama3.1:latest              # Final local fallback (free)
```

### Cost-Optimized Routing

```python
# Automatically routes to cheapest provider
provider = lb.select_provider(
    providers=["gpt-4o", "gpt-4o-mini", "claude-3-5-haiku-20241022"],
    strategy=RoutingStrategy.COST_OPTIMIZED,
    context_tokens=2000
)
# Result: gpt-4o-mini ($0.15/1M tokens vs $5/1M for gpt-4o)
```

## Monitoring and Analytics

### Queue Monitoring

```bash
# View queue depths
python3 scripts/request_queue.py --stats
```

Output:
```json
{
  "timestamp": "2025-11-09T12:00:00",
  "queues": {
    "gpt-4o": {
      "CRITICAL": 0,
      "HIGH": 3,
      "NORMAL": 12,
      "LOW": 5
    }
  },
  "total_requests": 20
}
```

### Cache Analytics

```bash
# View semantic cache statistics
python3 scripts/semantic_cache.py --stats
```

Output:
```json
{
  "total_cached_prompts": 1247,
  "redis_memory_used": "15.2MB",
  "similarity_threshold": 0.85,
  "embedding_model": "all-MiniLM-L6-v2"
}
```

### Load Balancer Metrics

```bash
# View provider metrics
python3 scripts/advanced_load_balancer.py --view-metrics openai
```

Output:
```json
{
  "provider_name": "openai",
  "health_score": 0.98,
  "avg_latency_ms": 320.5,
  "error_rate": 0.02,
  "current_load": 5,
  "rate_limit_remaining": 2850,
  "cost_per_1k_tokens": 0.005,
  "capacity_score": 0.95
}
```

## Migration Guide

### From v1.x to v2.0

1. **Update configuration files**:
   ```bash
   # Providers and mappings already updated in v2.0
   # Generate new LiteLLM config
   python3 scripts/simple-generate-config.py
   ```

2. **Set API keys**:
   ```bash
   export OPENAI_API_KEY="sk-..."
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

3. **Update client code** (optional):
   ```python
   # Old: Direct provider reference
   model="ollama/llama3.1:latest"

   # New: Use model name or capability alias
   model="llama3.1:latest"  # Or: model="general_chat"
   ```

4. **Enable advanced features** (optional):
   - Semantic caching: Set `SEMANTIC_CACHE_THRESHOLD`
   - Request queuing: Integrate `request_queue.py` in your application
   - Multi-region: Configure `multi-region.yaml` for your needs

## Troubleshooting

### Common Issues

**1. API Key Not Found**
```
Error: AuthenticationError: Invalid API key
Solution: Ensure environment variables are set:
  export OPENAI_API_KEY="sk-..."
  export ANTHROPIC_API_KEY="sk-ant-..."
```

**2. Semantic Cache Miss Rate Too High**
```
Issue: Low cache hit rate
Solution: Adjust similarity threshold:
  export SEMANTIC_CACHE_THRESHOLD=0.80  # Lower = more lenient
```

**3. Queue Full Errors**
```
Error: Queue full for gpt-4o at HIGH priority
Solution: Increase queue size:
  export MAX_QUEUE_SIZE=2000
```

**4. Cross-Provider Fallback Not Working**
```
Issue: Requests fail instead of falling back
Solution: Check fallback chains in model-mappings.yaml
  Ensure fallback models exist and are active
```

## Future Enhancements

Planned for v2.1:
- [ ] Automatic retry with exponential backoff
- [ ] Request deduplication
- [ ] Advanced cost analytics dashboard
- [ ] Multi-model ensemble responses
- [ ] Streaming response optimization
- [ ] Token usage prediction and quota management

## Support

For issues and questions:
- Documentation: `docs/` directory
- Serena memories: `.serena/memories/`
- GitHub Issues: Repository issue tracker

## Version History

- **v2.0** (2025-11-09): Major update with OpenAI, Anthropic, semantic caching, request queuing, multi-region support, and advanced load balancing
- **v1.6** (2025-10-29): Ollama Cloud provider
- **v1.5** (2025-10-25): vLLM integration
- **v1.0** (2025-10-01): Initial release with Ollama and llama.cpp
