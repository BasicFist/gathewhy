#!/usr/bin/env python3
"""
Configuration Consistency Validator
====================================
Validates model name consistency across all configuration files.

Addresses Codex-identified risk: "Model name consistency across configs"

Checks:
1. Model names in providers.yaml match model-mappings.yaml
2. Model names in model-mappings.yaml match litellm-unified.yaml
3. Backend model references are consistent
4. No typos or case mismatches
5. All routing targets exist in provider registry

Usage:
    python3 scripts/validate-config-consistency.py
    python3 scripts/validate-config-consistency.py --fix-common-issues

Exit codes:
    0: All validations passed
    1: Validation errors found
    2: Configuration file errors (missing, invalid YAML)
"""

import argparse
import sys
from pathlib import Path

import yaml


class Colors:
    """ANSI color codes for terminal output"""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


class ConfigValidator:
    """Validates consistency across AI backend configuration files"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = project_root / "config"

        # Configuration files
        self.providers_file = self.config_dir / "providers.yaml"
        self.mappings_file = self.config_dir / "model-mappings.yaml"
        self.litellm_file = self.config_dir / "litellm-unified.yaml"

        # Loaded configurations
        self.providers_config = None
        self.mappings_config = None
        self.litellm_config = None

        # Extracted model names
        self.provider_models: dict[str, set[str]] = {}
        self.mapping_models: set[str] = set()
        self.litellm_models: set[str] = set()

        # Validation errors
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def log_info(self, message: str):
        """Print info message"""
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

    def log_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}[✓]{Colors.NC} {message}")

    def log_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")
        self.warnings.append(message)

    def log_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")
        self.errors.append(message)

    def load_configurations(self) -> bool:
        """Load all configuration files"""
        self.log_info("Loading configuration files...")

        try:
            # Load providers.yaml
            if not self.providers_file.exists():
                self.log_error(f"Missing file: {self.providers_file}")
                return False
            with open(self.providers_file) as f:
                self.providers_config = yaml.safe_load(f)
            self.log_success(f"Loaded {self.providers_file.name}")

            # Load model-mappings.yaml
            if not self.mappings_file.exists():
                self.log_error(f"Missing file: {self.mappings_file}")
                return False
            with open(self.mappings_file) as f:
                self.mappings_config = yaml.safe_load(f)
            self.log_success(f"Loaded {self.mappings_file.name}")

            # Load litellm-unified.yaml
            if not self.litellm_file.exists():
                self.log_error(f"Missing file: {self.litellm_file}")
                return False
            with open(self.litellm_file) as f:
                self.litellm_config = yaml.safe_load(f)
            self.log_success(f"Loaded {self.litellm_file.name}")

            return True

        except yaml.YAMLError as e:
            self.log_error(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            self.log_error(f"Error loading configurations: {e}")
            return False

    def extract_provider_models(self):
        """Extract model names from providers.yaml"""
        self.log_info("Extracting model names from providers.yaml...")

        providers = self.providers_config.get("providers", {})

        for provider_name, provider_config in providers.items():
            if provider_config.get("status") != "active":
                continue

            models = provider_config.get("models", [])
            model_names = set()

            for model in models:
                if isinstance(model, dict):
                    name = model.get("name")
                    if name:
                        model_names.add(name)
                elif isinstance(model, str):
                    model_names.add(model)

            if model_names:
                self.provider_models[provider_name] = model_names
                self.log_success(f"  {provider_name}: {len(model_names)} models")

    def extract_mapping_models(self):
        """Extract model names from model-mappings.yaml"""
        self.log_info("Extracting model names from model-mappings.yaml...")

        # Exact matches
        exact_matches = self.mappings_config.get("exact_matches", {})
        for model_name in exact_matches:
            self.mapping_models.add(model_name)

        # Load balancing configs
        load_balancing = self.mappings_config.get("load_balancing", {})
        for model_name in load_balancing:
            self.mapping_models.add(model_name)

        # Fallback chains
        fallback_chains = self.mappings_config.get("fallback_chains", {})
        for model_name in fallback_chains:
            if model_name != "default":
                self.mapping_models.add(model_name)

        self.log_success(f"  Found {len(self.mapping_models)} model definitions")

    def extract_litellm_models(self):
        """Extract model names from litellm-unified.yaml"""
        self.log_info("Extracting model names from litellm-unified.yaml...")

        model_list = self.litellm_config.get("model_list", [])

        for model_entry in model_list:
            model_name = model_entry.get("model_name")
            if model_name:
                self.litellm_models.add(model_name)

                # Also extract the actual model path from litellm_params
                litellm_params = model_entry.get("litellm_params", {})
                model_path = litellm_params.get("model", "")

                # Extract model name after provider prefix (e.g., "ollama/llama3.1:8b" -> "llama3.1:8b")
                if "/" in model_path:
                    parts = model_path.split("/", 1)
                    if len(parts) > 1:
                        actual_model = parts[1]
                        # Store mapping for validation
                        model_entry["_extracted_model"] = actual_model

        self.log_success(f"  Found {len(self.litellm_models)} model definitions")

    def validate_provider_to_mapping_consistency(self):
        """Validate that models in providers.yaml are referenced in model-mappings.yaml"""
        self.log_info("Validating providers → mappings consistency...")

        inconsistencies_found = False

        for provider_name, models in self.provider_models.items():
            for model_name in models:
                # Check if model is referenced in exact_matches
                if model_name not in self.mapping_models:
                    self.log_warning(
                        f"Model '{model_name}' from provider '{provider_name}' "
                        f"not found in model-mappings.yaml exact_matches"
                    )
                    inconsistencies_found = True

        if not inconsistencies_found:
            self.log_success("All provider models have routing definitions")

    def validate_mapping_to_provider_consistency(self):
        """Validate that model routes target existing providers"""
        self.log_info("Validating mappings → providers consistency...")

        active_providers = {
            name
            for name, config in self.providers_config.get("providers", {}).items()
            if config.get("status") == "active"
        }

        exact_matches = self.mappings_config.get("exact_matches", {})

        for model_name, route_config in exact_matches.items():
            provider = route_config.get("provider")

            # Check primary provider exists
            if provider and provider not in active_providers:
                self.log_error(f"Model '{model_name}' routes to non-existent provider '{provider}'")

            # Check fallback provider exists
            fallback = route_config.get("fallback")
            if fallback and fallback not in active_providers:
                self.log_error(
                    f"Model '{model_name}' fallback provider '{fallback}' does not exist"
                )

        if not self.errors:
            self.log_success("All routing targets reference existing providers")

    def validate_litellm_consistency(self):
        """Validate LiteLLM model definitions match provider models"""
        self.log_info("Validating LiteLLM model definitions...")

        model_list = self.litellm_config.get("model_list", [])

        # Collect all provider model names for fuzzy matching
        all_provider_models = set()
        for models in self.provider_models.values():
            all_provider_models.update(models)

        for model_entry in model_list:
            model_name = model_entry.get("model_name")
            litellm_params = model_entry.get("litellm_params", {})
            model_path = litellm_params.get("model", "")

            # Extract actual model name
            extracted_model = None
            if "/" in model_path:
                parts = model_path.split("/", 1)
                if len(parts) > 1:
                    extracted_model = parts[1]

            # Validate extracted model exists in providers
            # Check if it's a vLLM HuggingFace path (acceptable)
            if (
                extracted_model
                and extracted_model not in all_provider_models
                and not extracted_model.startswith("meta-llama/")
                and not extracted_model.startswith("mistralai/")
                and not extracted_model.startswith("Qwen/")
            ):
                self.log_warning(
                    f"LiteLLM model '{model_name}' references '{extracted_model}' "
                    f"which is not defined in providers.yaml"
                )

    def validate_naming_conventions(self):
        """Validate model naming conventions and detect typos"""
        self.log_info("Validating naming conventions...")

        # Common typo patterns
        similar_names: dict[str, list[str]] = {}

        all_models = set()
        all_models.update(self.mapping_models)
        all_models.update(self.litellm_models)
        for models in self.provider_models.values():
            all_models.update(models)

        # Group similar names (simple Levenshtein-like check)
        for model_a in all_models:
            for model_b in all_models:
                if model_a != model_b:
                    # Check if names are very similar (same base, different suffix)
                    base_a = model_a.lower().replace("-", "").replace("_", "").replace(":", "")
                    base_b = model_b.lower().replace("-", "").replace("_", "").replace(":", "")

                    # If 80% similar, flag as potential typo
                    similarity = len(set(base_a) & set(base_b)) / max(len(base_a), len(base_b))
                    if similarity > 0.8 and similarity < 1.0:
                        if model_a not in similar_names:
                            similar_names[model_a] = []
                        similar_names[model_a].append(model_b)

        if similar_names:
            self.log_warning("Potential typos or naming inconsistencies detected:")
            for model, similars in similar_names.items():
                print(f"    '{model}' similar to: {', '.join(similars)}")
        else:
            self.log_success("No obvious naming inconsistencies detected")

    def validate_backend_model_references(self):
        """Validate backend_model references in model-mappings.yaml"""
        self.log_info("Validating backend_model references...")

        exact_matches = self.mappings_config.get("exact_matches", {})

        # Collect all provider model names
        all_provider_models = set()
        for models in self.provider_models.values():
            all_provider_models.update(models)

        for model_name, route_config in exact_matches.items():
            backend_model = route_config.get("backend_model")

            # Check if backend_model exists in providers
            if backend_model and backend_model not in all_provider_models:
                self.log_warning(
                    f"Model '{model_name}' references backend_model '{backend_model}' "
                    f"which is not defined in providers.yaml"
                )

        if not self.warnings[-1:] or "backend_model" not in self.warnings[-1]:
            self.log_success("All backend_model references are valid")

    def run_validation(self) -> bool:
        """Run all validation checks"""
        print(f"\n{Colors.BLUE}{'=' * 70}{Colors.NC}")
        print(f"{Colors.BLUE}Configuration Consistency Validation{Colors.NC}")
        print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}\n")

        # Load configurations
        if not self.load_configurations():
            return False

        print()  # Spacing

        # Extract model names from all configs
        self.extract_provider_models()
        self.extract_mapping_models()
        self.extract_litellm_models()

        print()  # Spacing

        # Run validation checks
        self.validate_provider_to_mapping_consistency()
        self.validate_mapping_to_provider_consistency()
        self.validate_backend_model_references()
        self.validate_litellm_consistency()
        self.validate_naming_conventions()

        # Summary
        print(f"\n{Colors.BLUE}{'=' * 70}{Colors.NC}")
        print(f"{Colors.BLUE}Validation Summary{Colors.NC}")
        print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}\n")

        print(f"Providers validated: {len(self.provider_models)}")
        print(f"Routing definitions: {len(self.mapping_models)}")
        print(f"LiteLLM models: {len(self.litellm_models)}")
        print(f"\nWarnings: {len(self.warnings)}")
        print(f"Errors: {len(self.errors)}")

        if self.errors:
            print(f"\n{Colors.RED}❌ Validation FAILED{Colors.NC}")
            return False
        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️  Validation passed with warnings{Colors.NC}")
            return True
        print(f"\n{Colors.GREEN}✅ All validations passed{Colors.NC}")
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate configuration consistency across AI backend configs"
    )
    parser.add_argument(
        "--fix-common-issues",
        action="store_true",
        help="Attempt to fix common naming inconsistencies (not implemented yet)",
    )

    parser.parse_args()

    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Run validation
    validator = ConfigValidator(project_root)
    success = validator.run_validation()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
