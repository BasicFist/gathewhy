#!/usr/bin/env python3
"""
Download curated GGUF weights for the llama.cpp Python endpoint.

Uses the manifest at config/llamacpp-models.yaml to keep metadata centralized.
The manifest contains `repo_id`, `filename`, and `storage_dir` entries for each
model so both download automation and configuration generation stay in sync.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "config" / "llamacpp-models.yaml"
DEFAULT_ROOT = Path("/home/miko/LAB/models/gguf/library")


def load_manifest() -> list[dict[str, str]]:
    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
            payload = yaml.safe_load(fh) or {}
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"Manifest not found: {MANIFEST_PATH}") from exc
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"Invalid YAML in manifest: {exc}") from exc

    models = payload.get("models", [])
    if not models:
        raise SystemExit("Manifest does not contain any models.")
    return models


def ensure_auth(hf_bin: str) -> None:
    env = os.environ.copy()
    token = env.get("HF_TOKEN", "")
    result = subprocess.run(
        [hf_bin, "auth", "whoami"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            "Hugging Face authentication required. "
            "Export HF_TOKEN or run `hf auth login` before downloading."
        )


def hf_download(hf_bin: str, repo_id: str, filename: str, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    args = [
        hf_bin,
        "download",
        repo_id,
        filename,
        "--local-dir",
        str(target_dir),
        "--revision",
        "main",
    ]
    result = subprocess.run(args, env=env, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to download {filename} from {repo_id}: {result.stderr.strip()}"
        )


def main() -> int:
    model_root = Path(os.environ.get("MODEL_ROOT", DEFAULT_ROOT))
    hf_bin = os.environ.get("HF_BIN") or subprocess.run(
        ["which", "hf"], capture_output=True, text=True, check=False
    ).stdout.strip()

    if not hf_bin:
        raise SystemExit(
            "hf CLI not found. Install with `pip install huggingface_hub[cli]`."
        )

    ensure_auth(hf_bin)
    models = load_manifest()

    print(f"Model library root: {model_root}")
    model_root.mkdir(parents=True, exist_ok=True)

    for entry in models:
        alias = entry["alias"]
        repo_id = entry["repo_id"]
        filename = entry["filename"]
        storage_dir = entry["storage_dir"]
        target_dir = model_root / storage_dir

        print(f"→ Downloading {alias} ({filename})...")
        try:
            hf_download(hf_bin, repo_id, filename, target_dir)
        except RuntimeError as exc:
            print(f"   ✗ {exc}", file=sys.stderr)
            return 1

        target_path = target_dir / filename
        print(f"   Stored at {target_path}")

    print("All requested models downloaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
