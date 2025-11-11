#!/usr/bin/env bash
set -euo pipefail

: "${LITELLM_HOST:=http://127.0.0.1:4000}"
: "${LITELLM_HEALTH_ENDPOINT:=/health/liveliness}"
: "${PROM_HOST:=http://127.0.0.1:9090}"
: "${LITELLM_API_KEY:=${LITELLM_MASTER_KEY:-}}"
: "${GUM_BIN:=$(command -v gum || true)}"

have_gum() {
    [[ -n "$GUM_BIN" ]] && command -v "$GUM_BIN" >/dev/null 2>&1
}

render_header() {
    local text="$1"
    if have_gum; then
        "$GUM_BIN" style --border double --padding "0 2" --border-foreground 63 --foreground 212 "$text"
    else
        printf '== %s ==\n' "$text"
    fi
}

render_status_line() {
    local label="$1" status="$2" message="$3"
    local icon color
    case "$status" in
        active|running)
            icon="●"
            color=10
            ;;
        inactive|failed)
            icon="●"
            color=9
            ;;
        *)
            icon="●"
            color=214
            ;;
    esac

    if have_gum; then
        "$GUM_BIN" style --foreground "$color" "$icon" | tr -d '\n'
        printf ' %s %s\n' "$label" "$message"
    else
        printf '[%s] %s %s\n' "$status" "$label" "$message"
    fi
}

render_table() {
    # Reads CSV from stdin.
    if have_gum; then
        "$GUM_BIN" table "$@"
    else
        column -t -s ','
    fi
}

render_logs() {
    if have_gum; then
        "$GUM_BIN" format --markdown
    else
        cat
    fi
}

_litellm_curl() {
    local url="$1"
    local args=(-sSL "$url")
    if [[ -n "$LITELLM_API_KEY" ]]; then
        args=(-sSL -H "Authorization: Bearer $LITELLM_API_KEY" "$url")
    fi
    curl "${args[@]}"
}

http_get_json() {
    _litellm_curl "$1"
}

with_temp_csv() {
    local tmp
    tmp=$(mktemp)
    trap 'rm -f "$tmp"' EXIT
    "$@" | tee "$tmp" >/dev/null
}
