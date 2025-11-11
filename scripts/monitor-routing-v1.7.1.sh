#!/usr/bin/env bash
# ============================================================================
# Routing v1.7.1 Monitoring Script
# ============================================================================
#
# Monitors key metrics for routing v1.7.1 deployment:
# - Provider distribution
# - Availability metrics
# - TTFB performance (Time To First Byte)
#
# Usage:
#   ./scripts/monitor-routing-v1.7.1.sh [--watch] [--duration HOURS]
#
# ============================================================================

set -euo pipefail

# Configuration
LITELLM_URL="${LITELLM_URL:-http://localhost:4000}"
MONITORING_INTERVAL="${MONITORING_INTERVAL:-60}"  # seconds
WATCH_MODE="${1:-}"
DURATION_HOURS="${2:-24}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Check dependencies
check_dependencies() {
    local missing=()

    for cmd in curl jq bc; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Install with: sudo apt-get install ${missing[*]}"
        exit 1
    fi
}

# Test provider connectivity
test_provider() {
    local provider_name="$1"
    local provider_url="$2"
    local start_time
    local end_time
    local ttfb

    start_time=$(date +%s%3N)  # milliseconds

    if curl -s -m 5 "$provider_url/v1/models" > /dev/null 2>&1; then
        end_time=$(date +%s%3N)
        ttfb=$((end_time - start_time))
        echo "$ttfb"
        return 0
    else
        echo "-1"
        return 1
    fi
}

# Get provider statistics from LiteLLM
get_provider_stats() {
    log_info "Fetching provider distribution..."

    # Check if metrics endpoint is available
    if curl -s -m 5 "$LITELLM_URL/metrics" > /dev/null 2>&1; then
        log_success "Metrics endpoint available"
        curl -s "$LITELLM_URL/metrics" | grep "litellm_requests_" || true
    else
        log_warn "Metrics endpoint not available (Prometheus callbacks disabled)"
        log_info "Provider distribution will be estimated from direct tests"
    fi
}

# Test TTFB for all providers
test_all_providers_ttfb() {
    log_info "Testing TTFB for all providers..."

    echo -e "\n${BLUE}Provider${NC} | ${BLUE}Port${NC} | ${BLUE}Status${NC} | ${BLUE}TTFB (ms)${NC}"
    echo "---------|------|--------|----------"

    # Ollama
    ttfb=$(test_provider "Ollama" "http://localhost:11434")
    if [ "$ttfb" != "-1" ]; then
        echo -e "Ollama   | 11434 | ${GREEN}UP${NC}     | $ttfb"
    else
        echo -e "Ollama   | 11434 | ${RED}DOWN${NC}   | N/A"
    fi

    # llama.cpp Python
    ttfb=$(test_provider "llama_cpp_python" "http://localhost:8000")
    if [ "$ttfb" != "-1" ]; then
        echo -e "llama.cpp (Python) | 8000 | ${GREEN}UP${NC}     | $ttfb"
    else
        echo -e "llama.cpp (Python) | 8000 | ${RED}DOWN${NC}   | N/A"
    fi

    # llama.cpp Native
    ttfb=$(test_provider "llama_cpp_native" "http://localhost:8080")
    if [ "$ttfb" != "-1" ]; then
        echo -e "llama.cpp (Native) | 8080 | ${GREEN}UP${NC}     | $ttfb"
    else
        echo -e "llama.cpp (Native) | 8080 | ${YELLOW}DOWN${NC}   | N/A (optional)"
    fi

    # vLLM
    ttfb=$(test_provider "vLLM" "http://localhost:8001")
    if [ "$ttfb" != "-1" ]; then
        echo -e "vLLM     | 8001 | ${GREEN}UP${NC}     | $ttfb"
    else
        echo -e "vLLM     | 8001 | ${YELLOW}DOWN${NC}   | N/A (optional)"
    fi

    echo ""
}

# Calculate availability estimate
calculate_availability() {
    log_info "Calculating system availability..."

    local ollama_up=false
    local llamacpp_up=false
    local cloud_available=true  # Assume cloud is available

    # Test Ollama
    if test_provider "Ollama" "http://localhost:11434" > /dev/null 2>&1; then
        ollama_up=true
    fi

    # Test llama.cpp (either Python or Native)
    if test_provider "llama_cpp_python" "http://localhost:8000" > /dev/null 2>&1 || \
       test_provider "llama_cpp_native" "http://localhost:8080" > /dev/null 2>&1; then
        llamacpp_up=true
    fi

    # Calculate current availability
    if $ollama_up && $llamacpp_up; then
        log_success "All local providers UP - Maximum availability"
        echo -e "  ${GREEN}Estimated availability: 99.9999% (6 nines)${NC}"
    elif $ollama_up || $llamacpp_up; then
        log_warn "One local provider DOWN - Degraded mode"
        echo -e "  ${YELLOW}Estimated availability: 99.99% (4 nines)${NC}"
    else
        log_error "All local providers DOWN - Cloud-only mode"
        echo -e "  ${YELLOW}Estimated availability: 99.9% (3 nines, cloud only)${NC}"
    fi

    echo ""
}

# Main monitoring function
run_monitoring() {
    clear
    echo "========================================"
    echo "Routing v1.7.1 Monitoring Dashboard"
    echo "========================================"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Duration: $DURATION_HOURS hours"
    echo ""

    # Provider connectivity
    test_all_providers_ttfb

    # Availability calculation
    calculate_availability

    # Provider stats from LiteLLM
    get_provider_stats

    echo "========================================"
    echo "Monitoring Targets (from implementation):"
    echo "  • Provider distribution: 40% llama_cpp utilization"
    echo "  • Availability: >99.999%"
    echo "  • TTFB improvement: llama_cpp should improve P95"
    echo "========================================"
}

# Watch mode
run_watch_mode() {
    log_info "Starting watch mode (refresh every ${MONITORING_INTERVAL}s)"
    log_info "Press Ctrl+C to stop"
    echo ""

    local start_time
    local elapsed_seconds
    local elapsed_hours

    start_time=$(date +%s)

    while true; do
        run_monitoring

        # Calculate elapsed time
        elapsed_seconds=$(($(date +%s) - start_time))
        elapsed_hours=$(echo "scale=2; $elapsed_seconds / 3600" | bc)

        echo ""
        echo "Elapsed: ${elapsed_hours}h / ${DURATION_HOURS}h"

        # Check if duration exceeded
        if (( $(echo "$elapsed_hours >= $DURATION_HOURS" | bc -l) )); then
            log_success "Monitoring duration of ${DURATION_HOURS} hours completed"
            break
        fi

        echo "Next refresh in ${MONITORING_INTERVAL}s..."
        sleep "$MONITORING_INTERVAL"
    done
}

# Main execution
main() {
    check_dependencies

    if [ "$WATCH_MODE" = "--watch" ]; then
        if [ "${2:-}" != "" ]; then
            DURATION_HOURS="$2"
        fi
        run_watch_mode
    else
        run_monitoring

        echo ""
        log_info "Run with '--watch' for continuous monitoring:"
        log_info "  ./scripts/monitor-routing-v1.7.1.sh --watch 24"
    fi
}

main "$@"
