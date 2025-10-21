#!/bin/bash
# Validate LiteLLM observability stack setup
# Checks all Phase 2 components: monitoring, debugging, profiling, load testing

set -e

echo "==========================================================================="
echo "🔍 LiteLLM Observability Stack Validation"
echo "==========================================================================="
echo ""

ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

# =============================================================================
# 1. CONFIGURATION VALIDATION
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Configuration Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check litellm-unified.yaml exists and is valid
if [ -f "config/litellm-unified.yaml" ]; then
    check_pass "litellm-unified.yaml exists"

    # Validate YAML syntax
    if python3 -c "import yaml; yaml.safe_load(open('config/litellm-unified.yaml'))" 2>/dev/null; then
        check_pass "litellm-unified.yaml syntax valid"
    else
        check_fail "litellm-unified.yaml syntax invalid"
    fi

    # Check for observability settings
    if grep -q "litellm_settings:" config/litellm-unified.yaml; then
        check_pass "litellm_settings configured"
    else
        check_fail "litellm_settings missing"
    fi

    # Check Prometheus configuration
    if grep -q "callbacks:.*prometheus" config/litellm-unified.yaml; then
        check_pass "Prometheus callbacks configured"
    else
        check_warn "Prometheus callbacks not configured"
    fi

    # Check logging configuration
    if grep -q "logging:" config/litellm-unified.yaml; then
        check_pass "Logging configured"
    else
        check_warn "Logging configuration missing"
    fi

    # Check tracing configuration
    if grep -q "tracing:" config/litellm-unified.yaml; then
        check_pass "Request tracing configured"
    else
        check_warn "Request tracing not configured"
    fi
else
    check_fail "config/litellm-unified.yaml not found"
fi

echo ""

# =============================================================================
# 2. MONITORING STACK
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Monitoring Stack"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check docker-compose.yml
if [ -f "monitoring/docker-compose.yml" ]; then
    check_pass "docker-compose.yml exists"
else
    check_fail "monitoring/docker-compose.yml not found"
fi

# Check Prometheus configuration
if [ -f "monitoring/prometheus/prometheus.yml" ]; then
    check_pass "Prometheus config exists"
else
    check_fail "monitoring/prometheus/prometheus.yml not found"
fi

# Check Grafana datasource
if [ -f "monitoring/grafana/datasources/prometheus.yml" ]; then
    check_pass "Grafana datasource config exists"
else
    check_fail "monitoring/grafana/datasources/prometheus.yml not found"
fi

# Check Grafana dashboard provisioning
if [ -f "monitoring/grafana/dashboards/dashboards.yml" ]; then
    check_pass "Grafana dashboard provisioning exists"
else
    check_fail "monitoring/grafana/dashboards/dashboards.yml not found"
fi

# Check all 5 Grafana dashboards
DASHBOARDS=("01-overview" "02-tokens" "03-performance" "04-provider-health" "05-system-health")
MISSING_DASHBOARDS=0

for dashboard in "${DASHBOARDS[@]}"; do
    if [ -f "monitoring/grafana/dashboards/${dashboard}.json" ]; then
        # Validate JSON syntax
        if python3 -c "import json; json.load(open('monitoring/grafana/dashboards/${dashboard}.json'))" 2>/dev/null; then
            check_pass "Dashboard: ${dashboard}.json valid"
        else
            check_fail "Dashboard: ${dashboard}.json invalid JSON"
        fi
    else
        check_fail "Dashboard: ${dashboard}.json missing"
        ((MISSING_DASHBOARDS++))
    fi
done

if [ $MISSING_DASHBOARDS -eq 0 ]; then
    check_pass "All 5 Grafana dashboards present"
fi

echo ""

# =============================================================================
# 3. DEBUGGING TOOLS
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐛 Debugging Tools"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DEBUG_TOOLS=("analyze-logs.py" "tail-requests.py" "test-request.py")
for tool in "${DEBUG_TOOLS[@]}"; do
    if [ -f "scripts/debugging/${tool}" ]; then
        if [ -x "scripts/debugging/${tool}" ]; then
            check_pass "${tool} exists and executable"
        else
            check_warn "${tool} exists but not executable"
        fi

        # Check Python syntax
        if python3 -m py_compile "scripts/debugging/${tool}" 2>/dev/null; then
            check_pass "${tool} Python syntax valid"
        else
            check_fail "${tool} Python syntax errors"
        fi
    else
        check_fail "scripts/debugging/${tool} not found"
    fi
done

# Check README
if [ -f "scripts/debugging/README.md" ]; then
    check_pass "Debugging tools documentation exists"
else
    check_warn "scripts/debugging/README.md missing"
fi

echo ""

# =============================================================================
# 4. PROFILING TOOLS
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚡ Profiling Tools"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PROFILING_TOOLS=("profile-latency.py" "profile-throughput.py" "compare-providers.py")
for tool in "${PROFILING_TOOLS[@]}"; do
    if [ -f "scripts/profiling/${tool}" ]; then
        if [ -x "scripts/profiling/${tool}" ]; then
            check_pass "${tool} exists and executable"
        else
            check_warn "${tool} exists but not executable"
        fi

        # Check Python syntax
        if python3 -m py_compile "scripts/profiling/${tool}" 2>/dev/null; then
            check_pass "${tool} Python syntax valid"
        else
            check_fail "${tool} Python syntax errors"
        fi
    else
        check_fail "scripts/profiling/${tool} not found"
    fi
done

# Check README
if [ -f "scripts/profiling/README.md" ]; then
    check_pass "Profiling tools documentation exists"
else
    check_warn "scripts/profiling/README.md missing"
fi

echo ""

# =============================================================================
# 5. LOAD TESTING
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Load Testing Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Locust file
if [ -f "scripts/loadtesting/locust/litellm_locustfile.py" ]; then
    check_pass "Locust test file exists"

    # Check Python syntax
    if python3 -m py_compile "scripts/loadtesting/locust/litellm_locustfile.py" 2>/dev/null; then
        check_pass "Locust file Python syntax valid"
    else
        check_fail "Locust file Python syntax errors"
    fi
else
    check_fail "scripts/loadtesting/locust/litellm_locustfile.py not found"
fi

# Check k6 files
K6_TESTS=("litellm-load-test.js" "smoke-test.js")
for test in "${K6_TESTS[@]}"; do
    if [ -f "scripts/loadtesting/k6/${test}" ]; then
        check_pass "k6 test: ${test} exists"

        # Basic JavaScript syntax check (check for common errors)
        if grep -q "export default function" "scripts/loadtesting/k6/${test}"; then
            check_pass "${test} has k6 structure"
        else
            check_warn "${test} may be missing k6 structure"
        fi
    else
        check_fail "scripts/loadtesting/k6/${test} not found"
    fi
done

# Check README
if [ -f "scripts/loadtesting/README.md" ]; then
    check_pass "Load testing documentation exists"
else
    check_warn "scripts/loadtesting/README.md missing"
fi

echo ""

# =============================================================================
# 6. DOCUMENTATION
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "docs/observability.md" ]; then
    check_pass "Observability guide exists"

    # Check for key sections
    if grep -q "## Monitoring Stack" docs/observability.md; then
        check_pass "Monitoring Stack section present"
    fi

    if grep -q "## Debugging Tools" docs/observability.md; then
        check_pass "Debugging Tools section present"
    fi

    if grep -q "## Performance Profiling" docs/observability.md; then
        check_pass "Performance Profiling section present"
    fi

    if grep -q "## Load Testing" docs/observability.md; then
        check_pass "Load Testing section present"
    fi
else
    check_fail "docs/observability.md not found"
fi

echo ""

# =============================================================================
# 7. DEPENDENCY CHECKS
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    check_pass "Python: $PYTHON_VERSION"
else
    check_fail "Python 3 not installed"
fi

# Check Docker (for monitoring stack)
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    check_pass "Docker: $DOCKER_VERSION"
else
    check_warn "Docker not installed (required for monitoring stack)"
fi

# Check docker-compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    check_pass "docker-compose: $COMPOSE_VERSION"
else
    check_warn "docker-compose not installed (required for monitoring stack)"
fi

# Check Python packages (optional)
if python3 -c "import requests" 2>/dev/null; then
    check_pass "Python 'requests' package installed"
else
    check_warn "Python 'requests' not installed (required for some tools)"
fi

if python3 -c "import locust" 2>/dev/null; then
    check_pass "Locust installed"
else
    check_warn "Locust not installed (optional for load testing)"
fi

# Check k6 (optional)
if command -v k6 &> /dev/null; then
    K6_VERSION=$(k6 version)
    check_pass "k6: $K6_VERSION"
else
    check_warn "k6 not installed (optional for load testing)"
fi

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo "==========================================================================="
echo "📊 Validation Summary"
echo "==========================================================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED!${NC}"
    echo ""
    echo "The observability stack is fully configured and ready to use."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  PASSED WITH WARNINGS${NC}"
    echo ""
    echo "Warnings: $WARNINGS"
    echo ""
    echo "The observability stack is functional but has optional components missing."
    echo "Review warnings above for recommendations."
    exit 0
else
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo ""
    echo "Errors: $ERRORS"
    echo "Warnings: $WARNINGS"
    echo ""
    echo "Critical issues found. Please fix the errors above before using the observability stack."
    exit 1
fi
