# Ollama Cloud Setup & Operations

## Prerequisites

- LiteLLM unified backend already running (`systemctl --user status litellm.service`)
- `OLLAMA_API_KEY` from https://ollama.com/settings/keys
- Python 3.11+ environment for running `generate-litellm-config.py`

## 1. Configure Environment

```bash
export OLLAMA_API_KEY="your-key-here"
# Persist for future shells
if ! grep -q OLLAMA_API_KEY ~/.bashrc; then
  echo 'export OLLAMA_API_KEY="your-key-here"' >> ~/.bashrc
fi
```

## 2. Enable Provider in config/providers.yaml

Add the `ollama_cloud` provider block (already committed). Confirm the status is `active`.

## 3. Update Model Routing

Ensure `config/model-mappings.yaml` contains exact matches and fallback chains for the six cloud models:

- `deepseek-v3.1:671b-cloud`
- `qwen3-coder:480b-cloud`
- `kimi-k2:1t-cloud`
- `gpt-oss:120b-cloud`
- `gpt-oss:20b-cloud`
- `glm-4.6:cloud`

## 4. Regenerate LiteLLM Config

```bash
cd ~/LAB/ai/backend/ai-backend-unified
python3 scripts/generate-litellm-config.py
cp config/litellm-unified.yaml runtime/config/litellm.yaml
systemctl --user restart litellm.service
```

## 5. Validate

```bash
./scripts/validate-unified-backend.sh
curl http://localhost:4000/v1/models | jq '.data[] | select(.id | contains("cloud")) | .id'
```

Expected models:

- `deepseek-v3.1:671b-cloud`
- `qwen3-coder:480b-cloud`
- `kimi-k2:1t-cloud`
- `gpt-oss:120b-cloud`
- `gpt-oss:20b-cloud`
- `glm-4.6:cloud`

## 6. Usage Tips

- Use local models for iterative work; reserve cloud models for heavy lifts.
- Requests automatically fall back from local → vLLM → cloud.
- Monitor usage via structured logs or Grafana (once Prometheus metrics are enabled).
- Set `AI_BACKEND_METRICS_HOST/PORT` if you expose metrics via the community exporter.

## 7. Troubleshooting

| Symptom | Fix |
|---------|-----|
| 401 Unauthorized | `echo $OLLAMA_API_KEY` → ensure service environment inherits it |
| Models missing | Rerun generator & restart LiteLLM |
| High latency | Local GPU saturated → use smaller models or scale down requests |
| Crush duplicates | Apply `CRUSH-CONFIG-FIX.json` as documented |

## 8. Related Docs

- `CLOUD_MODELS_READY.md`
- `docs/crush-integration.md`
- `docs/local-vs-cloud-routing.md`
- `CRUSH-CONFIG-AUDIT.md`
- `CRUSH-FIX-APPLIED.md`
