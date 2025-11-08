#!/usr/bin/env python3
"""
Configuration Migration Tool
=============================

Migrates configuration files between schema versions.

Usage:
    python3 scripts/migrate-config.py --check               # Check version compatibility
    python3 scripts/migrate-config.py --auto                # Auto-migrate to latest
    python3 scripts/migrate-config.py --from 1.0.0 --to 2.0.0   # Specific migration

Examples:
    # Check current versions
    $ python3 scripts/migrate-config.py --check
    providers.yaml: v1.0.0 (migration available to v2.0.0)
    model-mappings.yaml: v1.0.0 (migration available to v2.0.0)

    # Auto-migrate to latest
    $ python3 scripts/migrate-config.py --auto
    🔄 Migrating providers.yaml from v1.0.0 to v2.0.0
    ✅ Migration complete
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.migrations import migrate_config, find_migration_path, MigrationError
from config.schemas.version import SCHEMA_VERSION, validate_version, get_breaking_changes

# Configuration paths
PROJECT_ROOT = Path(__file__).parent.parent
PROVIDERS_FILE = PROJECT_ROOT / "config" / "providers.yaml"
MAPPINGS_FILE = PROJECT_ROOT / "config" / "model-mappings.yaml"


def get_config_version(config_path: Path) -> str:
    """Extract version from configuration file"""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        metadata = config.get("metadata", {})
        return metadata.get("schema_version", "1.0.0")  # Default to 1.0.0 if missing
    except Exception as e:
        print(f"❌ Error reading {config_path}: {e}")
        return "0.0.0"


def check_versions():
    """Check current configuration versions"""
    print("📋 Configuration Version Status")
    print("=" * 60)
    print(f"\nCurrent Schema Version: {SCHEMA_VERSION}\n")

    configs = [
        ("providers.yaml", PROVIDERS_FILE, "providers"),
        ("model-mappings.yaml", MAPPINGS_FILE, "mappings"),
    ]

    needs_migration = False

    for name, path, config_type in configs:
        current_version = get_config_version(path)
        is_valid, message = validate_version(current_version, SCHEMA_VERSION)

        status_icon = "✅" if is_valid else "⚠️"
        print(f"{status_icon} {name}: v{current_version}")
        print(f"   {message}")

        if not is_valid:
            needs_migration = True
            # Show breaking changes
            breaking = get_breaking_changes(current_version, SCHEMA_VERSION)
            if breaking:
                print(f"\n   Breaking changes:")
                for change in breaking:
                    print(f"     - {change}")

        print()

    if needs_migration:
        print("⚠️  Migration required. Run with --auto to migrate automatically")
        return 1
    else:
        print("✅ All configurations up to date")
        return 0


def migrate_file(config_path: Path, config_type: str, from_version: str, to_version: str, dry_run: bool = False):
    """Migrate a single configuration file"""
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating {config_path.name}")
    print(f"  From: v{from_version}")
    print(f"  To:   v{to_version}")
    print()

    # Load configuration
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Backup original
    if not dry_run:
        backup_path = config_path.parent / f"{config_path.name}.backup-v{from_version}"
        with open(backup_path, 'w') as f:
            yaml.dump(config, f, indent=2, default_flow_style=False)
        print(f"  📦 Backup created: {backup_path.name}")

    # Migrate
    try:
        migrated = migrate_config(config, config_type, from_version, to_version)

        if dry_run:
            print(f"  ℹ️  Dry run - no files modified")
        else:
            # Write migrated configuration
            with open(config_path, 'w') as f:
                yaml.dump(migrated, f, indent=2, default_flow_style=False)
            print(f"  ✅ Migration complete: {config_path.name}")

    except MigrationError as e:
        print(f"  ❌ Migration failed: {e}")
        raise


def auto_migrate(dry_run: bool = False):
    """Auto-migrate all configurations to latest version"""
    print("🔄 Auto-Migration to Latest Schema")
    print("=" * 60)

    configs = [
        ("providers.yaml", PROVIDERS_FILE, "providers"),
        ("model-mappings.yaml", MAPPINGS_FILE, "mappings"),
    ]

    for name, path, config_type in configs:
        current_version = get_config_version(path)

        if current_version == SCHEMA_VERSION:
            print(f"\n✓ {name} already at v{SCHEMA_VERSION}")
            continue

        try:
            migrate_file(path, config_type, current_version, SCHEMA_VERSION, dry_run)
        except MigrationError as e:
            print(f"\n❌ Failed to migrate {name}: {e}")
            return 1

    print("\n" + "=" * 60)
    if dry_run:
        print("✅ Dry run complete - no files modified")
    else:
        print("✅ All migrations complete!")
        print("\nNext steps:")
        print("  1. Review migrated configurations")
        print("  2. Regenerate LiteLLM config: python3 scripts/generate-litellm-config.py")
        print("  3. Validate: python3 scripts/validate-config-schema.py")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Migrate configuration files between schema versions"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check current configuration versions"
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-migrate to latest schema version"
    )

    parser.add_argument(
        "--from",
        dest="from_version",
        help="Source version"
    )

    parser.add_argument(
        "--to",
        dest="to_version",
        help="Target version"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )

    args = parser.parse_args()

    try:
        if args.check:
            return check_versions()

        if args.auto:
            return auto_migrate(args.dry_run)

        if args.from_version and args.to_version:
            # Manual migration
            configs = [
                ("providers.yaml", PROVIDERS_FILE, "providers"),
                ("model-mappings.yaml", MAPPINGS_FILE, "mappings"),
            ]

            for name, path, config_type in configs:
                migrate_file(path, config_type, args.from_version, args.to_version, args.dry_run)

            return 0

        # No arguments - show help
        parser.print_help()
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
