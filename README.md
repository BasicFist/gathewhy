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

- **Quick Start**: `docs/quick-start.md` - Get started in under 5 minutes
- **Model Selection**: `docs/model-selection-guide.md` - Choose the right model for your use case
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

## Configuration Hot-Reload

Safe configuration updates without service downtime:

```bash
# Validate configuration before deploying
./scripts/reload-litellm-config.sh --validate-only

# Deploy with confirmation
./scripts/reload-litellm-config.sh

# Force reload without confirmation
./scripts/reload-litellm-config.sh --force
```

**Features**:
- ✅ Automatic configuration validation (YAML syntax, required fields)
- ✅ Automatic backup before reload (timestamped in `backups/`)
- ✅ Service health verification after reload
- ✅ Automatic rollback on failure
- ✅ Configuration diff display before reload

**Workflow**:
1. Update `config/litellm-unified.yaml`
2. Run validation: `./scripts/reload-litellm-config.sh --validate-only`
3. Review changes and reload: `./scripts/reload-litellm-config.sh`
4. Service automatically validates and rolls back if issues detected

## Configuration Consistency Validation

Automatic validation of model name consistency across all configuration files:

```bash
# Manual validation
python3 scripts/validate-config-consistency.py

# Automatic validation on git commit (pre-commit hook installed)
git add config/
git commit -m "Update model configuration"  # Validation runs automatically
```

**Validation Checks**:
- ✅ Model names in `providers.yaml` match `model-mappings.yaml`
- ✅ Routing targets reference existing active providers
- ✅ Backend model references are valid
- ✅ LiteLLM model definitions align with provider models
- ✅ Naming convention consistency (detect typos)

**Pre-Commit Hook**:
- Automatically validates configuration before commits
- Blocks commits with validation errors
- Prevents deployment of inconsistent configurations
- Addresses Codex-identified risk: "Model name consistency across configs"

**Bypass (not recommended)**:
```bash
git commit --no-verify  # Skip validation hook
```

## Redis Cache Management

Provider-isolated caching with monitoring and management tools:

```bash
# View cache statistics
./scripts/monitor-redis-cache.sh

# List all cache keys
./scripts/monitor-redis-cache.sh --keys

# Continuous monitoring (updates every 5s)
./scripts/monitor-redis-cache.sh --watch

# Flush cache (requires confirmation)
./scripts/monitor-redis-cache.sh --flush
```

**Cache Strategy**:
- ✅ Global namespace prefix (`litellm:`) prevents conflicts
- ✅ Model name automatically included in cache keys
- ✅ Per-provider cache isolation via model naming
- ✅ Configurable TTL (default: 1 hour)
- ✅ Addresses Codex-identified risk: "Redis cache implications"

**Monitoring**:
- Cache hit rate tracking
- Provider-specific key counts
- Memory usage statistics
- TTL management

## Port Conflict Management

Explicit port registry and automated conflict detection:

```bash
# Check all registered ports
./scripts/check-port-conflicts.sh

# Check only required ports (litellm_gateway, ollama, redis)
./scripts/check-port-conflicts.sh --required

# Check specific port
./scripts/check-port-conflicts.sh --port 8001

# Attempt to free conflicting ports (kills processes with confirmation)
./scripts/check-port-conflicts.sh --fix
```

**Port Registry** (`config/ports.yaml`):
- ✅ 13 service ports documented (LiteLLM, Ollama, vLLM, llama.cpp, OpenWebUI, monitoring)
- ✅ 3 reserved ports for future expansion
- ✅ Port ranges defined by service category
- ✅ Health check commands for each service
- ✅ Addresses Codex-identified risk: "Port conflicts"

**Conflict Detection**:
- Multi-method port checking (netstat, ss, lsof)
- Process identification for occupied ports
- Optional automated conflict resolution
- Supports multiple check modes (all, required, specific)

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

GitHub Actions pipeline (`.github/workflows/validate-config.yml`) runs on every push and PR:

**Pipeline Stages** (~3-5 minutes total):

1. **YAML Syntax Validation** (<30s)
   - yamllint with custom rules
   - Python YAML parsing verification
   - All config/*.yaml files

2. **Schema Validation** (<30s)
   - Pydantic model validation
   - Cross-configuration consistency
   - Model name typo detection

3. **Secret Scanning** (<30s)
   - detect-secrets baseline check
   - Prevents credential leaks
   - Auto-fails on new secrets

4. **Documentation Sync** (<30s)
   - Provider config ↔ architecture.md
   - Serena memory completeness (8 required files)
   - Auto-generated marker verification

5. **Generated Config Check** (<30s)
   - AUTO-GENERATED marker presence
   - Prevents manual edits to generated files

6. **Comprehensive System Validation** (~1-2min)
   - Runs `scripts/validate-all-configs.sh --json`
   - 11 system-wide checks (YAML, models, ports, providers, Redis, schema, backups)
   - JSON output uploaded as artifact (30-day retention)
   - **Local equivalent**: `./scripts/validate-all-configs.sh`

7. **Integration Tests** (optional, manual dispatch)
   - Provider health checks
   - Requires active provider services

**Artifacts**:
- `validation-results` - JSON summary of all checks (30 days)
- `test-coverage` - HTML coverage reports (if tests run)

**Running Locally**:
```bash
# Quick validation (same as CI stage 6)
./scripts/validate-all-configs.sh

# With JSON output (CI format)
./scripts/validate-all-configs.sh --json | jq .

# Critical checks only
./scripts/validate-all-configs.sh --critical
```

**Expected Runtime**:
- Full pipeline: **3-5 minutes**
- Comprehensive validation alone: **1-2 minutes**
- Local validation: **~10 seconds** (depends on provider reachability)

**Failure Handling**:
- Pipeline fails on: YAML errors, schema violations, new secrets, failed validations
- Warnings allowed: Provider offline (vLLM), backup warnings
- Auto-rollback: Not triggered by CI (pre-commit hook prevents bad commits)

For complete testing documentation, see [`tests/README.md`](tests/README.md).

## Current Providers

| Provider | Port | Status | Models |
|----------|------|--------|--------|
| Ollama | 11434 | ✅ Active | llama3.1:8b, qwen2.5-coder:7b |
| llama.cpp (Python) | 8000 | ✅ Active | GGUF models |
| llama.cpp (Native) | 8080 | ✅ Active | GGUF models |
| vLLM | 8001 | ✅ Active | Qwen2.5-Coder-7B-Instruct-AWQ |

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

### Recently Completed ✅

- **vLLM Provider Integration** (2025-10-21)
  - AWQ-quantized Qwen2.5-Coder-7B model deployed
  - Production integration via LiteLLM gateway
  - Comprehensive testing and validation complete

- **Phase 1: Foundation & Risk Mitigation** (2025-10-21)
  - Configuration hot-reload script with automatic backup/rollback
  - Configuration consistency validator (model name validation)
  - Pre-commit git hook for automatic validation
  - Redis cache namespacing with monitoring tools
  - Port conflict detection and management system
  - Addresses Codex-identified deployment risks (4/6 features complete)

### In Progress 🔄

- Documentation refinement based on usage feedback
- Performance monitoring and optimization

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
