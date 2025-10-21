#!/usr/bin/env bash
#
# Comprehensive Validation Script
# Single command to validate entire AI backend configuration
#
# Usage:
#   ./scripts/validate-all-configs.sh              # Run all checks
#   ./scripts/validate-all-configs.sh --json       # JSON output for CI/CD
#   ./scripts/validate-all-configs.sh --critical   # Critical checks only
#

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Flags
JSON_OUTPUT=false
CRITICAL_ONLY=false

# Results tracking
declare -A results
total_checks=0
passed_checks=0
failed_checks=0
warnings=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --critical)
            CRITICAL_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--json] [--critical]"
            echo ""
            echo "Options:"
            echo "  --json      Output in JSON format for CI/CD"
            echo "  --critical  Run only critical checks (ports, reachability, Redis)"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            exit 1
            ;;
    esac
done

log_info() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${GREEN}[INFO]${NC} $1"
    fi
}

log_success() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${GREEN}[✓]${NC} $1"
    fi
}

log_warn() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${YELLOW}[WARN]${NC} $1"
    fi
}

log_error() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${RED}[ERROR]${NC} $1"
    fi
}

record_result() {
    local check_name=$1
    local status=$2  # "pass", "fail", "warn"
    local message=$3

    results["$check_name"]="$status:$message"
    total_checks=$((total_checks + 1))

    case $status in
        pass)
            passed_checks=$((passed_checks + 1))
            ;;
        fail)
            failed_checks=$((failed_checks + 1))
            ;;
        warn)
            warnings=$((warnings + 1))
            ;;
    esac
}

# ============================================================================
# CHECK 1: YAML Syntax Validation
# ============================================================================

check_yaml_syntax() {
    if [[ "$CRITICAL_ONLY" == "true" ]]; then
        return 0
    fi

    log_info "Check 1/7: YAML syntax validation"

    local configs=(
        "$PROJECT_ROOT/config/providers.yaml"
        "$PROJECT_ROOT/config/model-mappings.yaml"
        "$PROJECT_ROOT/config/litellm-unified.yaml"
        "$PROJECT_ROOT/config/ports.yaml"
    )

    local all_valid=true

    for config in "${configs[@]}"; do
        if [[ ! -f "$config" ]]; then
            log_error "  Config not found: $(basename $config)"
            record_result "yaml_syntax_$(basename $config)" "fail" "File not found"
            all_valid=false
            continue
        fi

        if python3 -c "import yaml; yaml.safe_load(open('$config'))" 2>/dev/null; then
            log_success "  $(basename $config) - valid"
            record_result "yaml_syntax_$(basename $config)" "pass" "Valid YAML"
        else
            log_error "  $(basename $config) - INVALID"
            record_result "yaml_syntax_$(basename $config)" "fail" "Invalid YAML syntax"
            all_valid=false
        fi
    done

    if [[ "$all_valid" == "true" ]]; then
        log_success "All YAML configs valid"
    else
        log_error "Some YAML configs invalid"
    fi

    echo ""
}

# ============================================================================
# CHECK 2: Model ID Consistency
# ============================================================================

check_model_consistency() {
    if [[ "$CRITICAL_ONLY" == "true" ]]; then
        return 0
    fi

    log_info "Check 2/7: Model ID consistency"

    if [[ -f "$SCRIPT_DIR/validate-config-consistency.py" ]]; then
        if python3 "$SCRIPT_DIR/validate-config-consistency.py" > /dev/null 2>&1; then
            log_success "Model consistency valid"
            record_result "model_consistency" "pass" "All models consistent"
        else
            # Check if it's warnings only or actual errors
            local output=$(python3 "$SCRIPT_DIR/validate-config-consistency.py" 2>&1)
            if echo "$output" | grep -q "0 errors"; then
                log_warn "Model consistency has warnings (non-critical)"
                record_result "model_consistency" "warn" "Warnings present but no errors"
            else
                log_error "Model consistency check failed"
                record_result "model_consistency" "fail" "Consistency errors detected"
            fi
        fi
    else
        log_warn "Consistency validator not found"
        record_result "model_consistency" "warn" "Validator script missing"
    fi

    echo ""
}

# ============================================================================
# CHECK 3: Port Availability
# ============================================================================

check_port_availability() {
    log_info "Check 3/7: Port availability (required ports)"

    if [[ -f "$SCRIPT_DIR/check-port-conflicts.sh" ]]; then
        # Check required ports only for comprehensive check
        # This will show which ports are in use (expected for running services)
        local output=$("$SCRIPT_DIR/check-port-conflicts.sh" --required 2>&1 || true)

        # Count conflicts (expected conflicts are running services)
        local conflicts=$(echo "$output" | grep -c "IN USE" || true)

        if [[ $conflicts -eq 0 ]]; then
            log_warn "No ports in use - services may not be running"
            record_result "port_availability" "warn" "No ports in use"
        else
            log_success "Port check complete - $conflicts ports in use (expected for running services)"
            record_result "port_availability" "pass" "$conflicts ports allocated to services"
        fi
    else
        log_warn "Port conflict checker not found"
        record_result "port_availability" "warn" "Port checker script missing"
    fi

    echo ""
}

# ============================================================================
# CHECK 4: Provider Reachability
# ============================================================================

check_provider_reachability() {
    log_info "Check 4/7: Provider reachability"

    local providers_healthy=0
    local providers_down=0

    # LiteLLM Gateway (most critical)
    if curl -sf http://localhost:4000/health > /dev/null 2>&1; then
        log_success "  LiteLLM Gateway (4000) - responding"
        providers_healthy=$((providers_healthy + 1))
    else
        log_error "  LiteLLM Gateway (4000) - NOT responding"
        providers_down=$((providers_down + 1))
        record_result "provider_litellm" "fail" "Gateway not responding"
    fi

    # Ollama
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        log_success "  Ollama (11434) - responding"
        providers_healthy=$((providers_healthy + 1))
    else
        log_warn "  Ollama (11434) - not responding"
        providers_down=$((providers_down + 1))
        record_result "provider_ollama" "warn" "Ollama not responding"
    fi

    # vLLM
    if curl -sf http://localhost:8001/v1/models > /dev/null 2>&1; then
        log_success "  vLLM (8001) - responding"
        providers_healthy=$((providers_healthy + 1))
    else
        log_warn "  vLLM (8001) - not responding"
        providers_down=$((providers_down + 1))
        record_result "provider_vllm" "warn" "vLLM not responding"
    fi

    if [[ $providers_healthy -gt 0 ]]; then
        log_success "Provider check: $providers_healthy healthy, $providers_down down"
        if [[ $providers_healthy -eq 1 ]]; then
            record_result "provider_reachability" "pass" "LiteLLM gateway responding"
        else
            record_result "provider_reachability" "pass" "$providers_healthy providers healthy"
        fi
    else
        log_error "All providers down"
        record_result "provider_reachability" "fail" "No providers responding"
    fi

    echo ""
}

# ============================================================================
# CHECK 5: Redis Connectivity
# ============================================================================

check_redis_connectivity() {
    log_info "Check 5/7: Redis connectivity"

    if command -v redis-cli &> /dev/null; then
        if redis-cli -h 127.0.0.1 -p 6379 ping > /dev/null 2>&1; then
            log_success "Redis (6379) - responding"

            # Check cache namespace
            local cache_keys=$(redis-cli --scan --pattern "litellm:*" 2>/dev/null | wc -l)
            log_info "  LiteLLM cache keys: $cache_keys"
            record_result "redis_connectivity" "pass" "Redis responding with $cache_keys cache keys"
        else
            log_error "Redis (6379) - not responding"
            record_result "redis_connectivity" "fail" "Redis not responding"
        fi
    else
        log_warn "redis-cli not available - cannot check Redis"
        record_result "redis_connectivity" "warn" "redis-cli not installed"
    fi

    echo ""
}

# ============================================================================
# CHECK 6: Configuration Schema Compliance
# ============================================================================

check_schema_compliance() {
    if [[ "$CRITICAL_ONLY" == "true" ]]; then
        return 0
    fi

    log_info "Check 6/7: Configuration schema compliance"

    # Check required fields in litellm-unified.yaml
    local config="$PROJECT_ROOT/config/litellm-unified.yaml"

    if [[ ! -f "$config" ]]; then
        log_error "litellm-unified.yaml not found"
        record_result "schema_compliance" "fail" "Config file missing"
        echo ""
        return
    fi

    local all_fields_present=true

    # Check for model_list
    if grep -q "model_list:" "$config"; then
        log_success "  model_list: present"
    else
        log_error "  model_list: MISSING"
        all_fields_present=false
    fi

    # Check for litellm_settings
    if grep -q "litellm_settings:" "$config"; then
        log_success "  litellm_settings: present"
    else
        log_error "  litellm_settings: MISSING"
        all_fields_present=false
    fi

    # Check for router_settings
    if grep -q "router_settings:" "$config"; then
        log_success "  router_settings: present"
    else
        log_error "  router_settings: MISSING"
        all_fields_present=false
    fi

    if [[ "$all_fields_present" == "true" ]]; then
        record_result "schema_compliance" "pass" "All required fields present"
    else
        record_result "schema_compliance" "fail" "Missing required fields"
    fi

    echo ""
}

# ============================================================================
# CHECK 7: Backup Integrity
# ============================================================================

check_backup_integrity() {
    if [[ "$CRITICAL_ONLY" == "true" ]]; then
        return 0
    fi

    log_info "Check 7/7: Backup integrity"

    if [[ -f "$SCRIPT_DIR/verify-backup.sh" ]]; then
        # Check latest backup
        if "$SCRIPT_DIR/verify-backup.sh" > /dev/null 2>&1; then
            log_success "Latest backup verified"
            record_result "backup_integrity" "pass" "Latest backup valid"
        else
            log_warn "Backup verification failed or no backups found"
            record_result "backup_integrity" "warn" "No valid backups or verification failed"
        fi
    else
        log_warn "Backup verification script not found"
        record_result "backup_integrity" "warn" "Verifier script missing"
    fi

    echo ""
}

# ============================================================================
# Output Functions
# ============================================================================

output_summary() {
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        output_json
    else
        output_text
    fi
}

output_text() {
    echo -e "${BLUE}=== Validation Summary ===${NC}"
    echo ""
    echo "Total checks:  $total_checks"
    echo -e "${GREEN}Passed:        $passed_checks${NC}"
    if [[ $warnings -gt 0 ]]; then
        echo -e "${YELLOW}Warnings:      $warnings${NC}"
    fi
    if [[ $failed_checks -gt 0 ]]; then
        echo -e "${RED}Failed:        $failed_checks${NC}"
    fi
    echo ""

    if [[ $failed_checks -eq 0 ]]; then
        if [[ $warnings -gt 0 ]]; then
            echo -e "${YELLOW}✓ Validation passed with warnings${NC}"
            exit 0
        else
            echo -e "${GREEN}✓ All validation checks passed${NC}"
            exit 0
        fi
    else
        echo -e "${RED}✗ Validation failed - $failed_checks check(s) failed${NC}"
        exit 1
    fi
}

output_json() {
    echo "{"
    echo "  \"summary\": {"
    echo "    \"total\": $total_checks,"
    echo "    \"passed\": $passed_checks,"
    echo "    \"failed\": $failed_checks,"
    echo "    \"warnings\": $warnings"
    echo "  },"
    echo "  \"checks\": {"

    local first=true
    for check_name in "${!results[@]}"; do
        local result="${results[$check_name]}"
        local status="${result%%:*}"
        local message="${result#*:}"

        if [[ "$first" != "true" ]]; then
            echo ","
        fi
        first=false

        echo -n "    \"$check_name\": {\"status\": \"$status\", \"message\": \"$message\"}"
    done

    echo ""
    echo "  }"
    echo "}"

    if [[ $failed_checks -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo -e "${BLUE}=== AI Backend Unified - Comprehensive Validation ===${NC}"
        echo ""
    fi

    # Run all checks
    check_yaml_syntax
    check_model_consistency
    check_port_availability
    check_provider_reachability
    check_redis_connectivity
    check_schema_compliance
    check_backup_integrity

    # Output results
    output_summary
}

main
