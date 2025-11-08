#!/usr/bin/env python3
"""
Unified Configuration Manager
==============================

Single command to manage all configuration layers.
Simplifies the 3-layer configuration structure:
  providers.yaml → model-mappings.yaml → litellm-unified.yaml

Usage:
    python3 scripts/config-manager.py validate          # Validate all configs
    python3 scripts/config-manager.py generate          # Generate LiteLLM config
    python3 scripts/config-manager.py migrate           # Migrate to latest version
    python3 scripts/config-manager.py status            # Show configuration status
    python3 scripts/config-manager.py add-provider      # Interactive provider addition
    python3 scripts/config-manager.py test-routing      # Test model routing

Examples:
    # Full workflow
    $ python3 scripts/config-manager.py status
    $ python3 scripts/config-manager.py validate
    $ python3 scripts/config-manager.py generate
    $ python3 scripts/config-manager.py test-routing --model llama3.1:8b
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


class Colors:
    """ANSI color codes"""
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status"""
    print(f"{Colors.BLUE}→{Colors.NC} {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"{Colors.GREEN}✓{Colors.NC} {description} - Success\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}✗{Colors.NC} {description} - Failed\n")
        return False


def cmd_validate(args):
    """Validate all configuration files"""
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}Configuration Validation{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

    steps = [
        (["python3", str(SCRIPTS_DIR / "validate-config-schema.py")],
         "Schema validation"),
        (["python3", str(SCRIPTS_DIR / "validate-config-consistency.py")],
         "Consistency validation"),
        ([str(SCRIPTS_DIR / "validate-all-configs.sh")],
         "Comprehensive validation"),
    ]

    all_passed = True
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            all_passed = False
            if not args.continue_on_error:
                print(f"\n{Colors.RED}✗ Validation failed - stopping{Colors.NC}")
                return 1

    if all_passed:
        print(f"{Colors.GREEN}✓ All validations passed{Colors.NC}")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠ Some validations failed{Colors.NC}")
        return 1


def cmd_generate(args):
    """Generate LiteLLM configuration"""
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}Configuration Generation{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

    # Validate first
    if not args.skip_validation:
        print(f"{Colors.BLUE}→{Colors.NC} Pre-generation validation...\n")
        if cmd_validate(args) != 0:
            print(f"\n{Colors.RED}✗ Validation failed - aborting generation{Colors.NC}")
            return 1

    # Generate
    cmd = ["python3", str(SCRIPTS_DIR / "generate-litellm-config.py")]
    if run_command(cmd, "Generate LiteLLM config"):
        print(f"\n{Colors.GREEN}✓ Configuration generated successfully{Colors.NC}")
        print(f"\nNext steps:")
        print(f"  1. Review: config/litellm-unified.yaml")
        print(f"  2. Test: curl http://localhost:4000/v1/models")
        print(f"  3. Restart: systemctl --user restart litellm.service")
        return 0
    else:
        print(f"\n{Colors.RED}✗ Generation failed{Colors.NC}")
        return 1


def cmd_migrate(args):
    """Migrate configurations to latest version"""
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}Configuration Migration{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

    cmd = ["python3", str(SCRIPTS_DIR / "migrate-config.py")]

    if args.check_only:
        cmd.append("--check")
    elif args.dry_run:
        cmd.extend(["--auto", "--dry-run"])
    else:
        cmd.append("--auto")

    if run_command(cmd, "Migrate configurations"):
        if not args.check_only and not args.dry_run:
            print(f"\n{Colors.GREEN}✓ Migration completed{Colors.NC}")
            print(f"\nRegenerate LiteLLM config:")
            print(f"  python3 scripts/config-manager.py generate")
        return 0
    else:
        return 1


def cmd_status(args):
    """Show configuration status"""
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}Configuration Status{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

    # Load configurations
    providers_file = PROJECT_ROOT / "config" / "providers.yaml"
    mappings_file = PROJECT_ROOT / "config" / "model-mappings.yaml"
    litellm_file = PROJECT_ROOT / "config" / "litellm-unified.yaml"

    try:
        with open(providers_file) as f:
            providers = yaml.safe_load(f)
        with open(mappings_file) as f:
            mappings = yaml.safe_load(f)
        with open(litellm_file) as f:
            litellm = yaml.safe_load(f)

        # Providers
        active_providers = [
            name for name, cfg in providers.get("providers", {}).items()
            if cfg.get("status") == "active"
        ]
        print(f"{Colors.GREEN}Providers:{Colors.NC}")
        print(f"  Active: {len(active_providers)}")
        for name in active_providers:
            prov = providers["providers"][name]
            model_count = len(prov.get("models", []))
            print(f"    - {name}: {model_count} models ({prov.get('type')})")

        # Routing
        print(f"\n{Colors.GREEN}Routing:{Colors.NC}")
        exact = len(mappings.get("exact_matches", {}))
        patterns = len(mappings.get("patterns", []))
        fallbacks = len(mappings.get("fallback_chains", {}))
        print(f"  Exact matches: {exact}")
        print(f"  Pattern rules: {patterns}")
        print(f"  Fallback chains: {fallbacks}")

        # LiteLLM
        print(f"\n{Colors.GREEN}LiteLLM Config:{Colors.NC}")
        models = len(litellm.get("model_list", []))
        print(f"  Registered models: {models}")

        # Version
        version = providers.get("metadata", {}).get("schema_version", "unknown")
        print(f"  Schema version: {version}")

        print(f"\n{Colors.GREEN}✓ All configuration files loaded successfully{Colors.NC}")
        return 0

    except Exception as e:
        print(f"{Colors.RED}✗ Error loading configurations: {e}{Colors.NC}")
        return 1


def cmd_test_routing(args):
    """Test model routing"""
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}Test Model Routing{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

    if not args.model:
        print(f"{Colors.RED}✗ --model parameter required{Colors.NC}")
        return 1

    # Load model mappings
    mappings_file = PROJECT_ROOT / "config" / "model-mappings.yaml"
    try:
        with open(mappings_file) as f:
            mappings = yaml.safe_load(f)

        model = args.model
        print(f"Testing routing for model: {Colors.BLUE}{model}{Colors.NC}\n")

        # Check exact match
        exact = mappings.get("exact_matches", {})
        if model in exact:
            config = exact[model]
            print(f"{Colors.GREEN}✓ Exact match found:{Colors.NC}")
            print(f"  Provider: {config.get('provider')}")
            print(f"  Priority: {config.get('priority')}")
            if config.get('fallback'):
                print(f"  Fallback: {config.get('fallback')}")
            return 0

        # Check patterns
        import re
        patterns = mappings.get("patterns", [])
        for pattern_config in patterns:
            pattern = pattern_config.get("pattern", "")
            if re.match(pattern, model):
                print(f"{Colors.GREEN}✓ Pattern match found:{Colors.NC}")
                print(f"  Pattern: {pattern}")
                print(f"  Provider: {pattern_config.get('provider')}")
                return 0

        print(f"{Colors.YELLOW}⚠ No routing found for model{Colors.NC}")
        print(f"\nAvailable exact matches:")
        for m in list(exact.keys())[:10]:
            print(f"  - {m}")
        return 1

    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.NC}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Unified Configuration Manager - Simplifies 3-layer config structure"
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Validate
    validate_parser = subparsers.add_parser('validate', help='Validate all configurations')
    validate_parser.add_argument('--continue-on-error', action='store_true',
                                  help='Continue even if validation fails')

    # Generate
    generate_parser = subparsers.add_parser('generate', help='Generate LiteLLM config')
    generate_parser.add_argument('--skip-validation', action='store_true',
                                  help='Skip pre-generation validation')

    # Migrate
    migrate_parser = subparsers.add_parser('migrate', help='Migrate to latest version')
    migrate_parser.add_argument('--check-only', action='store_true',
                                 help='Only check version compatibility')
    migrate_parser.add_argument('--dry-run', action='store_true',
                                 help='Show what would change without modifying files')

    # Status
    subparsers.add_parser('status', help='Show configuration status')

    # Test routing
    test_parser = subparsers.add_parser('test-routing', help='Test model routing')
    test_parser.add_argument('--model', help='Model name to test')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatch to command handler
    commands = {
        'validate': cmd_validate,
        'generate': cmd_generate,
        'migrate': cmd_migrate,
        'status': cmd_status,
        'test-routing': cmd_test_routing,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
