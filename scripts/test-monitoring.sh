#!/bin/bash
# =============================================================================
# Test Monitoring Stack with Playwright
# =============================================================================
#
# Validates Grafana dashboard is configured and accessible using Playwright
# browser automation.
#
# Prerequisites:
#   - Grafana running on :3000
#   - Prometheus running on :9090
#   - Dashboard imported in Grafana
#
# Usage:
#   ./scripts/test-monitoring.sh [--install] [--headed]
#
# Options:
#   --install: Install playwright browsers first
#   --headed:  Run browser in headed mode (visible)
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Parse arguments
INSTALL_BROWSERS=false
HEADED=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --install)
            INSTALL_BROWSERS=true
            shift
            ;;
        --headed)
            HEADED=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

cd "$PROJECT_ROOT"

print_header "Monitoring Stack Test with Playwright"

# Check prerequisites
print_info "Checking prerequisites..."

# Check if Grafana is running
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    print_success "Grafana is running on :3000"
else
    print_error "Grafana is not accessible on :3000"
    print_info "Start Grafana: systemctl --user start grafana"
    exit 1
fi

# Check if Prometheus is running
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    print_success "Prometheus is running on :9090"
else
    print_error "Prometheus is not accessible on :9090"
    print_info "Start Prometheus: systemctl --user start prometheus"
    exit 1
fi

# Check Python dependencies
print_info "Checking Python dependencies..."

if ! python3 -c "import pytest" 2>/dev/null; then
    print_error "pytest not installed"
    print_info "Install with: pip install -r requirements.txt"
    exit 1
fi

if ! python3 -c "import playwright" 2>/dev/null; then
    print_error "playwright not installed"
    print_info "Install with: pip install -r requirements.txt"
    exit 1
fi

print_success "Python dependencies installed"

# Install Playwright browsers if requested
if [ "$INSTALL_BROWSERS" = true ]; then
    print_info "Installing Playwright browsers..."
    python3 -m playwright install chromium
    print_success "Playwright browsers installed"
fi

# Check if browsers are installed
if ! python3 -m playwright install --dry-run chromium > /dev/null 2>&1; then
    print_error "Playwright browsers not installed"
    print_info "Install with: ./scripts/test-monitoring.sh --install"
    exit 1
fi

# Run tests
print_header "Running Monitoring Tests"

PYTEST_ARGS="-v -s tests/monitoring/test_grafana_dashboard.py"

if [ "$HEADED" = true ]; then
    print_info "Running in headed mode (browser visible)..."
    PLAYWRIGHT_HEADED=1 pytest $PYTEST_ARGS
else
    print_info "Running in headless mode..."
    pytest $PYTEST_ARGS
fi

TEST_EXIT_CODE=$?

# Show results
echo
print_header "Test Results"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "All monitoring tests passed!"
    echo
    print_info "Screenshots saved to: tests/monitoring/screenshots/"
    echo
    print_info "You can view the dashboard at: http://localhost:3000"
else
    print_error "Some tests failed (exit code: $TEST_EXIT_CODE)"
    echo
    print_info "Check the output above for details"
    print_info "Screenshots may help debug: tests/monitoring/screenshots/"
fi

exit $TEST_EXIT_CODE
