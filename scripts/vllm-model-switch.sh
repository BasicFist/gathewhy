#!/usr/bin/env bash
# vLLM Model Switching Script
# Manages single-instance vLLM deployment with model hot-swapping
#
# CONSTRAINT: 16GB VRAM can only fit ONE vLLM model at a time
# Each model needs ~12-13GB (model + KV cache)

set -e

DEFAULT_VLLM_BIN="/home/miko/venvs/vllm/bin/vllm"
: "${VLLM_BIN:=$DEFAULT_VLLM_BIN}"

if [[ ! -x "$VLLM_BIN" ]]; then
    if command -v vllm >/dev/null 2>&1; then
        VLLM_BIN="$(command -v vllm)"
    else
        echo "[✗] Unable to locate vllm executable. Set VLLM_BIN before running." >&2
        exit 1
    fi
fi

# Tunable defaults informed by https://docs.vllm.ai/en/stable/configuration/
: "${VLLM_PORT:=8001}"
: "${VLLM_MAX_NUM_SEQS:=16}"
: "${VLLM_MAX_BATCHED_TOKENS:=8192}"
: "${VLLM_MAX_MODEL_LEN:=32768}"
: "${VLLM_GMEM_UTIL:=0.85}"
: "${VLLM_SERVED_NAME:=workspace-coder}"
LOG_DIR="${VLLM_LOG_DIR:-/tmp}"

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

# Compose common vLLM arguments (overridable via env)
build_common_args() {
    COMMON_ARGS=(
        --host "${VLLM_HOST:-127.0.0.1}"
        --port "$VLLM_PORT"
        --gpu-memory-utilization "$VLLM_GMEM_UTIL"
        --dtype auto
        --enforce-eager
        --trust-remote-code
        --enable-prefix-caching
        --max-model-len "$VLLM_MAX_MODEL_LEN"
        --max-num-seqs "$VLLM_MAX_NUM_SEQS"
        --max-num-batched-tokens "$VLLM_MAX_BATCHED_TOKENS"
        --served-model-name "$VLLM_SERVED_NAME"
    )

    if [[ -n "${VLLM_LOG_STATS:-}" ]]; then
        COMMON_ARGS+=(--log-stats)
    fi
}

# Start Qwen Coder model
start_qwen() {
    log_info "Starting Qwen2.5-Coder-7B-Instruct-AWQ..."
    build_common_args

    nohup "$VLLM_BIN" serve Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \
        "${COMMON_ARGS[@]}" \
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

    build_common_args

    nohup "$VLLM_BIN" serve solidrust/dolphin-2.8-mistral-7b-v02-AWQ \
        "${COMMON_ARGS[@]}" \
        --quantization awq \
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
