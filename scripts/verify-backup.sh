#!/usr/bin/env bash
#
# Backup Verification Script
# Validates YAML syntax and content of configuration backups
#
# Usage:
#   ./scripts/verify-backup.sh                    # Verify latest backup
#   ./scripts/verify-backup.sh <backup-file>      # Verify specific backup
#   ./scripts/verify-backup.sh --all              # Verify all backups
#

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly BACKUP_DIR="../openwebui/backups"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Mode
MODE="latest"
SPECIFIC_FILE=""

# Parse arguments
if [[ $# -eq 0 ]]; then
    MODE="latest"
elif [[ "$1" == "--all" ]]; then
    MODE="all"
elif [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $0 [--all | <backup-file>]"
    echo ""
    echo "Modes:"
    echo "  (none)         Verify latest backup"
    echo "  --all          Verify all backups"
    echo "  <backup-file>  Verify specific backup file"
    exit 0
else
    MODE="specific"
    SPECIFIC_FILE="$1"
fi

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

verify_yaml_syntax() {
    local file=$1

    if ! python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
        return 1
    fi
    return 0
}

verify_required_fields() {
    local file=$1

    # Check for model_list
    if ! grep -q "model_list:" "$file"; then
        log_error "  Missing required field: model_list"
        return 1
    fi

    # Check for litellm_settings
    if ! grep -q "litellm_settings:" "$file"; then
        log_error "  Missing required field: litellm_settings"
        return 1
    fi

    # Check for router_settings
    if ! grep -q "router_settings:" "$file"; then
        log_error "  Missing required field: router_settings"
        return 1
    fi

    return 0
}

verify_backup() {
    local file=$1
    local filename=$(basename "$file")

    echo -e "${BLUE}Verifying:${NC} $filename"

    # Check file exists
    if [[ ! -f "$file" ]]; then
        log_error "  File not found"
        return 1
    fi

    # Check YAML syntax
    if ! verify_yaml_syntax "$file"; then
        log_error "  YAML syntax invalid"
        return 1
    fi
    log_success "  YAML syntax valid"

    # Check required fields
    if ! verify_required_fields "$file"; then
        log_error "  Required fields missing"
        return 1
    fi
    log_success "  Required fields present"

    # Get file size
    local size=$(du -h "$file" | cut -f1)
    log_info "  Size: $size"

    # Get timestamp from filename
    if [[ "$filename" =~ backup-([0-9]{8}_[0-9]{6}) ]]; then
        local timestamp="${BASH_REMATCH[1]}"
        local date_part="${timestamp:0:8}"
        local time_part="${timestamp:9:6}"
        local formatted_date="${date_part:0:4}-${date_part:4:2}-${date_part:6:2}"
        local formatted_time="${time_part:0:2}:${time_part:2:2}:${time_part:4:2}"
        log_info "  Created: $formatted_date $formatted_time"
    fi

    log_success "Backup valid"
    echo ""
    return 0
}

main() {
    echo -e "${BLUE}=== Backup Verification ===${NC}"
    echo ""

    local verified=0
    local failed=0

    case "$MODE" in
        latest)
            # Find latest backup
            local latest=$(ls -t "$BACKUP_DIR"/litellm.yaml.backup-* 2>/dev/null | head -1)
            if [[ -z "$latest" ]]; then
                log_error "No backups found in $BACKUP_DIR"
                exit 1
            fi

            if verify_backup "$latest"; then
                verified=1
            else
                failed=1
            fi
            ;;

        specific)
            if verify_backup "$SPECIFIC_FILE"; then
                verified=1
            else
                failed=1
            fi
            ;;

        all)
            local backups=($(ls -t "$BACKUP_DIR"/litellm.yaml.backup-* 2>/dev/null))
            if [[ ${#backups[@]} -eq 0 ]]; then
                log_error "No backups found in $BACKUP_DIR"
                exit 1
            fi

            log_info "Found ${#backups[@]} backups"
            echo ""

            for backup in "${backups[@]}"; do
                if verify_backup "$backup"; then
                    verified=$((verified + 1))
                else
                    failed=$((failed + 1))
                fi
            done
            ;;
    esac

    # Summary
    echo -e "${BLUE}=== Summary ===${NC}"
    log_success "Verified: $verified"
    if [[ $failed -gt 0 ]]; then
        log_error "Failed: $failed"
        exit 1
    else
        log_success "All backups valid"
        exit 0
    fi
}

main
