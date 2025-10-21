#!/usr/bin/env bash
#
# Common utilities for AI Backend scripts
# Source this file: source "$(dirname "$0")/common.sh"
#

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
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

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Common paths
get_project_root() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$script_dir/.." && pwd
}

get_config_dir() {
    echo "$(get_project_root)/config"
}

# Configuration file helpers
check_file_exists() {
    local file=$1
    if [[ ! -f "$file" ]]; then
        log_error "File not found: $file"
        return 1
    fi
    return 0
}

# Validation helpers
validate_yaml_syntax() {
    local file=$1
    if ! python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
        log_error "Invalid YAML syntax: $file"
        return 1
    fi
    return 0
}

# Export functions for use in sourcing scripts
export -f log_info log_success log_warn log_error log_debug
export -f get_project_root get_config_dir
export -f check_file_exists validate_yaml_syntax
