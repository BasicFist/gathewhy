#!/usr/bin/env python3
"""
Pydantic-based configuration schema validation for AI Backend Unified Infrastructure
Provides strong typing and semantic validation beyond YAML syntax checking
"""

import sys
from pathlib import Path
from typing import Any, Literal

import yaml
from common_utils import _resolve_env_var
from pydantic import BaseModel, Field, field_validator, model_validator

# ============================================================================
# PROVIDER CONFIGURATION MODELS
# ============================================================================


class ProviderModel(BaseModel):
    """Model definition within a provider"""

    name: str
    size: str | None = None
    quantization: str | None = None
    specialty: str | None = None
    context_length: int | None = None
    pulled_at: str | None = None


class ProviderConfig(BaseModel):
    """Individual provider configuration"""

    type: Literal[
        "ollama",
        "llama_cpp",
        "vllm",
        "openai",
        "anthropic",
        "openai_compatible",
        "tool_server",
        "web_ui",
    ]
    base_url: str
    status: Literal["active", "disabled", "pending_integration", "template"]
    description: str
    models: list[
        ProviderModel | str
    ] | None = []  # Allow both ProviderModel objects and simple strings
    health_endpoint: str | None = None
    features: list[str] | None = []
    configuration: dict[str, Any] | None = {}

    @field_validator("base_url")
    @classmethod
    def validate_url_format(cls, v):
        """Validate URL format, resolving env vars first."""
        resolved_url = _resolve_env_var(v)
        if not resolved_url.startswith(("http://", "https://")):
            raise ValueError(f"URL must start with http:// or https://, got: {v}")
        # Basic validation of format (allow placeholders for templates)
        import re

        if not re.match(r"^https?://[a-zA-Z0-9._-]+(:[A-Z0-9_]+|:[0-9]+)?(/.*)?$", resolved_url):
            raise ValueError(f"Invalid URL format: {v}")
        return v


class ProvidersYAML(BaseModel):
    """Complete providers.yaml structure"""

    providers: dict[str, ProviderConfig]
    metadata: dict[str, Any] | None = {}
    health_checks: dict[str, Any] | None = {}

    @model_validator(mode="after")
    def validate_active_providers(self):
        """Ensure at least one provider is active"""
        providers = self.providers
        active = [p for p in providers.values() if p.status == "active"]
        if len(active) == 0:
            raise ValueError('At least one provider must have status="active"')
        return self


# ============================================================================
# MODEL MAPPINGS CONFIGURATION MODELS
# ============================================================================


class ExactMatch(BaseModel):
    """Exact model name routing"""

    provider: str
    priority: Literal["primary", "secondary", "tertiary"]
    fallback: str | None = None
    description: str
    backend_model: str | None = None


class PatternRouting(BaseModel):
    """Pattern-based routing rule"""

    pattern: str
    provider: str
    fallback: str | None = None
    description: str

    @field_validator("pattern")
    @classmethod
    def validate_regex(cls, v):
        """Validate that pattern is valid regex"""
        import re

        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {v} - {e}") from e
        return v


class CapabilityRouting(BaseModel):
    """Capability-based routing configuration"""

    description: str
    provider: str | None = None
    providers: list[str] | None = None
    preferred_models: list[str] | None = []
    routing_strategy: str | None = None
    min_model_size: str | None = None
    min_context: int | None = None


class FallbackChain(BaseModel):
    """Fallback chain configuration"""

    description: str | None = "Fallback chain"  # Make description optional with default
    chain: list[str | dict[str, Any]]  # Allow both strings and dictionaries
    retry_attempts: int | None = 3
    retry_delay_ms: int | None = 500


class ModelMappingsYAML(BaseModel):
    """Complete model-mappings.yaml structure"""

    exact_matches: dict[str, ExactMatch]
    patterns: list[PatternRouting]
    capabilities: dict[str, CapabilityRouting]
    fallback_chains: dict[str, FallbackChain]
    load_balancing: dict[str, Any] | None = {}
    routing_rules: dict[str, Any] | None = {}
    special_cases: dict[str, Any] | None = {}
    metadata: dict[str, Any] | None = {}

    @model_validator(mode="after")
    def validate_provider_references(self):
        """Validate that referenced providers exist (requires providers.yaml context)"""
        # Note: Cross-file validation happens in validate_all_configs()
        return self


# ============================================================================
# LITELLM CONFIGURATION MODELS
# ============================================================================


class LiteLLMParams(BaseModel):
    """LiteLLM parameters for model configuration"""

    model: str
    api_base: str
    stream: bool | None = True

    @field_validator("api_base")
    @classmethod
    def validate_api_base(cls, v):
        """Validate API base URL format"""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"api_base must start with http:// or https://, got: {v}")
        return v


class ModelInfo(BaseModel):
    """Model metadata information"""

    tags: list[str]
    provider: str
    context_length: int | None = None
    notes: str | None = None


class ModelDefinition(BaseModel):
    """Individual model definition in LiteLLM config"""

    model_name: str
    litellm_params: LiteLLMParams
    model_info: ModelInfo


class LiteLLMSettings(BaseModel):
    """LiteLLM settings configuration"""

    request_timeout: int | None = 60
    stream_timeout: int | None = 0
    num_retries: int | None = 3
    timeout: int | None = 300
    cache: bool | None = False
    cache_params: dict[str, Any] | None = {}
    set_verbose: bool | None = False
    json_logs: bool | None = True


class RouterSettings(BaseModel):
    """Router settings configuration"""

    routing_strategy: str | None = "usage-based-routing-v2"
    model_group_alias: dict[str, list[str]] | None = {}
    allowed_fails: int | None = 3
    num_retries: int | None = 2
    timeout: int | None = 30
    cooldown_time: int | None = 60
    fallbacks: list[dict[str, Any]] | None = []


class ServerSettings(BaseModel):
    """Server settings configuration"""

    port: int = Field(ge=1, le=65535)
    host: str = "0.0.0.0"
    cors: dict[str, Any] | None = {}
    health_check_endpoint: str | None = "/health"
    prometheus: dict[str, Any] | None = {}

    @field_validator("port")
    @classmethod
    def validate_port_range(cls, v):
        """Ensure port is in valid range"""
        if not (1 <= v <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got: {v}")
        return v


class LiteLLMUnifiedYAML(BaseModel):
    """Complete litellm-unified.yaml structure"""

    model_list: list[ModelDefinition]
    litellm_settings: LiteLLMSettings | None = {}
    router_settings: RouterSettings | None = {}
    server_settings: ServerSettings | None = {}
    rate_limit_settings: dict[str, Any] | None = {}
    budget_settings: dict[str, Any] | None = {}
    debug: bool | None = False
    debug_router: bool | None = False
    test_mode: bool | None = False

    @model_validator(mode="after")
    def validate_model_list(self):
        """Validate that model_list is not empty"""
        model_list = self.model_list
        if len(model_list) == 0:
            raise ValueError("model_list cannot be empty")
        return self


# ============================================================================
# CROSS-CONFIGURATION VALIDATION
# ============================================================================


def validate_all_configs(providers_path: Path, mappings_path: Path, litellm_path: Path):
    """
    Perform cross-configuration validation
    - Ensure providers referenced in mappings exist
    - Ensure fallback models exist in litellm config
    - Validate routing consistency
    """
    errors = []

    try:
        # Load all configs
        with open(providers_path) as f:
            providers_data = yaml.safe_load(f)
        with open(mappings_path) as f:
            mappings_data = yaml.safe_load(f)
        with open(litellm_path) as f:
            litellm_data = yaml.safe_load(f)

        # Parse with Pydantic
        providers = ProvidersYAML(**providers_data)
        mappings = ModelMappingsYAML(**mappings_data)
        litellm = LiteLLMUnifiedYAML(**litellm_data)

        # Get active providers
        active_providers = {
            name for name, config in providers.providers.items() if config.status == "active"
        }

        # Check exact_matches reference active providers
        for model_name, config in mappings.exact_matches.items():
            if config.provider not in active_providers:
                errors.append(
                    f"Model '{model_name}' references inactive provider '{config.provider}'"
                )

        # Pre-compute known model identifiers for fallback validation
        known_model_names = {m.model_name for m in litellm.model_list} | set(
            mappings.exact_matches.keys()
        )

        # Check fallback chains reference active providers or known models
        for chain_name, chain in mappings.fallback_chains.items():
            for step in chain.chain:
                if isinstance(step, str):
                    references = [step]
                else:
                    references = [
                        ref
                        for ref in (
                            step.get("primary"),
                            step.get("secondary"),
                            step.get("tertiary"),
                        )
                        if ref
                    ]

                for reference in references:
                    if reference in active_providers or reference in known_model_names:
                        continue
                    errors.append(
                        f"Fallback chain '{chain_name}' references unknown provider/model '{reference}'"
                    )

        # Check litellm fallbacks reference existing models
        if litellm.router_settings and litellm.router_settings.fallbacks:
            model_names = {m.model_name for m in litellm.model_list}
            for fallback_config in litellm.router_settings.fallbacks:
                if "fallback_models" in fallback_config:
                    for fb_model in fallback_config["fallback_models"]:
                        if fb_model not in model_names:
                            errors.append(f"Fallback references non-existent model '{fb_model}'")

        return errors

    except Exception as e:
        return [f"Cross-validation error: {str(e)}"]


# ============================================================================
# MAIN VALIDATION FUNCTION
# ============================================================================


def main():
    """Main validation function"""
    config_dir = Path(__file__).parent.parent / "config"

    providers_file = config_dir / "providers.yaml"
    mappings_file = config_dir / "model-mappings.yaml"
    litellm_file = config_dir / "litellm-unified.yaml"

    errors = []

    print("🔍 Validating AI Backend Configuration...")
    print()

    # Validate providers.yaml
    print("📋 Validating providers.yaml...")
    try:
        with open(providers_file) as f:
            providers_data = yaml.safe_load(f)
        ProvidersYAML(**providers_data)
        print("  ✅ providers.yaml is valid")
    except Exception as e:
        error_msg = f"  ❌ providers.yaml validation failed: {str(e)}"
        print(error_msg)
        errors.append(error_msg)

    # Validate model-mappings.yaml
    print("📋 Validating model-mappings.yaml...")
    try:
        with open(mappings_file) as f:
            mappings_data = yaml.safe_load(f)
        ModelMappingsYAML(**mappings_data)
        print("  ✅ model-mappings.yaml is valid")
    except Exception as e:
        error_msg = f"  ❌ model-mappings.yaml validation failed: {str(e)}"
        print(error_msg)
        errors.append(error_msg)

    # Validate litellm-unified.yaml
    print("📋 Validating litellm-unified.yaml...")
    try:
        with open(litellm_file) as f:
            litellm_data = yaml.safe_load(f)
        LiteLLMUnifiedYAML(**litellm_data)
        print("  ✅ litellm-unified.yaml is valid")
    except Exception as e:
        error_msg = f"  ❌ litellm-unified.yaml validation failed: {str(e)}"
        print(error_msg)
        errors.append(error_msg)

    # Cross-configuration validation
    print("🔗 Performing cross-configuration validation...")
    cross_errors = validate_all_configs(providers_file, mappings_file, litellm_file)
    if cross_errors:
        for err in cross_errors:
            print(f"  ❌ {err}")
            errors.extend(cross_errors)
    else:
        print("  ✅ Cross-configuration validation passed")

    print()

    if errors:
        print(f"❌ Validation failed with {len(errors)} error(s)")
        sys.exit(1)
    else:
        print("✅ All configuration validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
