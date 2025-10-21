# Configuration Schema Reference

**Complete reference for all configuration files**

---

## Overview

The AI Backend Unified uses a **configuration-as-code** approach with three human-edited source files that generate the final LiteLLM configuration:

```
providers.yaml + model-mappings.yaml + ports.yaml
                    ↓
          generate-litellm-config.py
                    ↓
          litellm-unified.yaml (AUTO-GENERATED)
```

---

## config/providers.yaml

**Purpose**: Provider registry and model catalog

### Schema

```yaml
providers:
  <provider_name>:                    # Unique provider identifier
    type: <provider_type>             # Required: openai, ollama, vllm, llama_cpp
    base_url: <url>                   # Required: Provider API endpoint
    status: <status>                  # Required: active, inactive, deprecated
    health_endpoint: <path>           # Optional: Health check path
    models:                           # Optional: List of available models
      - name: <model_name>            # Required: Model identifier
        version: <version>            # Optional: Model version
        quantization: <quant>         # Optional: GGUF, AWQ, GPTQ, etc.
        context_length: <int>         # Optional: Max context window
        parameters: <params>          # Optional: Model parameter count
```

### Example

```yaml
providers:
  ollama:
    type: ollama
    base_url: "http://localhost:11434"
    status: active
    health_endpoint: "/api/tags"
    models:
      - name: "llama3.1:8b"
        version: "8b"
        quantization: "Q4_K_M"
        context_length: 131072
        parameters: "8B"

  vllm:
    type: vllm
    base_url: "http://localhost:8001"
    status: active
    health_endpoint: "/v1/models"
    models:
      - name: "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"
        version: "2.5"
        quantization: "AWQ"
        parameters: "7B"
```

### Field Descriptions

**provider_name**: Internal identifier (use lowercase, underscores allowed)

**type**: Provider type determines API compatibility
- `ollama`: Ollama API
- `vllm`: vLLM OpenAI-compatible API
- `openai`: OpenAI/Azure/compatible APIs
- `llama_cpp`: llama.cpp server

**base_url**: Full URL including protocol and port

**status**:
- `active`: Currently available for routing
- `inactive`: Temporarily disabled (not in routing)
- `deprecated`: Marked for removal

**health_endpoint**: Relative path for health checks (auto-prepended to base_url)

**models**: Array of model objects (optional but recommended for documentation)

---

## config/model-mappings.yaml

**Purpose**: Routing rules and fallback chains

### Schema

```yaml
exact_matches:
  <model_name>:
    provider: <provider_name>            # Required: Provider from providers.yaml
    backend_model: <backend_model_name>  # Optional: Provider's model name (if different)
    capabilities:                        # Optional: Model capabilities
      - <capability>

pattern_matches:
  - pattern: <regex>                     # Required: Regex pattern for model names
    provider: <provider_name>            # Required: Target provider

load_balancing:
  <model_name>:
    strategy: <strategy>                 # Required: round_robin, least_loaded, weighted
    providers:                           # Required: List of providers
      - name: <provider_name>
        weight: <int>                    # Optional: For weighted strategy

fallback_chains:
  <model_name>:
    chain:                               # Required: Ordered list of providers
      - <provider_name>
      - <fallback_provider>

capabilities:
  <capability_name>:
    preferred_models:                    # Required: Ordered by preference
      - <model_name>
```

### Example

```yaml
exact_matches:
  "llama3.1:8b":
    provider: ollama
    capabilities:
      - general_purpose
      - code_generation

  "qwen-coder-vllm":
    provider: vllm
    backend_model: "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"
    capabilities:
      - code_generation
      - code_analysis

pattern_matches:
  - pattern: "^Qwen/.*"
    provider: vllm

  - pattern: ".*:8b$"
    provider: ollama

load_balancing:
  llama2-13b:
    strategy: round_robin
    providers:
      - name: vllm
      - name: llama_cpp_native

fallback_chains:
  llama2-13b-vllm:
    chain:
      - vllm              # Primary
      - ollama            # Secondary
      - llama_cpp_python  # Tertiary

capabilities:
  code_generation:
    preferred_models:
      - qwen-coder-vllm
      - qwen2.5-coder:7b
      - llama3.1:8b

  high_throughput:
    preferred_models:
      - llama2-13b-vllm
      - qwen-coder-vllm
```

### Routing Precedence

1. **Exact match** (highest priority)
2. **Capability-based routing**
3. **Pattern matching**
4. **Default provider** (Ollama)

---

## config/ports.yaml

**Purpose**: Port allocation and conflict management

### Schema

```yaml
services:
  <service_name>:
    port: <port_number>              # Required: 1-65535
    protocol: <protocol>             # Required: http, tcp, udp
    description: <description>       # Required: Service description
    health_check: <url>              # Optional: Health check URL
    required: <boolean>              # Optional: true if critical service
```

### Example

```yaml
services:
  litellm_gateway:
    port: 4000
    protocol: http
    description: "LiteLLM unified gateway (main entry point)"
    health_check: "http://localhost:4000/health"
    required: true

  ollama:
    port: 11434
    protocol: http
    description: "Ollama local model server"
    health_check: "http://localhost:11434/api/tags"
    required: true

  vllm:
    port: 8001
    protocol: http
    description: "vLLM high-performance inference"
    health_check: "http://localhost:8001/v1/models"
    required: false
```

---

## config/litellm-unified.yaml (AUTO-GENERATED)

**⚠️ DO NOT EDIT MANUALLY - Regenerated from source configs**

This file is generated by `scripts/generate-litellm-config.py` and contains:

- **model_list**: All models from providers.yaml with litellm_params
- **router_settings**: Routing rules from model-mappings.yaml
- **litellm_settings**: Cache, CORS, telemetry settings
- **general_settings**: Server configuration

### Generation Command

```bash
python3 scripts/generate-litellm-config.py
```

### Structure

```yaml
# AUTO-GENERATED - DO NOT EDIT
# Generated: <timestamp>
# Version: <git-hash or timestamp>

model_list:
  - model_name: <name>
    litellm_params:
      model: <provider>/<backend_model>
      api_base: <provider_base_url>

router_settings:
  routing_strategy: <strategy>
  model_group_alias:
    <alias>: <model_name>
  fallbacks:
    <model>: [<fallback1>, <fallback2>]

litellm_settings:
  cache: true
  cache_params:
    type: redis
    host: localhost
    port: 6379

general_settings:
  master_key: <key>
  database_url: <url>
```

---

## Configuration Defaults

### Default Values

```yaml
# Providers
status: active (if not specified)
health_endpoint: /health

# Model Mappings
routing_strategy: simple-shuffle
fallback: ollama (if chain not specified)

# Ports
protocol: http (if not specified)
required: false (if not specified)

# LiteLLM
cache_ttl: 3600 (1 hour)
timeout: 600 (10 minutes)
max_retries: 2
```

### Override Precedence

1. Explicit value in config file (highest)
2. Generated default from scripts
3. LiteLLM built-in default (lowest)

---

## Schema Validation

### Pydantic Models

The configuration uses Pydantic models for validation:

```python
# Provider validation
class Provider(BaseModel):
    type: Literal["ollama", "vllm", "openai", "llama_cpp"]
    base_url: HttpUrl
    status: Literal["active", "inactive", "deprecated"]
    health_endpoint: Optional[str]
    models: Optional[List[Model]]

# Model validation
class Model(BaseModel):
    name: str
    version: Optional[str]
    quantization: Optional[str]
    context_length: Optional[int]
    parameters: Optional[str]

# Routing validation
class ExactMatch(BaseModel):
    provider: str  # Must exist in providers.yaml
    backend_model: Optional[str]
    capabilities: Optional[List[str]]
```

### Validation Commands

```bash
# Schema validation
python3 scripts/validate-config-schema.py

# Consistency validation
python3 scripts/validate-config-consistency.py

# Full validation
./scripts/validate-all-configs.sh
```

---

## Common Patterns

### Adding a Provider

1. Add to `providers.yaml` with all required fields
2. Add routing rules to `model-mappings.yaml`
3. Add port to `ports.yaml` (if new service)
4. Regenerate config
5. Deploy

### Removing a Provider

1. Set `status: deprecated` in `providers.yaml`
2. Remove from fallback chains in `model-mappings.yaml`
3. Regenerate config
4. Monitor for usage
5. After grace period: remove entirely

### Model Aliasing

```yaml
# In model-mappings.yaml
exact_matches:
  "gpt-4":                    # Alias (what clients use)
    provider: ollama
    backend_model: "llama3.1:8b"  # Real model
```

### Capability-Based Routing

```yaml
capabilities:
  fast_response:
    preferred_models:
      - llama-cpp-native-model
      - ollama-small-model

  high_quality:
    preferred_models:
      - vllm-large-model
      - ollama-large-model
```

---

## Best Practices

1. **Always validate** after editing configs
2. **Use descriptive names** for providers and models
3. **Document capabilities** in provider model entries
4. **Test routing** after adding new models
5. **Keep backups** before major changes (reload script does this automatically)
6. **Version control** all source configs
7. **Never edit** litellm-unified.yaml manually
8. **Use exact matches** for known models (faster routing)
9. **Add fallback chains** for critical models
10. **Monitor health** endpoints regularly

---

**See `QUICK-REFERENCE.md` for common tasks**
**See `README.md` for comprehensive documentation**
