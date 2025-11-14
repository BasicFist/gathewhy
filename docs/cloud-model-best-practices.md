# Cloud Model Best Practices

Guidelines for running the large Ollama Cloud models through the unified LiteLLM gateway. These settings keep latency reasonable, prevent runaway spend, and make the fallback chain predictable.

---

## Overview

- Cloud models are declared in `config/providers.yaml` under `ollama_cloud`.
- They become available after running `python3 scripts/generate-litellm-config.py`.
- LiteLLM is restarted automatically (`systemctl --user restart litellm.service`).
- Crush/OpenWebUI pull their model list from `GET /v1/models`.

Keep a Redis cache and fallback routes enabled; these high-parameter models are slow, and offloading work to local models saves both time and money whenever possible.

---

## Core settings (all cloud models)

| Setting | Recommendation | Where to set it |
|---------|----------------|-----------------|
| Auth | Clients stay keyless; only the provider’s `OLLAMA_API_KEY` is required so the gateway can call Ollama Cloud on behalf of users. | `~/.config/codex/secrets.env` (synced to systemd). |
| Timeouts | Leave `request_timeout: 60`, `timeout: 300` in `litellm_settings`. Increase per model if you expect long outputs (> 8K tokens). | `config/providers.yaml` → regenerate → restart. |
| Streaming | Keep `stream: true`. Only disable if a client can’t handle tokens. | In model definition under `litellm_params`. |
| Cache | Redis is on by default (`cache: true`, `ttl: 3600`). Increase TTL for expensive calls or set `metadata["cache_key"]` in your app. | `litellm_settings.cache_params` or per request metadata. |
| Prompt size | Chunk inputs if combined prompt + completion exceeds 16K tokens (or the model limit). | Application layer. |
| Fallbacks | Maintain the fallback order in `router_settings`. If a cloud call fails, LiteLLM should transparently fallback to a cheaper/local model. | `config/model-mappings.yaml`. |
| Cost tracking | Use metadata (e.g. `{"project":"thesis"}`) and monitor LiteLLM logs / Prometheus metrics. | Call metadata. |

Basic tuning can be applied with an `extra_body` block in each `litellm_params`. Example for GPT-OSS 20B:

```yaml
extra_body:
  temperature: 0.5
  top_p: 0.85
  frequency_penalty: 0.2
  max_tokens: 1500
```

---

## Model-specific guidance

### DeepSeek V3.1 (671B)
- Role: advanced reasoning, math, data analysis.
- Defaults: `temperature=0.3`, `max_tokens=2048`.
- Context: 128K+ but very slow; rely on fallback to smaller models for quick tasks.
- Tip: Keep streaming enabled; it streams chunked paragraphs slowly but refuses connections if you try to pull huge completions fast.

### Qwen3-Coder 480B
- Role: code generation/refactoring, translation.
- Defaults: `temperature=0.2`, `top_p=0.8`, `presence_penalty=0.1`.
- Context: 32K.
- Tip: Tag capability group `code_generation` to prefer this model only when a long-form code task is detected.

### Kimi K2 1T
- Role: research synthesis, multi-doc summarisation, multi-lingual reasoning.
- Defaults: `temperature=0.4`, `max_tokens=1024`, `frequency_penalty=0.3`.
- Context: 128K.
- Tip: Hard-cap `max_tokens` for front-end prompts. The model tends to produce very long outputs unless capped.

### GPT-OSS 120B & 20B
- Role: general knowledge chat. Use 120B for “best” answers, 20B as cheaper fallback.
- Defaults: `temperature=0.6` (120B), `0.5` (20B); `top_p=0.85`.
- Tip: Provide both versions in the router config. LiteLLM can promote 20B to first choice during outages or when you need cheaper throughput.

### GLM 4.6 Cloud (Ollama)
- Role: bilingual (Chinese/English) general chat, structured writing.
- Defaults: `temperature=0.45`, `top_p=0.9`, `max_tokens=1536`.
- Tip: Pair with an English local fallback to keep bilingual tasks from going entirely to the cloud.

### Extended Catalog Examples
- **aya-expanse:32b-cloud** – multilingual policy/finance assistant. Add an `extra_body.temperature` of `0.3` to keep responses precise and pair it with `qwen3-coder:480b-cloud` for complex translations.
- **phi-4:mini-cloud** – 14B-class chat model for budget-sensitive workloads. Use `max_tokens: 768` to keep responses snappy and let the router fall back to `gpt-oss:20b-cloud` for larger prompts.
- **llama-guard3:cloud** – moderation stage that inspects prompts/responses before forwarding to the main model. Configure it as the first hop in a fallback chain, then call your conversational model if the guard marks the request as safe.

---

## UI integration (OpenWebUI)

1. Ensure `ai/services/openwebui/config/litellm.yaml` has a model entry for the cloud model:

   ```yaml
   - model_name: gpt-oss-cloud
   litellm_params:
       model: ollama_chat/gpt-oss:20b-cloud
       api_base: ${OLLAMA_CLOUD_BASE_URL:https://api.ollama.com/v1}
     model_info:
       tags: ["general", "cloud", "20b"]
       provider: ollama_cloud
   ```

2. Restart OpenWebUI if running as a service:

   ```bash
   systemctl --user restart openwebui.service
   ```

3. Reload the browser; the model appears in the picker with the tag badges.

Apply the same pattern for any new cloud slot—add it to `providers.yaml`, regenerate LiteLLM, and mirror it in OpenWebUI if it should be user-selectable.

---

## Change checklist

1. Update `config/providers.yaml` and (if needed) `config/model-mappings.yaml`.
2. Generate config: `python3 scripts/generate-litellm-config.py`.
3. Restart service: `systemctl --user restart litellm.service`.
4. Verify models: `curl http://127.0.0.1:4000/v1/models`.
5. If OpenWebUI is running, restart it.

Repeat whenever you add or retune a model; this keeps everything declarative.
