#!/usr/bin/env bash
#
# Smoke Test - Quick health check for AI Backend Infrastructure
# Tests critical services in under 10 seconds
#
# Usage:
#   ./scripts/smoke-test.sh              # Run all checks
#   ./scripts/smoke-test.sh --verbose    # Show detailed output
#
# Exit codes:
#   0: All services healthy
#   1: One or more services failed

set -euo pipefail

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Flags
VERBOSE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--verbose]"
            echo ""
            echo "Quick smoke test for AI Backend Infrastructure"
            echo ""
            echo "Options:"
            echo "  -v, --verbose    Show detailed output"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# Test results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

log_test() {
    local test_name=$1
    local status=$2
    local message=$3

    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ "$status" == "pass" ]]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓${NC} $test_name"
        [[ "$VERBOSE" == "true" ]] && echo "  → $message"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} $test_name"
        echo -e "  ${RED}→ $message${NC}"
    fi
}

# ============================================================================
# SMOKE TESTS
# ============================================================================

echo "🔥 AI Backend Smoke Test"
echo "========================"
echo ""

# Test 1: LiteLLM Gateway
if curl -sf --max-time 5 http://localhost:4000/health > /dev/null 2>&1; then
    log_test "LiteLLM Gateway (port 4000)" "pass" "Responding to health checks"
else
    log_test "LiteLLM Gateway (port 4000)" "fail" "Not responding - check systemctl --user status litellm.service"
fi

# Test 2: Ollama
if curl -sf --max-time 5 http://localhost:11434/api/tags > /dev/null 2>&1; then
    model_count=$(curl -s http://localhost:11434/api/tags 2>/dev/null | grep -c '"name"' || echo 0)
    log_test "Ollama (port 11434)" "pass" "$model_count models available"
else
    log_test "Ollama (port 11434)" "fail" "Not responding - check systemctl --user status ollama.service"
fi

# Test 3: Redis Cache
if command -v redis-cli &> /dev/null; then
    if redis-cli -h 127.0.0.1 -p 6379 ping > /dev/null 2>&1; then
        cache_keys=$(redis-cli --scan --pattern "litellm:*" 2>/dev/null | wc -l)
        log_test "Redis Cache (port 6379)" "pass" "$cache_keys LiteLLM cache keys"
    else
        log_test "Redis Cache (port 6379)" "fail" "Not responding - check systemctl status redis"
    fi
else
    log_test "Redis Cache (port 6379)" "skip" "redis-cli not installed"
fi

# Test 4: Configuration Files
config_valid=true
for config_file in config/providers.yaml config/model-mappings.yaml config/litellm-unified.yaml; do
    if [[ ! -f "$config_file" ]]; then
        config_valid=false
        break
    fi
    if ! python3 -c "import yaml; yaml.safe_load(open('$config_file'))" 2>/dev/null; then
        config_valid=false
        break
    fi
done

if [[ "$config_valid" == "true" ]]; then
    log_test "Configuration Files" "pass" "All config files present and valid YAML"
else
    log_test "Configuration Files" "fail" "Invalid or missing configuration files"
fi

# Test 5: LiteLLM API Endpoint
if curl -sf --max-time 5 http://localhost:4000/v1/models > /dev/null 2>&1; then
    model_count=$(curl -s http://localhost:4000/v1/models 2>/dev/null | grep -o '"id"' | wc -l)
    log_test "LiteLLM Models Endpoint" "pass" "$model_count models registered"
else
    log_test "LiteLLM Models Endpoint" "fail" "Cannot fetch model list"
fi

# Test 6: vLLM (optional - may not always be running)
if curl -sf --max-time 3 http://localhost:8001/v1/models > /dev/null 2>&1; then
    vllm_model=$(curl -s http://localhost:8001/v1/models 2>/dev/null | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    log_test "vLLM (port 8001) [optional]" "pass" "Running: $vllm_model"
elif [[ "$VERBOSE" == "true" ]]; then
    log_test "vLLM (port 8001) [optional]" "skip" "Not running (optional service)"
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "========================"
echo "Summary"
echo "========================"
echo "Tests run:    $TESTS_RUN"
echo -e "Passed:       ${GREEN}$TESTS_PASSED${NC}"

if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "Failed:       ${RED}$TESTS_FAILED${NC}"
    echo ""
    echo -e "${RED}✗ Smoke test FAILED${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Check service status: systemctl --user status litellm.service ollama.service"
    echo "  2. Check logs: journalctl --user -u litellm.service -f"
    echo "  3. Run full validation: ./scripts/validate-all-configs.sh"
    exit 1
else
    echo ""
    echo -e "${GREEN}✓ All smoke tests PASSED${NC}"
    echo ""
    echo "System is healthy and ready to use!"
    exit 0
fi
