# AI Unified Backend - System Architecture

## Overview

The AI Unified Backend provides a single API endpoint that routes requests to multiple LLM inference providers, enabling LAB projects to consume AI services through a consistent interface while maintaining flexibility in provider selection.

## Architecture Diagram

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

## Component Responsibilities

### LAB Projects Layer
**Role**: Consumers of AI services
**Communication**: Standard OpenAI API calls to `http://localhost:4000`
**Benefits**:
- Provider-agnostic code
- Automatic failover
- No provider-specific logic needed

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

**Configuration**: `config/litellm-unified.yaml`

### Provider Layer
**Role**: Actual LLM inference execution
**Providers**:

#### 1. Ollama
- **Port**: 11434
- **Type**: General-purpose local server
- **Models**: llama3.1:8b, qwen2.5-coder:7b
- **Best For**: Quick prototyping, easy model management
- **Location**: Integrated in OpenWebUI

#### 2. llama.cpp
- **Ports**: 8000 (Python), 8080 (Native C++)
- **Type**: High-performance CUDA-optimized inference
- **Models**: GGUF quantized models
- **Best For**: Maximum single-request performance
- **Location**: `../openwebui/backends/llama.cpp`

#### 3. vLLM
- **Port**: 8001
- **Type**: Production-grade batched inference
- **Models**: Qwen/Qwen2.5-Coder-7B-Instruct-AWQ, solidrust/dolphin-2.8-mistral-7b-v02-AWQ
- **Best For**: High concurrency, code generation
- **Location**: Managed via systemd services

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
   - Caches result in Redis
   - Returns OpenAI-compatible response
   - Updates metrics

5. Client Receives
   Standard OpenAI format response
```

### Routing Decision Logic

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

## Data Flow Patterns

### Synchronous Request-Response
```
Client → LiteLLM → Provider → LiteLLM → Client
Timeline: ~50-500ms for 8B models
Use Case: Simple completions, chat messages
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
- Endpoints:
  - Ollama: `GET /api/tags`
  - llama.cpp: `GET /v1/models`
  - vLLM: `GET /v1/models`

**Provider States**:
- `active`: Healthy, accepting requests
- `degraded`: High latency, but functional
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

**Cache Keys**: Hash of (model, messages, temperature, max_tokens)
**TTL**: 3600 seconds (1 hour)
**Hit Rate Target**: >30%
**Cache Invalidation**: Time-based (TTL expiry)

**Benefits**:
- 50-80% latency reduction for repeated queries
- Reduced provider load
- Cost savings for cloud providers

### Load Balancing Strategies

**Usage-Based Routing**:
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

### Rate Limiting
- **Current**: Disabled (local development)
- **Production**: Enable per-model rate limits
- **Config**: `rate_limit_settings` in litellm.yaml

## Monitoring & Observability

### Dashboard Infrastructure

The system provides **dual dashboard implementations** for comprehensive real-time monitoring:

#### Enhanced Textual Dashboard (PTUI)
**File**: `scripts/ai-dashboard-enhanced.py`
**Framework**: Textual (Python TUI)

**Features**:
- Real-time provider health with visual indicators (🟢/🔴)
- Performance comparison widgets for latency analysis
- Request inspector with live updates
- Configuration editor integration
- Auto-refreshing metrics display

**Usage**:
```bash
python3 scripts/ai-dashboard-enhanced.py
# q=quit, r=refresh, c=config_editor
```

**Best For**: Interactive troubleshooting, development workflows, visual exploration

#### WTH Dashboard Widgets
**Location**: `wth-widgets/litellm/`
**Framework**: Shell-based modular widgets

**Available Widgets**:
1. `health-status.sh` - Service health overview
2. `providers-overview.sh` - Provider status matrix
3. `litellm-metrics.sh` - Prometheus metrics sampler
4. `cache-performance.sh` - Redis cache statistics
5. `provider-score.sh` - Performance scoring
6. `litellm-logs.sh` - Recent proxy logs
7. `litellm-status.sh` - Detailed service status
8. `common.sh` - Shared helper functions

**Usage**:
```bash
# Install and configure
./scripts/install-wth-dashboard.sh

# Run WTH dashboard
wth run --config ~/.config/wth/wth.yaml
```

**Best For**: Persistent monitoring, tmux/screen integration, low resource overhead

**Dashboard Selection**:
- **Development**: Enhanced Textual for rich interactivity
- **Production**: WTH for lightweight persistent monitoring
- **Incident Response**: Both - WTH for baseline, Textual for deep dive
- **Performance Tuning**: WTH widgets for scripted before/after comparison

See `09-monitoring-dashboards.md` for complete dashboard documentation.

---

### Metrics (Prometheus)

**Endpoint**: `http://localhost:9090/metrics`
**Scrape Interval**: 15 seconds

**Provider Metrics**:
- `provider_requests_total{provider="ollama"}` - Request counter by provider
- `provider_latency_seconds{provider="vllm", quantile="0.95"}` - P95 latency
- `provider_errors_total{provider="llama_cpp"}` - Error counter
- `provider_availability{provider="ollama"}` - Health status (0/1)

**Router Metrics**:
- `router_routing_decisions{strategy="pattern_match"}` - Routing strategy usage
- `router_fallback_triggered{original_provider="vllm"}` - Fallback activations
- `cache_hit_rate{}` - Cache effectiveness ratio
- `router_load_balance_distribution{provider="ollama"}` - Traffic distribution

**System Metrics**:
- `active_connections` - Current concurrent connections
- `request_queue_size` - Pending request count
- `total_throughput_tokens_per_second` - System-wide token throughput

**Example PromQL Queries** (used by dashboards):
```promql
# Request rate (last 5 minutes)
rate(litellm_requests_total[5m])

# P95 latency by provider
histogram_quantile(0.95, rate(litellm_request_duration_seconds_bucket[5m]))

# Error rate
rate(litellm_requests_total{status="error"}[5m]) /
rate(litellm_requests_total[5m])

# Cache effectiveness
litellm_cache_hits / (litellm_cache_hits + litellm_cache_misses)
```

---

### Logging

**Log Destination**:
- systemd journal: `journalctl --user -u litellm.service`
- File-based: `/var/log/litellm/litellm.log` (if configured)

**Structured JSON Logs**:
```json
{
  "timestamp": "2025-11-11T14:30:00Z",
  "level": "INFO",
  "event": "request_routed",
  "model": "llama3.1:8b",
  "provider": "ollama",
  "latency_ms": 127,
  "cache_hit": false,
  "request_id": "req_abc123"
}
```

**Log Levels**:
- `DEBUG`: Routing decisions, cache lookups, health check details
- `INFO`: Successful requests, provider switches, configuration reloads
- `WARN`: Fallback triggers, high latency, degraded performance
- `ERROR`: Provider failures, timeout errors, configuration errors

**Log Analysis Tools**:
```bash
# Real-time monitoring
./wth-widgets/litellm/bin/litellm-logs.sh

# Error tracking
journalctl --user -u litellm.service | grep ERROR

# Performance analysis
journalctl --user -u litellm.service --since "1 hour ago" | \
  grep latency_ms | jq '.latency_ms' | \
  awk '{sum+=$1; count++} END {print "Avg:", sum/count "ms"}'
```

---

### Testing Infrastructure

**Kimi K2 Routing Test** - `test_kimi_routing.sh`

Validates routing, load balancing, and fallback chains:

**Test Cases**:
1. **Direct Model Request** - Exact match routing to `ollama_cloud`
2. **Capability-Based Routing** - Load balancing across reasoning model pool

**Usage**:
```bash
./test_kimi_routing.sh

# Expected output:
# Test 1: Direct request to kimi-k2:1t-cloud
# [Response from Kimi K2]
#
# Test 2: Reasoning capability request
# [Response from load-balanced model]
```

**Troubleshooting**:
```bash
# FAILED - Check OLLAMA_API_KEY
echo $OLLAMA_API_KEY

# Verify routing
grep "kimi-k2:1t-cloud" config/model-mappings.yaml

# Test LiteLLM routing
curl http://localhost:4000/v1/models | jq '.data[] | select(.id == "kimi-k2:1t-cloud")'
```

## Extensibility

### Adding New Provider

**Steps**:
1. Add entry to `config/providers.yaml`
2. Define routing rules in `config/model-mappings.yaml`
3. Add model definition to `config/litellm-unified.yaml`
4. Update this architecture document
5. Run validation script

**Example: Adding Anthropic**:
```yaml
# config/providers.yaml
anthropic:
  type: anthropic
  base_url: https://api.anthropic.com/v1
  status: active
  requires_api_key: true
  env_var: ANTHROPIC_API_KEY

# config/litellm-unified.yaml
model_list:
  - model_name: claude-3-sonnet
    litellm_params:
      model: anthropic/claude-3-sonnet-20240229
      api_key: ${ANTHROPIC_API_KEY}
```

### Custom Routing Strategies

Extend `config/model-mappings.yaml`:
```yaml
custom_strategies:
  cost_optimized:
    description: "Prefer cheapest provider"
    logic: |
      1. Calculate cost per request
      2. Route to cheapest available
      3. Fall back to quality if within 10% cost

  quality_first:
    description: "Always use best quality model"
    priority_order:
      - vllm (13B+)
      - ollama (8B)
      - llama_cpp (backup)
```

## Integration Points

### Future: GraphQL Interface

Planned enhancement for complex queries:
```graphql
query {
  generateText(
    model: "llama3.1:8b"
    prompt: "Hello"
    providers: [OLLAMA, VLLM]
    routing: FASTEST
  ) {
    text
    provider_used
    latency_ms
  }
}
```

## Related Documentation

- **Provider Registry**: See `02-provider-registry.md`
- **Routing Configuration**: See `03-routing-config.md`
- **Model Mappings**: See `04-model-mappings.md`
- **Integration Guide**: See `05-integration-guide.md`
- **OpenWebUI CLAUDE.md**: Full OpenWebUI architecture details
