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
    api_key="not-needed"  # pragma: allowlist secret
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
│   ├── litellm-unified.yaml    # Extended LiteLLM config with observability
│   └── schemas/                # Pydantic validation schemas
├── docs/                       # Documentation
│   ├── architecture.md
│   ├── adding-providers.md
│   ├── consuming-api.md
│   ├── troubleshooting.md
│   └── observability.md        # Phase 2: Observability guide
├── monitoring/                 # Monitoring stack (Phase 2)
│   ├── docker-compose.yml      # Prometheus + Grafana stack
│   ├── prometheus/
│   │   └── prometheus.yml      # Metrics scraping config
│   └── grafana/
│       ├── datasources/        # Auto-provisioned datasources
│       └── dashboards/         # 5 pre-built dashboards (JSON)
├── scripts/                    # Utilities and automation
│   ├── debugging/              # Phase 2: Request tracing
│   │   ├── analyze-logs.py
│   │   ├── tail-requests.py
│   │   ├── test-request.py
│   │   └── README.md
│   ├── profiling/              # Phase 2: Performance analysis
│   │   ├── profile-latency.py
│   │   ├── profile-throughput.py
│   │   ├── compare-providers.py
│   │   └── README.md
│   ├── loadtesting/            # Phase 2: Capacity planning
│   │   ├── locust/
│   │   │   └── litellm_locustfile.py
│   │   ├── k6/
│   │   │   ├── litellm-load-test.js
│   │   │   └── smoke-test.js
│   │   └── README.md
│   ├── validate-unified-backend.sh
│   ├── validate-observability.sh  # Phase 2 validation
│   ├── generate-litellm-config.py
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

**Phase 2: Developer Tools & Observability** - Complete observability stack for production monitoring, debugging, performance profiling, and load testing.

### Stack Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  OBSERVABILITY ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│  1. MONITORING (Real-time Metrics)                             │
│     • Prometheus + Grafana                                      │
│     • 5 pre-built dashboards                                    │
│     • 30-day metric retention                                   │
│                                                                  │
│  2. DEBUGGING (Request Tracing)                                │
│     • JSON structured logging                                   │
│     • Request ID tracing                                        │
│     • 3 analysis utilities                                      │
│                                                                  │
│  3. PROFILING (Performance Analysis)                            │
│     • Latency profiling (TTFB breakdown)                        │
│     • Throughput testing                                        │
│     • Provider comparison                                       │
│                                                                  │
│  4. LOAD TESTING (Capacity Planning)                            │
│     • Locust (Python, Web UI)                                   │
│     • k6 (JavaScript, CLI)                                      │
│     • Multiple test scenarios                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Quick Start

**1. Start Monitoring Stack**
```bash
cd monitoring
docker compose up -d

# Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

**2. Monitor Requests Live**
```bash
./scripts/debugging/tail-requests.py

# Filter by model
./scripts/debugging/tail-requests.py --model llama3.1:8b

# Show only errors
./scripts/debugging/tail-requests.py --level ERROR
```

**3. Profile Performance**
```bash
# Latency analysis
./scripts/profiling/profile-latency.py

# Find optimal concurrency
./scripts/profiling/profile-throughput.py --sweep

# Compare providers
./scripts/profiling/compare-providers.py
```

**4. Run Load Tests**
```bash
# Quick smoke test
k6 run scripts/loadtesting/k6/smoke-test.js

# Full load test
k6 run scripts/loadtesting/k6/litellm-load-test.js

# Interactive Locust testing
cd scripts/loadtesting/locust
locust -f litellm_locustfile.py --host http://localhost:4000
# Open http://localhost:8089
```

### Monitoring Stack

**Grafana Dashboards (5 total)**:
- **Overview**: Request rate, error rate, latency (P50/P95/P99), Redis health
- **Token Usage**: Cost tracking, consumption by model/provider
- **Performance**: Latency comparison, heatmaps, P95 trends
- **Provider Health**: Success rates, failure analysis, traffic distribution
- **System Health**: Redis metrics, cache hit rate, infrastructure status

**Prometheus Metrics**:
- Token consumption (input, output, total)
- Request tracking (success, failure, rate)
- Latency (total, TTFB, API call time)
- Deployment health (per-provider success/failure)
- System health (Redis latency, self-latency)

**Configuration**: `config/litellm-unified.yaml` (litellm_settings section)

### Debugging Tools

**Scripts** (`scripts/debugging/`):
- `analyze-logs.py` - Offline analysis (errors, performance, usage patterns)
- `tail-requests.py` - Real-time monitoring with filtering
- `test-request.py` - Make test requests with detailed debugging

**Logging Features**:
- JSON-formatted structured logs
- Request ID generation for distributed tracing
- Slow request detection (>5s threshold)
- Metadata preservation across request lifecycle

**Log Location**: `/var/log/litellm/requests.log` (configurable)

### Performance Profiling

**Scripts** (`scripts/profiling/`):
- `profile-latency.py` - TTFB, network time, token generation speed
- `profile-throughput.py` - Concurrency sweep, RPS measurement
- `compare-providers.py` - Side-by-side provider benchmarking

**Capabilities**:
- Latency statistics (mean, median, P50, P95, P99)
- Optimal concurrency recommendations
- JSON export for regression tracking
- Provider performance comparison

### Load Testing Suite

**Locust** (Python, Interactive):
- Realistic user traffic patterns (60/25/15 model distribution)
- Web UI for interactive testing
- Stress testing modes
- HTML report generation

**k6** (JavaScript, CI/CD):
- 3 scenarios: gradual ramp-up, spike test, constant load
- Built-in performance thresholds
- JSON export for automation
- CI/CD pipeline integration

**Test Scenarios**:
- Smoke test (5 users, 30s) - Quick validation
- Load test (10-50 users, 5-10m) - Normal operation
- Stress test (100-500 users, 10-30m) - Find limits
- Spike test (sudden 10x) - Resilience testing

### Validation

```bash
# Validate entire observability stack
./scripts/validate-observability.sh
```

**Checks**:
- ✅ Configuration files (YAML syntax, settings)
- ✅ Monitoring stack (Prometheus, Grafana, dashboards)
- ✅ Debugging tools (syntax, executability)
- ✅ Profiling utilities (syntax, executability)
- ✅ Load testing files (Locust, k6)
- ✅ Documentation completeness

For complete observability documentation, see [`docs/observability.md`](docs/observability.md).

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
   - Configuration hot-reload script with automatic backup/rollback
   - Configuration consistency validator (model name validation)
   - Pre-commit git hook for automatic validation
   - Redis cache namespacing with monitoring tools
   - Port conflict detection and management system

3. **Phase 2: CI/CD & Automation**
   - GitHub Actions CI/CD pipeline (6-stage validation)
   - Configuration generation script with versioning and rollback support
   - Automated backup procedures

4. **Phase 3: Testing Infrastructure**
   - 75+ automated tests (unit, integration, contract)
   - Test pyramid with comprehensive coverage (>90% unit tests)
   - Rollback testing automation (8-step validation)
   - pytest configuration with parallel execution support

5. **Phase 2: Developer Tools & Observability** (2025-10-21)
   - **Monitoring Stack**: Prometheus + Grafana with 5 pre-built dashboards
   - **Debugging Tools**: 3 request tracing utilities (analyze, tail, test)
   - **Performance Profiling**: 3 profiling scripts (latency, throughput, comparison)
   - **Load Testing Suite**: Locust + k6 with multiple test scenarios
   - **Configuration**: Extended litellm-unified.yaml with observability settings
   - **Documentation**: Comprehensive observability guide (docs/observability.md)
   - **Validation**: Complete observability stack validation script

### Recently Completed ✅

- **vLLM Provider Integration** (2025-10-21)
  - AWQ-quantized Qwen2.5-Coder-7B model deployed
  - Production integration via LiteLLM gateway
  - Comprehensive testing and validation complete

- **Phase 2: Developer Tools & Observability** (2025-10-21)
  - Production-grade monitoring with Prometheus + Grafana
  - Request tracing with JSON logging and request IDs
  - Performance profiling with latency/throughput analysis
  - Load testing with Locust and k6
  - Complete observability documentation and validation

### In Progress 🔄

- Performance monitoring and optimization based on observability data
- Advanced Grafana dashboard customization

### Future Enhancements ⏳

- OpenAI/Anthropic provider integration
- Enhanced caching strategies (semantic caching)
- Request queuing and prioritization
- Multi-region provider support
- Advanced load balancing algorithms
- Automated performance regression detection in CI/CD
- Alert integration (PagerDuty, Slack)

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
