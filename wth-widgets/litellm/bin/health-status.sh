#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

render_header "Santé des déploiements"

health_json=$(http_get_json "$LITELLM_HOST/health?details=true" 2>/dev/null || http_get_json "$LITELLM_HOST/health" 2>/dev/null || true)

if [[ -z "$health_json" ]]; then
    if have_gum; then
        "$GUM_BIN" style --foreground 9 "Impossible de joindre $LITELLM_HOST/health"
    else
        echo "Erreur: impossible de joindre $LITELLM_HOST/health"
    fi
    exit 1
fi

if jq -e '.healthy_endpoints' >/dev/null 2>&1 <<<"$health_json"; then
    healthy_count=$(jq -r '.healthy_count // (.healthy_endpoints | length // 0)' <<<"$health_json")
    unhealthy_count=$(jq -r '.unhealthy_count // (.unhealthy_endpoints | length // 0)' <<<"$health_json")

    jq -r '.healthy_endpoints[]? | [.model // "unknown", (.last_health_check_status // "healthy")] | @tsv' <<<"$health_json" |
        while IFS=$'\t' read -r model status; do
            provider=${model%%/*}
            model_name=${model#*/}
            render_status_line "$provider/$model_name" "active" "$status"
        done

    if jq -e '.unhealthy_endpoints | length > 0' >/dev/null <<<"$health_json"; then
        echo
        jq -r '.unhealthy_endpoints[]? | [.model // "unknown", (.error // "Erreur inconnue")] | @tsv' <<<"$health_json" |
            while IFS=$'\t' read -r model error; do
                render_status_line "$model" "failed" "$error"
            done
    fi

    total=$((healthy_count + unhealthy_count))
    if have_gum; then
        "$GUM_BIN" style --margin "1 0" --padding "0 1" --border rounded --border-foreground 63 \
            "Total: $total | ✓ $healthy_count | ✗ $unhealthy_count"
    else
        echo "Total: $total (OK: $healthy_count / KO: $unhealthy_count)"
    fi
else
    status=$(jq -r '.status // "unknown"' <<<"$health_json")
    render_status_line "LiteLLM" "$status" "$(jq -r '.message? // ""' <<<"$health_json")"
fi
