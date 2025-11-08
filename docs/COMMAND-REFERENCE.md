# AI Backend Unified - Command Reference

## Dashboard Commands

### Standard Dashboard
```bash
# Run the original production dashboard
python3 scripts/ai-dashboard

# Or run via executable
./scripts/ai-dashboard
```

### Enhanced Dashboard (Real - Current Production)
```bash
# Run the enhanced dashboard with REAL API connections (Production Dashboard)
python3 scripts/ai-dashboard-enhanced.py

# This dashboard features:
# - 4-panel layout (providers, request inspector, performance, routing)
# - Real connection to provider endpoints (Ollama, llama.cpp, vLLM)
# - Live request monitoring from actual API calls
# - Dynamic provider health checks
# - Proper error handling for unreachable services
# - Model count from actual providers
# - No simulated data - all requests connect to real endpoints

# Environment variable override:
LITELLM_GATEWAY_URL=http://localhost:4000 python3 scripts/ai-dashboard-enhanced.py

# The file scripts/ai-dashboard-enhanced-real.py was consolidated into the main enhanced dashboard
# as of November 7, 2025, eliminating all simulated data components
```
```

## Health Check Commands
```bash
# Check all providers status
./scripts/validate-unified-backend.sh

# Check individual providers
curl http://localhost:4000/health  # LiteLLM gateway
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/v1/models  # llama.cpp
curl http://localhost:8001/v1/models  # vLLM

# Check system health
./scripts/check-system-health.sh
```

## Configuration Management
```bash
# Reload configuration with validation
./scripts/reload-litellm-config.sh

# Validate configuration before deploying
./scripts/reload-litellm-config.sh --validate-only

# Check config consistency
python3 scripts/validate-config-consistency.py

# Generate config from source files
python3 scripts/generate-litellm-config.py
```

## Port Management
```bash
# Check all registered ports
./scripts/check-port-conflicts.sh

# Check only required ports
./scripts/check-port-conflicts.sh --required

# Attempt to fix port conflicts
./scripts/check-port-conflicts.sh --fix
```

## Redis Cache Management
```bash
# Monitor Redis cache
./scripts/monitor-redis-cache.sh

# View cache keys
./scripts/monitor-redis-cache.sh --keys

# Monitor continuously
./scripts/monitor-redis-cache.sh --watch

# Flush cache (requires confirmation)
./scripts/monitor-redis-cache.sh --flush
```

## Testing Commands
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit              # Fast unit tests
pytest -m integration       # Integration tests (requires providers)
pytest -m contract          # Provider contract tests

# Run with coverage
pytest --cov=config --cov-report=html

# Test configuration validation
./scripts/validate-all-configs.sh
```

## Model Routing Visualization
```bash
# Visualize model routing (ASCII format)
python3 scripts/model-routing-visualizer.py

# Generate DOT graph for Graphviz
python3 scripts/model-routing-visualizer.py --dot --output=model-routing.dot

# Output in JSON format
python3 scripts/model-routing-visualizer.py --json
```

## Monitoring Stack
```bash
# Start monitoring stack (Prometheus + Grafana)
cd monitoring
docker compose up -d

# Check monitoring health
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana (admin/admin)

# Monitor requests live
./scripts/debugging/tail-requests.py

# Profile performance
./scripts/profiling/profile-latency.py
./scripts/profiling/profile-throughput.py
./scripts/profiling/compare-providers.py

# Run load tests
k6 run scripts/loadtesting/k6/smoke-test.js
```

## Production Commands
```bash
# Deploy to production (with validation)
./scripts/deploy-production.sh

# Backup configuration before changes
./scripts/backup-config.sh

# Test rollback capability
./scripts/test-rollback.sh

# Rollback to previous version
./scripts/rollback-config.sh
```

## Quick Checks
```bash
# Verify system status
./scripts/health-check.sh

# Check if all required services are running
systemctl --user list-units --state=running | grep -E "(ollama|litellm|vllm|llamacpp)"

# View recent logs
journalctl --user -u litellm.service -n 20
```

## Security & Access Checks
```bash
# Validate API key configuration
./scripts/validate-api-keys.sh

# Check authentication settings
./scripts/check-authentication.sh

# Audit configuration for security issues
python3 scripts/security-audit.py
```
