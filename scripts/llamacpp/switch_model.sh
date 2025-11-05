#!/usr/bin/env bash
# Switch the active llama.cpp model by updating the current.gguf symlink.
# Usage: scripts/llamacpp/switch_model.sh <alias>
set -euo pipefail

MODELS_ROOT="${MODELS_ROOT:-/home/miko/LAB/models/gguf/library}"
ACTIVE_DIR="${ACTIVE_DIR:-/home/miko/LAB/models/gguf/active}"
SYSTEMD_UNIT="llamacpp-python.service"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <model-alias>" >&2
  exit 1
fi

alias="$1"

case "$alias" in
  llama-cpp-llama3.1)
    target="Meta-Llama-3.1-8B-Instruct-Q4_K_M/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    ;;
  llama-cpp-mistral-nemo)
    target="Mistral-Nemo-Instruct-2407-Q4_K_M/Mistral-Nemo-Instruct-2407.Q4_K_M.gguf"
    ;;
  llama-cpp-deepseek-coder-lite)
    target="DeepSeek-Coder-V2-Lite-Q4_K_M/DeepSeek-Coder-V2-Lite-Instruct.Q4_K_M.gguf"
    ;;
  llama-cpp-openhermes-2.5)
    target="OpenHermes-2.5-Mistral-Q5_K_M/openhermes-2.5-mistral-7b.Q5_K_M.gguf"
    ;;
  llama-cpp-phi3-medium)
    target="Phi-3-medium-4k-instruct-Q4_K_M/phi-3-medium-4k-instruct.Q4_K_M.gguf"
    ;;
  llama-cpp-mixtral-8x7b)
    target="Mixtral-8x7B-Instruct-v0.1-Q4_K_M/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
    ;;
  *)
    echo "Unknown alias '$alias'." >&2
    exit 1
    ;;
esac

src="${MODELS_ROOT}/${target}"
if [[ ! -f "${src}" ]]; then
  echo "Model file not found: ${src}" >&2
  exit 1
fi

mkdir -p "${ACTIVE_DIR}"
ln -sf "${src}" "${ACTIVE_DIR}/current.gguf"

echo "Restarting ${SYSTEMD_UNIT}..."
systemctl --user restart "${SYSTEMD_UNIT}"
echo "${alias} is now active."
