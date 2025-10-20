# Test Suite Documentation

Comprehensive testing infrastructure for AI Backend Unified Infrastructure.

## Test Pyramid

```
        🔺 E2E Tests (Future)
       🔺🔺 Integration Tests (Active)
      🔺🔺🔺 Contract Tests (Active)
     🔺🔺🔺🔺 Unit Tests (Active)
    🔺🔺🔺🔺🔺 Config Validation (Active)
```

## Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/
│   └── test_routing.py            # Routing logic tests (no dependencies)
├── integration/
│   └── test_integration.py        # End-to-end routing tests (requires providers)
├── contract/
│   └── test_provider_contracts.sh # Provider API compliance tests
└── fixtures/                      # Test data and mock configurations
```

---

## Setup

### Install Dependencies

```bash
# Install all testing dependencies
pip install -r requirements.txt

# Verify pytest is available
pytest --version
```

### Configure Test Environment

```bash
# Ensure providers are running for integration tests
systemctl --user status ollama.service
systemctl --user status litellm.service

# Verify LiteLLM gateway accessible
curl http://localhost:4000/v1/models
```

---

## Running Tests

### Quick Start

```bash
# Run all unit tests (fast, no dependencies)
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=scripts --cov-report=html

# Run specific test file
pytest tests/unit/test_routing.py -v

# Run specific test class
pytest tests/unit/test_routing.py::TestExactMatchRouting -v
```

### Unit Tests

**Purpose**: Validate routing logic without external dependencies

```bash
# All unit tests
pytest tests/unit/ -v

# Run only fast tests
pytest tests/unit/ -m "not slow"

# Parallel execution (faster)
pytest tests/unit/ -n auto
```

**Test categories**:
- Exact match routing
- Pattern matching
- Capability-based routing
- Fallback chain integrity
- Load balancing weights
- Provider references
- Rate limit configuration

### Contract Tests

**Purpose**: Verify provider API compliance

```bash
# All providers
bash tests/contract/test_provider_contracts.sh

# Specific provider
bash tests/contract/test_provider_contracts.sh --provider ollama
bash tests/contract/test_provider_contracts.sh --provider vllm

# Strict mode (fail fast)
bash tests/contract/test_provider_contracts.sh --strict
```

**Tests**:
- Health endpoint accessibility
- Models endpoint structure
- Response time thresholds
- Provider-specific features

### Integration Tests

**Purpose**: Test end-to-end routing with real providers

**⚠️ Requires active providers to run**

```bash
# All integration tests (slow)
pytest tests/integration/ -v

# Skip slow tests
pytest tests/integration/ -m "not slow"

# Specific categories
pytest tests/integration/ -k "routing"
pytest tests/integration/ -k "cache"
pytest tests/integration/ -k "streaming"

# With coverage
pytest tests/integration/ --cov=scripts --cov-report=term
```

**Test categories**:
- Basic routing to correct providers
- Fallback chain execution
- Cache behavior (requires Redis)
- Streaming responses
- Error handling
- Performance thresholds
- Rate limiting enforcement

**Markers**:
- `@pytest.mark.integration` - Integration test
- `@pytest.mark.slow` - Slow-running test
- `@pytest.mark.requires_ollama` - Requires Ollama provider
- `@pytest.mark.requires_redis` - Requires Redis cache

### Rollback Tests

**Purpose**: Verify configuration rollback procedures

```bash
# Full rollback test
bash scripts/test-rollback.sh

# Dry run (see what would happen)
bash scripts/test-rollback.sh --dry-run

# Skip service restarts (faster)
bash scripts/test-rollback.sh --skip-restart
```

**Test scenarios**:
1. Verify current state healthy
2. Create backup of working config
3. Apply intentionally broken config
4. Detect system degradation
5. Execute rollback procedure
6. Verify successful recovery
7. Confirm no data loss
8. Validate documentation exists

---

## Test Markers

Use markers to selectively run tests:

```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Only tests requiring Ollama
pytest -m requires_ollama

# Exclude slow tests
pytest -m "not slow"

# Combine markers
pytest -m "integration and not slow"
```

**Available markers**:
- `unit` - Unit tests (no dependencies)
- `integration` - Integration tests (requires providers)
- `contract` - Contract tests (API compliance)
- `slow` - Slow-running tests (>5 seconds)
- `requires_ollama` - Requires Ollama provider
- `requires_llamacpp` - Requires llama.cpp provider
- `requires_vllm` - Requires vLLM provider
- `requires_redis` - Requires Redis cache

---

## Continuous Integration

### Pre-commit (Local)

Tests run automatically on `git commit`:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### GitHub Actions (Remote)

Automated testing on push/PR:

```yaml
# .github/workflows/validate-config.yml
- Unit tests (always)
- Contract tests (optional)
- Integration tests (optional, requires providers)
- Rollback tests (optional)
```

---

## Writing New Tests

### Unit Test Template

```python
# tests/unit/test_my_feature.py
import pytest

@pytest.mark.unit
class TestMyFeature:
    """Test my feature functionality"""

    def test_basic_behavior(self, providers_config):
        """Verify basic behavior works"""
        # Arrange
        input_data = "test"

        # Act
        result = my_function(input_data)

        # Assert
        assert result == expected
```

### Integration Test Template

```python
# tests/integration/test_my_integration.py
import pytest
import requests

@pytest.mark.integration
@pytest.mark.requires_ollama
class TestMyIntegration:
    """Test my integration with real providers"""

    def test_end_to_end_flow(self, litellm_url):
        """Test complete workflow"""
        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Test"}]
        }

        response = requests.post(
            f"{litellm_url}/v1/chat/completions",
            json=payload
        )

        assert response.status_code == 200
```

### Contract Test Template

```bash
# tests/contract/test_my_provider.sh

test_my_provider_contract() {
    echo "Testing my provider..."

    if curl -s http://localhost:9999/health; then
        test_passed "Provider health check"
    else
        test_failed "Provider health check" "Connection refused"
    fi
}
```

---

## Shared Fixtures

Available in `conftest.py`:

```python
# Configuration fixtures
providers_config    # providers.yaml loaded
mappings_config     # model-mappings.yaml loaded
litellm_config      # litellm-unified.yaml loaded

# Filtered data
active_providers    # Only active providers
exact_matches       # Exact model matches
fallback_chains     # Fallback configurations
capability_routing  # Capability-based routing

# URLs
litellm_url         # http://localhost:4000
provider_urls       # Map of provider names to URLs

# Mock data (for unit tests)
mock_providers      # Mock provider configuration
mock_mappings       # Mock model mappings

# Helpers
load_yaml_file(path)           # Load YAML file
validate_url_format(url)       # Validate URL
validate_port_range(port)      # Validate port
```

---

## Coverage Reports

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=scripts --cov-report=html --cov-report=term

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Goals

- **Unit tests**: >90% of routing logic
- **Integration tests**: Core user paths
- **Contract tests**: All provider APIs
- **Overall**: >80% code coverage

---

## Performance Testing

### Response Time Benchmarks

```bash
# Test provider response times
pytest tests/integration/test_integration.py::TestPerformance -v

# Expected thresholds:
# - Ollama: <10s
# - llama.cpp native: <5s
# - llama.cpp python: <7s
# - vLLM: <8s (with batching)
```

### Concurrent Load Testing

```bash
# Test concurrent request handling
pytest tests/integration/test_integration.py::TestPerformance::test_concurrent_requests_handled -v

# Uses ThreadPoolExecutor for parallel requests
```

---

## Troubleshooting

### Tests Failing

**Provider not responding**:
```bash
# Check provider status
systemctl --user status ollama.service
systemctl --user status litellm.service

# Restart if needed
systemctl --user restart ollama.service
systemctl --user restart litellm.service
```

**Port already in use**:
```bash
# Check what's using the port
lsof -i :4000
lsof -i :11434

# Kill or restart the service
```

**Import errors**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify imports work
python3 -c "import pytest; import pydantic; import yaml"
```

**Timeout errors**:
```bash
# Increase timeout for slow systems
pytest tests/integration/ --timeout=60

# Or skip slow tests
pytest -m "not slow"
```

### Common Issues

**"No module named 'conftest'"**:
- Run pytest from project root
- Ensure tests/ directory has conftest.py

**"Provider not found"**:
- Check provider is active in providers.yaml
- Verify provider service is running
- Check base_url is correct

**"Connection refused"**:
- Provider not running
- Wrong port configured
- Firewall blocking connection

---

## Best Practices

### Test Isolation

- Each test should be independent
- Use fixtures for shared setup
- Clean up after tests
- Don't rely on test execution order

### Test Naming

```python
# Good names
test_exact_match_routes_correctly()
test_fallback_triggers_on_primary_failure()
test_rate_limit_enforced_after_threshold()

# Bad names
test1()
test_stuff()
test_it_works()
```

### Assertions

```python
# Good assertions
assert response.status_code == 200, "Request should succeed"
assert model_count > 0, "Should have at least one model"

# Provide helpful messages
assert len(fallback_chain) >= 2, \
    f"Fallback chain for {model} should have 2+ models, got {len(fallback_chain)}"
```

### Markers Usage

Always use appropriate markers:

```python
@pytest.mark.unit  # No external dependencies
@pytest.mark.integration  # Requires real providers
@pytest.mark.slow  # Takes >5 seconds
@pytest.mark.requires_redis  # Needs Redis running
```

---

## Test Maintenance

### Monthly Tasks

- Review and update test thresholds
- Check for flaky tests
- Update fixtures with new models
- Verify coverage remains high

### When Adding Features

1. Write tests first (TDD)
2. Cover happy path and edge cases
3. Add integration tests if needed
4. Update this documentation
5. Run full test suite before commit

### When Fixing Bugs

1. Write failing test reproducing bug
2. Fix the bug
3. Verify test now passes
4. Add regression test to suite

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Last Updated:** 2025-10-20
**Maintained By:** AI Backend Unified Infrastructure Team
