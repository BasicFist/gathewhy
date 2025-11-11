#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

: "${PROM_HOST:=http://127.0.0.1:9090}"

render_header "Performance du cache"

metrics=$(curl -fsS "$PROM_HOST/metrics" 2>/dev/null || true)
if [[ -z "$metrics" ]]; then
    if have_gum; then
        "$GUM_BIN" style --foreground 9 "Prometheus indisponible sur $PROM_HOST"
    else
        echo "Impossible de joindre $PROM_HOST"
    fi
    exit 1
fi

hits=$(grep -m1 'litellm_cache_hit_total' <<<"$metrics" | awk '{print $NF+0}')
misses=$(grep -m1 'litellm_cache_miss_total' <<<"$metrics" | awk '{print $NF+0}')
total=$((hits + misses))

if (( total > 0 )); then
    hit_rate=$(echo "scale=2; ($hits / $total) * 100" | bc -l)
else
    hit_rate=0
fi

savings=$(echo "scale=2; $hits * 0.002" | bc -l)

printf 'Métrique,Valeur\nCache Hits,%s\nCache Misses,%s\nHit Rate,%s%%\nÉconomies estimées,$%s\n' "$hits" "$misses" "$hit_rate" "$savings" > /tmp/cache.csv

render_table < /tmp/cache.csv --widths 20,20

connections=$(grep -m1 'litellm_redis_connection_pool_size' <<<"$metrics" | awk '{print $NF+0}')
if have_gum; then
    "$GUM_BIN" style --margin "1 0" --foreground 39 "Connexions Redis actives: ${connections:-N/A}"
else
    echo "Connexions Redis actives: ${connections:-N/A}"
fi

if (( $(echo "$hit_rate < 20" | bc -l) )); then
    if have_gum; then
        "$GUM_BIN" style --foreground 9 --bold "Hit rate faible: envisager d'ajuster le TTL"
    else
        echo "Hit rate faible"
    fi
fi

rm -f /tmp/cache.csv
