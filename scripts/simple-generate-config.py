#!/usr/bin/env python3
"""
Simple LiteLLM Configuration Generator (no dependencies beyond PyYAML).

Generates litellm-unified.yaml from providers.yaml and model-mappings.yaml.
"""

import sys
from datetime import datetime
from pathlib import Path

import yaml


# Custom YAML dumper for proper indentation
class IndentedDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


# Configuration paths
PROJECT_ROOT = Path(__file__).parent.parent
PROVIDERS_FILE = PROJECT_ROOT / "config" / "providers.yaml"
MAPPINGS_FILE = PROJECT_ROOT / "config" / "model-mappings.yaml"
OUTPUT_FILE = PROJECT_ROOT / "config" / "litellm-unified.yaml"


def load_yaml(file_path):
    """Load YAML file."""
    with open(file_path) as f:
        return yaml.safe_load(f)


def build_litellm_params(provider_type, provider_name, model_name, base_url, raw_model):
    """Build provider-specific LiteLLM parameters."""
    if provider_type == "ollama":
        prefix = "ollama_chat" if provider_name == "ollama_cloud" else "ollama"
        params = {"model": f"{prefix}/{model_name}", "api_base": base_url}
        if provider_name == "ollama_cloud":
            params["api_key"] = "os.environ/OLLAMA_API_KEY"
        if isinstance(raw_model, dict):
            options = raw_model.get("options")
            if options:
                params["extra_body"] = {"options": options}
        return params

    elif provider_type == "llama_cpp":
        return {"model": "openai/local-model", "api_base": base_url, "stream": True}

    elif provider_type == "vllm":
        api_base = base_url.rstrip("/")
        if not api_base.endswith("/v1"):
            api_base = f"{api_base}/v1"
        params = {
            "model": model_name,
            "api_base": api_base,
            "custom_llm_provider": "openai",
            "stream": True,
        }
        if not params.get("api_key"):
            params["api_key"] = "not-needed"
        return params

    elif provider_type == "openai":
        return {"model": model_name, "api_key": "os.environ/OPENAI_API_KEY"}

    elif provider_type == "anthropic":
        return {"model": model_name, "api_key": "os.environ/ANTHROPIC_API_KEY"}

    elif provider_type == "openai_compatible":
        return {"model": f"openai/{model_name}", "api_base": base_url}

    # Generic fallback
    return {"model": model_name, "api_base": base_url}


def build_tags(model):
    """Build tag list from model metadata."""
    if not isinstance(model, dict):
        return ["general"]

    tags = []
    if "specialty" in model:
        tags.append(model["specialty"])
    if "size" in model:
        tags.append(model["size"].lower())
    if "quantization" in model:
        tags.append(model["quantization"].lower())

    return tags or ["general"]


def generate_config():
    """Generate LiteLLM configuration."""
    print("Loading source configurations...")

    providers_data = load_yaml(PROVIDERS_FILE)
    mappings_data = load_yaml(MAPPINGS_FILE)

    print("Building model list...")

    model_list = []
    providers_config = providers_data.get("providers", {})

    for provider_name, provider_config in providers_config.items():
        if provider_config.get("status") != "active":
            print(f"  Skipping inactive provider: {provider_name}")
            continue

        provider_type = provider_config.get("type")
        base_url = provider_config.get("base_url")
        models = provider_config.get("models", [])

        print(f"  Processing provider: {provider_name} ({len(models)} models)")

        for raw_model in models:
            # Extract model name
            if isinstance(raw_model, str):
                model_name = raw_model
            elif isinstance(raw_model, dict):
                model_name = raw_model.get("name", raw_model.get("model"))
            else:
                continue

            # Build LiteLLM params
            litellm_params = build_litellm_params(
                provider_type, provider_name, model_name, base_url, raw_model
            )

            # Build tags
            tags = build_tags(raw_model)

            # Create model entry
            model_entry = {
                "model_name": model_name,
                "litellm_params": litellm_params,
                "model_info": {
                    "tags": tags,
                    "provider": provider_name,
                },
            }

            # Add context length if available
            if isinstance(raw_model, dict) and "context_length" in raw_model:
                model_entry["model_info"]["context_length"] = raw_model["context_length"]

            model_list.append(model_entry)

    print(f"Generated {len(model_list)} model entries")

    # Build configuration
    config = {
        "model_list": model_list,
        "litellm_settings": {
            "request_timeout": 60,
            "stream_timeout": 120,
            "num_retries": 3,
            "timeout": 300,
            "cache": True,
            "cache_params": {
                "type": "redis",
                "host": "127.0.0.1",
                "port": 6379,
                "ttl": 3600,
            },
            "set_verbose": True,
            "json_logs": True,
        },
        "router_settings": {
            "routing_strategy": "simple-shuffle",
            "allowed_fails": 5,
            "num_retries": 2,
            "timeout": 30,
            "cooldown_time": 60,
            "enable_pre_call_checks": True,
            "redis_host": "127.0.0.1",
            "redis_port": 6379,
        },
    }

    # Add model group aliases from capabilities
    capabilities = mappings_data.get("capabilities", {})
    model_group_alias = {}

    for cap_name, cap_config in capabilities.items():
        preferred_models = cap_config.get("preferred_models", [])
        if preferred_models:
            model_group_alias[cap_name] = preferred_models[:1]  # First model only for alias

    if model_group_alias:
        config["router_settings"]["model_group_alias"] = model_group_alias

    # Write configuration
    print(f"Writing configuration to {OUTPUT_FILE}...")

    header = f"""# ============================================================================
# AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
# ============================================================================
#
# Generated by: scripts/simple-generate-config.py
# Source files: config/providers.yaml, config/model-mappings.yaml
# Generated at: {datetime.now().isoformat()}
#
# To modify this configuration:
#   1. Edit config/providers.yaml or config/model-mappings.yaml
#   2. Run: python3 scripts/simple-generate-config.py
#
# ============================================================================

"""

    with open(OUTPUT_FILE, "w") as f:
        f.write(header)
        yaml.dump(config, f, Dumper=IndentedDumper, default_flow_style=False, sort_keys=False)

    print(f"✓ Configuration generated successfully!")
    print(f"  Total models: {len(model_list)}")
    print(f"  Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        generate_config()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
