#!/usr/bin/env python3
"""
Print logical configuration snapshot (JSON) for introspection.
Redacts secrets.
"""
import json
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
PROVIDERS_FILE = PROJECT_ROOT / "config" / "providers.yaml"
MAPPINGS_FILE = PROJECT_ROOT / "config" / "model-mappings.yaml"


def build_snapshot():
    with open(PROVIDERS_FILE) as f:
        providers = yaml.safe_load(f)

    with open(MAPPINGS_FILE) as f:
        mappings = yaml.safe_load(f)

    snapshot = {"providers": {}, "logical_models": [], "capabilities": {}, "routing": {}}

    # Process Providers (Redact secrets)
    for name, cfg in providers.get("providers", {}).items():
        cfg_copy = cfg.copy()
        if "configuration" in cfg_copy:
            # Redact known sensitive keys
            for k in list(cfg_copy["configuration"].keys()):
                if "key" in k.lower() or "token" in k.lower() or "password" in k.lower():
                    cfg_copy["configuration"][k] = "***REDACTED***"
        snapshot["providers"][name] = cfg_copy

    # Process Logical Models (Exact Matches)
    for name, cfg in mappings.get("exact_matches", {}).items():
        snapshot["logical_models"].append(
            {
                "name": name,
                "provider": cfg.get("provider"),
                "priority": cfg.get("priority"),
                "fallback": cfg.get("fallback"),
                "tags": ["logical_model"],
            }
        )

    # Process Capabilities
    snapshot["capabilities"] = mappings.get("capabilities", {})

    # Routing
    snapshot["routing"] = {
        "patterns": mappings.get("patterns", []),
        "fallbacks": mappings.get("fallback_chains", {}),
    }

    return snapshot


if __name__ == "__main__":
    print(json.dumps(build_snapshot(), indent=2))
