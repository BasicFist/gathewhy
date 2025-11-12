#!/usr/bin/env python3
"""
Swap the active llama.cpp model by updating current.gguf based on the manifest.

Usage:
    scripts/llamacpp/switch_model.sh <alias>
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "config" / "llamacpp-models.yaml"
MODELS_ROOT = Path(os.environ.get("MODELS_ROOT", "/home/miko/LAB/models/gguf/library"))
ACTIVE_DIR = Path(os.environ.get("ACTIVE_DIR", "/home/miko/LAB/models/gguf/active"))
SYSTEMD_UNIT = os.environ.get("SYSTEMD_UNIT", "llamacpp-python.service")


def load_manifest() -> dict[str, dict[str, str]]:
    try:
        data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"Manifest not found: {MANIFEST_PATH}") from exc
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"Invalid YAML in manifest: {exc}") from exc

    mapping: dict[str, dict[str, str]] = {}
    for entry in data.get("models", []):
        alias = entry.get("alias")
        if not alias:
            continue
        mapping[alias] = entry
    return mapping


def restart_service() -> None:
    subprocess.run(
        ["systemctl", "--user", "restart", SYSTEMD_UNIT],
        check=True,
        env={"PATH": "/usr/bin:/bin"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: scripts/llamacpp/switch_model.sh <alias>", file=sys.stderr)
        return 1

    alias = argv[1]
    manifest = load_manifest()

    if alias not in manifest:
        print(f"Unknown alias '{alias}'.", file=sys.stderr)
        return 1

    entry = manifest[alias]
    storage_dir = entry["storage_dir"]
    filename = entry["filename"]

    src = MODELS_ROOT / storage_dir / filename
    if not src.exists():
        print(f"Model file not found: {src}", file=sys.stderr)
        return 1

    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    target = ACTIVE_DIR / "current.gguf"
    if target.exists() or target.is_symlink():
        target.unlink()
    target.symlink_to(src)

    print(f"Restarting {SYSTEMD_UNIT}...")
    restart_service()
    print(f"{alias} is now active.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
