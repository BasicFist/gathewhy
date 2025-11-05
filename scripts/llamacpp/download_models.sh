#!/usr/bin/env bash
#
# Download curated GGUF weights for the llama.cpp Python endpoint.
# Requires the `hf` CLI and a Hugging Face token with access to TheBloke repos.
#
# Usage:
#   HF_TOKEN=hf_xxx scripts/llamacpp/download_models.sh
#   # or export HF_TOKEN globally / run `hf auth login` beforehand.
#
set -euo pipefail

MODEL_ROOT="${MODEL_ROOT:-/home/miko/LAB/models/gguf/library}"

MODELS=$(
  cat <<'EOF'
Meta-Llama-3.1-8B-Instruct-Q4_K_M|bartowski/Meta-Llama-3.1-8B-Instruct-GGUF|Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
Mistral-Nemo-Instruct-2407-Q4_K_M|QuantFactory/Mistral-Nemo-Instruct-2407-GGUF|Mistral-Nemo-Instruct-2407.Q4_K_M.gguf
DeepSeek-Coder-V2-Lite-Q4_K_M|QuantFactory/DeepSeek-Coder-V2-Lite-Instruct-GGUF|DeepSeek-Coder-V2-Lite-Instruct.Q4_K_M.gguf
OpenHermes-2.5-Mistral-Q5_K_M|TheBloke/OpenHermes-2.5-Mistral-7B-GGUF|openhermes-2.5-mistral-7b.Q5_K_M.gguf
Phi-3-medium-4k-instruct-Q4_K_M|ssmits/Phi-3-medium-4k-instruct-Q4_K_M-GGUF|phi-3-medium-4k-instruct.Q4_K_M.gguf
Mixtral-8x7B-Instruct-v0.1-Q4_K_M|TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF|mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf
EOF
)

HF_BIN="$(command -v hf || true)"
if [[ -z "${HF_BIN}" ]]; then
  echo "ERROR: hf CLI not found. Install with 'pip install huggingface_hub[cli]'." >&2
  exit 1
fi

echo "Model library root: ${MODEL_ROOT}"
mkdir -p "${MODEL_ROOT}"

echo "Checking Hugging Face authentication..."
if ! HF_TOKEN="${HF_TOKEN:-}" "${HF_BIN}" auth whoami >/dev/null 2>&1; then
  cat >&2 <<'MSG'
ERROR: Not authenticated with Hugging Face.
Please export HF_TOKEN or run `hf auth login` before downloading gated model files.
MSG
  exit 1
fi

while IFS='|' read -r DISPLAY_NAME REPO_ID FILENAME; do
  [[ -z "${DISPLAY_NAME}" ]] && continue
  TARGET_DIR="${MODEL_ROOT}/${DISPLAY_NAME}"
  mkdir -p "${TARGET_DIR}"

  echo "→ Downloading ${DISPLAY_NAME} (${FILENAME})..."
  HF_TOKEN="${HF_TOKEN:-}" "${HF_BIN}" download \
    "${REPO_ID}" "${FILENAME}" \
    --local-dir "${TARGET_DIR}" \
    --revision main

  echo "   Stored at ${TARGET_DIR}/${FILENAME}"
done <<< "${MODELS}"

echo "All requested models downloaded into ${MODEL_ROOT}."
