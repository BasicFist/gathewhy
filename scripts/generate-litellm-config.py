#!/usr/bin/env python3
"""
LiteLLM Configuration Generator.

Generates litellm-unified.yaml from source configurations:
- providers.yaml: Provider registry (source of truth for models)
- model-mappings.yaml: Routing rules and fallback chains

Features:
- Eliminates configuration redundancy
- Version tracking and rollback support
- Automatic backup before generation
- Post-generation validation
- Preserves manual security settings
- Structured logging for comprehensive audit trail

Usage:
    python3 scripts/generate-litellm-config.py
    python3 scripts/generate-litellm-config.py --validate-only
    python3 scripts/generate-litellm-config.py --rollback <version>

Examples:
    Generate fresh configuration:
        $ python3 scripts/generate-litellm-config.py
        [INFO    ] Configuration generated successfully

    Validate without generating:
        $ python3 scripts/generate-litellm-config.py --validate-only
        [INFO    ] Validation passed: 15 providers, 47 models

    Rollback to previous version:
        $ python3 scripts/generate-litellm-config.py --rollback v1.2.3
        [SUCCESS ] Rolled back to version v1.2.3
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


# Custom YAML dumper for proper indentation (yamllint compliance)
class IndentedDumper(yaml.Dumper):
    """Custom YAML dumper with proper sequence indentation for yamllint compliance."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


# Configuration paths
PROJECT_ROOT = Path(__file__).parent.parent
PROVIDERS_FILE = PROJECT_ROOT / "config" / "providers.yaml"
MAPPINGS_FILE = PROJECT_ROOT / "config" / "model-mappings.yaml"
OUTPUT_FILE = PROJECT_ROOT / "config" / "litellm-unified.yaml"
BACKUP_DIR = PROJECT_ROOT / "config" / "backups"
VERSION_FILE = PROJECT_ROOT / "config" / ".litellm-version"

# Configure structured logging
logger.remove()
logger.add(
    sys.stderr,
    format="<level>[{level: <8}]</level> {message}",
    level="INFO",
    colorize=True,
)


class ConfigGenerator:
    """
    Generate LiteLLM unified configuration from source files.

    This class orchestrates the generation of litellm-unified.yaml by:
    1. Loading provider registry and model mappings
    2. Building model list with provider-specific configurations
    3. Configuring router settings and fallback chains
    4. Generating router configuration for LiteLLM
    5. Creating a backup before writing output
    6. Validating the generated configuration

    Attributes:
        providers (dict): Parsed providers.yaml configuration
        mappings (dict): Parsed model-mappings.yaml configuration
        version (str): Generated version string (git hash or timestamp)
        timestamp (str): ISO format timestamp of generation
    """

    def __init__(self) -> None:
        """Initialize configuration generator with empty state."""
        self.providers: dict[str, Any] = {}
        self.mappings: dict[str, Any] = {}
        self.version: str = ""
        self.timestamp: str = datetime.now().isoformat()

    def load_sources(self) -> None:
        """
        Load source configuration files with error handling.

        Loads providers.yaml and model-mappings.yaml using safe YAML parsing.
        Logs detailed information about loaded configuration for audit purposes.

        Raises:
            FileNotFoundError: If source files don't exist
            yaml.YAMLError: If YAML syntax is invalid
        """
        logger.info("Loading source configurations...")

        try:
            with open(PROVIDERS_FILE) as f:
                self.providers = yaml.safe_load(f)
            logger.debug(
                "Loaded providers.yaml",
                file_path=str(PROVIDERS_FILE),
                size_bytes=PROVIDERS_FILE.stat().st_size,
            )
        except FileNotFoundError as e:
            logger.error(f"Providers file not found: {PROVIDERS_FILE}", error=str(e))
            raise
        except yaml.YAMLError as e:
            logger.error(
                f"Invalid YAML in providers.yaml: {e}",
                file_path=str(PROVIDERS_FILE),
                error=str(e),
            )
            raise

        try:
            with open(MAPPINGS_FILE) as f:
                self.mappings = yaml.safe_load(f)
            logger.debug(
                "Loaded model-mappings.yaml",
                file_path=str(MAPPINGS_FILE),
                size_bytes=MAPPINGS_FILE.stat().st_size,
            )
        except FileNotFoundError as e:
            logger.error(f"Mappings file not found: {MAPPINGS_FILE}", error=str(e))
            raise
        except yaml.YAMLError as e:
            logger.error(
                f"Invalid YAML in model-mappings.yaml: {e}",
                file_path=str(MAPPINGS_FILE),
                error=str(e),
            )
            raise

        # Log summary statistics
        provider_count = len(self.providers.get("providers", {}))
        exact_matches = len(self.mappings.get("exact_matches", {}))
        fallback_chains = len(self.mappings.get("fallback_chains", {}))

        logger.info(
            "Configuration sources loaded successfully",
            providers=provider_count,
            exact_matches=exact_matches,
            fallback_chains=fallback_chains,
        )

    def generate_version(self) -> str:
        """
        Generate version string based on git commit hash or timestamp.

        Attempts to generate version from current git commit hash for reproducibility.
        Falls back to ISO8601 timestamp if git is not available or repository
        context is not present.

        Returns:
            str: Version string in format "git-<hash>" or "YYYYMMDD-HHMMSS"

        Example:
            >>> gen = ConfigGenerator()
            >>> version = gen.generate_version()
            >>> print(version)  # "git-a1b2c3d" or "20251025-142530"
        """
        try:
            import subprocess

            git_hash = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=PROJECT_ROOT,
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
            logger.debug("Generated version from git", version=f"git-{git_hash}")
            return f"git-{git_hash}"
        except (subprocess.SubprocessError, OSError, FileNotFoundError) as e:
            # Fallback to timestamp if git not available
            timestamp_version = datetime.now().strftime("%Y%m%d-%H%M%S")
            logger.debug(
                "Git not available, using timestamp for version",
                version=timestamp_version,
                reason=type(e).__name__,
            )
            return timestamp_version

    def build_model_list(self) -> list[dict[str, Any]]:
        """
        Build LiteLLM model list from providers and model mappings.

        Constructs the model_list configuration section by:
        1. Iterating through all active providers
        2. For each provider model, building provider-specific LiteLLM parameters
        3. Extracting tags, context lengths, and descriptions from model metadata
        4. Creating standardized model entries for LiteLLM

        Returns:
            list[dict[str, Any]]: List of model entries with structure:
                {
                    "model_name": str,
                    "litellm_params": dict,  # Provider-specific parameters
                    "model_info": {
                        "provider": str,
                        "tags": list[str],
                        "context_length": int (optional),
                        "notes": str (optional),
                    }
                }

        Example:
            >>> gen = ConfigGenerator()
            >>> gen.load_sources()
            >>> models = gen.build_model_list()
            >>> print(f"Built {len(models)} model entries")
            Built 47 model entries
        """
        logger.info("Building model list from active providers...")

        model_list: list[dict[str, Any]] = []
        providers_config = self.providers.get("providers", {})

        # Process each active provider
        for provider_name, provider_config in providers_config.items():
            if provider_config.get("status") != "active":
                logger.debug(
                    "Skipping inactive provider",
                    provider=provider_name,
                    status=provider_config.get("status"),
                )
                continue

            provider_type = provider_config.get("type")
            base_url = provider_config.get("base_url")
            models = provider_config.get("models", [])

            logger.debug(
                "Processing provider",
                provider=provider_name,
                type=provider_type,
                model_count=len(models),
            )

            for model in models:
                model_name = model.get("name") if isinstance(model, dict) else model
                if not model_name:
                    logger.warning(
                        "Skipping model with no name",
                        provider=provider_name,
                        model_data=str(model),
                    )
                    continue

                # Build litellm_params based on provider type
                litellm_params = self._build_litellm_params(
                    provider_type, provider_name, model_name, base_url, model
                )

                # Build model_info
                model_info = {"tags": self._build_tags(model), "provider": provider_name}

                # Add context_length if available
                if isinstance(model, dict) and "context_length" in model:
                    model_info["context_length"] = model["context_length"]

                # Add notes if description available
                if isinstance(model, dict) and "description" in model:
                    model_info["notes"] = model["description"]

                # Create model entry
                model_entry: dict[str, Any] = {
                    "model_name": self._get_display_name(provider_name, model_name),
                    "litellm_params": litellm_params,
                    "model_info": model_info,
                }

                model_list.append(model_entry)
                logger.debug(
                    "Added model to list",
                    model_name=model_entry["model_name"],
                    provider=provider_name,
                )

        logger.info(
            "Model list generation complete",
            total_models=len(model_list),
            providers_processed=len(
                [p for p in providers_config.values() if p.get("status") == "active"]
            ),
        )
        return model_list

    def _build_litellm_params(
        self,
        provider_type: str,
        provider_name: str,
        model_name: str,
        base_url: str,
        raw_model: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build provider-specific LiteLLM parameters.

        Constructs the litellm_params dictionary with parameters specific to each
        provider type. This handles differences in API conventions and authentication.

        Args:
            provider_type (str): Type of provider (ollama, vllm, llama_cpp, etc.)
            provider_name (str): Name/identifier of the provider instance
            model_name (str): Model name in provider's format
            base_url (str): Base URL for provider API
            raw_model (dict): Raw model configuration from providers.yaml

        Returns:
            dict[str, Any]: LiteLLM compatible parameters including model, api_base,
                and provider-specific configuration

        Example:
            >>> params = gen._build_litellm_params(
            ...     "vllm", "vllm_local", "Qwen2.5-Coder", "http://localhost:8001", {}
            ... )
            >>> print(params["api_base"])
            http://localhost:8001/v1
        """
        if provider_type == "ollama":
            # Use ollama_chat/ for cloud provider (better chat responses)
            # Use ollama/ for local provider (compatibility)
            prefix = "ollama_chat" if provider_name == "ollama_cloud" else "ollama"
            params: dict = {"model": f"{prefix}/{model_name}", "api_base": base_url}
            options = raw_model.get("options")
            if options:
                params["extra_body"] = {"options": options}
            return params
        if provider_type == "llama_cpp":
            return {"model": "openai/local-model", "api_base": base_url, "stream": True}
        if provider_type == "vllm":
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
                params["api_key"] = "not-needed"  # pragma: allowlist secret
            return params
        if provider_type == "openai":
            return {"model": model_name, "api_key": "${OPENAI_API_KEY}"}
        if provider_type == "anthropic":
            return {"model": model_name, "api_key": "${ANTHROPIC_API_KEY}"}
        if provider_type == "openai_compatible":
            return {"model": f"openai/{model_name}", "api_base": base_url}
        # Generic fallback
        return {"model": model_name, "api_base": base_url}

    def _build_tags(self, model: dict[str, Any] | str) -> list[str]:
        """
        Build tag list from model metadata for categorization.

        Extracts and normalizes tags from model configuration including specialty,
        use case, size, and quantization. Useful for model discovery and filtering.

        Args:
            model (dict | str): Model configuration or simple model name string

        Returns:
            list[str]: List of normalized tags (lowercased). Defaults to ["general"]
                if no metadata tags are found.

        Example:
            >>> tags = gen._build_tags({
            ...     "name": "Qwen2.5-Coder",
            ...     "specialty": "code",
            ...     "quantization": "AWQ"
            ... })
            >>> print(tags)
            ['code', 'awq']
        """
        if not isinstance(model, dict):
            return ["general"]
        tags = []

        # Add specialty
        if "specialty" in model:
            tags.append(model["specialty"])

        # Add use_case
        if "use_case" in model:
            tags.append(model["use_case"])

        # Add size
        if "size" in model:
            tags.append(model["size"].lower())

        # Add quantization
        if "quantization" in model:
            tags.append(model["quantization"].lower())

        # Default tags if none
        if not tags:
            tags = ["general"]

        return tags

    def _get_display_name(self, provider_name: str, model_name: str) -> str:
        """
        Resolve display name for model in LiteLLM format.

        Checks mappings for explicit aliases, handles special cases for llama.cpp,
        and falls back to model name. Display name is used as the key for model
        requests through LiteLLM gateway.

        Args:
            provider_name (str): Name of the provider
            model_name (str): Original model name in provider format

        Returns:
            str: Display name to use in LiteLLM model list

        Example:
            >>> display_name = gen._get_display_name("llama_cpp_python", "mistral-7b")
            >>> print(display_name)
            "llama-cpp-python"  # or mapped alias
        """
        # Check mappings for explicit display name
        exact_matches = self.mappings.get("exact_matches", {})
        if model_name in exact_matches:
            return model_name

        # Look for alias where backend_model matches this provider model
        for alias, config in exact_matches.items():
            if config.get("backend_model") == model_name:
                return alias

        # For llama.cpp, use descriptive names
        if "llama_cpp" in provider_name:
            if "python" in provider_name:
                return "llama-cpp-python"
            if "native" in provider_name:
                return "llama-cpp-native"

        # Default: use model name
        return model_name

    def build_router_settings(self) -> dict:
        """Build router_settings from mappings"""
        print("\n🔀 Building router settings...")

        router_settings = {
            "routing_strategy": "simple-shuffle",  # Changed from usage-based-routing-v2 (not recommended for production)
            "model_group_alias": {},
            "allowed_fails": 3,
            "num_retries": 2,
            "timeout": 30,
            "cooldown_time": 60,
            "enable_pre_call_checks": True,
            "redis_host": "127.0.0.1",
            "redis_port": 6379,
            "fallbacks": [],
        }

        # Build model_group_alias from capabilities
        capabilities = self.mappings.get("capabilities", {})
        for capability, config in capabilities.items():
            models = config.get("preferred_models") or config.get("models") or []
            if models:
                router_settings["model_group_alias"][capability] = models

        # Build fallback chains
        fallback_chains = self.mappings.get("fallback_chains", {})
        known_models: set[str] = set(self.mappings.get("exact_matches", {}).keys())

        providers_config = self.providers.get("providers", {})
        for provider_name, provider_config in providers_config.items():
            if provider_config.get("status") != "active":
                continue

            for model in provider_config.get("models", []):
                model_name = model.get("name") if isinstance(model, dict) else model
                if model_name:
                    known_models.add(self._get_display_name(provider_name, model_name))

        for primary_model, chain in fallback_chains.items():
            candidates: list[str] = []
            for fallback_model in chain.get("chain", []):
                if fallback_model == primary_model:
                    continue
                if fallback_model not in known_models:
                    continue
                if fallback_model in candidates:
                    continue
                candidates.append(fallback_model)

            if candidates:
                fallback_entry = {primary_model: candidates}
                router_settings["fallbacks"].append(fallback_entry)

        print(f"  ✓ Created {len(router_settings['model_group_alias'])} capability groups")
        print(f"  ✓ Created {len(router_settings['fallbacks'])} fallback chains")

        return router_settings

    def build_rate_limit_settings(self) -> dict:
        """Build rate limiting settings from mappings"""
        print("\n⏱️  Building rate limit settings...")

        rate_limits = {"enabled": True, "limits": {}}

        # Get rate limits from mappings
        exact_matches = self.mappings.get("exact_matches", {})
        for model_name, config in exact_matches.items():
            if "rate_limit" in config:
                limits = config["rate_limit"]
                rate_limits["limits"][model_name] = {
                    "rpm": limits.get("rpm", 100),
                    "tpm": limits.get("tpm", 50000),
                }

        # Apply default limits for models without explicit config
        providers_config = self.providers.get("providers", {})
        for provider_name, provider_config in providers_config.items():
            if provider_config.get("status") != "active":
                continue

            for model in provider_config.get("models", []):
                model_name = model.get("name")
                display_name = self._get_display_name(provider_name, model_name)

                if display_name not in rate_limits["limits"]:
                    # Apply sensible defaults based on provider type
                    provider_type = provider_config.get("type")
                    rate_limits["limits"][display_name] = self._get_default_rate_limits(
                        provider_type
                    )

        print(f"  ✓ Configured rate limits for {len(rate_limits['limits'])} models")

        return rate_limits

    def _get_default_rate_limits(self, provider_type: str) -> dict:
        """Get default rate limits based on provider type"""
        defaults = {
            "ollama": {"rpm": 100, "tpm": 50000},
            "llama_cpp": {"rpm": 120, "tpm": 60000},
            "vllm": {"rpm": 50, "tpm": 100000},
            "openai": {"rpm": 60, "tpm": 150000},
            "anthropic": {"rpm": 50, "tpm": 100000},
        }
        return defaults.get(provider_type, {"rpm": 100, "tpm": 50000})

    def build_config(self) -> dict:
        """Build complete LiteLLM configuration"""
        print("\n🏗️  Building complete configuration...")

        config = {
            "# AUTO-GENERATED FILE": None,
            "# Generated by": "scripts/generate-litellm-config.py",
            "# Source files": "config/providers.yaml, config/model-mappings.yaml",
            "# Generated at": self.timestamp,
            "# Version": self.version,
            "# DO NOT EDIT MANUALLY": "- Changes will be overwritten on next generation",
            "# To modify": "- Edit providers.yaml or model-mappings.yaml, then regenerate",
            "model_list": self.build_model_list(),
            "litellm_settings": {
                "request_timeout": 60,
                "stream_timeout": 120,  # Changed from 0 (infinite) - set reasonable timeout
                "num_retries": 3,
                "timeout": 300,
                "cache": True,
                "cache_params": {"type": "redis", "host": "127.0.0.1", "port": 6379, "ttl": 3600},
                "set_verbose": True,  # Changed from False - enable verbose logging for debugging
                "json_logs": True,
                "callbacks": ["prometheus"],  # Added: Enable Prometheus metrics endpoint
            },
            "router_settings": self.build_router_settings(),
            "server_settings": {
                "port": 4000,
                "host": "0.0.0.0",
                "cors": {
                    "enabled": True,
                    "allowed_origins": [
                        "http://localhost:*",
                        "http://127.0.0.1:*",
                        "http://[::1]:*",
                    ],
                },
                "health_check_endpoint": "/health",
                # Removed invalid prometheus config - metrics served on port 4000 via callbacks
            },
            "rate_limit_settings": self.build_rate_limit_settings(),
            "general_settings": {
                "background_health_checks": True,  # Added: Enable background health checks
                "health_check_interval": 300,  # Added: Check every 5 minutes
                "health_check_details": False,  # Added: Hide sensitive info in responses
                "# Master Key Authentication": None,
                "# Uncomment to enable": None,
                "# master_key": "${LITELLM_MASTER_KEY}",
                "# Salt Key for DB encryption": None,
                "# salt_key": "${LITELLM_SALT_KEY}",
            },
            "debug": False,
            "debug_router": False,
            "test_mode": False,
        }

        print("  ✓ Configuration built successfully")
        return config

    def backup_existing(self):
        """Backup existing configuration before overwriting"""
        if not OUTPUT_FILE.exists():
            print("\nℹ️  No existing configuration to backup")
            return

        print("\n💾 Creating backup...")

        # Create backup directory
        BACKUP_DIR.mkdir(exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = BACKUP_DIR / f"litellm-unified.yaml.{timestamp}"

        # Copy existing file
        shutil.copy2(OUTPUT_FILE, backup_file)

        print(f"  ✓ Backed up to: {backup_file.relative_to(PROJECT_ROOT)}")

        # Keep only last 10 backups
        self._cleanup_old_backups()

    def _cleanup_old_backups(self, keep: int = 10):
        """Keep only the most recent N backups"""
        backups = sorted(
            BACKUP_DIR.glob("litellm-unified.yaml.*"), key=lambda p: p.stat().st_mtime, reverse=True
        )

        if len(backups) > keep:
            print(f"  Cleaning up old backups (keeping {keep})...")
            for old_backup in backups[keep:]:
                old_backup.unlink()
                print(f"    Removed: {old_backup.name}")

    def write_config(self, config: dict):
        """Write configuration to file"""
        print(f"\n✍️  Writing configuration to {OUTPUT_FILE.relative_to(PROJECT_ROOT)}...")

        # Custom YAML representer for cleaner output
        def represent_none(self, _):
            return self.represent_scalar("tag:yaml.org,2002:null", "")

        yaml.add_representer(type(None), represent_none)

        # Write configuration
        with open(OUTPUT_FILE, "w") as f:
            # Write header comments manually for better formatting
            f.write(
                "# ============================================================================\n"
            )
            f.write("# AUTO-GENERATED FILE - DO NOT EDIT MANUALLY\n")
            f.write(
                "# ============================================================================\n"
            )
            f.write("#\n")
            f.write("# Generated by: scripts/generate-litellm-config.py\n")
            f.write("# Source files: config/providers.yaml, config/model-mappings.yaml\n")
            f.write(f"# Generated at: {self.timestamp}\n")
            f.write(f"# Version: {self.version}\n")
            f.write("#\n")
            f.write("# To modify this configuration:\n")
            f.write("#   1. Edit config/providers.yaml or config/model-mappings.yaml\n")
            f.write("#   2. Run: python3 scripts/generate-litellm-config.py\n")
            f.write("#   3. Validate: python3 scripts/validate-config-schema.py\n")
            f.write("#\n")
            f.write(
                "# ============================================================================\n\n"
            )

            # Write YAML content (excluding comment keys)
            clean_config = {k: v for k, v in config.items() if not k.startswith("#")}
            yaml.dump(
                clean_config,
                f,
                Dumper=IndentedDumper,  # Fix: Use custom dumper for yamllint compliance
                default_flow_style=False,
                sort_keys=False,
                indent=2,
                width=120,
            )

        print("  ✓ Configuration written successfully")

    def save_version(self):
        """Save version information"""
        version_info = {
            "version": self.version,
            "timestamp": self.timestamp,
            "providers_file": str(PROVIDERS_FILE.relative_to(PROJECT_ROOT)),
            "mappings_file": str(MAPPINGS_FILE.relative_to(PROJECT_ROOT)),
            "output_file": str(OUTPUT_FILE.relative_to(PROJECT_ROOT)),
        }

        with open(VERSION_FILE, "w") as f:
            yaml.dump(version_info, f, indent=2, default_flow_style=False)

        print(f"\n📌 Version saved: {self.version}")

    def validate(self):
        """Validate generated configuration"""
        print("\n✅ Validating generated configuration...")

        try:
            import runpy

            validation_module = runpy.run_path(
                str(PROJECT_ROOT / "scripts" / "validate-config-schema.py")
            )
            validate_all_configs = validation_module.get("validate_all_configs")

            if validate_all_configs is None:
                raise ImportError("validate_all_configs not found in validate-config-schema.py")

            validate_all_configs(PROVIDERS_FILE, MAPPINGS_FILE, OUTPUT_FILE)

            print("  ✓ Validation passed")
            return True
        except Exception as e:
            print(f"  ❌ Validation failed: {e}")
            return False

    def generate(self):
        """Main generation workflow"""
        print("=" * 80)
        print("LiteLLM Configuration Generator")
        print("=" * 80)

        # Load sources
        self.load_sources()

        # Generate version
        self.version = self.generate_version()

        # Backup existing
        self.backup_existing()

        # Build configuration
        config = self.build_config()

        # Write configuration
        self.write_config(config)

        # Save version
        self.save_version()

        # Validate
        if self.validate():
            print("\n" + "=" * 80)
            print("✅ Configuration generated successfully!")
            print("=" * 80)
            print(f"\nOutput: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")
            print(f"Version: {self.version}")
            print(f"Backup: {BACKUP_DIR.relative_to(PROJECT_ROOT)}/")
            print("\nNext steps:")
            print("  1. Review generated configuration")
            print("  2. Test: curl http://localhost:4000/v1/models")
            print("  3. Apply: cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml")
            print("  4. Restart: systemctl --user restart litellm.service")
            return True
        print("\n" + "=" * 80)
        print("❌ Configuration generation failed validation")
        print("=" * 80)
        print("\nPlease fix validation errors and try again")
        return False


def list_backups():
    """List available backups"""
    if not BACKUP_DIR.exists():
        print("No backups available")
        return

    backups = sorted(
        BACKUP_DIR.glob("litellm-unified.yaml.*"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    if not backups:
        print("No backups available")
        return

    print("Available backups:")
    for backup in backups:
        timestamp = backup.name.split(".")[-1]
        size = backup.stat().st_size
        print(f"  - {timestamp} ({size} bytes)")


def rollback(version: str):
    """Rollback to previous configuration version"""
    backup_file = BACKUP_DIR / f"litellm-unified.yaml.{version}"

    if not backup_file.exists():
        print(f"❌ Backup not found: {version}")
        print("\nAvailable backups:")
        list_backups()
        return False

    print(f"📦 Rolling back to version: {version}")

    # Backup current file
    if OUTPUT_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        current_backup = BACKUP_DIR / f"litellm-unified.yaml.before-rollback-{timestamp}"
        shutil.copy2(OUTPUT_FILE, current_backup)
        print(f"  Current version backed up to: {current_backup.name}")

    # Restore backup
    shutil.copy2(backup_file, OUTPUT_FILE)
    print("  ✓ Restored from backup")

    print("\n✅ Rollback complete")
    print("\nNext steps:")
    print("  1. Restart: systemctl --user restart litellm.service")
    print("  2. Verify: curl http://localhost:4000/v1/models")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate LiteLLM configuration")
    parser.add_argument(
        "--validate-only", action="store_true", help="Only validate existing configuration"
    )
    parser.add_argument("--rollback", metavar="VERSION", help="Rollback to specific backup version")
    parser.add_argument(
        "--list-backups", action="store_true", help="List available backup versions"
    )

    args = parser.parse_args()

    try:
        if args.list_backups:
            list_backups()
        elif args.rollback:
            success = rollback(args.rollback)
            sys.exit(0 if success else 1)
        elif args.validate_only:
            generator = ConfigGenerator()
            generator.load_sources()
            success = generator.validate()
            sys.exit(0 if success else 1)
        else:
            generator = ConfigGenerator()
            success = generator.generate()
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
