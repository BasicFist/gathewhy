#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

: "${LITELLM_LOG_SOURCE:=journalctl --user -u litellm.service -n 40 --no-pager}"

render_header "LiteLLM Recent Logs"

if output=$(eval "$LITELLM_LOG_SOURCE" 2>&1); then
    printf '```\n%s\n```\n' "$output" | render_logs
else
    if have_gum; then
        "$GUM_BIN" style --foreground 9 "Failed: $LITELLM_LOG_SOURCE"
    else
        echo "Failed to read logs using: $LITELLM_LOG_SOURCE"
    fi
fi
