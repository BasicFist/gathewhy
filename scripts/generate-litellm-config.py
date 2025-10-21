#!/usr/bin/env python3
"""
LiteLLM Configuration Generator

Generates litellm-unified.yaml from source configurations:
- providers.yaml: Provider registry (source of truth for models)
- model-mappings.yaml: Routing rules and fallback chains

Features:
- Eliminates configuration redundancy
- Version tracking and rollback support
- Automatic backup before generation
- Post-generation validation
- Preserves manual security settings

Usage:
    python3 scripts/generate-litellm-config.py
    python3 scripts/generate-litellm-config.py --validate-only
    python3 scripts/generate-litellm-config.py --rollback <version>
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Configuration paths
PROJECT_ROOT = Path(__file__).parent.parent
PROVIDERS_FILE = PROJECT_ROOT / "config" / "providers.yaml"
MAPPINGS_FILE = PROJECT_ROOT / "config" / "model-mappings.yaml"
OUTPUT_FILE = PROJECT_ROOT / "config" / "litellm-unified.yaml"
BACKUP_DIR = PROJECT_ROOT / "config" / "backups"
VERSION_FILE = PROJECT_ROOT / "config" / ".litellm-version"


class ConfigGenerator:
    """Generate LiteLLM configuration from source files"""

    def __init__(self):
        self.providers: dict = {}
        self.mappings: dict = {}
        self.version: str = ""
        self.timestamp: str = datetime.now().isoformat()

    def load_sources(self):
        """Load source configuration files"""
        print("📖 Loading source configurations...")

        with open(PROVIDERS_FILE) as f:
            self.providers = yaml.safe_load(f)

        with open(MAPPINGS_FILE) as f:
            self.mappings = yaml.safe_load(f)

        print(f"  ✓ Loaded {len(self.providers.get('providers', {}))} providers")
        print(f"  ✓ Loaded {len(self.mappings.get('exact_matches', {}))} exact mappings")
        print(f"  ✓ Loaded {len(self.mappings.get('fallback_chains', {}))} fallback chains")

    def generate_version(self) -> str:
        """Generate version string based on git or timestamp"""
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
            return f"git-{git_hash}"
        except:
            # Fallback to timestamp if git not available
            return datetime.now().strftime("%Y%m%d-%H%M%S")

    def build_model_list(self) -> list[dict]:
        """Build model_list from providers and mappings"""
        print("\n🔨 Building model list...")

        model_list = []
        providers_config = self.providers.get("providers", {})

        # Process each active provider
        for provider_name, provider_config in providers_config.items():
            if provider_config.get("status") != "active":
                continue

            provider_type = provider_config.get("type")
            base_url = provider_config.get("base_url")
            models = provider_config.get("models", [])

            print(f"  Processing {provider_name} ({len(models)} models)...")

            for model in models:
                model_name = model.get("name")
                if not model_name:
                    continue

                # Build litellm_params based on provider type
                litellm_params = self._build_litellm_params(
                    provider_type, provider_name, model_name, base_url
                )

                # Build model_info
                model_info = {"tags": self._build_tags(model), "provider": provider_name}

                # Add context_length if available
                if "context_length" in model:
                    model_info["context_length"] = model["context_length"]

                # Add notes if description available
                if "description" in model:
                    model_info["notes"] = model["description"]

                # Create model entry
                model_entry = {
                    "model_name": self._get_display_name(provider_name, model_name),
                    "litellm_params": litellm_params,
                    "model_info": model_info,
                }

                model_list.append(model_entry)

        print(f"  ✓ Generated {len(model_list)} model entries")
        return model_list

    def _build_litellm_params(
        self, provider_type: str, provider_name: str, model_name: str, base_url: str
    ) -> dict:
        """Build litellm_params based on provider type"""
        if provider_type == "ollama":
            return {"model": f"ollama/{model_name}", "api_base": base_url}
        if provider_type == "llama_cpp":
            return {"model": "openai/local-model", "api_base": base_url, "stream": True}
        if provider_type == "vllm":
            return {"model": f"vllm/{model_name}", "api_base": base_url, "stream": True}
        if provider_type == "openai":
            return {"model": model_name, "api_key": "${OPENAI_API_KEY}"}
        if provider_type == "anthropic":
            return {"model": model_name, "api_key": "${ANTHROPIC_API_KEY}"}
        if provider_type == "openai_compatible":
            return {"model": f"openai/{model_name}", "api_base": base_url}
        # Generic fallback
        return {"model": model_name, "api_base": base_url}

    def _build_tags(self, model: dict) -> list[str]:
        """Build tags from model metadata"""
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
        """Get display name for model in LiteLLM"""
        # Check mappings for explicit display name
        exact_matches = self.mappings.get("exact_matches", {})
        if model_name in exact_matches:
            return model_name

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
            "routing_strategy": "usage-based-routing-v2",
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

        # Build model_group_alias from capability routing
        capabilities = self.mappings.get("capability_routing", {})
        for capability, config in capabilities.items():
            if "models" in config:
                router_settings["model_group_alias"][capability] = config["models"]

        # Build fallback chains
        fallback_chains = self.mappings.get("fallback_chains", {})
        for primary_model, chain in fallback_chains.items():
            fallback_entry = {"model": primary_model, "fallback_models": chain.get("chain", [])}
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
                "stream_timeout": 0,
                "num_retries": 3,
                "timeout": 300,
                "cache": True,
                "cache_params": {"type": "redis", "host": "127.0.0.1", "port": 6379, "ttl": 3600},
                "set_verbose": False,
                "json_logs": True,
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
                "prometheus": {"enabled": True, "port": 9090},
            },
            "rate_limit_settings": self.build_rate_limit_settings(),
            "general_settings": {
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
            yaml.dump(clean_config, f, default_flow_style=False, sort_keys=False, width=120)

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
            yaml.dump(version_info, f)

        print(f"\n📌 Version saved: {self.version}")

    def validate(self):
        """Validate generated configuration"""
        print("\n✅ Validating generated configuration...")

        try:
            # Import validation script
            sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
            from validate_config_schema import validate_all_configs

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
