# AI Backend Unified Infrastructure - Testing Patterns

**Memory Type**: Testing Strategy
**Created**: 2025-10-20
**Last Updated**: 2025-10-20

## Testing Pyramid

```
        🔺 E2E Tests (Playwright)
       🔺🔺 Integration Tests
      🔺🔺🔺 Contract Tests
     🔺🔺🔺🔺 Unit Tests
    🔺🔺🔺🔺🔺 Configuration Validation
```

## Test Categories

### 1. Configuration Validation (Pre-commit)

**Purpose**: Prevent invalid configurations from being committed

**Tools**:
- Pydantic schema validation
- YAML syntax checking
- Secret detection

**Location**: `scripts/validate-config-schema.py`

**Run**:
```bash
# Automatic on commit
git commit -m "message"

# Manual
python3 scripts/validate-config-schema.py
```

**Tests**:
- YAML syntax validity
- Required fields presence
- URL format correctness
- Port range validation (1-65535)
- Provider status values
- Cross-configuration consistency
- Fallback chain integrity
- Model reference validity

---

### 2. Unit Tests (Routing Logic)

**Purpose**: Validate routing decisions without external dependencies

**Tools**: pytest

**Location**: `tests/test_routing.py`

**Pattern**:
```python
def test_exact_match_routing():
    """Verify exact model names route to correct provider"""
    mappings = load_model_mappings()
    assert route_model("llama3.1:8b") == "ollama"
    assert route_model("llama2-13b-vllm") == "vllm"

def test_pattern_matching():
    """Verify regex patterns match expected models"""
    assert matches_pattern("meta-llama/.*", "meta-llama/Llama-2-13b")
    assert not matches_pattern("meta-llama/.*", "ollama/llama3.1")

def test_fallback_chain_integrity():
    """Ensure fallback chains reference active providers"""
    providers = get_active_providers()
    chains = get_fallback_chains()
    for chain in chains:
        for provider in chain.providers:
            assert provider in providers

def test_load_balancing_weights():
    """Verify load balancing weights sum to 1.0"""
    redundant = get_redundant_models()
    for model, config in redundant.items():
        total = sum(p.weight for p in config.providers)
        assert abs(total - 1.0) < 0.01
```

**Run**:
```bash
pytest tests/test_routing.py -v
```

---

### 3. Contract Tests (Provider APIs)

**Purpose**: Verify providers adhere to expected API contracts

**Tools**: bash, curl, jq

**Location**: `tests/test_provider_contracts.sh`

**Pattern**:
```bash
test_provider_health() {
    provider=$1
    endpoint=$2

    response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")

    if [ "$response" = "200" ]; then
        echo "✅ $provider health check passed"
    else
        echo "❌ $provider health check failed (HTTP $response)"
        return 1
    fi
}

test_models_endpoint() {
    provider=$1
    endpoint=$2

    # Verify response structure
    models=$(curl -s "$endpoint" | jq -e '.data | length')

    if [ "$models" -gt 0 ]; then
        echo "✅ $provider has $models models"
    else
        echo "❌ $provider returned no models"
        return 1
    fi
}
```

**Tests**:
- Health endpoints accessible
- Models endpoint returns valid JSON
- Model list structure correct
- Provider-specific fields present
- Response times within thresholds

**Run**:
```bash
bash tests/test_provider_contracts.sh
```

---

### 4. Integration Tests (Routing Behavior)

**Purpose**: Verify end-to-end routing with real providers

**Tools**: pytest, requests

**Location**: `tests/test_integration.py`

**Pattern**:
```python
def test_exact_match_routes_correctly():
    """Verify exact model name routes to expected provider"""
    # Request to Ollama model
    response = requests.post(
        "http://localhost:4000/v1/chat/completions",
        json={
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    # Verify response came from Ollama (check logs or response metadata)

def test_fallback_on_provider_failure():
    """Verify fallback chain executes when primary fails"""
    # Stop primary provider
    subprocess.run(["systemctl", "--user", "stop", "ollama.service"])

    try:
        # Request should fallback to secondary
        response = requests.post(
            "http://localhost:4000/v1/chat/completions",
            json={
                "model": "llama3.1:8b",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            }
        )

        assert response.status_code == 200
        # Should have used fallback (check logs)

    finally:
        # Restart primary
        subprocess.run(["systemctl", "--user", "start", "ollama.service"])

def test_streaming_response():
    """Verify streaming responses work correctly"""
    response = requests.post(
        "http://localhost:4000/v1/chat/completions",
        json={
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Count to 3"}],
            "stream": true,
            "max_tokens": 20
        },
        stream=True
    )

    chunks = []
    for line in response.iter_lines():
        if line:
            chunks.append(line.decode())

    assert len(chunks) > 0
    assert any("data:" in chunk for chunk in chunks)

def test_cache_behavior():
    """Verify Redis caching works"""
    payload = {
        "model": "llama3.1:8b",
        "messages": [{"role": "user", "content": "Unique test query 12345"}],
        "max_tokens": 10
    }

    # First request (miss)
    start1 = time.time()
    response1 = requests.post("http://localhost:4000/v1/chat/completions", json=payload)
    latency1 = time.time() - start1

    # Second request (hit)
    start2 = time.time()
    response2 = requests.post("http://localhost:4000/v1/chat/completions", json=payload)
    latency2 = time.time() - start2

    # Cache hit should be significantly faster
    assert latency2 < latency1 * 0.5
    assert response1.json() == response2.json()
```

**Run**:
```bash
# Requires providers running
pytest tests/test_integration.py -v
```

---

### 5. Rollback Tests

**Purpose**: Verify configuration rollback procedures work

**Tools**: bash

**Location**: `scripts/test-rollback.sh`

**Pattern**:
```bash
# Apply intentionally broken config
cp config/litellm-unified.yaml config/litellm-unified.yaml.backup
cat > config/litellm-unified.yaml << 'EOF'
model_list:
  - model_name: broken
    litellm_params:
      model: invalid://broken
EOF

# Apply and verify failure
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
sleep 5

# Verify degradation
curl -sf http://localhost:4000/v1/models > /dev/null || echo "Expected failure"

# Execute rollback
cp config/litellm-unified.yaml.backup config/litellm-unified.yaml
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
sleep 5

# Verify recovery
model_count=$(curl -s http://localhost:4000/v1/models | jq '.data | length')
if [ "$model_count" -gt 0 ]; then
    echo "✅ Rollback successful"
else
    echo "❌ Rollback failed"
    exit 1
fi
```

---

### 6. Performance Tests

**Purpose**: Measure and benchmark routing performance

**Tools**: bash, time, curl

**Pattern**:
```bash
test_response_time() {
    model=$1
    expected_max_ms=$2

    start=$(date +%s%3N)
    curl -s -X POST http://localhost:4000/v1/chat/completions \
        -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}], \"max_tokens\": 10}" \
        > /dev/null
    end=$(date +%s%3N)

    latency=$((end - start))

    if [ $latency -lt $expected_max_ms ]; then
        echo "✅ $model: ${latency}ms (< ${expected_max_ms}ms)"
    else
        echo "❌ $model: ${latency}ms (> ${expected_max_ms}ms)"
        return 1
    fi
}

# Test each provider
test_response_time "llama-cpp-native" 500   # Fastest
test_response_time "llama3.1:8b" 2000        # Medium
test_response_time "llama2-13b-vllm" 3000    # Batched (may be slower for single requests)
```

---

## Testing Workflow

### Development Cycle

```bash
# 1. Make configuration changes
vim config/providers.yaml

# 2. Pre-commit validation (automatic)
git add config/providers.yaml
git commit -m "Add new provider"  # Runs validation hooks

# 3. If validation passes, continue
python3 scripts/generate-litellm-config.py
python3 scripts/validate-config-schema.py

# 4. Run unit tests
pytest tests/test_routing.py -v

# 5. Apply configuration (test environment first)
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service

# 6. Run integration tests
pytest tests/test_integration.py -v

# 7. Run full validation
bash scripts/validate-unified-backend.sh

# 8. If all pass, commit and push
git push
```

### CI/CD Pipeline (Phase 2)

```yaml
# .github/workflows/validate-config.yml
jobs:
  validate:
    steps:
      - Validate YAML syntax
      - Run Pydantic schema validation
      - Run unit tests
      - (Optional) Run integration tests with mock providers
```

---

## Test Data Management

### Mock Configurations

**Location**: `tests/fixtures/`

**Pattern**:
```python
@pytest.fixture
def mock_providers():
    return {
        "providers": {
            "test_provider": {
                "type": "openai_compatible",
                "base_url": "http://localhost:9999",
                "status": "active",
                "models": [
                    {"name": "test-model", "size": "7B"}
                ]
            }
        }
    }

@pytest.fixture
def mock_mappings():
    return {
        "exact_matches": {
            "test-model": {
                "provider": "test_provider",
                "priority": "primary",
                "description": "Test model"
            }
        }
    }
```

### Test Isolation

- Each test suite has independent fixtures
- Integration tests use test-specific models
- Mock providers for unit tests
- Cleanup after integration tests

---

## Continuous Monitoring Tests

**Purpose**: Validate system health in production

**Pattern**:
```bash
# Run every 15 minutes via cron
*/15 * * * * /home/miko/LAB/ai/backend/ai-backend-unified/scripts/validate-unified-backend.sh --silent

# Or systemd timer (Phase 4)
```

**Tests**:
- Provider health
- Model availability
- Basic completion success
- Response time within thresholds
- No errors in logs (last 15 min)

---

## Test Coverage Goals

- Configuration validation: 100%
- Routing logic: 90%+
- Provider contracts: 100%
- Integration tests: Core user paths covered
- Rollback procedure: Tested and verified

## Testing Best Practices

1. **Test in order**: Config validation → Unit → Contract → Integration
2. **Isolate tests**: Each test should be independent
3. **Use fixtures**: Reusable test data and mocks
4. **Fast feedback**: Unit tests should run in seconds
5. **Real conditions**: Integration tests use actual providers
6. **Document failures**: Capture logs and state for debugging
7. **Automate**: Pre-commit hooks and CI/CD integration
8. **Monitor**: Continuous health checks in production

## Future Testing Enhancements

- Load testing with multiple concurrent requests
- Chaos engineering (random provider failures)
- Performance regression detection
- Security scanning (penetration testing)
- Compliance validation (SOC 2 requirements)
