#!/usr/bin/env bash
# Prune stale llama.cpp and vLLM cache directories to reclaim disk/V RAM pressure.
#
# Removes cache entries older than CACHE_MAX_DAYS (default 7) from:
#   - ~/.cache/vllm
#   - ~/.cache/huggingface
#   - ~/.cache/llama.cpp (if present)
#
# Designed to run as a systemd user timer (see llm-cache-prune.service/timer).
set -euo pipefail

CACHE_MAX_DAYS="${CACHE_MAX_DAYS:-7}"
TARGETS=(
  "${HOME}/.cache/vllm"
  "${HOME}/.cache/huggingface"
  "${HOME}/.cache/llama.cpp"
)

log() {
  printf '[LLM-CACHE] %s\n' "$*"
}

for dir in "${TARGETS[@]}"; do
  if [[ ! -d "${dir}" ]]; then
    continue
  fi

  log "Pruning caches in ${dir} older than ${CACHE_MAX_DAYS} days"
  find "${dir}" -mindepth 1 -maxdepth 1 -mtime +"${CACHE_MAX_DAYS}" -exec rm -rf {} + 2>/dev/null || true
done

log "Cache pruning complete."
