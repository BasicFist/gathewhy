# AI Backend Unified Infrastructure - Project Index

**Version**: 1.0
**Last Updated**: 2025-10-21
**Project Type**: Configuration & Documentation Coordination Layer

## Quick Navigation

- [Project Overview](#project-overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Development Workflow](#development-workflow)
- [Documentation Map](#documentation-map)

---

## Project Overview

### Purpose
Single LiteLLM gateway (port 4000) routing requests to multiple LLM inference providers in the LAB ecosystem.

### Key Insight
This is a **coordination and documentation project** - it contains NO application code. It provides:
- Configuration files defining provider registry and routing rules
- Documentation of the unified architecture
- Validation scripts for health checking
- Serena memories for knowledge preservation

### Related Projects
- **OpenWebUI** (`../openwebui/`): Contains the actual LiteLLM server, Ollama integration, llama.cpp backends
- **CrushVLLM** (`../CRUSHVLLM/`): vLLM inference engine with MCP integration

---

## Quick Start

### For New Users

```bash
# 1. Check system health
cd ai-backend-unified
./scripts/validate-unified-backend.sh

# 2. View available models
curl http://localhost:4000/v1/models | jq

# 3. Test a completion
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

### For Developers

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run tests
pytest -m unit

# 3. Validate configuration
python3 scripts/validate-config-schema.py

# 4. Install pre-commit hooks
pre-commit install
```

### For LAB Projects

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000",  # Unified gateway
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="llama3.1:8b",  # Routes to Ollama
    messages=[{"role": "user", "content": "Hello"}]
)
```

See [docs/consuming-api.md](docs/consuming-api.md) for complete integration guide.

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│            LAB AI Backend Infrastructure                │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │     Single Entry Point: LiteLLM :4000            │  │
│  │  OpenAI-Compatible API + MCP Protocol            │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                     │
│         ┌─────────┼──────────┬──────────┐              │
│         │         │          │          │              │
│         ▼         ▼          ▼          ▼              │
│    ┌────────┐ ┌──────┐ ┌────────┐ ┌─────────┐         │
│    │ Ollama │ │llama │ │ vLLM   │ │ Future  │         │
│    │ :11434 │ │.cpp  │ │ :8001  │ │Providers│         │
│    └────────┘ └──────┘ └────────┘ └─────────┘         │
└─────────────────────────────────────────────────────────┘
```

### Request Flow

1. LAB project sends request to `http://localhost:4000`
2. LiteLLM receives request, extracts model name
3. LiteLLM consults routing configuration
4. Request routed to appropriate provider (Ollama/llama.cpp/vLLM)
5. Provider processes request, returns response
6. LiteLLM forwards response to client

### Routing Decision Logic

Priority order:
1. **Exact model name match** (e.g., "llama3.1:8b" → Ollama)
2. **Capability-based routing** (e.g., code_generation → qwen2.5-coder)
3. **Pattern matching** (e.g., "meta-llama/*" → vLLM)
4. **Default provider** (Ollama)

With automatic fallback chains for fault tolerance.

See [docs/architecture.md](docs/architecture.md) for complete architecture documentation.

---

## Configuration

### Configuration Files

| File | Type | Purpose |
|------|------|---------|
| `config/providers.yaml` | **SOURCE** | Provider registry (models, URLs, status) |
| `config/model-mappings.yaml` | **SOURCE** | Routing rules and fallback chains |
| `config/litellm-unified.yaml` | **GENERATED** | LiteLLM configuration (DO NOT EDIT) |

### Provider Registry Structure

```yaml
# config/providers.yaml
providers:
  ollama:
    type: ollama
    base_url: http://127.0.0.1:11434
    status: active  # active | inactive | deprecated
    models:
      - name: llama3.1:8b
        size: "8B"
        quantization: Q4_K_M
    health_endpoint: /api/tags
```

### Model Routing Structure

```yaml
# config/model-mappings.yaml
routing:
  exact_matches:
    "llama3.1:8b":
      provider: ollama
      fallback_chain: ["llama_cpp_python"]

  capability_routing:
    code_generation:
      - model: qwen2.5-coder:7b
        provider: ollama
```

### Configuration Workflow

```bash
# 1. Edit source files
vim config/providers.yaml
vim config/model-mappings.yaml

# 2. Generate LiteLLM config
python3 scripts/generate-litellm-config.py

# 3. Validate schemas
python3 scripts/validate-config-schema.py

# 4. Test changes
pytest -m unit

# 5. Deploy (if ready)
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

See [docs/adding-providers.md](docs/adding-providers.md) for provider integration guide.

---

## Testing

### Test Pyramid

```
     /\           E2E Tests (Future)
    /  \
   /----\         Integration (25+ tests, requires providers)
  /------\
 /--------\       Contract (API compliance)
/----------\
/------------\    Unit (30+ tests, >90% coverage)
```

### Running Tests

```bash
# Run all tests
pytest

# Run by category
pytest -m unit              # Fast, no dependencies
pytest -m integration       # Requires active providers
pytest -m contract          # Provider API compliance

# Run with coverage
pytest --cov=scripts --cov-report=html

# Rollback testing
./scripts/test-rollback.sh
```

### Test Markers

- `unit` - Unit tests (no external dependencies)
- `integration` - Integration tests (requires providers)
- `contract` - Contract tests (API compliance)
- `slow` - Slow-running tests (>5 seconds)
- `requires_ollama` - Requires Ollama provider
- `requires_vllm` - Requires vLLM provider
- `requires_redis` - Requires Redis cache
- `monitoring` - Monitoring stack validation

See [tests/README.md](tests/README.md) for complete testing documentation.

---

## Monitoring

### Stack Components

| Component | Port | Purpose |
|-----------|------|---------|
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Visualization dashboards |
| **Loki** | 3100 | Log aggregation |
| **Promtail** | 9080 | Log shipping |

### Quick Setup

```bash
# Install monitoring stack
./scripts/setup-monitoring.sh --install-binaries

# Start services
systemctl --user enable prometheus grafana loki promtail
systemctl --user start prometheus grafana loki promtail

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### What's Monitored

**Metrics** (Prometheus):
- LiteLLM: Request rate, latency (P50/P95), error rate
- Providers: Availability, error rates, response times
- Cache: Hit rate, memory usage
- System: CPU, memory, disk

**Logs** (Loki):
- LiteLLM gateway logs with JSON parsing
- Provider service logs
- Critical system events
- Redis logs

**Alerts** (Prometheus):
- 8 alert groups (Gateway, Providers, Cache, etc.)
- 3 severity levels (Critical, Warning, Info)

**Dashboard** (Grafana):
- 11 panels covering all critical metrics
- Real-time request distribution
- Provider health status
- Active alerts table

See [monitoring/README.md](monitoring/README.md) for complete monitoring documentation.

---

## Development Workflow

### Before Starting Work

```bash
# 1. Activate Serena project (for context)
serena activate ai-backend-unified

# 2. Check current status
./scripts/validate-unified-backend.sh

# 3. Review Serena memories (if needed)
# Architecture, provider registry, routing config, etc.
```

### Making Changes

#### Adding a Provider

```bash
# 1. Update provider registry
vim config/providers.yaml
# Add: type, base_url, status, models, health_endpoint

# 2. Update routing rules
vim config/model-mappings.yaml
# Add: exact matches, fallback chains, capabilities

# 3. Generate LiteLLM config
python3 scripts/generate-litellm-config.py

# 4. Update Serena memory
vim .serena/memories/02-provider-registry.md

# 5. Validate & test
python3 scripts/validate-config-schema.py
pytest -m unit
tests/contract/test_provider_contracts.sh --provider new_provider

# 6. Comprehensive validation
./scripts/validate-unified-backend.sh
```

#### Adding a Model

```bash
# 1. Pull/deploy model on provider
ollama pull llama3.2:3b  # For Ollama

# 2. Update provider registry
vim config/providers.yaml
# Add model to provider's models list

# 3. Update routing
vim config/model-mappings.yaml
# Add exact match entry

# 4. Regenerate & validate
python3 scripts/generate-litellm-config.py
python3 scripts/validate-config-schema.py

# 5. Test availability
curl http://localhost:4000/v1/models | jq
```

### Before Committing

```bash
# 1. Run pre-commit hooks
pre-commit run --all-files

# 2. Run tests
pytest -m unit --cov=scripts

# 3. Validate everything
python3 scripts/validate-config-schema.py
./scripts/validate-unified-backend.sh

# 4. Update documentation (if needed)
# - Update docs/ if architecture changed
# - Update .serena/memories/ if patterns changed
```

### Deployment Process

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete production deployment checklist.

Quick summary:
1. Backup current configuration
2. Generate and copy new configuration
3. Restart LiteLLM service
4. Run smoke tests
5. Monitor for 24-48 hours

---

## Documentation Map

### User Guides
- [README.md](README.md) - Project overview and quick start
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [COMMAND-REFERENCE.md](COMMAND-REFERENCE.md) - Command reference
- [docs/consuming-api.md](docs/consuming-api.md) - API usage examples
- [docs/troubleshooting.md](docs/troubleshooting.md) - Common issues

### Developer Guides
- [CLAUDE.md](../CLAUDE.md) - Claude Code integration guide
- [docs/architecture.md](docs/architecture.md) - Complete system design
- [docs/adding-providers.md](docs/adding-providers.md) - Provider integration
- [docs/security-setup.md](docs/security-setup.md) - Security configuration
- [scripts/README.md](scripts/README.md) - Scripts documentation
- [tests/README.md](tests/README.md) - Testing documentation
- [monitoring/README.md](monitoring/README.md) - Monitoring documentation

### Operations Guides
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment checklist
- [.serena/memories/06-troubleshooting-patterns.md](.serena/memories/06-troubleshooting-patterns.md) - Troubleshooting patterns
- [.serena/memories/07-operational-runbooks.md](.serena/memories/07-operational-runbooks.md) - Operational runbooks

### Knowledge Base (Serena Memories)
- `.serena/memories/01-architecture.md` - System architecture
- `.serena/memories/02-provider-registry.md` - Provider configurations
- `.serena/memories/03-routing-config.md` - Routing strategies
- `.serena/memories/04-model-mappings.md` - Model mappings
- `.serena/memories/05-integration-guide.md` - LAB integration examples
- `.serena/memories/06-troubleshooting-patterns.md` - Common issues
- `.serena/memories/07-operational-runbooks.md` - Operations procedures
- `.serena/memories/08-testing-patterns.md` - Testing strategies

---

## Key Ports Reference

| Service | Port | Purpose |
|---------|------|---------|
| **LiteLLM** | **4000** | **Unified gateway (main entry point)** |
| Ollama | 11434 | Local model server |
| llama.cpp (Python) | 8000 | Python bindings server |
| llama.cpp (Native) | 8080 | C++ native server |
| vLLM | 8001 | High-performance inference |
| OpenWebUI | 5000 | Web interface |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Visualization |
| Loki | 3100 | Log aggregation |
| Promtail | 9080 | Log shipping |

---

## Current Status

### Active Providers
- ✅ Ollama (11434) - llama3.1:8b, qwen2.5-coder:7b
- ✅ llama.cpp Python (8000) - GGUF models
- ✅ llama.cpp Native (8080) - GGUF models
- 🔄 vLLM (8001) - Integration in progress

### Implementation Status

**Completed** ✅
- Phase 0: Foundation (pre-commit hooks, Pydantic validation)
- Phase 1: Configuration & Security (8 Serena memories, security hardening)
- Phase 2: CI/CD & Automation (GitHub Actions, config generation, rollback)
- Phase 3: Testing Infrastructure (75+ tests, >90% coverage)
- Phase 4: Monitoring & Observability (Prometheus, Grafana, Loki, alerts)

**In Progress** 🔄
- vLLM provider integration and testing
- Production deployment to LAB infrastructure

**Future Enhancements** ⏳
- OpenAI/Anthropic provider integration
- Enhanced caching strategies
- Request queuing and prioritization
- Multi-region provider support

---

## Tech Stack

**Languages**: Python 3, Bash, YAML
**Frameworks**: LiteLLM, Pydantic, Pytest
**Tools**: Pre-commit, Serena, Prometheus, Grafana, Loki
**CI/CD**: GitHub Actions

**Dependencies**:
- pydantic>=2.0.0 (schema validation)
- pyyaml>=6.0 (YAML parsing)
- pytest>=7.4.0 (testing framework)
- requests>=2.31.0 (HTTP client)

---

## Support

### Common Commands

```bash
# Check system health
./scripts/validate-unified-backend.sh

# Run tests
pytest -m unit

# Validate configuration
python3 scripts/validate-config-schema.py

# View logs
journalctl --user -u litellm.service -f

# Restart service
systemctl --user restart litellm.service
```

### Getting Help

1. **Troubleshooting**: [docs/troubleshooting.md](docs/troubleshooting.md)
2. **Serena Memories**: `.serena/memories/` for accumulated knowledge
3. **Documentation**: [docs/](docs/) for guides and examples
4. **Tests**: [tests/README.md](tests/README.md) for test examples

---

## Contributing

### Quality Standards
- ✅ All configuration changes must pass Pydantic validation
- ✅ Unit test coverage must remain >90%
- ✅ Provider contracts must comply with OpenAI API format
- ✅ Integration tests must pass for all active providers
- ✅ Rollback procedures must be tested before production

### Development Workflow
1. Update configuration (source files)
2. Generate LiteLLM config
3. Validate schemas
4. Run tests
5. Update documentation and memories
6. Commit and push (pre-commit hooks validate)

See [CLAUDE.md](../CLAUDE.md) for detailed development workflow.

---

**Last Updated**: 2025-10-21
**Maintained By**: LAB AI Infrastructure Team
**License**: Part of LAB ecosystem
