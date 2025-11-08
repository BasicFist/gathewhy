# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Unified Backend Infrastructure** - A configuration-driven LLM gateway coordination project that provides a single entry point (LiteLLM on port 4000) routing requests to multiple LLM inference providers: Ollama, llama.cpp, and vLLM. This is a **configuration and automation project**, not an application codebase. The actual gateway runs in the OpenWebUI project; this project manages configuration, validation, testing, and observability.

## Architecture

```
LAB Projects (request llama3.1:8b)
              ↓
LiteLLM Gateway :4000 (single endpoint, transparent routing)
              ↓
     ┌────────┼────────┬──────────┐
     ↓        ↓        ↓          ↓
Ollama    llama.cpp  vLLM    (Future providers)
:11434    :8000/:8080 :8001
```

**Key Characteristics**:
- **Configuration-driven**: Providers and routing defined in YAML, no code changes needed
- **Extensible**: Add providers by updating `config/providers.yaml` and `config/model-mappings.yaml`
- **Validation-heavy**: Multiple layers of validation (YAML syntax, schemas, consistency checks)
- **Well-tested**: 75+ automated tests (unit, integration, contract, rollback)
- **Observable**: Complete monitoring stack with Prometheus, Grafana, structured logging

## Common Development Tasks

### Configuration Management

```bash
# View the source of truth for all providers
cat config/providers.yaml

# View model-to-provider routing rules
cat config/model-mappings.yaml

# View generated LiteLLM gateway configuration (do NOT edit directly)
cat config/litellm-unified.yaml  # AUTO-GENERATED marker at top

# Regenerate LiteLLM config after updating providers or model mappings
python3 scripts/generate-litellm-config.py
```

### Validation Workflow

```bash
# Run comprehensive validation (11 checks: YAML, models, ports, providers, Redis, schema, etc.)
./scripts/validate-all-configs.sh

# Run critical checks only (faster)
./scripts/validate-all-configs.sh --critical

# JSON output for CI/CD integration
./scripts/validate-all-configs.sh --json | jq .

# Check specific aspects
python3 scripts/validate-config-schema.py      # Pydantic schema validation
python3 scripts/validate-config-consistency.py # Cross-config consistency
./scripts/check-port-conflicts.sh              # Port availability
```

### Testing

```bash
# Run all tests
pytest

# Run by category
pytest -m unit        # Fast unit tests (~10s), no external deps
pytest -m integration # Requires Ollama + vLLM running
pytest -m contract    # Provider API compliance

# Run with coverage
pytest --cov=config --cov-report=html

# Run specific test
pytest tests/unit/test_routing.py::test_model_routing

# Run with verbose output
pytest -v

# Run in parallel (faster for large test suites)
pytest -n auto
```

### Adding a New Provider

1. **Update provider registry**:
   ```bash
   vim config/providers.yaml  # Add provider entry with type, base_url, models
   ```

2. **Define routing rules**:
   ```bash
   vim config/model-mappings.yaml  # Add model→provider mappings and fallback chains
   ```

3. **Generate LiteLLM config**:
   ```bash
   python3 scripts/generate-litellm-config.py
   python3 scripts/validate-config-schema.py  # Validate schemas
   python3 scripts/validate-config-consistency.py  # Check consistency
   ```

4. **Test the changes**:
   ```bash
   pytest -m unit  # Unit tests pass first
   pytest -m contract  # Provider contract compliance
   pytest -m integration  # End-to-end with real providers (if available)
   ```

5. **Update documentation and memories**:
   - Add provider info to Serena memories in `.serena/memories/`
   - Document in relevant docs files

6. **Commit with validation**:
   ```bash
   git add config/ .serena/memories/
   git commit -m "feat: add <provider> provider"
   # Pre-commit hooks will validate automatically
   ```

### Monitoring & Debugging

```bash
# Health check all providers
./scripts/validate-unified-backend.sh

# Start monitoring stack (Prometheus + Grafana)
cd monitoring && docker compose up -d

# Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090

# Monitor requests in real-time
./scripts/debugging/tail-requests.py

# Analyze historical logs
./scripts/debugging/analyze-logs.py

# Test specific request with debugging
./scripts/debugging/test-request.py --model llama3.1:8b --prompt "Hello"

# Profile provider performance
./scripts/profiling/profile-latency.py      # TTFB analysis
./scripts/profiling/profile-throughput.py   # Concurrency testing
./scripts/profiling/compare-providers.py    # Side-by-side comparison

# Run load tests
cd scripts/loadtesting/locust && locust -f litellm_locustfile.py --host http://localhost:4000
# or
k6 run scripts/loadtesting/k6/smoke-test.js
```

### Configuration Hot-Reload

```bash
# Update configuration safely without downtime
./scripts/reload-litellm-config.sh --validate-only  # Dry run
./scripts/reload-litellm-config.sh                   # Apply changes with automatic backup
./scripts/reload-litellm-config.sh --force           # Force reload

# Features:
# ✅ Automatic YAML validation
# ✅ Automatic backup before reload (timestamped)
# ✅ Service health verification after reload
# ✅ Automatic rollback on failure
# ✅ Configuration diff display
```

### Redis Cache Management

```bash
# View cache statistics and health
./scripts/monitor-redis-cache.sh

# List all cache keys
./scripts/monitor-redis-cache.sh --keys

# Continuous monitoring (updates every 5s)
./scripts/monitor-redis-cache.sh --watch

# Clear cache (with confirmation)
./scripts/monitor-redis-cache.sh --flush
```

### Port Management

```bash
# Check all registered ports
./scripts/check-port-conflicts.sh

# Check only required ports (LiteLLM, Ollama, Redis)
./scripts/check-port-conflicts.sh --required

# Check specific port
./scripts/check-port-conflicts.sh --port 4000

# Attempt to free conflicting ports
./scripts/check-port-conflicts.sh --fix
```

## Project Structure

```
ai-backend-unified/
├── .github/workflows/          # CI/CD pipeline (GitHub Actions)
│   └── validate.yml            # 6-stage validation pipeline
├── .serena/                    # Serena project integration
│   ├── project.yml
│   └── memories/               # 8 knowledge base files
├── config/                     # Configuration source of truth
│   ├── providers.yaml          # Provider registry (edit this)
│   ├── model-mappings.yaml     # Routing rules (edit this)
│   ├── litellm-unified.yaml    # Generated LiteLLM config (AUTO-GENERATED, don't edit)
│   ├── ports.yaml              # Port registry
│   ├── backups/                # Auto-created backups on reload
│   └── schemas/                # Pydantic validation models
├── scripts/                    # Automation and utilities
│   ├── generate-litellm-config.py     # Generate config from YAML sources
│   ├── validate-config-schema.py      # Pydantic validation
│   ├── validate-config-consistency.py # Cross-config consistency check
│   ├── validate-all-configs.sh        # Comprehensive validation (11 checks)
│   ├── validate-unified-backend.sh    # Provider health checks
│   ├── check-port-conflicts.sh        # Port availability check
│   ├── monitor-redis-cache.sh         # Cache monitoring
│   ├── reload-litellm-config.sh       # Safe config hot-reload
│   ├── check-port-conflicts.sh        # Port conflict detection
│   ├── debugging/                     # Request analysis tools
│   ├── profiling/                     # Performance analysis tools
│   ├── loadtesting/                   # Load test suites
│   ├── manage-providers.py            # Provider management utility
│   ├── ptui_dashboard.py              # TUI monitoring dashboard
│   └── monitor*                       # Various monitoring scripts
├── tests/                      # Comprehensive test suite (75+ tests)
│   ├── unit/                   # Unit tests (30+, fast)
│   ├── integration/            # Integration tests (25+, requires providers)
│   ├── contract/               # Provider contract compliance
│   ├── monitoring/             # Monitoring stack validation
│   ├── fixtures/               # Test data and fixtures
│   ├── conftest.py             # Pytest configuration
│   └── README.md               # Testing documentation
├── monitoring/                 # Observability stack
│   ├── docker-compose.yml      # Prometheus + Grafana
│   ├── prometheus.yml          # Metrics scraping config
│   └── grafana/                # 5 pre-built dashboards
├── docs/                       # Documentation
│   ├── architecture.md         # System design
│   ├── adding-providers.md     # Provider integration guide
│   ├── consuming-api.md        # API usage for LAB projects
│   ├── observability.md        # Monitoring and debugging guide
│   ├── troubleshooting.md      # Common issues and solutions
│   ├── quick-start.md          # Quick start guide
│   └── model-selection-guide.md # Choose the right model
├── web-ui/                     # Web dashboard (optional UI)
│   ├── app.py                  # Flask application
│   └── database.py             # SQLite database
├── .pre-commit-config.yaml     # Pre-commit hooks for validation
├── pyproject.toml              # Project metadata and ruff/pytest config
├── requirements.txt            # Python dependencies
└── README.md                   # Project README
```

## Configuration Files (Source of Truth)

### `config/providers.yaml` - Provider Registry

Defines all available LLM providers: type, endpoint, models, status. This is the source of truth. Example:

```yaml
providers:
  ollama:
    type: "ollama"
    base_url: "http://localhost:11434"
    status: "active"
    models:
      - name: "llama3.1:8b"
        quantization: "Q4"
  vllm:
    type: "vllm"
    base_url: "http://localhost:8001"
    status: "active"
    models:
      - name: "Qwen2.5-Coder-7B-Instruct-AWQ"
```

### `config/model-mappings.yaml` - Routing Rules

Defines how model requests route to providers with fallback chains. Example:

```yaml
routes:
  exact_matches:
    "llama3.1:8b":
      provider: "ollama"
      fallback_chain: ["vllm"]

  patterns:
    "qwen*":
      provider: "vllm"
      fallback_chain: ["ollama"]
```

### `config/litellm-unified.yaml` - Generated LiteLLM Config

**IMPORTANT**: This file is AUTO-GENERATED. Do NOT edit directly. It's generated from `providers.yaml` and `model-mappings.yaml` via `scripts/generate-litellm-config.py`. It contains the complete LiteLLM gateway configuration including observability settings.

## Testing Strategy

### Test Pyramid

```
     E2E (Rollback validation)
    /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
   / Integration Tests    \    25+ tests (requires providers)
  /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
 / Contract Tests         \    Provider API compliance
/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
/‾‾‾‾ Unit Tests ‾‾‾‾‾‾‾‾\  30+ tests (fast, no deps)
```

### Test Categories

```bash
# Fast unit tests (10-15 seconds)
pytest -m unit

# Integration tests (5+ minutes, requires Ollama + vLLM)
pytest -m integration

# Provider compliance tests
pytest -m contract

# Monitoring stack tests
pytest -m monitoring

# Specific provider tests
pytest -m requires_ollama    # Tests requiring Ollama
pytest -m requires_vllm      # Tests requiring vLLM
pytest -m requires_redis     # Tests requiring Redis

# Slow tests (>5 seconds)
pytest -m slow
```

### CI/CD Pipeline

GitHub Actions (`.github/workflows/validate.yml`) runs on every push:

1. **YAML Syntax Validation** - yamllint + Python YAML parsing
2. **Schema Validation** - Pydantic model validation
3. **Secret Scanning** - detect-secrets baseline check
4. **Documentation Sync** - Architecture & Serena memory completeness
5. **Generated Config Check** - AUTO-GENERATED marker validation
6. **Comprehensive System Validation** - 11-check system validation (local: `./scripts/validate-all-configs.sh`)
7. **Integration Tests** (optional) - Requires active providers

All stages run in ~3-5 minutes total.

## Quality Standards

### Code Quality Tools

```bash
# Lint with ruff (configured in pyproject.toml)
ruff check scripts/ tests/

# Auto-fix safe issues
ruff check --fix scripts/ tests/

# Format code
ruff format scripts/ tests/

# Type checking (optional)
mypy scripts/ tests/
```

### Pre-Commit Hooks

Configuration in `.pre-commit-config.yaml`:
- YAML linting (yamllint)
- Secret detection (detect-secrets)
- Configuration validation (custom hooks)

Hooks run automatically on `git commit`. To bypass (not recommended):
```bash
git commit --no-verify
```

## Related Projects

- **OpenWebUI** (`../openwebui/`): Contains actual LiteLLM server, Ollama integration, llama.cpp backends

## Important Notes

- **Configuration is sacred**: Changes to `providers.yaml` or `model-mappings.yaml` flow through multiple validation layers
- **Never edit litellm-unified.yaml directly**: It's auto-generated. Edit source files instead and regenerate
- **Validation before deployment**: Always run `./scripts/validate-all-configs.sh` before committing config changes
- **Test coverage target**: Unit tests maintain >90% coverage
- **Rollback-safe**: Configuration changes are automatically backed up; rollback is one command

## Git Workflow

```bash
# Create feature branch for config changes
git checkout -b feat/add-provider-xyz

# Make configuration changes
vim config/providers.yaml
vim config/model-mappings.yaml

# Regenerate and validate
python3 scripts/generate-litellm-config.py
./scripts/validate-all-configs.sh

# Test changes
pytest -m unit
pytest -m integration  # if providers available

# Update documentation/memories
vim docs/adding-providers.md
vim .serena/memories/*.md

# Commit (pre-commit hooks validate automatically)
git add config/ docs/ .serena/memories/
git commit -m "feat: add provider xyz with routing rules"

# Push (CI/CD pipeline validates on GitHub)
git push origin feat/add-provider-xyz
```

## Debugging

### Provider Not Responding

```bash
# Check if provider is running
curl http://localhost:11434/api/tags      # Ollama
curl http://localhost:8000/v1/models      # llama.cpp (Python)
curl http://localhost:8001/v1/models      # vLLM

# Check LiteLLM routing
curl http://localhost:4000/v1/models | jq

# Review LiteLLM logs
./scripts/debugging/tail-requests.py
journalctl --user -u litellm.service -f
```

### Configuration Validation Fails

```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config/providers.yaml'))"

# Run comprehensive validation with details
./scripts/validate-all-configs.sh

# Check specific validation
python3 scripts/validate-config-schema.py
python3 scripts/validate-config-consistency.py
```

### Model Routing Not Working

```bash
# Test specific model routing
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.1:8b", "messages": [{"role": "user", "content": "test"}]}'

# Check model mappings
grep "llama3.1:8b" config/model-mappings.yaml
grep "llama3.1:8b" config/litellm-unified.yaml

# Analyze request with debugging
./scripts/debugging/test-request.py --model llama3.1:8b --debug
./scripts/debugging/analyze-logs.py --model llama3.1:8b
```

## Documentation Structure

- **README.md** - Project overview and quick start
- **docs/architecture.md** - System design and request flows
- **docs/adding-providers.md** - Step-by-step provider integration guide
- **docs/consuming-api.md** - How LAB projects use the unified endpoint
- **docs/observability.md** - Monitoring, debugging, profiling, load testing
- **docs/quick-start.md** - Get started in 5 minutes
- **docs/troubleshooting.md** - Common issues and solutions
- **tests/README.md** - Testing documentation and test categories
- **scripts/README.md** - Scripts documentation

## Key Concepts

### Provider Abstraction

Users request models by name (e.g., "llama3.1:8b"). LiteLLM routes transparently to the appropriate provider via rules in `config/model-mappings.yaml`. If a provider is down, automatic fallback chains route to secondary/tertiary providers.

### Configuration Generation

Source files (`providers.yaml`, `model-mappings.yaml`) are edited by humans. These are transformed into `litellm-unified.yaml` by `scripts/generate-litellm-config.py`. The generated file is never edited directly—it contains the `AUTO-GENERATED` marker at the top.

### Validation Layers

1. **Pre-commit hooks**: Local validation before commits
2. **Configuration schema**: Pydantic validation of structure and types
3. **Consistency validation**: Cross-file model name verification
4. **Port conflict detection**: Ensure no port collisions
5. **Provider health checks**: Endpoints actually respond
6. **CI/CD pipeline**: Full validation on every push
7. **Integration tests**: End-to-end routing verification

### Observability

- **Prometheus metrics**: Token usage, request counts, latency (P50/P95/P99)
- **Grafana dashboards**: 5 pre-built dashboards (overview, tokens, performance, health, system)
- **Structured logging**: JSON logs with request IDs for tracing
- **Debugging tools**: Request analysis, latency profiling, provider comparison
- **Load testing**: Locust (interactive) and k6 (CI/CD friendly)

## Common Mistakes

- ❌ Editing `litellm-unified.yaml` directly (it's auto-generated)
- ❌ Adding providers without updating both config files
- ❌ Committing config changes without running validation
- ❌ Assuming vLLM is always running (it's optional and may not be deployed)
- ❌ Not checking fallback chains when a provider is down
- ✅ Always edit `providers.yaml` and `model-mappings.yaml`
- ✅ Always regenerate with `scripts/generate-litellm-config.py`
- ✅ Always validate with `./scripts/validate-all-configs.sh`
- ✅ Always test before committing

## Quick Commands Reference

```bash
# Validate everything
./scripts/validate-all-configs.sh

# Run all tests
pytest

# Add new provider
vim config/providers.yaml
vim config/model-mappings.yaml
python3 scripts/generate-litellm-config.py
./scripts/validate-all-configs.sh

# Check provider health
./scripts/validate-unified-backend.sh

# Start monitoring
cd monitoring && docker compose up -d

# Monitor requests
./scripts/debugging/tail-requests.py

# Test model routing
curl http://localhost:4000/v1/models | jq

# Check port conflicts
./scripts/check-port-conflicts.sh

# Hot-reload config
./scripts/reload-litellm-config.sh
```
