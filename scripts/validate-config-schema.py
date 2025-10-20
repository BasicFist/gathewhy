#!/usr/bin/env python3
"""
Pydantic-based configuration schema validation for AI Backend Unified Infrastructure
Provides strong typing and semantic validation beyond YAML syntax checking
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl, validator, root_validator
import yaml
import sys
from pathlib import Path

# ============================================================================
# PROVIDER CONFIGURATION MODELS
# ============================================================================

class ProviderModel(BaseModel):
    """Model definition within a provider"""
    name: str
    size: Optional[str] = None
    quantization: Optional[str] = None
    specialty: Optional[str] = None
    context_length: Optional[int] = None
    pulled_at: Optional[str] = None

class ProviderConfig(BaseModel):
    """Individual provider configuration"""
    type: Literal["ollama", "llama_cpp", "vllm", "openai", "anthropic", "openai_compatible"]
    base_url: str
    status: Literal["active", "disabled", "pending_integration", "template"]
    description: str
    models: Optional[List[ProviderModel]] = []
    health_endpoint: Optional[str] = None
    features: Optional[List[str]] = []
    configuration: Optional[Dict[str, Any]] = {}

    @validator('base_url')
    def validate_url_format(cls, v):
        """Validate URL format without requiring https"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError(f'URL must start with http:// or https://, got: {v}')
        # Basic validation of format
        import re
        if not re.match(r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$', v):
            raise ValueError(f'Invalid URL format: {v}')
        return v

class ProvidersYAML(BaseModel):
    """Complete providers.yaml structure"""
    providers: Dict[str, ProviderConfig]
    metadata: Optional[Dict[str, Any]] = {}
    health_checks: Optional[Dict[str, Any]] = {}

    @root_validator
    def validate_active_providers(cls, values):
        """Ensure at least one provider is active"""
        providers = values.get('providers', {})
        active = [p for p in providers.values() if p.status == 'active']
        if len(active) == 0:
            raise ValueError('At least one provider must have status="active"')
        return values

# ============================================================================
# MODEL MAPPINGS CONFIGURATION MODELS
# ============================================================================

class ExactMatch(BaseModel):
    """Exact model name routing"""
    provider: str
    priority: Literal["primary", "secondary", "tertiary"]
    fallback: Optional[str] = None
    description: str
    backend_model: Optional[str] = None

class PatternRouting(BaseModel):
    """Pattern-based routing rule"""
    pattern: str
    provider: str
    fallback: Optional[str] = None
    description: str

    @validator('pattern')
    def validate_regex(cls, v):
        """Validate that pattern is valid regex"""
        import re
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f'Invalid regex pattern: {v} - {e}')
        return v

class CapabilityRouting(BaseModel):
    """Capability-based routing configuration"""
    description: str
    provider: Optional[str] = None
    providers: Optional[List[str]] = None
    preferred_models: Optional[List[str]] = []
    routing_strategy: Optional[str] = None
    min_model_size: Optional[str] = None
    min_context: Optional[int] = None

class FallbackChain(BaseModel):
    """Fallback chain configuration"""
    description: str
    chain: List[Dict[str, Any]]
    retry_attempts: Optional[int] = 3
    retry_delay_ms: Optional[int] = 500

class ModelMappingsYAML(BaseModel):
    """Complete model-mappings.yaml structure"""
    exact_matches: Dict[str, ExactMatch]
    patterns: List[PatternRouting]
    capabilities: Dict[str, CapabilityRouting]
    fallback_chains: Dict[str, FallbackChain]
    load_balancing: Optional[Dict[str, Any]] = {}
    routing_rules: Optional[Dict[str, Any]] = {}
    special_cases: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}

    @root_validator
    def validate_provider_references(cls, values):
        """Validate that referenced providers exist (requires providers.yaml context)"""
        # Note: Cross-file validation happens in validate_all_configs()
        return values

# ============================================================================
# LITELLM CONFIGURATION MODELS
# ============================================================================

class LiteLLMParams(BaseModel):
    """LiteLLM parameters for model configuration"""
    model: str
    api_base: str
    stream: Optional[bool] = True

    @validator('api_base')
    def validate_api_base(cls, v):
        """Validate API base URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError(f'api_base must start with http:// or https://, got: {v}')
        return v

class ModelInfo(BaseModel):
    """Model metadata information"""
    tags: List[str]
    provider: str
    context_length: Optional[int] = None
    notes: Optional[str] = None

class ModelDefinition(BaseModel):
    """Individual model definition in LiteLLM config"""
    model_name: str
    litellm_params: LiteLLMParams
    model_info: ModelInfo

class LiteLLMSettings(BaseModel):
    """LiteLLM settings configuration"""
    request_timeout: Optional[int] = 60
    stream_timeout: Optional[int] = 0
    num_retries: Optional[int] = 3
    timeout: Optional[int] = 300
    cache: Optional[bool] = False
    cache_params: Optional[Dict[str, Any]] = {}
    set_verbose: Optional[bool] = False
    json_logs: Optional[bool] = True

class RouterSettings(BaseModel):
    """Router settings configuration"""
    routing_strategy: Optional[str] = "usage-based-routing-v2"
    model_group_alias: Optional[Dict[str, List[str]]] = {}
    allowed_fails: Optional[int] = 3
    num_retries: Optional[int] = 2
    timeout: Optional[int] = 30
    cooldown_time: Optional[int] = 60
    fallbacks: Optional[List[Dict[str, Any]]] = []

class ServerSettings(BaseModel):
    """Server settings configuration"""
    port: int = Field(ge=1, le=65535)
    host: str = "0.0.0.0"
    cors: Optional[Dict[str, Any]] = {}
    health_check_endpoint: Optional[str] = "/health"
    prometheus: Optional[Dict[str, Any]] = {}

    @validator('port')
    def validate_port_range(cls, v):
        """Ensure port is in valid range"""
        if not (1 <= v <= 65535):
            raise ValueError(f'Port must be between 1 and 65535, got: {v}')
        return v

class LiteLLMUnifiedYAML(BaseModel):
    """Complete litellm-unified.yaml structure"""
    model_list: List[ModelDefinition]
    litellm_settings: Optional[LiteLLMSettings] = {}
    router_settings: Optional[RouterSettings] = {}
    server_settings: Optional[ServerSettings] = {}
    rate_limit_settings: Optional[Dict[str, Any]] = {}
    budget_settings: Optional[Dict[str, Any]] = {}
    debug: Optional[bool] = False
    debug_router: Optional[bool] = False
    test_mode: Optional[bool] = False

    @root_validator
    def validate_model_list(cls, values):
        """Validate that model_list is not empty"""
        model_list = values.get('model_list', [])
        if len(model_list) == 0:
            raise ValueError('model_list cannot be empty')
        return values

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
            name for name, config in providers.providers.items()
            if config.status == 'active'
        }

        # Check exact_matches reference active providers
        for model_name, config in mappings.exact_matches.items():
            if config.provider not in active_providers:
                errors.append(
                    f"Model '{model_name}' references inactive provider '{config.provider}'"
                )

        # Check fallback chains reference active providers
        for chain_name, chain in mappings.fallback_chains.items():
            for step in chain.chain:
                provider = step.get('primary') or step.get('secondary') or step.get('tertiary')
                if provider and provider not in active_providers:
                    errors.append(
                        f"Fallback chain '{chain_name}' references inactive provider '{provider}'"
                    )

        # Check litellm fallbacks reference existing models
        if litellm.router_settings and litellm.router_settings.fallbacks:
            model_names = {m.model_name for m in litellm.model_list}
            for fallback_config in litellm.router_settings.fallbacks:
                if 'fallback_models' in fallback_config:
                    for fb_model in fallback_config['fallback_models']:
                        if fb_model not in model_names:
                            errors.append(
                                f"Fallback references non-existent model '{fb_model}'"
                            )

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
        providers = ProvidersYAML(**providers_data)
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
        mappings = ModelMappingsYAML(**mappings_data)
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
        litellm = LiteLLMUnifiedYAML(**litellm_data)
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

if __name__ == '__main__':
    main()
