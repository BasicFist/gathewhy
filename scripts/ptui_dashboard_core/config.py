"""Configuration helpers for the PTUI dashboard."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .models import Service

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "config" / "providers.yaml"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def validate_env_float(name: str, default: str, min_val: float, max_val: float) -> float:
    """Validate float environment variables while enforcing sane bounds."""

    value_str = os.getenv(name, default)
    try:
        value = float(value_str)
    except ValueError as exc:
        print(f"Invalid {name}: {exc}. Using default: {default}", file=sys.stderr)
        return float(default)

    if not min_val <= value <= max_val:
        print(
            f"Invalid {name}: must be between {min_val} and {max_val}, got {value}. Using default: {default}",
            file=sys.stderr,
        )
        return float(default)
    return value


DEFAULT_HTTP_TIMEOUT = validate_env_float("PTUI_HTTP_TIMEOUT", "10", 0.5, 120.0)
AUTO_REFRESH_SECONDS = validate_env_float("PTUI_REFRESH_SECONDS", "5", 1.0, 60.0)


def _default_services() -> list[Service]:
    return [
        Service("LiteLLM Gateway", "http://localhost:4000", "/health/liveliness", required=True),
        Service("Ollama", "http://localhost:11434", "/api/tags", required=True),
        Service("llama.cpp (Python)", "http://localhost:8000", "/v1/models", required=False),
        Service("llama.cpp (Native)", "http://localhost:8080", "/v1/models", required=False),
        Service("vLLM", "http://localhost:8001", "/v1/models", required=False),
    ]


def load_services_from_config() -> list[Service]:
    """Load services from config/providers.yaml with a well-defined fallback."""

    if not CONFIG_FILE.exists():
        return _default_services()

    try:
        try:
            import yaml  # type: ignore
        except ImportError:
            return _default_services()

        with open(CONFIG_FILE) as handle:
            config = yaml.safe_load(handle)

        if not config or "providers" not in config:
            return _default_services()

        services: list[Service] = []
        providers = config.get("providers", {})
        provider_map = {
            "ollama": ("Ollama", "/api/tags", True),
            "vllm": ("vLLM", "/v1/models", False),
            "llama_cpp_python": ("llama.cpp (Python)", "/v1/models", False),
            "llama_cpp_native": ("llama.cpp (Native)", "/v1/models", False),
            "litellm_gateway": ("LiteLLM Gateway", "/health/liveliness", True),
        }

        for key, provider_data in providers.items():
            if provider_data.get("status") != "active":
                continue

            base_url = provider_data.get("base_url", "")
            if key in provider_map:
                display_name, endpoint, required = provider_map[key]
            else:
                display_name = provider_data.get("description", key)
                endpoint = provider_data.get("health_endpoint", "/health")
                required = False

            services.append(Service(display_name, base_url, endpoint, required))

        if not any(service.name == "LiteLLM Gateway" for service in services):
            services.insert(0, Service("LiteLLM Gateway", "http://localhost:4000", "/health/liveliness", True))

        return services or _default_services()
    except Exception as exc:  # pragma: no cover - fallback guard
        print(f"Warning: Failed to load providers config: {exc}", file=sys.stderr)
        return _default_services()
