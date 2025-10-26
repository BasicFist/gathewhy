# AI Backend Unified - Quick Reference

**One-page cheatsheet for common tasks**

---

## Common Tasks

### 🔧 Configuration Changes

```bash
# 1. Edit source configs
vim config/providers.yaml
vim config/model-mappings.yaml

# 2. Regenerate LiteLLM config
python3 scripts/generate-litellm-config.py

# 3. Validate
python3 scripts/validate-config-schema.py
./scripts/validate-all-configs.sh

# 4. Deploy (with backup & rollback)
./scripts/reload-litellm-config.sh

# Or force deploy (skip confirmation)
./scripts/reload-litellm-config.sh --force
```

---

### ➕ Add New Provider

```bash
# 1. Add to config/providers.yaml
providers:
  new_provider:
    type: openai
    base_url: http://localhost:PORT
    status: active
    models:
      - name: model-name

# 2. Add routing in config/model-mappings.yaml
exact_matches:
  model-name:
    provider: new_provider

# 3. Regenerate & deploy
python3 scripts/generate-litellm-config.py
./scripts/reload-litellm-config.sh
```

---

### ➕ Add New Model

```bash
# 1. Pull model on provider
ollama pull llama3.2:3b

# 2. Add to providers.yaml
models:
  - name: "llama3.2:3b"
    version: "3b"

# 3. Add exact match in model-mappings.yaml
exact_matches:
  "llama3.2:3b":
    provider: ollama

# 4. Regenerate & deploy
python3 scripts/generate-litellm-config.py
./scripts/reload-litellm-config.sh

# 5. Test
curl http://localhost:4000/v1/models | jq '.data[] | select(.id=="llama3.2:3b")'
```

---

### ✅ Validation & Testing

```bash
# Quick validation (all checks)
./scripts/validate-all-configs.sh

# With JSON output
./scripts/validate-all-configs.sh --json | jq .

# Critical checks only
./scripts/validate-all-configs.sh --critical

# Run tests
pytest -m unit                    # Fast unit tests
pytest -m integration             # Integration tests (requires providers)
pytest --cov=scripts              # With coverage

# Test specific provider
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

---

### 🔍 Monitoring & Debugging

```bash
# Check health
curl http://localhost:4000/health
curl http://localhost:4000/v1/models | jq

# View service logs
journalctl --user -u litellm.service -f
journalctl --user -u litellm.service --since "10 min ago"

# Monitor Redis cache
./scripts/monitor-redis-cache.sh

# Check port conflicts
./scripts/check-port-conflicts.sh

# Validate runtime
./scripts/validate-unified-backend.sh
```

---

### 🔙 Rollback & Recovery

```bash
# List backups
ls -lt ../openwebui/config/backups/

# Manual rollback
cp ../openwebui/config/backups/litellm.yaml.backup-TIMESTAMP \
   ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service

# Test backup rotation
./scripts/test-backup-rotation.sh

# Verify backup integrity
./scripts/verify-backup.sh
```

---

### 📊 Key Ports

| Service | Port | Check |
|---------|------|-------|
| **LiteLLM Gateway** | **4000** | `curl http://localhost:4000/health` |
| Ollama | 11434 | `curl http://localhost:11434/api/tags` |
| llama.cpp (Python) | 8000 | `curl http://localhost:8000/v1/models` |
| llama.cpp (Native) | 8080 | `curl http://localhost:8080/v1/models` |
| vLLM | 8001 | `curl http://localhost:8001/v1/models` |
| Redis | 6379 | `redis-cli ping` |

---

### 🛠️ Development Workflow

```bash
# Start session
cd ai-backend-unified
git status && git branch

# Make changes
vim config/*.yaml

# Validate locally
./scripts/validate-all-configs.sh
pytest -m unit

# Commit
git add -A
git commit -m "feat: description"
# Pre-commit hooks run automatically (validation, linting, type checking)

# Deploy
./scripts/reload-litellm-config.sh
```

---

### 📝 Configuration Files

| File | Purpose | Edit? |
|------|---------|-------|
| `config/providers.yaml` | Provider registry | ✅ YES |
| `config/model-mappings.yaml` | Routing rules | ✅ YES |
| `config/ports.yaml` | Port allocation | ✅ YES |
| `config/litellm-unified.yaml` | LiteLLM config | ❌ NO (AUTO-GENERATED) |

**⚠️ NEVER edit `litellm-unified.yaml` manually - it's regenerated from sources**

---

### 🚨 Troubleshooting

**Provider not responding:**
```bash
# Check service status
systemctl --user status ollama.service
systemctl --user status litellm.service

# Check health endpoints
curl http://localhost:11434/api/tags
curl http://localhost:4000/health

# View logs
journalctl --user -u litellm.service --since "5 min ago"
```

**Config validation fails:**
```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config/providers.yaml'))"

# Run consistency check
python3 scripts/validate-config-consistency.py

# Check detailed errors
./scripts/validate-all-configs.sh
```

**Model not routing correctly:**
```bash
# Check model list
curl http://localhost:4000/v1/models | jq '.data[].id'

# Check routing config
grep -A5 "model-name" config/model-mappings.yaml

# Test routing
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "model-name", "messages": [...]}' \
  -v  # Verbose to see routing
```

---

### 🔑 Quick Command Reference

```bash
# Validation
./scripts/validate-all-configs.sh              # Full validation
python3 scripts/validate-config-schema.py      # Schema only
python3 scripts/validate-config-consistency.py # Consistency only

# Configuration
python3 scripts/generate-litellm-config.py     # Regenerate config
./scripts/reload-litellm-config.sh             # Deploy config

# Monitoring
./scripts/monitor-redis-cache.sh               # Cache stats
./scripts/check-port-conflicts.sh              # Port check
./scripts/validate-unified-backend.sh          # Runtime validation

# Backup & Recovery
./scripts/test-backup-rotation.sh              # Test rotation
./scripts/verify-backup.sh                     # Verify backups

# Testing
pytest -m unit                                 # Unit tests
pytest -m integration                          # Integration tests
./scripts/test-rollback.sh                     # Rollback test
```

---

**See `README.md` for comprehensive documentation**
**See `docs/troubleshooting.md` for detailed troubleshooting guide**
