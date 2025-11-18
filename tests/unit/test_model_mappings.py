"""Unit tests for the model-mappings.yaml configuration file."""

from pathlib import Path

import pytest
import yaml

# Define the path to the model-mappings.yaml file
MAPPINGS_FILE = Path(__file__).parent.parent.parent / "config" / "model-mappings.yaml"


@pytest.fixture(scope="module")
def model_mappings_config():
    """Load the model-mappings.yaml configuration once for all tests."""
    with open(MAPPINGS_FILE) as f:
        return yaml.safe_load(f)


def test_model_mappings_file_exists():
    """Verify that model-mappings.yaml file exists."""
    assert MAPPINGS_FILE.exists(), f"model-mappings.yaml not found at {MAPPINGS_FILE}"


def test_model_mappings_is_valid_yaml(model_mappings_config):
    """Verify that model-mappings.yaml is valid YAML."""
    # The fixture already attempts to load it, so if it's loaded, it's valid YAML
    assert isinstance(
        model_mappings_config, dict
    ), "model-mappings.yaml is not a valid YAML dictionary"


def test_model_mappings_contains_expected_sections(model_mappings_config):
    """Verify that key sections are present in model-mappings.yaml."""
    expected_sections = [
        "exact_matches",
        "patterns",
        "capabilities",
        "load_balancing",
        "fallback_chains",
        "routing_rules",
        "special_cases",
        "metadata",
    ]
    for section in expected_sections:
        assert section in model_mappings_config, f"Missing expected section: '{section}'"


def test_exact_matches_structure(model_mappings_config):
    """Verify the structure of the 'exact_matches' section."""
    exact_matches = model_mappings_config.get("exact_matches", {})
    assert isinstance(exact_matches, dict), "'exact_matches' should be a dictionary"
    for model_name, config in exact_matches.items():
        assert isinstance(model_name, str), f"Model name '{model_name}' should be a string"
        assert isinstance(config, dict), f"Config for model '{model_name}' should be a dictionary"
        assert "provider" in config, f"Config for '{model_name}' missing 'provider' key"
        assert "priority" in config, f"Config for '{model_name}' missing 'priority' key"
        assert "fallback" in config, f"Config for '{model_name}' missing 'fallback' key"
        assert "description" in config, f"Config for '{model_name}' missing 'description' key"


def test_capabilities_structure(model_mappings_config):
    """Verify the structure of the 'capabilities' section."""
    capabilities = model_mappings_config.get("capabilities", {})
    assert isinstance(capabilities, dict), "'capabilities' should be a dictionary"
    for capability_name, config in capabilities.items():
        assert isinstance(
            capability_name, str
        ), f"Capability name '{capability_name}' should be a string"
        assert isinstance(
            config, dict
        ), f"Config for capability '{capability_name}' should be a dictionary"
        assert "description" in config, f"Config for '{capability_name}' missing 'description' key"
        assert (
            "routing_strategy" in config
        ), f"Config for '{capability_name}' missing 'routing_strategy' key"
