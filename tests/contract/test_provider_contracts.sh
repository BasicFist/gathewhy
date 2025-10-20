#!/usr/bin/env bash
#
# Contract Tests for Provider APIs
#
# Verifies that each provider adheres to expected API contracts:
# - Health endpoints respond correctly
# - Models endpoint returns valid JSON structure
# - Required fields are present
# - Response times are within acceptable thresholds
#
# Usage:
#   bash tests/contract/test_provider_contracts.sh
#   bash tests/contract/test_provider_contracts.sh --provider ollama
#   bash tests/contract/test_provider_contracts.sh --strict

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Configuration
TIMEOUT=5
STRICT_MODE=false
SPECIFIC_PROVIDER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --strict)
            STRICT_MODE=true
            shift
            ;;
        --provider)
            SPECIFIC_PROVIDER="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
test_passed() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
}

test_failed() {
    echo -e "${RED}❌ $1${NC}"
    echo -e "${RED}   Error: $2${NC}"
    ((TESTS_FAILED++))
    ((TESTS_RUN++))

    if [ "$STRICT_MODE" = true ]; then
        exit 1
    fi
}

test_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test provider health endpoint
test_provider_health() {
    local provider_name=$1
    local health_url=$2
    local expected_status=${3:-200}

    echo ""
    echo "Testing $provider_name health endpoint..."

    # Test endpoint accessibility
    if response=$(curl -s -w "\n%{http_code}" --max-time "$TIMEOUT" "$health_url" 2>&1); then
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')

        if [ "$http_code" = "$expected_status" ]; then
            test_passed "$provider_name health endpoint accessible (HTTP $http_code)"
        else
            test_failed "$provider_name health check" "Expected HTTP $expected_status, got $http_code"
        fi
    else
        test_failed "$provider_name health check" "Connection failed or timeout"
    fi
}

# Test models endpoint
test_models_endpoint() {
    local provider_name=$1
    local models_url=$2

    echo ""
    echo "Testing $provider_name models endpoint..."

    # Test endpoint accessibility
    if response=$(curl -s -w "\n%{http_code}" --max-time "$TIMEOUT" "$models_url" 2>&1); then
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')

        if [ "$http_code" != "200" ]; then
            test_failed "$provider_name models endpoint" "HTTP $http_code"
            return
        fi

        test_passed "$provider_name models endpoint accessible (HTTP 200)"

        # Verify JSON structure
        if echo "$body" | jq empty 2>/dev/null; then
            test_passed "$provider_name models endpoint returns valid JSON"

            # Check for data field (OpenAI-compatible format)
            if echo "$body" | jq -e '.data' >/dev/null 2>&1; then
                test_passed "$provider_name models response has 'data' field"

                # Count models
                model_count=$(echo "$body" | jq '.data | length')
                if [ "$model_count" -gt 0 ]; then
                    test_passed "$provider_name has $model_count models available"
                else
                    test_warning "$provider_name has no models available"
                fi

                # Verify model structure (first model)
                if echo "$body" | jq -e '.data[0].id' >/dev/null 2>&1; then
                    test_passed "$provider_name models have 'id' field"
                else
                    test_failed "$provider_name model structure" "Missing 'id' field"
                fi

            else
                # Ollama-specific format
                if echo "$body" | jq -e '.models' >/dev/null 2>&1; then
                    test_passed "$provider_name uses Ollama format (has 'models' field)"

                    model_count=$(echo "$body" | jq '.models | length')
                    if [ "$model_count" -gt 0 ]; then
                        test_passed "$provider_name has $model_count models available"
                    fi
                else
                    test_warning "$provider_name uses non-standard response format"
                fi
            fi

        else
            test_failed "$provider_name models response" "Invalid JSON"
        fi

    else
        test_failed "$provider_name models endpoint" "Connection failed or timeout"
    fi
}

# Test response time
test_response_time() {
    local provider_name=$1
    local url=$2
    local max_time_ms=$3

    echo ""
    echo "Testing $provider_name response time..."

    start_time=$(date +%s%3N)
    if curl -s --max-time "$TIMEOUT" "$url" > /dev/null 2>&1; then
        end_time=$(date +%s%3N)
        elapsed=$((end_time - start_time))

        if [ "$elapsed" -lt "$max_time_ms" ]; then
            test_passed "$provider_name responds in ${elapsed}ms (< ${max_time_ms}ms)"
        else
            test_warning "$provider_name responds in ${elapsed}ms (> ${max_time_ms}ms threshold)"
        fi
    else
        test_failed "$provider_name response time test" "Request failed"
    fi
}

# Test provider-specific features
test_ollama_features() {
    echo ""
    echo "Testing Ollama-specific features..."

    # Test tags endpoint (Ollama specific)
    if response=$(curl -s http://localhost:11434/api/tags 2>&1); then
        if echo "$response" | jq -e '.models' >/dev/null 2>&1; then
            test_passed "Ollama /api/tags endpoint accessible"

            # Check for model details
            if echo "$response" | jq -e '.models[0].name' >/dev/null 2>&1; then
                test_passed "Ollama models have name field"
            fi

            if echo "$response" | jq -e '.models[0].size' >/dev/null 2>&1; then
                test_passed "Ollama models have size field"
            fi
        fi
    fi
}

test_llamacpp_features() {
    local port=$1

    echo ""
    echo "Testing llama.cpp features (port $port)..."

    # Test props endpoint
    if response=$(curl -s "http://localhost:$port/props" 2>&1); then
        if echo "$response" | jq empty 2>/dev/null; then
            test_passed "llama.cpp /props endpoint accessible"
        fi
    fi
}

test_vllm_features() {
    echo ""
    echo "Testing vLLM-specific features..."

    # Test version endpoint
    if response=$(curl -s http://localhost:8001/version 2>&1); then
        if [ -n "$response" ]; then
            test_passed "vLLM /version endpoint accessible"
        fi
    fi

    # Test health endpoint
    if response=$(curl -s http://localhost:8001/health 2>&1); then
        if [ -n "$response" ]; then
            test_passed "vLLM /health endpoint accessible"
        fi
    fi
}

# Main test execution
echo "================================"
echo "Provider Contract Tests"
echo "================================"
echo ""
echo "Configuration:"
echo "  Timeout: ${TIMEOUT}s"
echo "  Strict mode: $STRICT_MODE"
[ -n "$SPECIFIC_PROVIDER" ] && echo "  Testing only: $SPECIFIC_PROVIDER"
echo ""

# Test Ollama
if [ -z "$SPECIFIC_PROVIDER" ] || [ "$SPECIFIC_PROVIDER" = "ollama" ]; then
    echo "========================================"
    echo "Testing Ollama Provider"
    echo "========================================"

    test_provider_health "Ollama" "http://localhost:11434/api/tags" 200
    test_models_endpoint "Ollama" "http://localhost:11434/api/tags"
    test_response_time "Ollama" "http://localhost:11434/api/tags" 1000
    test_ollama_features
fi

# Test llama.cpp (Python bindings)
if [ -z "$SPECIFIC_PROVIDER" ] || [ "$SPECIFIC_PROVIDER" = "llama_cpp_python" ]; then
    echo ""
    echo "========================================"
    echo "Testing llama.cpp Python Provider"
    echo "========================================"

    test_provider_health "llama.cpp-python" "http://localhost:8000/v1/models" 200
    test_models_endpoint "llama.cpp-python" "http://localhost:8000/v1/models"
    test_response_time "llama.cpp-python" "http://localhost:8000/v1/models" 500
    test_llamacpp_features 8000
fi

# Test llama.cpp (Native)
if [ -z "$SPECIFIC_PROVIDER" ] || [ "$SPECIFIC_PROVIDER" = "llama_cpp_native" ]; then
    echo ""
    echo "========================================"
    echo "Testing llama.cpp Native Provider"
    echo "========================================"

    test_provider_health "llama.cpp-native" "http://localhost:8080/v1/models" 200
    test_models_endpoint "llama.cpp-native" "http://localhost:8080/v1/models"
    test_response_time "llama.cpp-native" "http://localhost:8080/v1/models" 500
    test_llamacpp_features 8080
fi

# Test vLLM
if [ -z "$SPECIFIC_PROVIDER" ] || [ "$SPECIFIC_PROVIDER" = "vllm" ]; then
    echo ""
    echo "========================================"
    echo "Testing vLLM Provider"
    echo "========================================"

    test_provider_health "vLLM" "http://localhost:8001/v1/models" 200
    test_models_endpoint "vLLM" "http://localhost:8001/v1/models"
    test_response_time "vLLM" "http://localhost:8001/v1/models" 2000
    test_vllm_features
fi

# Test LiteLLM Gateway
if [ -z "$SPECIFIC_PROVIDER" ] || [ "$SPECIFIC_PROVIDER" = "litellm" ]; then
    echo ""
    echo "========================================"
    echo "Testing LiteLLM Gateway"
    echo "========================================"

    test_provider_health "LiteLLM" "http://localhost:4000/health" 200
    test_models_endpoint "LiteLLM" "http://localhost:4000/v1/models"
    test_response_time "LiteLLM" "http://localhost:4000/v1/models" 1000
fi

# Summary
echo ""
echo "================================"
echo "Test Summary"
echo "================================"
echo "Total tests run: $TESTS_RUN"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All contract tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some contract tests failed${NC}"
    exit 1
fi
