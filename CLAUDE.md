# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Unified Backend Infrastructure** - A configuration-driven LLM gateway coordination project that provides a single entry point (LiteLLM on port 4000) routing requests to multiple LLM inference providers: Ollama, llama.cpp, and vLLM. This is a **configuration and automation project**, not an application codebase. The actual gateway runs in the OpenWebUI project; this project manages configuration, validation, testing, and observability.

**Critical Understanding**: This is a **metaprogramming project** where YAML configurations are the "source code" and Python scripts are the "compiler toolchain". The architecture treats configuration as data that flows through multiple transformation and validation layers before becoming executable LiteLLM configuration.

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

## Core Design Patterns

### 1. Configuration-as-Code Pipeline

The project implements a multi-stage configuration transformation pipeline:

```
providers.yaml + model-mappings.yaml
         ↓
  [YAML Parser]
         ↓
  [Pydantic Schema Validation] (scripts/validate-config-schema.py)
         ↓
  [Cross-Config Consistency Check] (scripts/validate-config-consistency.py)
         ↓
  [Configuration Generator] (scripts/generate-litellm-config.py)
         ↓
  litellm-unified.yaml (AUTO-GENERATED)
         ↓
  [Post-Generation Validation]
         ↓
  [Backup & Versioning]
         ↓
  [LiteLLM Service Reload]
```

**Key Insight**: The generator (`generate-litellm-config.py`) is the compiler. It reads source configurations, validates semantics, generates intermediate representations, and outputs executable configuration with embedded metadata for traceability.

### 2. Provider Abstraction Layer

The system uses a **provider registry pattern** where each provider implements a common interface:

```python
class ProviderConfig(BaseModel):
    type: Literal["ollama", "llama_cpp", "vllm", "openai", "anthropic", ...]
    base_url: str
    status: Literal["active", "disabled", "pending_integration", "template"]
    models: list[ProviderModel | str]
    health_endpoint: str | None
```

**Pattern**: Abstract Factory + Registry. Providers are declaratively registered in `providers.yaml`, and the generator uses type-specific parameter builders (`_build_litellm_params()`) to construct provider-specific configurations.

**Gotcha**: Provider types are **not** runtime-extensible. Adding a new provider type requires updating the Pydantic schema (`Literal` enum) and adding a corresponding case in `_build_litellm_params()`.

### 3. Routing Decision Hierarchy

Model request routing follows a strict precedence hierarchy implemented in `model-mappings.yaml`:

1. **Exact Matches** (highest priority) - `exact_matches` dict
   - Direct model name → provider mapping
   - Example: `"llama3.1:latest"` → `ollama`

2. **Capability-Based Routing** - `capabilities` dict
   - Semantic routing by use case
   - Example: `code_generation` → `["qwen2.5-coder:7b", "qwen-coder-vllm"]`

3. **Pattern Matching** - `patterns` list
   - Regex-based routing rules
   - Example: `"^Qwen/.*"` → `vllm`

4. **Default Fallback** - `routing_rules.default_provider`
   - Last resort when no rules match

**Implementation Note**: LiteLLM's router evaluates these rules at request time. The generator creates the `router_settings` and `fallback_chains` sections that drive this behavior.

### 4. Fault Tolerance Through Fallback Chains

The system implements **circuit breaker + failover chains**:

```yaml
fallback_chains:
  "llama3.1:latest":
    chain:
      - qwen2.5-coder:7b      # Secondary
      - qwen-coder-vllm        # Tertiary
      - dolphin-uncensored-vllm # Last resort
```

**Pattern**: Chain of Responsibility with provider health tracking. LiteLLM maintains provider health state and automatically routes through the chain when failures occur.

**Gotcha**: Circular fallback chains are not detected at configuration time. The generator validates that fallback models exist in `known_models` set but doesn't check for cycles.

### 5. Validation Layers (Defense in Depth)

The project implements **layered validation** inspired by compiler design:

**Layer 1: Lexical Analysis**
- YAML syntax validation (yamllint)
- Python YAML parsing (`yaml.safe_load`)

**Layer 2: Semantic Validation**
- Pydantic schema validation (`validate-config-schema.py`)
- Type checking, enum validation, regex pattern validation

**Layer 3: Consistency Validation**
- Cross-file consistency checks (`validate-config-consistency.py`)
- Model name existence in provider registry
- Fallback chain validity

**Layer 4: Port Conflict Detection**
- Port availability checking (`check-port-conflicts.sh`)
- Service health endpoint validation

**Layer 5: Integration Testing**
- Provider contract tests (`tests/contract/`)
- End-to-end routing tests (`tests/integration/`)

**Pattern**: This is a **validation pipeline** where each layer catches progressively more complex errors. Early layers are fast and catch syntax errors; later layers are expensive and catch semantic/runtime issues.

### 6. Backup and Rollback Strategy

Configuration changes follow a **transactional pattern** with automatic backups:

```
generate-litellm-config.py
    ↓
[Backup existing config with timestamp]
    ↓
[Generate new config]
    ↓
[Validate generated config]
    ↓
[Write to output file] ← Atomic operation
    ↓
[Cleanup old backups (keep last 10)]
```

**Implementation**: The `backup_existing()` method creates timestamped backups in `config/backups/` before any mutation. Rollback is a simple file copy from the backup directory.

**Gotcha**: Backups are file-level only. Rolling back doesn't automatically restart the LiteLLM service or verify service health.

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

## Architectural Deep Dive

### Testing Strategy & Test Categories

The project uses **pytest markers** to organize 75+ tests into distinct categories with different requirements:

```python
# Test pyramid structure
@pytest.mark.unit          # Fast, no external deps (~10s total)
@pytest.mark.integration   # Requires running providers (~5+ min)
@pytest.mark.contract      # Provider API compliance tests
@pytest.mark.monitoring    # Observability stack tests
@pytest.mark.slow          # Tests >5 seconds each

# Provider-specific markers
@pytest.mark.requires_ollama
@pytest.mark.requires_vllm
@pytest.mark.requires_redis
```

**Test Fixtures Architecture** (`tests/conftest.py`):
- **Session-scoped fixtures**: Configuration loaded once per test run
- **Function-scoped fixtures**: Mock providers/mappings for unit tests
- **Shared fixtures**: `providers_config`, `mappings_config`, `litellm_config`, `active_providers`

**Key Insight**: Unit tests use **mock fixtures** with predictable data, while integration tests use **session fixtures** that read actual configuration files. This allows unit tests to run without any external dependencies.

**Test Organization Pattern**:
```
tests/
├── unit/              # Pure logic tests, no I/O
├── integration/       # End-to-end with real providers
├── contract/          # Provider API compliance
├── monitoring/        # Grafana/Prometheus validation
├── fixtures/          # Shared test data
└── conftest.py        # Pytest configuration & fixtures
```

### Observability Architecture

The monitoring stack follows the **Prometheus + Grafana + Loki pattern**:

```
LiteLLM Gateway
    ↓ (metrics)
  :9090 /metrics endpoint
    ↓
Prometheus (scraping)
    ↓
Grafana (visualization)
    ↓
5 Pre-built Dashboards:
  1. Overview (request rates, error rates)
  2. Token Usage (cost tracking)
  3. Performance (latency percentiles)
  4. Health (provider status)
  5. System (resource utilization)
```

**Key Scripts**:
- `scripts/debugging/tail-requests.py` - Real-time request monitoring
- `scripts/debugging/analyze-logs.py` - Historical log analysis
- `scripts/profiling/profile-latency.py` - TTFB (Time To First Byte) analysis
- `scripts/profiling/profile-throughput.py` - Concurrency testing
- `scripts/profiling/compare-providers.py` - Side-by-side provider benchmarking

**Structured Logging Pattern**:
```python
# Loguru-based structured logging with context
logger.info(
    "Configuration generated successfully",
    providers=provider_count,
    exact_matches=exact_matches,
    version=self.version
)
```

**Gotcha**: The monitoring stack runs in Docker Compose (`monitoring/docker-compose.yml`), but LiteLLM service runs as a systemd user service. Port 9090 is used by both Prometheus (for scraping) and LiteLLM's Prometheus exporter.

### Hot-Reload & Zero-Downtime Deployment

The `scripts/reload-litellm-config.sh` script implements **safe hot-reload**:

```bash
# 1. Validate new config
python3 scripts/validate-all-configs.sh --critical

# 2. Backup current config (timestamped)
cp config/litellm-unified.yaml config/backups/litellm-unified.yaml.$(date +%s)

# 3. Apply new config
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml

# 4. Reload service (graceful restart)
systemctl --user reload-or-restart litellm.service

# 5. Health check after reload
curl -s http://localhost:4000/health | jq .

# 6. Automatic rollback on failure
if [ $? -ne 0 ]; then
    cp config/backups/litellm-unified.yaml.* ../openwebui/config/litellm.yaml
    systemctl --user restart litellm.service
fi
```

**Pattern**: This implements **blue-green deployment at the configuration level** with automatic rollback on health check failure.

### Load Testing Infrastructure

The project provides two load testing tools for different use cases:

**1. Locust (Interactive, Real-time Monitoring)**
- Location: `scripts/loadtesting/locust/litellm_locustfile.py`
- Use case: Manual testing, bottleneck identification
- Features: Web UI, real-time charts, distributed load generation

**2. k6 (CI/CD, Automated Regression)**
- Location: `scripts/loadtesting/k6/smoke-test.js`
- Use case: Automated performance regression testing
- Features: Scriptable thresholds, CI/CD integration, custom metrics

**Load Test Scenarios**:
```javascript
// Smoke test: Light load, verify basic functionality
// Load test: Expected production load
// Stress test: Beyond expected load until failure
// Spike test: Sudden traffic surges
// Soak test: Sustained load for extended period
```

### Redis Caching Strategy

LiteLLM uses **Redis for response caching** to reduce provider load:

```yaml
cache_params:
  type: "redis"
  host: "127.0.0.1"
  port: 6379
  ttl: 3600  # 1 hour cache lifetime
```

**Cache Management Script** (`scripts/monitor-redis-cache.sh`):
- View cache statistics (hit rate, key count, memory usage)
- List all cache keys with TTL
- Watch mode for continuous monitoring
- Flush cache with confirmation

**Pattern**: This is a **transparent caching layer**. Applications see reduced latency and costs without code changes.

**Gotcha**: Redis is a hard dependency. If Redis is down, LiteLLM may fail to start or degrade performance (depending on configuration).

### Port Management & Conflict Detection

The `scripts/check-port-conflicts.sh` script implements **preemptive port conflict detection**:

```bash
# Check all registered ports from config/ports.yaml
./scripts/check-port-conflicts.sh

# Check only critical ports (LiteLLM, Ollama, Redis)
./scripts/check-port-conflicts.sh --required

# Attempt to free conflicting ports
./scripts/check-port-conflicts.sh --fix
```

**Pattern**: This is **defensive programming** - detect conflicts before service start rather than debugging failed starts.

### Version Tracking & Git Integration

The generator embeds **version metadata** in generated configs:

```python
def generate_version(self) -> str:
    """Generate version from git commit hash or timestamp"""
    git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
    return f"git-{git_hash}"
```

**Version File** (`config/.litellm-version`):
```yaml
version: "git-a1b2c3d"
timestamp: "2025-10-25T14:30:00"
providers_file: "config/providers.yaml"
mappings_file: "config/model-mappings.yaml"
output_file: "config/litellm-unified.yaml"
```

**Pattern**: This enables **configuration traceability** - every generated config can be traced back to source files and git commit.

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

## Common Mistakes & Gotchas

### Configuration Anti-Patterns

- ❌ **Editing `litellm-unified.yaml` directly** (it's auto-generated, changes will be overwritten)
  - ✅ Always edit `providers.yaml` and `model-mappings.yaml` instead

- ❌ **Adding providers without updating both config files**
  - ✅ Update `providers.yaml` AND `model-mappings.yaml` for routing rules

- ❌ **Committing config changes without running validation**
  - ✅ Always run `./scripts/validate-all-configs.sh` before commit

- ❌ **Assuming vLLM is always running**
  - ✅ Check `systemctl --user status vllm.service` or verify with health endpoint

- ❌ **Not checking fallback chains when a provider is down**
  - ✅ Test routing with `curl http://localhost:4000/v1/models | jq`

- ❌ **Forgetting to restart LiteLLM after config changes**
  - ✅ Use `./scripts/reload-litellm-config.sh` for safe hot-reload

### Non-Obvious Behaviors

**1. Display Name Resolution (`_get_display_name()`)**

The generator has complex logic for choosing the "public" model name:
- Checks `exact_matches` for explicit aliases first
- Searches for `backend_model` matches in mappings
- Special case for llama.cpp providers (e.g., "llama-cpp-python")
- Falls back to provider's original model name

**Gotcha**: If you want to alias a model (e.g., map "qwen-coder" → "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"), you must add it to `exact_matches` in `model-mappings.yaml` with the `backend_model` field set.

**2. Provider-Specific Parameter Building (`_build_litellm_params()`)**

Different providers require different LiteLLM parameters:
- **Ollama**: Prefixes model with `"ollama/"`, passes options in `extra_body`
- **vLLM**: Adds `/v1` to base_url, sets `custom_llm_provider: "openai"`, requires fake API key
- **llama.cpp**: Sets model to `"openai/local-model"` (generic identifier)

**Gotcha**: Adding a new provider type requires updating the `_build_litellm_params()` method with provider-specific logic. There's no plugin architecture for this.

**3. Fallback Chain Validation (`build_router_settings()`)**

The generator validates fallback chains against `known_models` set:
```python
for fallback_model in chain.get("chain", []):
    if fallback_model not in known_models:
        continue  # Silently skips invalid fallback
```

**Gotcha**: Invalid fallback models are **silently skipped**, not reported as errors. This can result in shorter-than-expected fallback chains without any warning.

**4. Rate Limit Defaults (`_get_default_rate_limits()`)**

Models without explicit rate limits get provider-specific defaults:
```python
defaults = {
    "ollama": {"rpm": 100, "tpm": 50000},
    "vllm": {"rpm": 50, "tpm": 100000},
}
```

**Gotcha**: These defaults may not match your actual hardware capabilities. Always test under load and adjust rate limits in `model-mappings.yaml` if needed.

**5. YAML Dumper Indentation (`IndentedDumper`)**

The project uses a custom YAML dumper for yamllint compliance:
```python
class IndentedDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)
```

**Gotcha**: Standard `yaml.dump()` creates yamllint-incompatible YAML. Always use `Dumper=IndentedDumper` when writing YAML files.

**6. Backup Retention Policy (`_cleanup_old_backups()`)**

The generator keeps only the last 10 backups:
```python
backups = sorted(BACKUP_DIR.glob("litellm-unified.yaml.*"), ...)
for old_backup in backups[10:]:
    old_backup.unlink()
```

**Gotcha**: Backups older than the 10 most recent are **automatically deleted**. If you need long-term backup history, copy backups to a separate location.

**7. Validation Module Import Pattern**

The generator validates by **importing and running** the validation script:
```python
validation_module = runpy.run_path("scripts/validate-config-schema.py")
validate_all_configs = validation_module.get("validate_all_configs")
validate_all_configs(...)
```

**Gotcha**: This couples the generator to the validation script's internal API. If you rename `validate_all_configs()` function, the generator will fail silently.

**8. Provider Status Filtering**

Only providers with `status: "active"` are included in generated config:
```python
if provider_config.get("status") != "active":
    continue
```

**Gotcha**: Providers with `status: "disabled"` or `status: "template"` are completely excluded from the generated config, even if they're referenced in fallback chains. This can cause silent fallback chain truncation.

**9. Redis Dependency (Now Optional)**

LiteLLM's cache configuration includes graceful degradation:
```python
"cache_params": {
    "type": "redis",
    "host": "127.0.0.1",
    "port": 6379,
    "ttl": 3600
},
"fallback_to_no_cache_on_redis_error": True  # ✅ Graceful degradation
```

**How it works**: If Redis is unavailable, LiteLLM will log a warning and automatically disable caching instead of failing. To completely disable caching, set `cache: False` in the generated config or edit the generator to change the default.

**10. Model Name Collision Resolution**

If multiple providers have models with the same name, **last one wins**:
```python
for model in provider_config.get("models", []):
    model_entry = {"model_name": model_name, ...}
    model_list.append(model_entry)  # No deduplication
```

**Gotcha**: LiteLLM's router may route to the wrong provider if model names collide. Always use unique display names or explicit aliases in `exact_matches`.

### Development Workflow Best Practices

1. **Always validate before committing**:
   ```bash
   ./scripts/validate-all-configs.sh && git add config/
   ```

2. **Test configuration changes in isolation**:
   ```bash
   python3 scripts/generate-litellm-config.py --validate-only
   ```

3. **Use backups directory for rollback**:
   ```bash
   ls -lt config/backups/ | head  # Show recent backups
   python3 scripts/generate-litellm-config.py --rollback 20251025-143000
   ```

4. **Monitor provider health continuously**:
   ```bash
   watch -n 5 './scripts/validate-unified-backend.sh'
   ```

5. **Review generated config diffs before applying**:
   ```bash
   diff config/litellm-unified.yaml config/backups/litellm-unified.yaml.*
   ```

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
