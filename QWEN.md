# AI Unified Backend Infrastructure - QWEN Context

## Overview

This is the AI Unified Backend Infrastructure project, which provides a single, consistent API endpoint that routes to multiple LLM inference providers. It serves as the central gateway for all LLM providers in the LAB ecosystem, abstracting away the complexity of managing multiple backends.

### Architecture
The system uses LiteLLM as a unified gateway that routes requests to multiple LLM providers:

- **Ollama** (local models, general-purpose) - Port 11434
- **llama.cpp** (CUDA-optimized, native performance) - Ports 8000/8080
- **vLLM** (high-throughput, production-grade) - Port 8001
- **Future providers** (OpenAI, Anthropic, custom servers)

The unified endpoint runs on port 4000 with OpenAI-compatible API format.

### Key Features

1. **Single Entry Point**: All LAB projects consume AI services via one endpoint: `http://localhost:4000`
2. **Provider Abstraction**: Users request models by name, LiteLLM routes to appropriate provider automatically
3. **Extensibility**: Add new providers by updating configuration files, no code changes required
4. **OpenAI Compatibility**: Standard OpenAI API format works across all providers
5. **Advanced Routing**: Supports exact matches, pattern matching, capability-based routing, load balancing
6. **Observability**: Complete monitoring stack with Prometheus, Grafana, and 5 pre-built dashboards
7. **Configuration Management**: Hot-reload with automatic validation, backup, and rollback
8. **Testing Infrastructure**: 75+ automated tests across unit, integration, and contract testing

## Project Structure

```
ai-backend-unified/
├── config/                     # Configuration files
│   ├── providers.yaml          # Provider registry (source of truth)
│   ├── model-mappings.yaml     # Model routing rules
│   ├── litellm-unified.yaml    # Extended LiteLLM config with observability
│   └── schemas/                # Pydantic validation schemas
├── docs/                       # Documentation
├── monitoring/                 # Monitoring stack (Prometheus + Grafana)
├── scripts/                    # Utilities and automation
│   ├── debugging/              # Request tracing utilities
│   ├── profiling/              # Performance analysis tools
│   ├── loadtesting/            # Locust and k6 load testing
│   └── various validation and management scripts
├── tests/                      # Automated test suite
│   ├── unit/                   # Unit tests (30+ tests)
│   ├── integration/            # Integration tests (25+ tests)
│   └── contract/               # Provider contract tests
├── web-ui/                     # Gradio-based model testing interface
├── .serena/                    # Serena project configuration
└── various configuration and documentation files
```

## Core Configuration Files

### config/providers.yaml
- Master catalog of all LLM inference providers
- Contains provider types, base URLs, health endpoints, models available
- Defines provider features, capabilities, and hardware requirements
- Includes health check configuration

### config/model-mappings.yaml
- Defines routing rules for how LiteLLM routes model requests
- Supports exact model name routing, pattern-based routing, and capability-based routing
- Defines load balancing configuration and fallback chains
- Includes routing rules and special cases

### config/litellm-unified.yaml
- Auto-generated LiteLLM configuration file
- Contains model list with provider mappings
- Includes router settings, rate limiting, CORS configuration
- Should NOT be edited manually

## Building and Running

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### Starting the Services

1. **Start individual providers** (Ollama, llama.cpp, vLLM):
   - These run as systemd user services in most cases
   - Check with `systemctl --user status <service-name>`

2. **Start LiteLLM gateway**:
   - Usually runs as `litellm.service` systemd user service
   - Or manually: `litellm --config config/litellm-unified.yaml`

3. **Start monitoring stack**:
   ```bash
   cd monitoring
   docker compose up -d
   ```

4. **Start Web UI** (optional):
   ```bash
   cd web-ui
   python3 app.py
   ```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit              # Fast unit tests
pytest -m integration       # Integration tests (requires providers)
pytest -m contract          # Provider contract tests

# Run with coverage
pytest --cov=config --cov-report=html

# Run validation script
./scripts/validate-unified-backend.sh
```

### Using the API

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000",  # LiteLLM unified gateway
    api_key="not-needed"  # pragma: allowlist secret
)

response = client.chat.completions.create(
    model="llama3.1:8b",  # Routes to Ollama
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Development Conventions

### Configuration Management
- Never edit `litellm-unified.yaml` directly; it's auto-generated
- Update `providers.yaml` and `model-mappings.yaml` as the source of truth
- Run `python3 scripts/generate-litellm-config.py` to regenerate

### Validation
- All configuration changes must pass Pydantic validation
- Unit test coverage must remain >90%
- Pre-commit hooks validate configuration before commits
- Integration tests must pass for all active providers

### Adding New Providers
1. Update `config/providers.yaml` with provider details
2. Add routing rules in `config/model-mappings.yaml`
3. Run `python3 scripts/generate-litellm-config.py`
4. Validate with `./scripts/validate-unified-backend.sh`
5. Add to Serena memories and update documentation

## Important Scripts

- `./scripts/validate-unified-backend.sh` - Comprehensive validation
- `./scripts/generate-litellm-config.py` - Regenerate LiteLLM config
- `./scripts/validate-config-consistency.py` - Check config consistency
- `./scripts/reload-litellm-config.sh` - Safe config reload with rollback
- `./scripts/monitor-redis-cache.sh` - Redis cache management
- `./scripts/check-port-conflicts.sh` - Port conflict detection
- `./scripts/test-rollback.sh` - Rollback testing
- `./scripts/monitor [command]` - User-friendly monitoring interface

## Monitoring and Observability

The system includes comprehensive monitoring with:
- Prometheus for metrics collection
- Grafana for dashboards (5 pre-built dashboards)
- JSON structured logging with request IDs
- 3 debugging utilities for request analysis
- Performance profiling tools
- Load testing suite with Locust and k6

## Web UI Interface

A Gradio-based interface for testing and comparing models:
- Chat interface with multiple models
- Side-by-side model comparison
- Analytics and request history
- Request logging to SQLite database
- Available at http://localhost:5001

## Troubleshooting

Check service status:
```bash
systemctl --user status litellm.service
journalctl --user -u litellm.service -f
```

Validate configuration:
```bash
./scripts/validate-unified-backend.sh
python3 scripts/validate-config-consistency.py
```

Check all providers:
```bash
curl http://localhost:4000/health
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8001/v1/models  # vLLM
```

## Serena Integration

This project is configured as a Serena project with comprehensive memories in `.serena/memories/` for architecture knowledge. Activate with:
```bash
serena activate ai-backend-unified
```
