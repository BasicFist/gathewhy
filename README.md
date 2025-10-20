# AI Unified Backend Infrastructure

**Single entry point for all LLM providers in LAB ecosystem**

## Overview

The AI Unified Backend provides a single, consistent API endpoint that routes to multiple LLM inference providers:
- **Ollama** (local models, general-purpose)
- **llama.cpp** (CUDA-optimized, native performance)
- **vLLM** (high-throughput, production-grade)
- **Future providers** (OpenAI, Anthropic, custom servers)

## Architecture

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

## Quick Start

### For Consumers (LAB Projects)

```python
# Use unified endpoint instead of individual providers
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000",  # LiteLLM unified gateway
    api_key="not-needed"
)

# Route to any provider transparently
response = client.chat.completions.create(
    model="llama3.1:8b",  # Routes to Ollama
    # model="llama2-13b-vllm",  # Routes to vLLM
    messages=[{"role": "user", "content": "Hello"}]
)
```

### For Developers

```bash
# Check all providers status
./scripts/validate-unified-backend.sh

# Add new provider
# 1. Edit config/providers.yaml
# 2. Update config/litellm-unified.yaml
# 3. Test with validation script

# View configuration
cat config/providers.yaml
cat config/model-mappings.yaml
```

## Project Structure

```
ai-backend-unified/
├── .github/                    # CI/CD workflows
│   └── workflows/
│       └── validate.yml        # Automated validation pipeline
├── .serena/                    # Serena project configuration
│   ├── project.yml             # Project settings
│   └── memories/               # Knowledge base (8 files)
├── config/                     # Configuration files
│   ├── providers.yaml          # Provider registry (source of truth)
│   ├── model-mappings.yaml     # Model routing rules
│   ├── litellm-unified.yaml    # Extended LiteLLM config (generated)
│   └── schemas/                # Pydantic validation schemas
├── docs/                       # Documentation
│   ├── architecture.md
│   ├── adding-providers.md
│   ├── consuming-api.md
│   └── troubleshooting.md
├── monitoring/                 # Observability stack
│   ├── prometheus/             # Metrics collection
│   ├── grafana/                # Dashboards and visualization
│   ├── loki/                   # Log aggregation
│   ├── systemd/                # Service definitions
│   └── README.md               # Monitoring documentation
├── scripts/                    # Utilities and automation
│   ├── validate-unified-backend.sh
│   ├── generate-litellm-config.py
│   ├── setup-monitoring.sh
│   └── test-rollback.sh
├── tests/                      # Automated test suite
│   ├── unit/                   # Unit tests (30+ tests)
│   ├── integration/            # Integration tests (25+ tests)
│   ├── contract/               # Provider contract tests
│   └── README.md               # Testing documentation
└── README.md                   # This file
```

## Component Projects

This coordination project references:
- **OpenWebUI**: `/home/miko/LAB/dev/openwebui/` - Gateway + Ollama + llama.cpp
- **CrushVLLM**: `/home/miko/LAB/dev/CRUSHVLLM/` - vLLM inference engine

## Key Concepts

### Single Entry Point
All LAB projects consume AI services via **one endpoint**: `http://localhost:4000`

### Provider Abstraction
Users request models by name, LiteLLM routes to appropriate provider automatically.

### Extensibility
Add new providers by updating configuration files, no code changes required.

### OpenAI Compatibility
Standard OpenAI API format works across all providers.

## Documentation

- **Architecture**: `docs/architecture.md` - Complete system design
- **Adding Providers**: `docs/adding-providers.md` - Integration guide
- **API Usage**: `docs/consuming-api.md` - How to use from LAB projects
- **Troubleshooting**: `docs/troubleshooting.md` - Common issues

## Serena Integration

This project is configured as a Serena project with comprehensive memories:

```bash
# Activate project
serena activate ai-backend-unified

# Access memories for architecture knowledge
# Serena will have complete context about all providers and routing
```

## Health Monitoring

```bash
# Check all providers
curl http://localhost:4000/health

# Check specific provider
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/v1/models  # llama.cpp
curl http://localhost:8001/v1/models  # vLLM

# Run comprehensive validation
./scripts/validate-unified-backend.sh
```

## Monitoring & Observability

Comprehensive monitoring stack for metrics, logs, and alerts:

### Stack Components

| Component | Purpose | Port | Documentation |
|-----------|---------|------|---------------|
| **Prometheus** | Metrics collection | 9090 | [prometheus.io](https://prometheus.io) |
| **Grafana** | Visualization | 3000 | [grafana.com](https://grafana.com) |
| **Loki** | Log aggregation | 3100 | [grafana.com/loki](https://grafana.com/loki) |
| **Promtail** | Log shipping | 9080 | [grafana.com/promtail](https://grafana.com/promtail) |

### Quick Setup

```bash
# Automated installation
./scripts/setup-monitoring.sh --install-binaries

# Start monitoring services
systemctl --user enable prometheus grafana loki promtail
systemctl --user start prometheus grafana loki promtail

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### What's Monitored

**Metrics** (Prometheus):
- LiteLLM gateway: Request rate, latency (P50/P95), error rate, fallback triggers
- Provider health: Availability, error rates, response times
- Cache performance: Hit rate, memory usage (Redis)
- System resources: CPU, memory, disk utilization
- Rate limiting: RPM usage, violations

**Logs** (Loki via Promtail):
- LiteLLM gateway logs with JSON parsing
- Provider service logs (Ollama, llama.cpp, vLLM)
- System logs (critical events only)
- Redis logs

**Alerts** (Prometheus):
- 8 alert groups: Gateway, Providers, Cache, Rate Limits, System, Fallbacks, Configuration
- 3 severity levels: Critical (page), Warning (investigate), Info (review)

### Dashboard

Pre-configured Grafana dashboard (`monitoring/grafana/litellm-dashboard.json`):
- 11 panels covering all critical metrics
- Real-time request distribution by model
- Provider health status
- Active alerts table

**Import**: Grafana → Dashboards → Import → Upload dashboard JSON

For complete monitoring documentation, see [`monitoring/README.md`](monitoring/README.md).

## Testing & Quality

Comprehensive automated test suite:

### Test Pyramid

```
     /\
    /E2E\         scripts/test-rollback.sh (8-step rollback validation)
   /------\
  /Integr-\       tests/integration/ (25+ tests, real providers)
 /----------\
/--Contract--\    tests/contract/ (provider API compliance)
/--------------\
/---- Unit ----\  tests/unit/ (30+ tests, routing logic)
```

### Running Tests

```bash
# Run all tests
pytest

# Run by category
pytest -m unit              # Fast unit tests
pytest -m integration       # Integration tests (requires providers)
pytest -m contract          # Provider contract tests

# Run with coverage
pytest --cov=config --cov-report=html

# Rollback testing
./scripts/test-rollback.sh
```

### Test Coverage

- **Unit Tests**: Configuration validation, routing logic, fallback chains (>90% coverage)
- **Contract Tests**: Provider API compliance (OpenAI format, health endpoints)
- **Integration Tests**: End-to-end routing, caching, streaming, error handling
- **Rollback Tests**: Configuration rollback procedures (8-step validation)

### CI/CD Integration

GitHub Actions pipeline (`.github/workflows/validate.yml`):
1. **Validate**: YAML syntax, Pydantic schemas
2. **Unit Tests**: Fast tests without dependencies
3. **Integration**: Tests with Ollama (if available)
4. **Contract**: Provider API compliance
5. **Rollback**: Rollback procedure validation
6. **Report**: Test results and coverage

For complete testing documentation, see [`tests/README.md`](tests/README.md).

## Current Providers

| Provider | Port | Status | Models |
|----------|------|--------|--------|
| Ollama | 11434 | ✅ Active | llama3.1:8b, qwen2.5-coder:7b |
| llama.cpp (Python) | 8000 | ✅ Active | GGUF models |
| llama.cpp (Native) | 8080 | ✅ Active | GGUF models |
| vLLM | 8001 | 🔄 Integrating | Llama-2-13b-chat-hf |

## Implementation Status

### Completed ✅

1. **Phase 0: Foundation**
   - Pre-commit hooks framework for local validation
   - Pydantic validation environment for type-safe configuration

2. **Phase 1: Configuration & Security**
   - 8 Serena memory files with operational knowledge
   - Pydantic-based configuration validation (schemas + validation script)
   - Security hardening (CORS, rate limits, master key authentication)

3. **Phase 2: CI/CD & Automation**
   - GitHub Actions CI/CD pipeline (6-stage validation)
   - Configuration generation script with versioning and rollback support
   - Automated backup procedures

4. **Phase 3: Testing Infrastructure**
   - 75+ automated tests (unit, integration, contract)
   - Test pyramid with comprehensive coverage (>90% unit tests)
   - Rollback testing automation (8-step validation)
   - pytest configuration with parallel execution support

5. **Phase 4: Monitoring & Observability**
   - Prometheus metrics collection (LiteLLM, providers, system)
   - Grafana dashboards (11 panels, pre-configured)
   - Loki log aggregation (15-day retention)
   - Promtail log shipping from journald
   - 8 alert groups with 3 severity levels
   - Setup automation script

### In Progress 🔄

- vLLM provider integration and testing
- Production deployment to LAB infrastructure
- Documentation refinement based on usage feedback

### Future Enhancements ⏳

- OpenAI/Anthropic provider integration
- Enhanced caching strategies (semantic caching)
- Request queuing and prioritization
- Multi-region provider support
- Advanced load balancing algorithms

## Contributing

### Development Workflow

When adding new providers or models:

1. **Update Configuration** (Source of Truth):
   ```bash
   # Edit provider registry
   vim config/providers.yaml

   # Add routing rules
   vim config/model-mappings.yaml
   ```

2. **Generate & Validate**:
   ```bash
   # Generate litellm-unified.yaml from sources
   python3 scripts/generate-litellm-config.py

   # Validate schemas
   python3 scripts/validate-config-schema.py
   ```

3. **Test Changes**:
   ```bash
   # Run unit tests
   pytest -m unit

   # Run contract tests for new provider
   tests/contract/test_provider_contracts.sh

   # Run integration tests
   pytest -m integration
   ```

4. **Update Documentation**:
   - Add provider to relevant Serena memories (`.serena/memories/`)
   - Update this README if adding major features
   - Document any new routing patterns

5. **Commit & Push**:
   ```bash
   # Pre-commit hooks will validate automatically
   git add config/ .serena/memories/
   git commit -m "feat: add XYZ provider"
   git push

   # CI/CD pipeline will run full validation
   ```

### Quality Standards

- ✅ All configuration changes must pass Pydantic validation
- ✅ Unit test coverage must remain >90%
- ✅ Provider contracts must comply with OpenAI API format
- ✅ Integration tests must pass for all active providers
- ✅ Rollback procedures must be tested before production deployment

## License

Part of the LAB ecosystem.
