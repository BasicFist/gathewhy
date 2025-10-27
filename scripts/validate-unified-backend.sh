#!/bin/bash
# Validation script for AI Unified Backend Infrastructure
# Tests all providers, routing, and integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
    ((++TESTS_PASSED))
}

log_error() {
    echo -e "${RED}❌${NC} $1"
    ((++TESTS_FAILED))
}

test_endpoint() {
    local name=$1
    local url=$2
    local timeout=${3:-5}
    local optional=${4:-false}

    if output=$(curl -s -f --max-time "$timeout" "$url" 2>&1 >/dev/null); then
        log_success "$name is accessible"
        return 0
    elif [[ "$optional" == true ]]; then
        log_info "$name is not accessible (optional)"
        return 2
    else
        if [[ -n "$output" ]]; then
            log_error "$name is NOT accessible ($output)"
        else
            log_error "$name is NOT accessible"
        fi
        return 1
    fi
}

test_json_response() {
    local name=$1
    local url=$2
    local jq_filter=${3:-.}
    local optional=${4:-false}

    response=$(curl -s "$url")
    if echo "$response" | jq -e "$jq_filter" > /dev/null 2>&1; then
        log_success "$name returns valid JSON"
        return 0
    elif [[ "$optional" == true ]]; then
        log_info "$name returned invalid JSON (optional)"
        return 2
    else
        log_error "$name returns invalid JSON"
        echo "Response: $response"
        return 1
    fi
}

test_model_available() {
    local model_name=$1

    if curl -s http://localhost:4000/v1/models | jq -e ".data[] | select(.id == \"$model_name\")" > /dev/null; then
        log_success "Model '$model_name' is available"
        return 0
    else
        log_error "Model '$model_name' is NOT available"
        return 1
    fi
}

test_completion() {
    local model_name=$1
    local test_prompt=${2:-"Hello"}

    response=$(curl -s -X POST http://localhost:4000/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model_name\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$test_prompt\"}],
            \"max_tokens\": 50
        }")

    if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
        log_success "Completion with '$model_name' successful"
        return 0
    else
        log_error "Completion with '$model_name' failed"
        echo "Response: $response"
        return 1
    fi
}

echo "=================================="
echo "AI Unified Backend Validation"
echo "=================================="
echo ""

# ============================================================================
# PHASE 1: SYSTEM CHECKS
# ============================================================================

echo "=== Phase 1: System Checks ==="
echo ""

log_info "Checking systemd services..."

# Check LiteLLM service
if systemctl --user is-active litellm.service > /dev/null 2>&1; then
    log_success "LiteLLM service is running"
else
    log_error "LiteLLM service is NOT running"
    echo "  Run: systemctl --user start litellm.service"
fi

# Check Ollama service (if exists)
if systemctl --user list-unit-files | grep -q ollama.service; then
    if systemctl --user is-active ollama.service > /dev/null 2>&1; then
        log_success "Ollama service is running"
    else
        log_error "Ollama service exists but is NOT running"
    fi
fi

echo ""

# ============================================================================
# PHASE 2: PROVIDER HEALTH CHECKS
# ============================================================================

echo "=== Phase 2: Provider Health Checks ==="
echo ""

log_info "Testing provider endpoints..."

# Ollama
test_endpoint "Ollama" "http://localhost:11434/api/tags"
test_json_response "Ollama models list" "http://localhost:11434/api/tags" ".models"

# llama.cpp Python
if test_endpoint "llama.cpp Python" "http://localhost:8000/v1/models" 5 true; then
    test_json_response "llama.cpp Python models" "http://localhost:8000/v1/models" ".data"
fi

# llama.cpp Native
if test_endpoint "llama.cpp Native" "http://localhost:8080/v1/models" 5 true; then
    test_json_response "llama.cpp Native models" "http://localhost:8080/v1/models" ".data"
fi

# vLLM (may not be running)
if test_endpoint "vLLM" "http://localhost:8001/v1/models" 5 true; then
    test_json_response "vLLM models" "http://localhost:8001/v1/models" ".data"
fi

echo ""

# ============================================================================
# PHASE 3: LITELLM GATEWAY CHECKS
# ============================================================================

echo "=== Phase 3: LiteLLM Gateway Checks ==="
echo ""

log_info "Testing LiteLLM endpoint..."

# Test base endpoint
test_endpoint "LiteLLM API" "http://localhost:4000/v1/models"

# Test models endpoint returns valid structure
test_json_response "LiteLLM models list" "http://localhost:4000/v1/models" ".data | length > 0"

# Count available models
model_count=$(curl -s http://localhost:4000/v1/models | jq '.data | length')
log_info "Found $model_count models available"

echo ""

# ============================================================================
# PHASE 4: MODEL AVAILABILITY CHECKS
# ============================================================================

echo "=== Phase 4: Model Availability Checks ==="
echo ""

log_info "Checking expected models..."

# Core models that should be available
test_model_available "llama3.1:latest"
test_model_available "qwen2.5-coder:7b"

# vLLM models (optional)
test_model_available "qwen-coder-vllm" || log_info "qwen-coder-vllm not configured (optional)"
test_model_available "dolphin-uncensored-vllm" || log_info "dolphin-uncensored-vllm not configured (optional)"

echo ""

# ============================================================================
# PHASE 5: ROUTING TESTS
# ============================================================================

echo "=== Phase 5: Routing Tests ==="
echo ""

log_info "Testing model routing..."

# Test routing to Ollama
test_completion "llama3.1:latest" "Say hello"

# Test routing to code model
test_completion "qwen2.5-coder:7b" "Write hello world in Python"

# Test routing to vLLM (if configured)
if curl -s http://localhost:4000/v1/models | jq -e '.data[] | select(.id == "qwen-coder-vllm")' > /dev/null; then
    test_completion "qwen-coder-vllm" "Test"
fi
if curl -s http://localhost:4000/v1/models | jq -e '.data[] | select(.id == "dolphin-uncensored-vllm")' > /dev/null; then
    test_completion "dolphin-uncensored-vllm" "Test"
fi

echo ""

# ============================================================================
# PHASE 6: STREAMING TEST
# ============================================================================

echo "=== Phase 6: Streaming Test ==="
echo ""

log_info "Testing streaming responses..."

stream_response=$(curl -s -X POST http://localhost:4000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama3.1:latest",
        "messages": [{"role": "user", "content": "Count to 3"}],
        "stream": true,
        "max_tokens": 20
    }' || true)

streaming_supported=false
if [[ -n "$stream_response" ]] && echo "$stream_response" | grep -q "data:"; then
    log_success "Streaming response works"
    if echo "$stream_response" | grep -q "\[DONE\]"; then
        log_success "Streaming response includes [DONE] marker"
    else
        log_info "Streaming response missing [DONE] marker (optional)"
    fi
    streaming_supported=true
else
    log_info "Streaming response not available (optional)"
fi

echo ""

# ============================================================================
# PHASE 7: CONFIGURATION VALIDATION
# ============================================================================

echo "=== Phase 7: Configuration Validation ==="
echo ""

log_info "Validating configuration files..."

# Check if config files exist
if [ -f "config/providers.yaml" ]; then
    log_success "providers.yaml exists"
else
    log_error "providers.yaml NOT found"
fi

if [ -f "config/model-mappings.yaml" ]; then
    log_success "model-mappings.yaml exists"
else
    log_error "model-mappings.yaml NOT found"
fi

if [ -f "config/litellm-unified.yaml" ]; then
    log_success "litellm-unified.yaml exists"
else
    log_error "litellm-unified.yaml NOT found"
fi

# Validate YAML syntax
if command -v python3 > /dev/null 2>&1; then
    if python3 -c "import yaml; yaml.safe_load(open('config/providers.yaml'))" 2>/dev/null; then
        log_success "providers.yaml syntax is valid"
    else
        log_error "providers.yaml has YAML syntax errors"
    fi

    if python3 -c "import yaml; yaml.safe_load(open('config/model-mappings.yaml'))" 2>/dev/null; then
        log_success "model-mappings.yaml syntax is valid"
    else
        log_error "model-mappings.yaml has YAML syntax errors"
    fi

    if python3 -c "import yaml; yaml.safe_load(open('config/litellm-unified.yaml'))" 2>/dev/null; then
        log_success "litellm-unified.yaml syntax is valid"
    else
        log_error "litellm-unified.yaml has YAML syntax errors"
    fi
else
    log_info "Python3 not available, skipping YAML syntax validation"
fi

echo ""

# ============================================================================
# PHASE 8: PERFORMANCE CHECKS
# ============================================================================

echo "=== Phase 8: Performance Checks ==="
echo ""

log_info "Testing response times..."

# Test response time
start_time=$(date +%s%3N)
curl -s -X POST http://localhost:4000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama3.1:latest",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 10
    }' > /dev/null
end_time=$(date +%s%3N)

response_time=$((end_time - start_time))

if [ $response_time -lt 5000 ]; then
    log_success "Response time: ${response_time}ms (good)"
elif [ $response_time -lt 10000 ]; then
    log_info "Response time: ${response_time}ms (acceptable)"
else
    log_error "Response time: ${response_time}ms (slow)"
fi

echo ""

# ============================================================================
# PHASE 9: REDIS CACHE CHECK
# ============================================================================

echo "=== Phase 9: Redis Cache Check ==="
echo ""

if command -v redis-cli > /dev/null 2>&1; then
    if redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is running"

        # Check if cache is enabled
        if grep -q "cache: true" ../openwebui/config/litellm.yaml 2>/dev/null; then
            log_success "Redis caching is enabled in config"
        else
            log_info "Redis caching is not enabled (optional)"
        fi
    else
        log_info "Redis is not running (optional)"
    fi
else
    log_info "redis-cli not found, skipping Redis check"
fi

echo ""

# ============================================================================
# PHASE 9.5: CACHE HEALTH CHECK (LiteLLM /cache/ping endpoint)
# ============================================================================

echo "=== Phase 9.5: Cache Health Check ==="
echo ""

if curl -s http://localhost:4000/cache/ping > /dev/null 2>&1; then
    CACHE_STATUS=$(curl -s http://localhost:4000/cache/ping 2>/dev/null | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
    if [ "$CACHE_STATUS" = "healthy" ]; then
        log_success "Redis cache health check passed"

        # Get additional cache details
        CACHE_TYPE=$(curl -s http://localhost:4000/cache/ping 2>/dev/null | jq -r '.cache_type // "unknown"' 2>/dev/null || echo "unknown")
        log_info "Cache type: $CACHE_TYPE"
    elif [ "$CACHE_STATUS" = "unknown" ]; then
        log_info "Cache health endpoint returned unexpected response"
    else
        log_warning "Redis cache status: $CACHE_STATUS"
    fi
else
    log_info "Cache health endpoint not available (LiteLLM not running or endpoint not configured)"
fi

echo ""

# ============================================================================
# PHASE 9.6: PROMETHEUS METRICS CHECK
# ============================================================================

echo "=== Phase 9.6: Prometheus Metrics Check ==="
echo ""

if curl -s http://localhost:4000/metrics > /dev/null 2>&1; then
    METRIC_COUNT=$(curl -s http://localhost:4000/metrics 2>/dev/null | grep -c "^litellm_" 2>/dev/null || echo "0")
    if [ "$METRIC_COUNT" -gt 0 ]; then
        log_success "Prometheus metrics endpoint available ($METRIC_COUNT LiteLLM metrics)"
    else
        log_warning "Prometheus endpoint available but no LiteLLM metrics found"
        log_info "Ensure callbacks: ['prometheus'] is set in litellm_settings"
    fi
else
    log_info "Prometheus metrics endpoint not available (LiteLLM not running)"
fi

echo ""

# ============================================================================
# PHASE 10: DOCUMENTATION CHECK
# ============================================================================

echo "=== Phase 10: Documentation Check ==="
echo ""

log_info "Checking documentation files..."

docs=("README.md" "docs/architecture.md" "docs/adding-providers.md" "docs/consuming-api.md" "docs/troubleshooting.md")

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        log_success "$doc exists"
    else
        log_error "$doc NOT found"
    fi
done

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "=================================="
echo "Validation Summary"
echo "=================================="
echo ""
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All validation tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test integration from your LAB projects"
    echo "  2. Monitor performance: journalctl --user -u litellm.service -f"
    echo "  3. See docs/consuming-api.md for integration examples"
    exit 0
else
    echo -e "${RED}❌ Some validation tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: journalctl --user -u litellm.service"
    echo "  2. Verify provider health individually"
    echo "  3. See docs/troubleshooting.md for solutions"
    exit 1
fi
