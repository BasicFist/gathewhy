# Backend Observability & Control

This document describes the integrated observability, budgeting, and control system for the AI Backend Unified infrastructure.

## Overview

The backend implements a centralized callback pipeline that intercepts every LLM request to provide:
1.  **Structured Logging:** Detailed usage logs in SQLite.
2.  **Metrics:** Real-time Prometheus metrics (latency, cost, tokens).
3.  **Budgets:** Global budget enforcement per provider, model, or capability.
4.  **Control:** Dashboard integration for configuration and service management.

## Core Components

### 1. Callback Pipeline (`backend/callbacks.py`)
A `CallbackManager` executes a chain of callbacks for every request:
- `on_request(ctx)`: Called before the request is sent to the provider. Checks budgets.
- `on_success(ctx)`: Called after a successful response. Logs usage and updates metrics.
- `on_error(ctx)`: Called on failure. Logs errors and updates failure metrics.

### 2. Usage Logging (`runtime/usage/llm_usage.db`)
All requests are logged to a local SQLite database for audit and analysis.
**Schema:**
- `timestamp`: ISO8601 time
- `provider`: e.g., "ollama", "openai"
- `logical_model`: The model requested (e.g., "gpt-4")
- `concrete_model`: The actual model used
- `cost_usd`: Estimated cost
- `latency_ms`: Request duration
- `status`: "success" or "error"

### 3. Prometheus Metrics
Exposed via the LiteLLM `/metrics` endpoint (port 4000).
- `backend_llm_requests_total{provider, model, capability, status}`
- `backend_llm_latency_seconds{...}` (Histogram)
- `backend_llm_tokens_total{..., type="prompt|completion"}`
- `backend_llm_cost_usd_total{...}`
- `backend_llm_budget_exceeded_total{scope, target}`

### 4. Budgets (`runtime/budget_config.json`)
Budgets are defined in `config/providers.yaml` or `config/model-mappings.yaml` and exported to runtime.
**Example Config:**
```yaml
capabilities:
  code:
    budget:
      max_budget_usd: 10.0
      budget_window: "1d"
```
The backend checks these budgets *before* every request and logs warnings/metrics if exceeded.

### 5. Guardrails (`backend/security/guardrails.py`)
Basic security checks are performed on every prompt:
- **Secret Scanning:** Detects potential API keys (sk-..., gh_..., etc.).
- **Blocking:** High-risk violations can block the request (depending on LiteLLM version/config).

### 6. Caching
Local disk caching is available to reduce latency and costs for repetitive prompts.
- **Enable:** Set `AI_BACKEND_ENABLE_CACHE=true` in your environment (e.g., `.env` or systemd).
- **Storage:** Cached responses are stored in `.litellm_cache/`.

## Control & Introspection

### Dashboard (`scripts/ptui`)
The terminal dashboard (`ptui`) is the primary control center:
- **Monitor:** View real-time GPU usage and service health.
- **Control:** Start/Stop/Restart services (vLLM, Ollama).
- **Config:** Regenerate LiteLLM configuration or inspect the logical routing table.

### Introspection Script
To view the current logical configuration (redacted):
```bash
python3 scripts/print-logical-config.py
```

## Development

To add a new callback:
1.  Inherit from `Callback` in `backend/callbacks.py`.
2.  Implement `on_request`, `on_success`, and `on_error`.
3.  Register it in `backend/litellm_integration.py`.
