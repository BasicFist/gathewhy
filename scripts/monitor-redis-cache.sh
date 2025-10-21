#!/usr/bin/env bash
#
# Redis Cache Monitoring Script
# Monitors LiteLLM cache usage and provider-specific patterns
#
# Usage:
#   ./scripts/monitor-redis-cache.sh            # Show current cache stats
#   ./scripts/monitor-redis-cache.sh --keys     # List all cache keys
#   ./scripts/monitor-redis-cache.sh --flush    # Flush all LiteLLM cache (requires confirmation)
#   ./scripts/monitor-redis-cache.sh --watch    # Continuous monitoring (updates every 5s)
#

set -euo pipefail

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly REDIS_HOST="127.0.0.1"
readonly REDIS_PORT="6379"
readonly NAMESPACE="litellm"

# Flags
MODE="stats"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keys)
            MODE="keys"
            shift
            ;;
        --flush)
            MODE="flush"
            shift
            ;;
        --watch)
            MODE="watch"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--keys|--flush|--watch]"
            echo ""
            echo "Modes:"
            echo "  (none)    Show cache statistics"
            echo "  --keys    List all LiteLLM cache keys"
            echo "  --flush   Flush all LiteLLM cache keys (requires confirmation)"
            echo "  --watch   Continuous monitoring (updates every 5s)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if redis-cli is available
if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} redis-cli not found. Install with: sudo apt install redis-tools"
    exit 1
fi

# Check if Redis is running
if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Redis server not responding on ${REDIS_HOST}:${REDIS_PORT}"
    exit 1
fi

show_cache_stats() {
    echo -e "${BLUE}=== LiteLLM Redis Cache Statistics ===${NC}"
    echo ""

    # Total keys
    local total_keys=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern "${NAMESPACE}:*" | wc -l)
    echo -e "${GREEN}Total LiteLLM cache keys:${NC} $total_keys"

    # Redis info
    echo ""
    echo -e "${BLUE}Redis Server Info:${NC}"
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO stats | grep -E "^(keyspace_hits|keyspace_misses|expired_keys):"

    # Calculate hit rate
    local hits=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO stats | grep "^keyspace_hits:" | cut -d: -f2 | tr -d '\r')
    local misses=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO stats | grep "^keyspace_misses:" | cut -d: -f2 | tr -d '\r')

    if [[ -n "$hits" && -n "$misses" && $((hits + misses)) -gt 0 ]]; then
        local hit_rate=$(echo "scale=2; $hits * 100 / ($hits + $misses)" | bc)
        echo -e "${GREEN}Cache hit rate:${NC} ${hit_rate}%"
    fi

    # Memory usage
    echo ""
    echo -e "${BLUE}Memory Usage:${NC}"
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO memory | grep -E "^(used_memory_human|used_memory_peak_human):"

    # Provider-specific key counts (approximate based on model names)
    echo ""
    echo -e "${BLUE}Keys by Provider (approximate):${NC}"

    # Count keys containing provider patterns
    local ollama_count=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern "${NAMESPACE}:*" | grep -i "ollama\|llama3\|qwen2.5-coder" | wc -l)
    local vllm_count=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern "${NAMESPACE}:*" | grep -i "vllm\|llama2-13b" | wc -l)
    local llamacpp_count=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern "${NAMESPACE}:*" | grep -i "llama-cpp" | wc -l)

    echo "  Ollama models:     $ollama_count keys"
    echo "  vLLM models:       $vllm_count keys"
    echo "  llama.cpp models:  $llamacpp_count keys"
}

list_cache_keys() {
    echo -e "${BLUE}=== LiteLLM Cache Keys ===${NC}"
    echo ""

    local keys=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern "${NAMESPACE}:*")

    if [[ -z "$keys" ]]; then
        echo -e "${YELLOW}No cache keys found${NC}"
        return
    fi

    echo "$keys" | while IFS= read -r key; do
        # Get TTL
        local ttl=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" TTL "$key")

        # Format TTL
        if [[ $ttl -eq -1 ]]; then
            ttl_display="no expiry"
        elif [[ $ttl -eq -2 ]]; then
            ttl_display="expired"
        else
            ttl_display="${ttl}s"
        fi

        echo -e "${GREEN}${key}${NC} (TTL: ${ttl_display})"
    done
}

flush_cache() {
    echo -e "${YELLOW}[WARNING]${NC} This will flush ALL LiteLLM cache keys (${NAMESPACE}:*)"
    echo ""
    echo -n "Are you sure? Type 'yes' to confirm: "
    read -r response

    if [[ "$response" != "yes" ]]; then
        echo -e "${BLUE}[INFO]${NC} Flush cancelled"
        exit 0
    fi

    echo ""
    echo -e "${BLUE}[INFO]${NC} Flushing LiteLLM cache keys..."

    # Get all LiteLLM keys and delete them
    local keys=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --scan --pattern "${NAMESPACE}:*")
    local count=0

    if [[ -n "$keys" ]]; then
        echo "$keys" | while IFS= read -r key; do
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DEL "$key" > /dev/null
            count=$((count + 1))
        done
    fi

    echo -e "${GREEN}[✓]${NC} Flushed cache (approximate keys deleted: $count)"
}

watch_cache() {
    echo -e "${BLUE}=== LiteLLM Cache Monitor (updating every 5s) ===${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
    echo ""

    while true; do
        clear
        show_cache_stats
        sleep 5
    done
}

# Execute based on mode
case "$MODE" in
    stats)
        show_cache_stats
        ;;
    keys)
        list_cache_keys
        ;;
    flush)
        flush_cache
        ;;
    watch)
        watch_cache
        ;;
esac
