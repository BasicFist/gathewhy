#!/usr/bin/env python3
"""
Configuration Schema Versioning and Migration Support
=====================================================

Provides version management, migration tracking, and schema evolution support for
AI Backend Unified Infrastructure configuration files.

Features:
- Version tracking for configuration files
- Migration history and rollback capability
- Schema evolution validation
- Configuration file health checks
- Migration planning tools

Usage:
    python3 scripts/schema_versioning.py --check-version
    python3 scripts/schema_versioning.py --plan-migration v1.0 v2.0
    python3 scripts/schema_versioning.py --validate-migration
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

# ============================================================================
# SCHEMA DEFINITIONS BY VERSION
# ============================================================================


class SchemaVersions:
    """Define schema versions and their characteristics"""

    CURRENT_VERSION = "1.2.0"

    SCHEMA_HISTORY = {
        "1.0.0": {
            "name": "Initial AI Backend Configuration",
            "date": "2024-10-20",
            "config_files": {
                "providers.yaml": {"required": True, "key_fields": ["providers"]},
                "model-mappings.yaml": {"required": True, "key_fields": ["exact_matches", "patterns"]},
                "litellm-unified.yaml": {"required": True, "key_fields": ["model_list"]},
            },
            "breaking_changes": [],
            "deprecations": [],
            "migration_guide": "Initial version - no migration needed",
        },
        "1.1.0": {
            "name": "Enhanced Configuration Validation",
            "date": "2024-10-22",
            "config_files": {
                "providers.yaml": {
                    "required": True,
                    "key_fields": ["providers"],
                    "new_fields": ["metadata", "health_checks"],
                },
                "model-mappings.yaml": {
                    "required": True,
                    "key_fields": ["exact_matches", "patterns"],
                    "new_fields": ["fallback_chains", "capabilities"],
                },
                "litellm-unified.yaml": {
                    "required": True,
                    "key_fields": ["model_list"],
                    "new_fields": ["router_settings", "server_settings"],
                },
            },
            "breaking_changes": [],
            "deprecations": [],
            "migration_guide": """
            1. Add 'metadata' section to providers.yaml (optional)
            2. Add 'fallback_chains' section to model-mappings.yaml (optional)
            3. Validate with: python3 scripts/validate-config-schema.py
            """,
        },
        "1.2.0": {
            "name": "Advanced Schema Validation & Versioning",
            "date": "2024-10-25",
            "config_files": {
                "providers.yaml": {
                    "required": True,
                    "key_fields": ["providers"],
                    "new_fields": ["schema_version", "last_validated"],
                },
                "model-mappings.yaml": {
                    "required": True,
                    "key_fields": ["exact_matches"],
                    "new_fields": ["schema_version", "schema_metadata"],
                },
                "litellm-unified.yaml": {
                    "required": True,
                    "key_fields": ["model_list"],
                    "new_fields": ["schema_version", "config_metadata"],
                },
            },
            "breaking_changes": [],
            "deprecations": [],
            "migration_guide": """
            1. Add schema_version field to each config file
            2. Update configuration headers with schema_metadata
            3. Run validation: python3 scripts/validate-config-schema.py
            4. Store migration history in config backups
            """,
        },
    }

    @classmethod
    def get_version_info(cls, version: str) -> dict[str, Any]:
        """Get information about a specific schema version"""
        return cls.SCHEMA_HISTORY.get(version, {})

    @classmethod
    def get_migration_path(cls, from_version: str, to_version: str) -> list[str]:
        """Calculate migration path between versions"""
        versions = list(cls.SCHEMA_HISTORY.keys())
        try:
            from_idx = versions.index(from_version)
            to_idx = versions.index(to_version)

            if from_idx > to_idx:
                logger.error(f"Cannot downgrade from {from_version} to {to_version}")
                return []

            return versions[from_idx : to_idx + 1]
        except ValueError:
            logger.error(f"Unknown version: {from_version} or {to_version}")
            return []


# ============================================================================
# CONFIGURATION VERSION MANAGER
# ============================================================================


class ConfigVersionManager:
    """Manages configuration versioning and metadata"""

    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self.providers_file = self.config_dir / "providers.yaml"
        self.mappings_file = self.config_dir / "model-mappings.yaml"
        self.litellm_file = self.config_dir / "litellm-unified.yaml"
        self.version_file = self.config_dir / ".schema-version"
        self.migration_history_file = self.config_dir / ".migration-history"

    def get_current_schema_version(self) -> str:
        """Get current schema version from version file or configs"""
        # Check version file first
        if self.version_file.exists():
            try:
                with open(self.version_file) as f:
                    data = json.load(f)
                    return data.get("version", SchemaVersions.CURRENT_VERSION)
            except Exception as e:
                logger.warning(f"Error reading version file: {e}")

        # Fall back to current version
        return SchemaVersions.CURRENT_VERSION

    def set_schema_version(self, version: str) -> bool:
        """Set schema version in version file"""
        try:
            version_data = {
                "version": version,
                "updated_at": datetime.now().isoformat(),
                "schema_version": SchemaVersions.get_version_info(version),
            }

            with open(self.version_file, "w") as f:
                json.dump(version_data, f, indent=2)

            logger.info(f"Schema version updated to {version}")
            return True
        except Exception as e:
            logger.error(f"Error setting schema version: {e}")
            return False

    def add_version_metadata_to_config(self, file_path: Path, version: str) -> bool:
        """Add version metadata to a configuration file"""
        try:
            with open(file_path) as f:
                config = yaml.safe_load(f) or {}

            # Add version information
            config["schema_version"] = version
            config["last_validated"] = datetime.now().isoformat()

            with open(file_path, "w") as f:
                yaml.dump(config, f, sort_keys=False, default_flow_style=False)

            logger.info(f"Added version metadata to {file_path.name}")
            return True
        except Exception as e:
            logger.error(f"Error adding metadata to {file_path}: {e}")
            return False

    def record_migration(self, from_version: str, to_version: str, status: str = "success"):
        """Record migration in history file"""
        try:
            history = []
            if self.migration_history_file.exists():
                with open(self.migration_history_file) as f:
                    history = json.load(f)

            entry = {
                "timestamp": datetime.now().isoformat(),
                "from_version": from_version,
                "to_version": to_version,
                "status": status,
                "files_affected": [
                    str(self.providers_file.name),
                    str(self.mappings_file.name),
                    str(self.litellm_file.name),
                ],
            }

            history.append(entry)

            with open(self.migration_history_file, "w") as f:
                json.dump(history, f, indent=2)

            logger.info(f"Migration recorded: {from_version} → {to_version} ({status})")
            return True
        except Exception as e:
            logger.error(f"Error recording migration: {e}")
            return False

    def get_migration_history(self) -> list[dict]:
        """Get migration history"""
        if not self.migration_history_file.exists():
            return []

        try:
            with open(self.migration_history_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading migration history: {e}")
            return []


# ============================================================================
# SCHEMA VALIDATION & MIGRATION PLANNING
# ============================================================================


class SchemaMigrationPlanner:
    """Plans and validates configuration migrations between versions"""

    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self.version_manager = ConfigVersionManager(config_dir)
        self.issues: list[dict] = []
        self.warnings: list[dict] = []

    def check_schema_compatibility(self, from_version: str, to_version: str) -> bool:
        """Check if migration is compatible"""
        migration_path = SchemaVersions.get_migration_path(from_version, to_version)

        if not migration_path:
            logger.error(f"No migration path from {from_version} to {to_version}")
            return False

        logger.info(f"Migration path: {' → '.join(migration_path)}")

        # Check for breaking changes along the path
        breaking_changes = []
        for version in migration_path[1:]:
            version_info = SchemaVersions.get_version_info(version)
            if version_info.get("breaking_changes"):
                breaking_changes.extend(version_info["breaking_changes"])

        if breaking_changes:
            logger.warning(f"Breaking changes detected: {breaking_changes}")
            return False

        return True

    def validate_config_for_migration(self, file_path: Path) -> bool:
        """Validate configuration file is ready for migration"""
        try:
            with open(file_path) as f:
                config = yaml.safe_load(f)

            if not config:
                self.issues.append({"file": file_path.name, "issue": "Empty configuration"})
                return False

            return True
        except Exception as e:
            self.issues.append({"file": file_path.name, "issue": str(e)})
            return False

    def plan_migration(self, to_version: str) -> dict:
        """Plan migration to a target version"""
        current_version = self.version_manager.get_current_schema_version()

        plan = {
            "current_version": current_version,
            "target_version": to_version,
            "migration_path": SchemaVersions.get_migration_path(current_version, to_version),
            "steps": [],
            "rollback_procedure": [],
            "validation_checks": [],
        }

        # Generate migration steps
        for version in plan["migration_path"][1:]:
            version_info = SchemaVersions.get_version_info(version)
            plan["steps"].append(
                {
                    "version": version,
                    "name": version_info.get("name"),
                    "guide": version_info.get("migration_guide"),
                }
            )

        # Generate rollback procedure (reverse order)
        for version in reversed(plan["migration_path"][:-1]):
            plan["rollback_procedure"].append(
                {
                    "action": f"Restore backup from version {version}",
                    "command": f"cp config/backups/providers.yaml.{version} config/providers.yaml",
                }
            )

        # Add validation checks
        plan["validation_checks"] = [
            "Run: python3 scripts/validate-config-schema.py",
            "Run: python3 scripts/validate-config-consistency.py",
            "Test: curl http://localhost:4000/v1/models",
        ]

        return plan

    def print_migration_plan(self, plan: dict):
        """Pretty print migration plan"""
        print(f"\n{'=' * 70}")
        print(f"Migration Plan: {plan['current_version']} → {plan['target_version']}")
        print(f"{'=' * 70}\n")

        print("📋 Migration Path:")
        for version in plan["migration_path"]:
            print(f"  → {version}")

        print("\n🔧 Migration Steps:")
        for i, step in enumerate(plan["steps"], 1):
            print(f"\n  Step {i}: {step['version']} - {step['name']}")
            print(f"  {step['guide']}")

        print("\n🔄 Rollback Procedure:")
        for i, step in enumerate(plan["rollback_procedure"], 1):
            print(f"  {i}. {step['action']}")
            print(f"     {step['command']}")

        print("\n✅ Validation Checks:")
        for check in plan["validation_checks"]:
            print(f"  - {check}")

        print(f"\n{'=' * 70}\n")


# ============================================================================
# CONFIGURATION HEALTH CHECK
# ============================================================================


class ConfigHealthChecker:
    """Checks overall health and compliance of configuration files"""

    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self.health_status: dict[str, Any] = {}
        self.issues: list[str] = []

    def check_all_files_exist(self) -> bool:
        """Verify all required configuration files exist"""
        required_files = ["providers.yaml", "model-mappings.yaml", "litellm-unified.yaml"]

        missing = []
        for filename in required_files:
            file_path = self.config_dir / filename
            if not file_path.exists():
                missing.append(filename)
                self.issues.append(f"Missing required file: {filename}")

        self.health_status["files_exist"] = len(missing) == 0
        self.health_status["missing_files"] = missing

        return len(missing) == 0

    def check_file_sizes(self) -> bool:
        """Verify configuration files have reasonable sizes"""
        size_checks = {
            "providers.yaml": (1_000, 100_000),  # 1KB - 100KB
            "model-mappings.yaml": (2_000, 200_000),  # 2KB - 200KB
            "litellm-unified.yaml": (3_000, 300_000),  # 3KB - 300KB
        }

        all_ok = True
        for filename, (min_size, max_size) in size_checks.items():
            file_path = self.config_dir / filename
            if not file_path.exists():
                continue

            size = file_path.stat().st_size
            if size < min_size or size > max_size:
                all_ok = False
                self.issues.append(
                    f"File {filename} has unusual size: {size} bytes "
                    f"(expected {min_size}-{max_size})"
                )

        self.health_status["file_sizes_ok"] = all_ok
        return all_ok

    def check_yaml_validity(self) -> bool:
        """Verify all YAML files are valid"""
        yaml_files = ["providers.yaml", "model-mappings.yaml", "litellm-unified.yaml"]

        all_valid = True
        for filename in yaml_files:
            file_path = self.config_dir / filename
            if not file_path.exists():
                continue

            try:
                with open(file_path) as f:
                    yaml.safe_load(f)
            except Exception as e:
                all_valid = False
                self.issues.append(f"YAML error in {filename}: {str(e)}")

        self.health_status["yaml_valid"] = all_valid
        return all_valid

    def check_schema_version_consistency(self) -> bool:
        """Verify schema versions are consistent across files"""
        version_manager = ConfigVersionManager(self.config_dir)
        current_version = version_manager.get_current_schema_version()

        self.health_status["schema_version"] = current_version
        return True

    def run_health_check(self) -> bool:
        """Run comprehensive health check"""
        logger.info("Running configuration health check...")

        self.check_all_files_exist()
        self.check_file_sizes()
        self.check_yaml_validity()
        self.check_schema_version_consistency()

        self.health_status["overall_healthy"] = len(self.issues) == 0

        return self.health_status["overall_healthy"]

    def print_health_report(self):
        """Print formatted health check report"""
        print(f"\n{'=' * 70}")
        print("Configuration Health Check Report")
        print(f"{'=' * 70}\n")

        status_symbol = "✅" if self.health_status.get("overall_healthy") else "❌"
        print(f"{status_symbol} Overall Status: {'HEALTHY' if self.health_status.get('overall_healthy') else 'ISSUES FOUND'}\n")

        print(f"Files Exist: {'✅' if self.health_status.get('files_exist') else '❌'}")
        if self.health_status.get("missing_files"):
            print(f"  Missing: {', '.join(self.health_status['missing_files'])}")

        print(f"\nFile Sizes: {'✅' if self.health_status.get('file_sizes_ok') else '❌'}")

        print(f"\nYAML Valid: {'✅' if self.health_status.get('yaml_valid') else '❌'}")

        print(f"\nSchema Version: {self.health_status.get('schema_version')}")

        if self.issues:
            print(f"\n⚠️  Issues Found ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  - {issue}")

        print(f"\n{'=' * 70}\n")


# ============================================================================
# MAIN CLI
# ============================================================================


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Configuration schema versioning and migration support")

    parser.add_argument("--check-version", action="store_true", help="Check current schema version")
    parser.add_argument(
        "--plan-migration",
        nargs=2,
        metavar=("FROM", "TO"),
        help="Plan migration between versions",
    )
    parser.add_argument(
        "--validate-migration",
        action="store_true",
        help="Validate configuration readiness for migration",
    )
    parser.add_argument("--health-check", action="store_true", help="Run configuration health check")
    parser.add_argument("--history", action="store_true", help="Show migration history")

    args = parser.parse_args()

    config_dir = Path(__file__).parent.parent / "config"

    if args.check_version:
        manager = ConfigVersionManager(config_dir)
        version = manager.get_current_schema_version()
        print(f"Current schema version: {version}")
        version_info = SchemaVersions.get_version_info(version)
        print(f"  Name: {version_info.get('name')}")
        print(f"  Date: {version_info.get('date')}")

    elif args.plan_migration:
        from_version, to_version = args.plan_migration
        planner = SchemaMigrationPlanner(config_dir)

        if not planner.check_schema_compatibility(from_version, to_version):
            logger.error("Migration path is not compatible")
            sys.exit(1)

        plan = planner.plan_migration(to_version)
        planner.print_migration_plan(plan)

    elif args.validate_migration:
        planner = SchemaMigrationPlanner(config_dir)
        all_valid = True

        for file_path in [
            config_dir / "providers.yaml",
            config_dir / "model-mappings.yaml",
            config_dir / "litellm-unified.yaml",
        ]:
            if not planner.validate_config_for_migration(file_path):
                all_valid = False

        if planner.issues:
            logger.error("Migration validation failed:")
            for issue in planner.issues:
                print(f"  - {issue}")
            sys.exit(1)

        logger.info("✅ All configurations ready for migration")

    elif args.health_check:
        checker = ConfigHealthChecker(config_dir)
        checker.run_health_check()
        checker.print_health_report()

    elif args.history:
        manager = ConfigVersionManager(config_dir)
        history = manager.get_migration_history()

        if not history:
            print("No migration history found")
        else:
            print("\n📋 Migration History:")
            for entry in history:
                print(f"\n  {entry['timestamp']}")
                print(f"  {entry['from_version']} → {entry['to_version']} ({entry['status']})")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
