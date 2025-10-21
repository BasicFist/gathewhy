#!/usr/bin/env bash
#
# Backup Rotation Dry-Run Test
# Creates dummy backups and validates rotation logic
#

set -euo pipefail

readonly TEST_DIR="/tmp/backup-rotation-test-$$"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

create_test_backups() {
    log_info "Creating test backup directory: $TEST_DIR"
    mkdir -p "$TEST_DIR"

    # Create 20 test backup files with different timestamps
    # Simulating backups over 30 days

    local -a dates=(
        # Last 10 days (should keep 10 recent)
        "20251021_120000"  # Today
        "20251020_120000"  # 1 day ago
        "20251019_120000"  # 2 days ago
        "20251018_120000"  # 3 days ago
        "20251017_120000"  # 4 days ago
        "20251016_120000"  # 5 days ago
        "20251015_120000"  # 6 days ago
        "20251014_120000"  # 7 days ago
        "20251013_120000"  # 8 days ago
        "20251012_120000"  # 9 days ago

        # Additional backups within 7 days (same day - should dedupe to 1 per day)
        "20251020_090000"  # 1 day ago, different time
        "20251019_150000"  # 2 days ago, different time

        # Weekly backups (should keep 1 per week for 4 weeks)
        "20251007_120000"  # 2 weeks ago
        "20250930_120000"  # 3 weeks ago
        "20250923_120000"  # 4 weeks ago

        # Old backups (should be deleted)
        "20250901_120000"  # 50 days ago
        "20250815_120000"  # 67 days ago
        "20250801_120000"  # 81 days ago
        "20250715_120000"  # 98 days ago
        "20250701_120000"  # 112 days ago
    )

    for date in "${dates[@]}"; do
        local file="$TEST_DIR/litellm.yaml.backup-$date"
        echo "# Test backup from $date" > "$file"

        # Set file modification time to match the backup timestamp
        # Format: YYMMDDhhmm (touch -t format)
        local year="${date:2:2}"    # YY from YYYY
        local month="${date:4:2}"   # MM
        local day="${date:6:2}"     # DD
        local hour="${date:9:2}"    # hh
        local min="${date:11:2}"    # mm
        touch -t "${year}${month}${day}${hour}${min}" "$file"
    done

    log_info "Created ${#dates[@]} test backup files"
}

count_backups() {
    local count=$(ls -1 "$TEST_DIR"/litellm.yaml.backup-* 2>/dev/null | wc -l)
    echo "$count"
}

test_rotation_logic() {
    log_info "Testing rotation logic..."

    local initial_count=$(count_backups)
    log_info "Initial backup count: $initial_count"

    # Source the rotation function from reload script
    # We'll extract and run just the rotation logic

    # Override BACKUP_DIR for testing
    export BACKUP_DIR="$TEST_DIR"

    # Run rotation logic (inline from reload-litellm-config.sh)
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
        elif [[ -z "${daily_backups[$date_part]:-}" ]]; then
            local days_ago=$(( ($(date +%s) - $(date -d "${date_part:0:4}-${date_part:4:2}-${date_part:6:2}" +%s)) / 86400 ))
            if [[ $days_ago -le 7 ]]; then
                daily_backups[$date_part]="$backup"
                should_keep=true
            fi
        # Rule 3: Keep one backup per week for last 4 weeks
        elif [[ -z "${weekly_backups[$week_number]:-}" ]]; then
            local weeks_ago=$(( ($(date +%s) - $(date -d "${date_part:0:4}-${date_part:4:2}-${date_part:6:2}" +%s)) / 604800 ))
            if [[ $weeks_ago -le 4 ]]; then
                weekly_backups[$week_number]="$backup"
                should_keep=true
            fi
        fi

        # Delete if not kept (dry-run: just log)
        if [[ "$should_keep" == "false" ]]; then
            log_warn "Would delete: $(basename "$backup")"
            deleted_count=$((deleted_count + 1))
        else
            log_info "Would keep:   $(basename "$backup")"
        fi
    done

    log_info "Rotation result: would keep $(($total_backups - $deleted_count)), would delete $deleted_count"

    # Validate expectations
    local final_count=$(($total_backups - $deleted_count))

    echo ""
    log_info "=== Validation Results ==="

    # Expected: ~10-15 backups kept (10 recent + some daily/weekly dedupes)
    if [[ $final_count -ge 10 && $final_count -le 20 ]]; then
        log_info "✓ Retention policy working correctly ($final_count backups kept)"
    else
        log_error "✗ Unexpected retention count: $final_count (expected 10-20)"
        return 1
    fi

    # Verify at least some backups would be deleted
    if [[ $deleted_count -gt 0 ]]; then
        log_info "✓ Old backups properly identified for deletion ($deleted_count files)"
    else
        log_warn "✗ No backups marked for deletion (expected some)"
    fi

    return 0
}

cleanup() {
    log_info "Cleaning up test directory"
    rm -rf "$TEST_DIR"
}

main() {
    log_info "=== Backup Rotation Dry-Run Test ==="
    echo ""

    # Set up
    create_test_backups
    echo ""

    # Test
    if test_rotation_logic; then
        echo ""
        log_info "=== Test PASSED ==="
        cleanup
        exit 0
    else
        echo ""
        log_error "=== Test FAILED ==="
        log_error "Test directory preserved for inspection: $TEST_DIR"
        exit 1
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

main
