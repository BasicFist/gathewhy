#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

render_header "Vue d'ensemble des providers"

if ! response=$(http_get_json "$LITELLM_HOST/v1/models" 2>/dev/null); then
    if have_gum; then
        "$GUM_BIN" style --foreground 9 "Impossible d'atteindre $LITELLM_HOST/v1/models"
    else
        echo "Erreur: impossible de joindre $LITELLM_HOST/v1/models"
    fi
    exit 1
fi

if ! jq -e '.data' >/dev/null 2>&1 <<<"$response"; then
    msg=$(jq -r '.error.message // "Aucune donnée disponible (base non connectée ?)"' <<<"$response")
    if have_gum; then
        "$GUM_BIN" style --foreground 11 "$msg"
    else
        echo "$msg"
    fi
    exit 0
fi

declare -A counts
total=0

while IFS= read -r line; do
    model_id=$(jq -r '.id' <<<"$line")
    provider=$(jq -r '.metadata.provider // .owned_by // "unknown"' <<<"$line")
    ((counts[$provider]++))
    ((total++))
done < <(jq -c '.data[]' <<<"$response")

printf 'Provider,Modèles\n' > /tmp/providers-overview.csv
for provider in "${!counts[@]}"; do
    printf '%s,%s\n' "$provider" "${counts[$provider]}" >> /tmp/providers-overview.csv
done

render_table < /tmp/providers-overview.csv --widths 30,10
rm -f /tmp/providers-overview.csv

if have_gum; then
    "$GUM_BIN" style --foreground 10 --bold "Total: $total modèles"
else
    echo "Total: $total modèles"
fi
