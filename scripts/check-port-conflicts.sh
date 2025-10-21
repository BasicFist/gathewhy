#!/usr/bin/env bash
#
# Port Conflict Checker
# Verifies port availability and detects conflicts with port registry
#
# Usage:
#   ./scripts/check-port-conflicts.sh              # Check all registered ports
#   ./scripts/check-port-conflicts.sh --required   # Check only required ports
#   ./scripts/check-port-conflicts.sh --port 4000  # Check specific port
#   ./scripts/check-port-conflicts.sh --fix        # Attempt to free conflicting ports
#

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly PORTS_FILE="$PROJECT_ROOT/config/ports.yaml"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Flags
MODE="all"
SPECIFIC_PORT=""
FIX_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --required)
            MODE="required"
            shift
            ;;
        --port)
            MODE="specific"
            SPECIFIC_PORT="$2"
            shift 2
            ;;
        --fix)
            FIX_MODE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--required|--port PORT] [--fix]"
            echo ""
            echo "Modes:"
            echo "  (none)      Check all registered ports"
            echo "  --required  Check only required ports"
            echo "  --port N    Check specific port"
            echo ""
            echo "Options:"
            echo "  --fix       Attempt to free conflicting ports (kills processes)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_port_available() {
    local port=$1
    local service_name=$2

    # Check if port is in use using multiple methods for reliability

    # Method 1: netstat (if available)
    if command -v netstat &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":${port} "; then
            return 1  # Port in use
        fi
    fi

    # Method 2: ss (modern alternative)
    if command -v ss &> /dev/null; then
        if ss -tuln 2>/dev/null | grep -q ":${port} "; then
            return 1  # Port in use
        fi
    fi

    # Method 3: lsof (if available)
    if command -v lsof &> /dev/null; then
        if lsof -i ":${port}" &> /dev/null; then
            return 1  # Port in use
        fi
    fi

    return 0  # Port available
}

get_port_process() {
    local port=$1

    # Try lsof first (most detailed)
    if command -v lsof &> /dev/null; then
        local result=$(lsof -i ":${port}" 2>/dev/null | tail -n +2)
        if [[ -n "$result" ]]; then
            echo "$result"
            return
        fi
    fi

    # Fallback to ss
    if command -v ss &> /dev/null; then
        ss -tlnp 2>/dev/null | grep ":${port} " || echo "Unknown process"
    else
        echo "Unknown process (install lsof or ss for details)"
    fi
}

kill_port_process() {
    local port=$1
    local service_name=$2

    log_warning "Attempting to free port $port (service: $service_name)"

    if command -v lsof &> /dev/null; then
        local pids=$(lsof -t -i ":${port}" 2>/dev/null)

        if [[ -n "$pids" ]]; then
            echo "  Processes using port $port:"
            lsof -i ":${port}" 2>/dev/null | tail -n +2
            echo ""
            echo -n "  Kill these processes? [y/N] "
            read -r response

            if [[ "$response" =~ ^[Yy]$ ]]; then
                for pid in $pids; do
                    kill "$pid" 2>/dev/null && log_info "  Killed PID $pid" || log_error "  Failed to kill PID $pid"
                done
                sleep 1

                # Verify port is now free
                if check_port_available "$port" "$service_name"; then
                    log_success "  Port $port is now available"
                else
                    log_error "  Port $port still in use after kill attempt"
                fi
            else
                log_info "  Skipped killing processes"
            fi
        else
            log_info "  No processes found on port $port"
        fi
    else
        log_error "  lsof not available, cannot kill processes automatically"
        log_info "  Install lsof: sudo apt install lsof"
    fi
}

check_ports_from_yaml() {
    local check_required_only=$1

    log_info "Checking ports from registry: $PORTS_FILE"
    echo ""

    if [[ ! -f "$PORTS_FILE" ]]; then
        log_error "Port registry not found: $PORTS_FILE"
        exit 1
    fi

    # Parse YAML and check ports
    # This is a simple parser for our specific YAML structure
    local current_service=""
    local port=""
    local required=""
    local description=""

    local conflicts=0
    local checked=0

    while IFS= read -r line; do
        # Skip comments and empty lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$line" ]] && continue

        # Detect service name (non-indented line ending with :)
        if [[ "$line" =~ ^([a-z_]+):$ ]]; then
            current_service="${BASH_REMATCH[1]}"
            port=""
            required=""
            description=""
            continue
        fi

        # Parse port
        if [[ "$line" =~ ^[[:space:]]+port:[[:space:]]+([0-9]+) ]]; then
            port="${BASH_REMATCH[1]}"
        fi

        # Parse required
        if [[ "$line" =~ ^[[:space:]]+required:[[:space:]]+(true|false) ]]; then
            required="${BASH_REMATCH[1]}"
        fi

        # Parse description
        if [[ "$line" =~ ^[[:space:]]+description:[[:space:]]+\"(.+)\" ]]; then
            description="${BASH_REMATCH[1]}"
        fi

        # When we have all info for a service, check it
        if [[ -n "$current_service" && -n "$port" && -n "$required" && -n "$description" ]]; then
            # Skip if checking required only and this is not required
            if [[ "$check_required_only" == "true" && "$required" != "true" ]]; then
                current_service=""
                port=""
                required=""
                description=""
                continue
            fi

            checked=$((checked + 1))

            # Check port availability
            if check_port_available "$port" "$current_service"; then
                log_success "Port $port available - $current_service ($description)"
            else
                log_error "Port $port IN USE - $current_service ($description)"
                echo "  Process info:"
                get_port_process "$port" | sed 's/^/    /'

                conflicts=$((conflicts + 1))

                # Offer to fix if in fix mode
                if [[ "$FIX_MODE" == "true" ]]; then
                    kill_port_process "$port" "$current_service"
                fi
            fi

            # Reset for next service
            current_service=""
            port=""
            required=""
            description=""
        fi
    done < "$PORTS_FILE"

    echo ""
    log_info "Checked $checked ports, found $conflicts conflicts"

    return $conflicts
}

check_specific_port() {
    local port=$1

    log_info "Checking port $port"
    echo ""

    if check_port_available "$port" "custom"; then
        log_success "Port $port is available"
        return 0
    else
        log_error "Port $port is IN USE"
        echo ""
        echo "Process info:"
        get_port_process "$port"

        if [[ "$FIX_MODE" == "true" ]]; then
            echo ""
            kill_port_process "$port" "custom"
        fi

        return 1
    fi
}

main() {
    echo -e "${BLUE}=== Port Conflict Checker ===${NC}"
    echo ""

    case "$MODE" in
        all)
            check_ports_from_yaml "false"
            exit_code=$?
            ;;
        required)
            check_ports_from_yaml "true"
            exit_code=$?
            ;;
        specific)
            check_specific_port "$SPECIFIC_PORT"
            exit_code=$?
            ;;
    esac

    echo ""
    if [[ $exit_code -eq 0 ]]; then
        log_success "All checked ports are available"
        exit 0
    else
        log_error "Port conflicts detected"
        if [[ "$FIX_MODE" != "true" ]]; then
            log_info "Run with --fix to attempt automatic conflict resolution"
        fi
        exit 1
    fi
}

main
