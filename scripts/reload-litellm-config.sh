#!/usr/bin/env bash
#
# LiteLLM Configuration Hot-Reload Script
# Safely reloads LiteLLM configuration with validation and rollback capability
#
# Usage:
#   ./scripts/reload-litellm-config.sh [--validate-only] [--force]
#
# Options:
#   --validate-only   Only validate config without reloading
#   --force          Skip confirmation prompts
#

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly SOURCE_CONFIG="$PROJECT_ROOT/config/litellm-unified.yaml"
readonly DEPLOY_CONFIG="/home/miko/LAB/ai/services/openwebui/config/litellm.yaml"
readonly BACKUP_DIR="/home/miko/LAB/ai/services/openwebui/config/backups"
readonly SERVICE_NAME="litellm.service"
readonly HEALTH_ENDPOINT="http://localhost:4000/health"
readonly MODELS_ENDPOINT="http://localhost:4000/v1/models"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Flags
VALIDATE_ONLY=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--validate-only] [--force]"
            echo ""
            echo "Options:"
            echo "  --validate-only   Only validate config without reloading"
            echo "  --force          Skip confirmation prompts"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validation functions
validate_yaml_syntax() {
    local config_file=$1
    log_info "Validating YAML syntax: $config_file"

    if ! python3 -c "import yaml; yaml.safe_load(open('$config_file'))" 2>/dev/null; then
        log_error "YAML syntax validation failed"
        return 1
    fi

    log_info "✓ YAML syntax valid"
    return 0
}

validate_model_consistency() {
    local config_file=$1
    log_info "Validating model ID consistency"

    # Check if validation script exists
    if [[ ! -f "$SCRIPT_DIR/validate-config-schema.py" ]]; then
        log_warn "Consistency validator not found, skipping"
        return 0
    fi

    if ! python3 "$SCRIPT_DIR/validate-config-schema.py" "$config_file" 2>/dev/null; then
        log_error "Model consistency validation failed"
        return 1
    fi

    log_info "✓ Model consistency valid"
    return 0
}

validate_required_fields() {
    local config_file=$1
    log_info "Validating required configuration fields"

    # Check for model_list
    if ! grep -q "model_list:" "$config_file"; then
        log_error "Missing required field: model_list"
        return 1
    fi

    # Check for litellm_settings
    if ! grep -q "litellm_settings:" "$config_file"; then
        log_error "Missing required field: litellm_settings"
        return 1
    fi

    log_info "✓ Required fields present"
    return 0
}

check_service_health() {
    log_info "Checking LiteLLM service health"

    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sf "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
            log_info "✓ Service is healthy"
            return 0
        fi

        attempt=$((attempt + 1))
        sleep 1
    done

    log_error "Service health check failed after $max_attempts attempts"
    return 1
}

verify_models_loaded() {
    log_info "Verifying models are loaded"

    if ! curl -sf "$MODELS_ENDPOINT" | jq -e '.data | length > 0' > /dev/null 2>&1; then
        log_error "No models loaded in service"
        return 1
    fi

    local model_count=$(curl -sf "$MODELS_ENDPOINT" | jq -r '.data | length')
    log_info "✓ $model_count models loaded"
    return 0
}

create_backup() {
    log_info "Creating configuration backup"

    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"

    # Create timestamped backup
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/litellm.yaml.backup-$timestamp"

    if [[ -f "$DEPLOY_CONFIG" ]]; then
        cp "$DEPLOY_CONFIG" "$backup_file"
        log_info "✓ Backup created: $backup_file"
        echo "$backup_file"
    else
        log_warn "Deploy config not found, skipping backup"
        echo ""
    fi
}

rotate_backups() {
    log_info "Rotating backups (retention policy: 10 recent + 7 daily + 4 weekly)"

    # Get all backup files sorted by modification time (newest first)
    local backups=($(ls -t "$BACKUP_DIR"/litellm.yaml.backup-* 2>/dev/null))
    local total_backups=${#backups[@]}

    if [[ $total_backups -eq 0 ]]; then
        log_info "No backups to rotate"
        return 0
    fi

    # Keep last 10 backups (most recent)
    local keep_recent=10
    local kept_count=0
    local deleted_count=0

    # Associative arrays to track daily and weekly backups
    declare -A daily_backups
    declare -A weekly_backups

    for backup in "${backups[@]}"; do
        local filename=$(basename "$backup")

        # Extract date from filename: litellm.yaml.backup-YYYYMMDD_HHMMSS
        local date_part=$(echo "$filename" | sed 's/litellm.yaml.backup-\([0-9]\{8\}\).*/\1/')
        local day_of_week=$(date -d "${date_part:0:4}-${date_part:4:2}-${date_part:6:2}" +%u)  # 1-7 (Mon-Sun)
        local week_number=$(date -d "${date_part:0:4}-${date_part:4:2}-${date_part:6:2}" +%V)  # ISO week number

        local should_keep=false

        # Rule 1: Keep last 10 backups
        if [[ $kept_count -lt $keep_recent ]]; then
            should_keep=true
            kept_count=$((kept_count + 1))
        # Rule 2: Keep one backup per day for last 7 days
        elif [[ -z "${daily_backups[$date_part]}" ]]; then
            local days_ago=$(( ($(date +%s) - $(date -d "${date_part:0:4}-${date_part:4:2}-${date_part:6:2}" +%s)) / 86400 ))
            if [[ $days_ago -le 7 ]]; then
                daily_backups[$date_part]="$backup"
                should_keep=true
            fi
        # Rule 3: Keep one backup per week for last 4 weeks
        elif [[ -z "${weekly_backups[$week_number]}" ]]; then
            local weeks_ago=$(( ($(date +%s) - $(date -d "${date_part:0:4}-${date_part:4:2}-${date_part:6:2}" +%s)) / 604800 ))
            if [[ $weeks_ago -le 4 ]]; then
                weekly_backups[$week_number]="$backup"
                should_keep=true
            fi
        fi

        # Delete if not kept
        if [[ "$should_keep" == "false" ]]; then
            rm -f "$backup"
            deleted_count=$((deleted_count + 1))
        fi
    done

    log_info "✓ Backup rotation complete: kept $(($total_backups - $deleted_count)), deleted $deleted_count"
}

deploy_config() {
    log_info "Deploying configuration"

    # Copy source to deployment location
    cp "$SOURCE_CONFIG" "$DEPLOY_CONFIG"
    log_info "✓ Configuration deployed to $DEPLOY_CONFIG"
}

reload_service() {
    log_info "Reloading LiteLLM service"

    # Check service status before reload
    if ! systemctl --user is-active --quiet "$SERVICE_NAME"; then
        log_warn "Service is not running, starting instead"
        systemctl --user start "$SERVICE_NAME"
    else
        systemctl --user restart "$SERVICE_NAME"
    fi

    # Wait for service to stabilize
    sleep 5

    log_info "✓ Service reloaded"
}

rollback_config() {
    local backup_file=$1
    log_error "Rolling back to backup: $backup_file"

    if [[ -f "$backup_file" ]]; then
        cp "$backup_file" "$DEPLOY_CONFIG"
        systemctl --user restart "$SERVICE_NAME"
        log_info "✓ Rollback complete"
    else
        log_error "Backup file not found, cannot rollback"
    fi
}

show_diff() {
    if [[ -f "$DEPLOY_CONFIG" ]]; then
        log_info "Configuration changes:"
        echo ""
        diff -u "$DEPLOY_CONFIG" "$SOURCE_CONFIG" || true
        echo ""
    fi
}

# Main execution
main() {
    log_info "=== LiteLLM Configuration Reload ==="
    echo ""

    # Step 1: Validate source configuration
    log_info "Step 1/6: Validating source configuration"
    if ! validate_yaml_syntax "$SOURCE_CONFIG"; then
        exit 1
    fi

    if ! validate_required_fields "$SOURCE_CONFIG"; then
        exit 1
    fi

    # Optional: Model consistency validation
    validate_model_consistency "$SOURCE_CONFIG" || true

    echo ""

    # If validate-only mode, stop here
    if [[ "$VALIDATE_ONLY" == "true" ]]; then
        log_info "Validation complete (--validate-only mode)"
        exit 0
    fi

    # Step 2: Show diff
    log_info "Step 2/6: Showing configuration changes"
    show_diff

    # Step 3: Confirmation (unless --force)
    if [[ "$FORCE" != "true" ]]; then
        echo -n "Proceed with reload? [y/N] "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_warn "Reload cancelled"
            exit 0
        fi
    fi

    # Step 4: Create backup
    log_info "Step 3/6: Creating backup"
    backup_file=$(create_backup)
    rotate_backups
    echo ""

    # Step 5: Deploy configuration
    log_info "Step 4/6: Deploying configuration"
    if ! deploy_config; then
        log_error "Failed to deploy configuration"
        exit 1
    fi
    echo ""

    # Step 6: Reload service
    log_info "Step 5/6: Reloading service"
    if ! reload_service; then
        log_error "Failed to reload service"
        if [[ -n "$backup_file" ]]; then
            rollback_config "$backup_file"
        fi
        exit 1
    fi
    echo ""

    # Step 7: Verify service health
    log_info "Step 6/6: Verifying service health"
    if ! check_service_health; then
        log_error "Service health check failed"
        if [[ -n "$backup_file" ]]; then
            rollback_config "$backup_file"
        fi
        exit 1
    fi

    if ! verify_models_loaded; then
        log_error "Model verification failed"
        if [[ -n "$backup_file" ]]; then
            rollback_config "$backup_file"
        fi
        exit 1
    fi

    echo ""
    log_info "=== Reload Complete ==="
    log_info "Service: systemctl --user status $SERVICE_NAME"
    log_info "Health:  curl $HEALTH_ENDPOINT"
    log_info "Models:  curl $MODELS_ENDPOINT | jq"

    if [[ -n "$backup_file" ]]; then
        log_info "Backup:  $backup_file"
    fi
}

# Run main function
main
