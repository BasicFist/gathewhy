#!/usr/bin/env bash
#
# wait-for-service.sh - Wait for service to become healthy
#
# Usage:
#   wait-for-service.sh SERVICE_NAME HEALTH_ENDPOINT [MAX_WAIT_SECONDS]
#
# Examples:
#   wait-for-service.sh Redis http://localhost:6379 30
#   wait-for-service.sh LiteLLM http://localhost:4000/health 60
#   wait-for-service.sh Ollama http://localhost:11434/api/tags 30
#

set -euo pipefail

# Arguments
SERVICE_NAME="${1:-Service}"
ENDPOINT="${2:-}"
MAX_WAIT="${3:-30}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [[ -z "$ENDPOINT" ]]; then
    echo -e "${RED}Error: ENDPOINT required${NC}"
    echo "Usage: $0 SERVICE_NAME ENDPOINT [MAX_WAIT_SECONDS]"
    exit 1
fi

echo -e "${YELLOW}Waiting for $SERVICE_NAME to become healthy...${NC}"
echo "  Endpoint: $ENDPOINT"
echo "  Timeout: ${MAX_WAIT}s"

for i in $(seq 1 "$MAX_WAIT"); do
    if curl -sf "$ENDPOINT" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $SERVICE_NAME is healthy (after ${i}s)${NC}"
        exit 0
    fi

    if [[ $((i % 5)) -eq 0 ]]; then
        echo "  Still waiting... (${i}/${MAX_WAIT}s)"
    fi

    sleep 1
done

echo -e "${RED}❌ $SERVICE_NAME failed health check after ${MAX_WAIT}s${NC}"
exit 1
