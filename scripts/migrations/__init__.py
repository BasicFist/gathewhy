"""
Configuration Migration Framework
==================================

Provides infrastructure for migrating configuration files between schema versions.

Usage:
    from scripts.migrations import migrate_config

    new_config = migrate_config(old_config, from_version="1.0.0", to_version="2.0.0")
"""

from pathlib import Path
import yaml
from typing import Any


class MigrationError(Exception):
    """Raised when migration fails"""
    pass


class Migration:
    """Base class for migrations"""

    from_version: str
    to_version: str
    description: str

    def migrate_providers(self, config: dict) -> dict:
        """Migrate providers.yaml"""
        return config

    def migrate_mappings(self, config: dict) -> dict:
        """Migrate model-mappings.yaml"""
        return config

    def migrate_litellm(self, config: dict) -> dict:
        """Migrate litellm-unified.yaml"""
        return config

    def validate(self, config: dict) -> tuple[bool, list[str]]:
        """Validate migrated configuration"""
        return True, []


def get_all_migrations() -> list[Migration]:
    """Get all available migrations"""
    return [
        Migration_v1_to_v2(),
    ]


def find_migration_path(from_version: str, to_version: str) -> list[Migration]:
    """Find migration path between versions"""
    migrations = get_all_migrations()

    # Build migration graph
    path = []
    current = from_version

    while current != to_version:
        found = False
        for migration in migrations:
            if migration.from_version == current:
                path.append(migration)
                current = migration.to_version
                found = True
                break

        if not found:
            raise MigrationError(
                f"No migration path from {from_version} to {to_version}"
            )

        if len(path) > 10:  # Prevent infinite loops
            raise MigrationError("Migration path too long (possible cycle)")

    return path


def migrate_config(
    config: dict,
    config_type: str,
    from_version: str,
    to_version: str
) -> dict:
    """
    Migrate configuration from one version to another

    Args:
        config: Configuration dictionary
        config_type: One of "providers", "mappings", "litellm"
        from_version: Current version
        to_version: Target version

    Returns:
        Migrated configuration
    """
    if from_version == to_version:
        return config

    migrations = find_migration_path(from_version, to_version)

    print(f"🔄 Migrating {config_type} from v{from_version} to v{to_version}")
    print(f"   Migration path: {len(migrations)} step(s)")

    current_config = config

    for i, migration in enumerate(migrations, 1):
        print(f"   Step {i}/{len(migrations)}: {migration.description}")

        # Apply migration based on config type
        if config_type == "providers":
            current_config = migration.migrate_providers(current_config)
        elif config_type == "mappings":
            current_config = migration.migrate_mappings(current_config)
        elif config_type == "litellm":
            current_config = migration.migrate_litellm(current_config)
        else:
            raise ValueError(f"Unknown config type: {config_type}")

        # Validate
        is_valid, errors = migration.validate(current_config)
        if not is_valid:
            raise MigrationError(
                f"Migration validation failed:\n" + "\n".join(errors)
            )

    print(f"   ✅ Migration complete")
    return current_config


# ============================================================================
# SPECIFIC MIGRATIONS
# ============================================================================

class Migration_v1_to_v2(Migration):
    """Migration from v1.0.0 to v2.0.0"""

    from_version = "1.0.0"
    to_version = "2.0.0"
    description = "Add vLLM constraints, remove unimplemented features"

    def migrate_providers(self, config: dict) -> dict:
        """Ensure only one vLLM provider is active"""
        providers = config.get("providers", {})

        active_vllm = [
            name for name, cfg in providers.items()
            if cfg.get("type") == "vllm" and cfg.get("status") == "active"
        ]

        if len(active_vllm) > 1:
            print(f"   ⚠️  Found {len(active_vllm)} active vLLM providers: {', '.join(active_vllm)}")
            print(f"       Disabling all but first: {active_vllm[0]}")

            for name in active_vllm[1:]:
                providers[name]["status"] = "disabled"

        # Add version to metadata
        if "metadata" not in config:
            config["metadata"] = {}
        config["metadata"]["schema_version"] = self.to_version

        return config

    def migrate_mappings(self, config: dict) -> dict:
        """Remove/comment out unimplemented features"""
        # Comment out unimplemented routing rules
        if "routing_rules" in config:
            routing_rules = config["routing_rules"]

            # Remove unimplemented features
            for key in ["request_metadata_routing", "model_size_routing"]:
                if key in routing_rules:
                    print(f"   ⚠️  Removing unimplemented feature: routing_rules.{key}")
                    del routing_rules[key]

        # Update special cases
        if "special_cases" in config:
            special = config["special_cases"]

            # Remove unimplemented special cases
            for key in ["first_request_routing", "error_based_routing", "geographic_routing"]:
                if key in special:
                    print(f"   ⚠️  Removing unimplemented feature: special_cases.{key}")
                    del special[key]

        # Add version to metadata
        if "metadata" not in config:
            config["metadata"] = {}
        config["metadata"]["schema_version"] = self.to_version

        return config

    def migrate_litellm(self, config: dict) -> dict:
        """No changes needed for litellm config in v2.0.0"""
        return config

    def validate(self, config: dict) -> tuple[bool, list[str]]:
        """Validate migrated configuration"""
        errors = []

        # Check providers have version
        if "providers" in config:
            metadata = config.get("metadata", {})
            if metadata.get("schema_version") != self.to_version:
                errors.append(f"Missing schema_version in metadata")

        return len(errors) == 0, errors


if __name__ == "__main__":
    # Example usage
    print("Available migrations:")
    for mig in get_all_migrations():
        print(f"  {mig.from_version} → {mig.to_version}: {mig.description}")
