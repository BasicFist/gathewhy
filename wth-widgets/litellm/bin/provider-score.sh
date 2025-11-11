#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

: "${PROM_HOST:=http://127.0.0.1:9090}"

render_header "Score providers"

metrics_file=$(mktemp)
if ! curl -fsS "$PROM_HOST/metrics" > "$metrics_file"; then
    if have_gum; then
        "$GUM_BIN" style --foreground 9 "Prometheus indisponible sur $PROM_HOST"
    else
        echo "Impossible de joindre $PROM_HOST"
    fi
    rm -f "$metrics_file"
    exit 1
fi

printf 'Provider,RPM,Latence(ms),Erreurs%%,Score\n' > /tmp/provider-score.csv

providers=$(grep -o 'model_group="[^"]*"' "$metrics_file" | cut -d'"' -f2 | sort -u)

for provider in $providers; do
    reqs=$(awk -v p="$provider" '/litellm_requests_metric{/ && $0 ~ "model_group=\""p"\"" {sum+=$NF} END {print sum}' "$metrics_file")
    rpm=$(printf '%.0f' "${reqs:-0}")

    lat_avg=$(awk -v p="$provider" '/litellm_llm_api_latency_metric{/ && $0 ~ "model_group=\""p"\"" {sum+=$NF; count++} END {if(count>0) printf "%f", sum/count; else print "0"}' "$metrics_file")
    lat_ms=$(printf '%.0f' "$(echo "${lat_avg:-0}*1000" | bc -l)")

    success=$(awk -v p="$provider" '/litellm_deployment_success_responses{/ && $0 ~ "model_group=\""p"\"" {sum+=$NF} END {print sum}' "$metrics_file")
    failures=$(awk -v p="$provider" '/litellm_deployment_failure_responses{/ && $0 ~ "model_group=\""p"\"" {sum+=$NF} END {print sum}' "$metrics_file")
    total=$(( ${success:-0} + ${failures:-0} ))
    if (( total > 0 )); then
        error_pct=$(echo "scale=2; (${failures:-0} / $total) * 100" | bc -l)
    else
        error_pct=0
    fi

    score=$(echo "scale=0; 100 - ($lat_ms / 20) - ($error_pct * 5)" | bc -l)
    printf '%s,%s,%s,%.2f,%s\n' "$provider" "$rpm" "$lat_ms" "$error_pct" "$score" >> /tmp/provider-score.csv
done

render_table < /tmp/provider-score.csv --widths 15,10,12,12,10

best=$(tail -n +2 /tmp/provider-score.csv | sort -t',' -k5 -nr | head -1 | cut -d',' -f1)
if have_gum && [[ -n "$best" ]]; then
    "$GUM_BIN" style --margin "1 0" --foreground 10 --bold "Meilleur provider: $best"
fi

rm -f "$metrics_file" /tmp/provider-score.csv
