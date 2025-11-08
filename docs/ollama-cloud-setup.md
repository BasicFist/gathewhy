# Ollama Cloud Setup & Operations

## Prerequisites

- LiteLLM unified backend already running (`systemctl --user status litellm.service`)
- Access to LAB's secret store (SOPS + age)
- Two credentials from https://ollama.com/settings/keys:
  - **Ollama Key** (`OLLAMA_KEY`) – lets the local CLI talk to your account (pull/push)
  - **API Key** (`OLLAMA_API_KEY`) – authenticates REST/SDK calls (LiteLLM, etc.)
- Python 3.11+ environment for running `generate-litellm-config.py`

## 1. Configure Environment

> **Default behaviour:** the unified backend ships with `OLLAMA_ENABLE_CLOUD=false` and no keys, so cloud models automatically fall back to local capacity. Provide the keys below only if you intend to call cloud endpoints.

Add the keys to LAB's encrypted secret file and let direnv export them automatically:

```bash
cd ~/LAB

# decrypt, edit, re-encrypt (SOPS handles age encryption)
sops secrets/global.enc.env

# add/update entries inside the file (example)
# OLLAMA_KEY="acc_..."
# OLLAMA_API_KEY="api_..."
# OLLAMA_ENABLE_CLOUD="true"

# save & exit (SOPS re-encrypts automatically)
```

On the next `cd ~/LAB`, direnv will load the secrets (see `.envrc`). A trimmed-down env file is also written to `~/.config/lab-secrets/litellm.env` for systemd consumption.

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

# systemd picks up keys from ~/.config/lab-secrets/litellm.env (written by .envrc)
systemctl --user daemon-reload
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
| 401 Unauthorized | `echo $OLLAMA_API_KEY` & `echo $OLLAMA_KEY` → ensure direnv loaded secrets and `litellm.env` exists |
| Models missing | Rerun generator & restart LiteLLM |
| High latency | Local GPU saturated → use smaller models or scale down requests |
| Crush duplicates | Apply `CRUSH-CONFIG-FIX.json` as documented |

## 8. Related Docs

- `CLOUD_MODELS_READY.md`
- `docs/crush-integration.md`
- `docs/local-vs-cloud-routing.md`
- `CRUSH-CONFIG-AUDIT.md`
- `CRUSH-FIX-APPLIED.md`
