#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

: "${LITELLM_METRICS_ENDPOINT:=/metrics}"

render_header "LiteLLM Key Metrics"

if ! metrics=$(http_get_json "$LITELLM_HOST$LITELLM_METRICS_ENDPOINT" 2>/dev/null); then
    if have_gum; then
        "$GUM_BIN" style --foreground 9 "Failed to download metrics from $LITELLM_HOST$LITELLM_METRICS_ENDPOINT"
    else
        echo "Failed to download metrics from $LITELLM_HOST$LITELLM_METRICS_ENDPOINT"
    fi
    exit 1
fi

printf 'Metric,Value\n' > /tmp/litellm-metrics.csv

extract() {
    local name="$1" regex="$2"
    value=$(printf '%s\n' "$metrics" | awk "$regex" | head -1 | awk '{print $2}')
    printf '%s,%s\n' "$name" "${value:-N/A}" >> /tmp/litellm-metrics.csv
}

extract "Requests total" '/^litellm_requests_total/{print}'
extract "Cache hits" '/^litellm_cache_hits_total/{print}'
extract "Cache misses" '/^litellm_cache_misses_total/{print}'
extract "Avg latency (ms)" '/^litellm_latency_ms_sum/{sum=
$2; next} /^litellm_latency_ms_count/{count=$2; if (count>0) printf "litellm_latency_ms_avg %f\n", sum/count}'

render_table < /tmp/litellm-metrics.csv --widths 30,20
rm -f /tmp/litellm-metrics.csv
