#!/usr/bin/env python3
"""
Provider Management Script
Safely enable/disable models in LiteLLM unified configuration
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

CONFIG_FILE = Path(__file__).parent.parent / "config" / "litellm-unified.yaml"
BACKUP_DIR = Path(__file__).parent.parent / "config" / "backups"


def load_config():
    """Load the LiteLLM configuration"""
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def save_config(config, backup=True):
    """Save configuration with optional backup"""
    if backup:
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"litellm-unified.{timestamp}.yaml"
        shutil.copy2(CONFIG_FILE, backup_file)
        print(f"✓ Backup created: {backup_file}")

    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    print(f"✓ Configuration updated: {CONFIG_FILE}")


def list_models():
    """List all models with their status"""
    config = load_config()
    models = config.get("model_list", [])

    print("\n📋 Available Models:\n")
    for idx, model in enumerate(models, 1):
        model_name = model.get("model_name", "unknown")
        provider = model.get("model_info", {}).get("provider", "unknown")
        enabled = model.get("_disabled", False) is False
        status = "✅ ENABLED" if enabled else "❌ DISABLED"

        print(f"{idx}. {status} | {model_name} ({provider})")
        if "api_base" in model.get("litellm_params", {}):
            api_base = model["litellm_params"]["api_base"]
            print(f"   └─ Endpoint: {api_base}")

    return models


def enable_model(model_name):
    """Enable a model in the configuration"""
    config = load_config()
    models = config.get("model_list", [])

    found = False
    for model in models:
        if model.get("model_name") == model_name:
            if "_disabled" in model:
                del model["_disabled"]
            found = True
            print(f"✓ Enabled: {model_name}")
            break

    if not found:
        print(f"✗ Model not found: {model_name}", file=sys.stderr)
        return False

    save_config(config)
    return True


def disable_model(model_name):
    """Disable a model in the configuration"""
    config = load_config()
    models = config.get("model_list", [])

    found = False
    for model in models:
        if model.get("model_name") == model_name:
            model["_disabled"] = True
            found = True
            print(f"✓ Disabled: {model_name}")
            break

    if not found:
        print(f"✗ Model not found: {model_name}", file=sys.stderr)
        return False

    save_config(config)
    return True


def enable_provider(provider_name):
    """Enable all models from a specific provider"""
    config = load_config()
    models = config.get("model_list", [])

    count = 0
    for model in models:
        if model.get("model_info", {}).get("provider") == provider_name:
            if "_disabled" in model:
                del model["_disabled"]
            count += 1

    if count == 0:
        print(f"✗ No models found for provider: {provider_name}", file=sys.stderr)
        return False

    print(f"✓ Enabled {count} model(s) for provider: {provider_name}")
    save_config(config)
    return True


def disable_provider(provider_name):
    """Disable all models from a specific provider"""
    config = load_config()
    models = config.get("model_list", [])

    count = 0
    for model in models:
        if model.get("model_info", {}).get("provider") == provider_name:
            model["_disabled"] = True
            count += 1

    if count == 0:
        print(f"✗ No models found for provider: {provider_name}", file=sys.stderr)
        return False

    print(f"✓ Disabled {count} model(s) for provider: {provider_name}")
    save_config(config)
    return True


def get_providers():
    """Get list of unique providers"""
    config = load_config()
    models = config.get("model_list", [])
    providers = set()

    for model in models:
        provider = model.get("model_info", {}).get("provider")
        if provider:
            providers.add(provider)

    return sorted(providers)


def main():
    parser = argparse.ArgumentParser(description="Manage LiteLLM providers and models")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    subparsers.add_parser("list", help="List all models")

    # Enable/disable model
    enable_parser = subparsers.add_parser("enable", help="Enable a model")
    enable_parser.add_argument("model", help="Model name to enable")

    disable_parser = subparsers.add_parser("disable", help="Disable a model")
    disable_parser.add_argument("model", help="Model name to disable")

    # Enable/disable provider
    enable_prov = subparsers.add_parser("enable-provider", help="Enable all models from a provider")
    enable_prov.add_argument("provider", help="Provider name (ollama, vllm)")

    disable_prov = subparsers.add_parser(
        "disable-provider", help="Disable all models from a provider"
    )
    disable_prov.add_argument("provider", help="Provider name (ollama, vllm)")

    # List providers
    subparsers.add_parser("providers", help="List available providers")

    args = parser.parse_args()

    if args.command == "list":
        list_models()
    elif args.command == "enable":
        enable_model(args.model)
    elif args.command == "disable":
        disable_model(args.model)
    elif args.command == "enable-provider":
        enable_provider(args.provider)
    elif args.command == "disable-provider":
        disable_provider(args.provider)
    elif args.command == "providers":
        providers = get_providers()
        print("\n🔌 Available Providers:\n")
        for provider in providers:
            print(f"  • {provider}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
