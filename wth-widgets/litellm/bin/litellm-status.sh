#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

render_header "LiteLLM Service Health"

declare -A SERVICES=(
    ["LiteLLM Gateway"]="litellm.service"
    ["Ollama"]="ollama.service"
    ["llama.cpp (Python)"]="llamacpp-python.service"
    ["vLLM"]="vllm.service"
)

for name in "${!SERVICES[@]}"; do
    unit="${SERVICES[$name]}"
    if systemctl --user list-unit-files "$unit" >/dev/null 2>&1; then
        status=$(systemctl --user is-active "$unit" 2>/dev/null || echo "unknown")
    else
        status="not-installed"
    fi

    case "$status" in
        active)
            msg="(running)"
            ;;
        not-installed)
            msg="(unit missing)"
            ;;
        unknown)
            msg="(status unavailable)"
            ;;
        *)
            msg="($status)"
            ;;
    esac
    render_status_line "$name" "$status" "$msg"
done

echo
render_header "LiteLLM Router Health"

if response=$(http_get_json "$LITELLM_HOST$LITELLM_HEALTH_ENDPOINT" 2>/dev/null); then
    if have_gum; then
        "$GUM_BIN" style --foreground 10 "Router OK" && echo "$response"
    else
        echo "Router OK: $response"
    fi
else
    if have_gum; then
        "$GUM_BIN" style --foreground 9 "Router unreachable: $LITELLM_HOST$LITELLM_HEALTH_ENDPOINT"
    else
        echo "Router unreachable: $LITELLM_HOST$LITELLM_HEALTH_ENDPOINT"
    fi
fi
