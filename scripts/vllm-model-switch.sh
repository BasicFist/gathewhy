#!/usr/bin/env bash
# vLLM Model Switching Script
# Manages single-instance vLLM deployment with model hot-swapping
#
# CONSTRAINT: 16GB VRAM can only fit ONE vLLM model at a time
# Each model needs ~12-13GB (model + KV cache)

set -e

VLLM_BIN="/home/miko/venvs/vllm/bin/vllm"
VLLM_PORT=8001
LOG_DIR="/tmp"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if vLLM is running
check_vllm_status() {
    if pgrep -f "vllm serve" > /dev/null; then
        local pid=$(pgrep -f "vllm serve")
        local model=$(ps -p "$pid" -o args= | grep -oP "(?<=vllm serve ).+?(?= --)" || echo "unknown")
        log_info "vLLM is running on PID $pid"
        log_info "Current model: $model"
        return 0
    else
        log_warning "vLLM is not running"
        return 1
    fi
}

# Stop vLLM server
stop_vllm() {
    log_info "Stopping vLLM server..."

    if pgrep -f "vllm serve" > /dev/null; then
        pkill -f "vllm serve"
        sleep 3

        # Force kill if still running
        if pgrep -f "vllm serve" > /dev/null; then
            log_warning "Graceful shutdown failed, force killing..."
            pkill -9 -f "vllm serve"
            sleep 2
        fi

        log_success "vLLM server stopped"
    else
        log_info "vLLM is not running"
    fi
}

# Start Qwen Coder model
start_qwen() {
    log_info "Starting Qwen2.5-Coder-7B-Instruct-AWQ..."

    nohup "$VLLM_BIN" serve Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \
        --host 0.0.0.0 \
        --port "$VLLM_PORT" \
        --gpu-memory-utilization 0.85 \
        --dtype auto \
        --enforce-eager \
        --trust-remote-code \
        --enable-auto-tool-choice \
        --tool-call-parser hermes \
        > "$LOG_DIR/vllm-qwen-coder.log" 2>&1 &

    local pid=$!
    log_success "Qwen Coder started with PID: $pid"
    log_info "Log file: $LOG_DIR/vllm-qwen-coder.log"
    log_info "Waiting for model to load..."

    # Wait for server to be ready
    for i in {1..60}; do
        if curl -s http://localhost:$VLLM_PORT/v1/models > /dev/null 2>&1; then
            log_success "Model loaded and ready!"
            return 0
        fi
        sleep 2
    done

    log_error "Model failed to start within 120 seconds"
    return 1
}

# Start Dolphin model
start_dolphin() {
    log_info "Starting Dolphin-2.8-Mistral-7B-v02-AWQ..."

    nohup "$VLLM_BIN" serve solidrust/dolphin-2.8-mistral-7b-v02-AWQ \
        --host 0.0.0.0 \
        --port "$VLLM_PORT" \
        --quantization awq \
        --gpu-memory-utilization 0.8 \
        --dtype auto \
        --trust-remote-code \
        --max-model-len 8192 \
        --enable-auto-tool-choice \
        --tool-call-parser hermes \
        > "$LOG_DIR/vllm-dolphin.log" 2>&1 &

    local pid=$!
    log_success "Dolphin started with PID: $pid"
    log_info "Log file: $LOG_DIR/vllm-dolphin.log"
    log_info "Waiting for model to load..."

    # Wait for server to be ready
    for i in {1..60}; do
        if curl -s http://localhost:$VLLM_PORT/v1/models > /dev/null 2>&1; then
            log_success "Model loaded and ready!"
            return 0
        fi
        sleep 2
    done

    log_error "Model failed to start within 120 seconds"
    return 1
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [COMMAND]

vLLM Model Switching Script (Single Instance Strategy)
Hardware: 16GB VRAM - can only run ONE model at a time

Commands:
  status          Show current vLLM status
  qwen            Switch to Qwen2.5-Coder-7B (code generation)
  dolphin         Switch to Dolphin-2.8-Mistral-7B (uncensored conversational)
  stop            Stop vLLM server
  restart         Restart current model
  help            Show this help message

Examples:
  $0 status                    # Check what's running
  $0 qwen                      # Switch to Qwen Coder
  $0 dolphin                   # Switch to Dolphin

Models:
  Qwen Coder      - Code generation specialist, AWQ quantized (~12.6GB VRAM)
  Dolphin         - Uncensored conversational, AWQ quantized (~12-13GB VRAM)

Note: Switching models requires stopping the current server (brief downtime).
      LiteLLM will automatically failover to Ollama models during the switch.
EOF
}

# Main command handling
case "${1:-help}" in
    status)
        check_vllm_status
        ;;
    qwen)
        log_info "Switching to Qwen Coder..."
        stop_vllm
        start_qwen
        ;;
    dolphin)
        log_info "Switching to Dolphin..."
        stop_vllm
        start_dolphin
        ;;
    stop)
        stop_vllm
        ;;
    restart)
        if pgrep -f "vllm serve" > /dev/null; then
            local pid=$(pgrep -f "vllm serve")
            local current_model=$(ps -p "$pid" -o args= | grep -oP "(?<=vllm serve ).+?(?= --)" || echo "unknown")

            log_info "Restarting current model: $current_model"
            stop_vllm

            if [[ "$current_model" == *"Qwen"* ]]; then
                start_qwen
            elif [[ "$current_model" == *"dolphin"* ]]; then
                start_dolphin
            else
                log_error "Unknown model type, cannot restart"
                exit 1
            fi
        else
            log_error "No vLLM server is running"
            exit 1
        fi
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        log_error "Unknown command: $1"
        usage
        exit 1
        ;;
esac
