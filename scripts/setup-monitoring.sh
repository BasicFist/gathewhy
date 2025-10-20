#!/bin/bash
# =============================================================================
# Setup Monitoring Stack for AI Backend Unified Infrastructure
# =============================================================================
#
# Automated installation and configuration of:
# - Prometheus (metrics collection)
# - Grafana (visualization)
# - Loki (log aggregation)
# - Promtail (log shipping)
#
# Usage:
#   ./scripts/setup-monitoring.sh [--install-binaries] [--skip-services]
#
# Options:
#   --install-binaries: Download and install monitoring binaries
#   --skip-services:    Skip systemd service installation
#   --dry-run:          Show what would be done without executing
#
# =============================================================================

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MONITORING_DIR="$PROJECT_ROOT/monitoring"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

# Installation options
INSTALL_BINARIES=false
SKIP_SERVICES=false
DRY_RUN=false

# Binary versions
PROMETHEUS_VERSION="2.47.0"
GRAFANA_VERSION="10.1.5"
LOKI_VERSION="2.9.2"
PROMTAIL_VERSION="2.9.2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

execute_or_dry_run() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] $*"
    else
        "$@"
    fi
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_warning "$1 is not installed"
        return 1
    fi
}

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --install-binaries)
            INSTALL_BINARIES=true
            shift
            ;;
        --skip-services)
            SKIP_SERVICES=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--install-binaries] [--skip-services] [--dry-run]"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Pre-flight Checks
# =============================================================================

print_header "Pre-flight Checks"

# Check if running in LAB environment
if [[ ! "$PWD" =~ /LAB/ai/backend/ai-backend-unified ]]; then
    print_warning "Not in expected project directory"
    print_info "Current: $PWD"
    print_info "Expected: */LAB/ai/backend/ai-backend-unified"
fi

# Check directory structure
if [ ! -d "$MONITORING_DIR" ]; then
    print_error "Monitoring directory not found: $MONITORING_DIR"
    exit 1
fi

print_success "Project structure validated"

# Check for existing binaries
print_info "Checking for existing monitoring binaries..."
PROMETHEUS_EXISTS=$(check_command prometheus && echo true || echo false)
GRAFANA_EXISTS=$(check_command grafana-server && echo true || echo false)
LOKI_EXISTS=$(check_command loki && echo true || echo false)
PROMTAIL_EXISTS=$(check_command promtail && echo true || echo false)

# =============================================================================
# Install Binaries (Optional)
# =============================================================================

if [ "$INSTALL_BINARIES" = true ]; then
    print_header "Installing Monitoring Binaries"

    INSTALL_DIR="$HOME/.local/bin"
    execute_or_dry_run mkdir -p "$INSTALL_DIR"

    # Install Prometheus
    if [ "$PROMETHEUS_EXISTS" = false ]; then
        print_info "Downloading Prometheus $PROMETHEUS_VERSION..."
        execute_or_dry_run wget -q "https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz" -O /tmp/prometheus.tar.gz
        execute_or_dry_run tar -xzf /tmp/prometheus.tar.gz -C /tmp
        execute_or_dry_run cp /tmp/prometheus-${PROMETHEUS_VERSION}.linux-amd64/prometheus "$INSTALL_DIR/"
        execute_or_dry_run chmod +x "$INSTALL_DIR/prometheus"
        execute_or_dry_run rm -rf /tmp/prometheus.tar.gz /tmp/prometheus-${PROMETHEUS_VERSION}.linux-amd64
        print_success "Prometheus installed to $INSTALL_DIR/prometheus"
    fi

    # Install Loki
    if [ "$LOKI_EXISTS" = false ]; then
        print_info "Downloading Loki $LOKI_VERSION..."
        execute_or_dry_run wget -q "https://github.com/grafana/loki/releases/download/v${LOKI_VERSION}/loki-linux-amd64.zip" -O /tmp/loki.zip
        execute_or_dry_run unzip -q /tmp/loki.zip -d /tmp
        execute_or_dry_run cp /tmp/loki-linux-amd64 "$INSTALL_DIR/loki"
        execute_or_dry_run chmod +x "$INSTALL_DIR/loki"
        execute_or_dry_run rm -f /tmp/loki.zip /tmp/loki-linux-amd64
        print_success "Loki installed to $INSTALL_DIR/loki"
    fi

    # Install Promtail
    if [ "$PROMTAIL_EXISTS" = false ]; then
        print_info "Downloading Promtail $PROMTAIL_VERSION..."
        execute_or_dry_run wget -q "https://github.com/grafana/loki/releases/download/v${PROMTAIL_VERSION}/promtail-linux-amd64.zip" -O /tmp/promtail.zip
        execute_or_dry_run unzip -q /tmp/promtail.zip -d /tmp
        execute_or_dry_run cp /tmp/promtail-linux-amd64 "$INSTALL_DIR/promtail"
        execute_or_dry_run chmod +x "$INSTALL_DIR/promtail"
        execute_or_dry_run rm -f /tmp/promtail.zip /tmp/promtail-linux-amd64
        print_success "Promtail installed to $INSTALL_DIR/promtail"
    fi

    # Grafana requires package manager installation
    if [ "$GRAFANA_EXISTS" = false ]; then
        print_warning "Grafana requires system package installation"
        print_info "Install with: sudo apt-get install -y grafana (Debian/Ubuntu)"
        print_info "Or visit: https://grafana.com/grafana/download"
    fi

    # Update PATH if needed
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        print_info "Add to ~/.bashrc: export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
fi

# =============================================================================
# Create Required Directories
# =============================================================================

print_header "Creating Directory Structure"

DIRS=(
    "$MONITORING_DIR/prometheus/data"
    "$MONITORING_DIR/grafana/data"
    "$MONITORING_DIR/grafana/logs"
    "$MONITORING_DIR/grafana/plugins"
    "$MONITORING_DIR/grafana/provisioning/datasources"
    "$MONITORING_DIR/grafana/provisioning/dashboards"
    "$MONITORING_DIR/loki/data/wal"
    "$MONITORING_DIR/loki/data/boltdb-shipper-active"
    "$MONITORING_DIR/loki/data/boltdb-shipper-cache"
    "$MONITORING_DIR/loki/data/boltdb-shipper-compactor"
    "$MONITORING_DIR/loki/data/chunks"
    "$MONITORING_DIR/loki/data/rules"
)

for dir in "${DIRS[@]}"; do
    execute_or_dry_run mkdir -p "$dir"
done

print_success "Directory structure created"

# =============================================================================
# Configure Grafana Datasources
# =============================================================================

print_header "Configuring Grafana Datasources"

DATASOURCES_FILE="$MONITORING_DIR/grafana/provisioning/datasources/datasources.yml"

execute_or_dry_run cat > "$DATASOURCES_FILE" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://localhost:3100
    editable: false
EOF

print_success "Grafana datasources configured"

# =============================================================================
# Configure Grafana Dashboard Provisioning
# =============================================================================

print_header "Configuring Grafana Dashboards"

DASHBOARDS_FILE="$MONITORING_DIR/grafana/provisioning/dashboards/dashboards.yml"

execute_or_dry_run cat > "$DASHBOARDS_FILE" << EOF
apiVersion: 1

providers:
  - name: 'AI Backend'
    orgId: 1
    folder: 'AI Backend Unified'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: $MONITORING_DIR/grafana
      foldersFromFilesStructure: true
EOF

print_success "Grafana dashboard provisioning configured"

# =============================================================================
# Install Systemd Services
# =============================================================================

if [ "$SKIP_SERVICES" = false ]; then
    print_header "Installing Systemd Services"

    execute_or_dry_run mkdir -p "$SYSTEMD_USER_DIR"

    SERVICES=(
        "prometheus"
        "loki"
        "promtail"
        "grafana"
    )

    for service in "${SERVICES[@]}"; do
        SOURCE="$MONITORING_DIR/systemd/${service}.service"
        DEST="$SYSTEMD_USER_DIR/${service}.service"

        if [ -f "$SOURCE" ]; then
            execute_or_dry_run cp "$SOURCE" "$DEST"
            print_success "Installed ${service}.service"
        else
            print_error "Service file not found: $SOURCE"
        fi
    done

    # Reload systemd
    execute_or_dry_run systemctl --user daemon-reload
    print_success "Systemd daemon reloaded"
else
    print_warning "Skipping systemd service installation (--skip-services)"
fi

# =============================================================================
# Validation
# =============================================================================

print_header "Validation"

# Check configurations
CONFIGS=(
    "$MONITORING_DIR/prometheus/prometheus.yml"
    "$MONITORING_DIR/prometheus/alerts.yml"
    "$MONITORING_DIR/loki/loki-config.yml"
    "$MONITORING_DIR/loki/promtail-config.yml"
)

for config in "${CONFIGS[@]}"; do
    if [ -f "$config" ]; then
        print_success "Found: $(basename "$config")"
    else
        print_error "Missing: $config"
    fi
done

# =============================================================================
# Summary and Next Steps
# =============================================================================

print_header "Setup Complete"

echo ""
echo "Monitoring stack setup completed successfully!"
echo ""
echo "Next steps:"
echo ""
echo "1. Start services (if binaries installed):"
echo "   systemctl --user enable prometheus loki promtail grafana"
echo "   systemctl --user start prometheus loki promtail grafana"
echo ""
echo "2. Check service status:"
echo "   systemctl --user status prometheus"
echo "   systemctl --user status loki"
echo "   systemctl --user status promtail"
echo "   systemctl --user status grafana"
echo ""
echo "3. Access interfaces:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana:    http://localhost:3000 (admin/admin)"
echo "   Loki:       http://localhost:3100"
echo ""
echo "4. Import dashboard:"
echo "   - Login to Grafana"
echo "   - Navigate to Dashboards > Import"
echo "   - Upload: monitoring/grafana/litellm-dashboard.json"
echo ""
echo "5. Verify metrics:"
echo "   curl http://localhost:9090/api/v1/targets"
echo "   curl http://localhost:4000/metrics"
echo ""

if [ "$INSTALL_BINARIES" = false ]; then
    print_warning "Binaries not installed. Use --install-binaries or install manually:"
    [ "$PROMETHEUS_EXISTS" = false ] && echo "  - Prometheus: https://prometheus.io/download/"
    [ "$LOKI_EXISTS" = false ] && echo "  - Loki: https://github.com/grafana/loki/releases"
    [ "$PROMTAIL_EXISTS" = false ] && echo "  - Promtail: https://github.com/grafana/loki/releases"
    [ "$GRAFANA_EXISTS" = false ] && echo "  - Grafana: https://grafana.com/grafana/download"
fi

echo ""
print_success "Setup script completed"
