"""
Common utilities for AI Backend Python scripts
Import with: from common_utils import *
"""

import sys
from pathlib import Path
from typing import Any

import yaml

# ANSI color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def log_info(message: str) -> None:
    """Log info message"""
    print(f"{GREEN}[INFO]{NC} {message}")


def log_success(message: str) -> None:
    """Log success message"""
    print(f"{GREEN}[✓]{NC} {message}")


def log_warn(message: str) -> None:
    """Log warning message"""
    print(f"{YELLOW}[WARN]{NC} {message}")


def log_error(message: str) -> None:
    """Log error message"""
    print(f"{RED}[ERROR]{NC} {message}", file=sys.stderr)


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent


def get_config_dir() -> Path:
    """Get config directory path"""
    return get_project_root() / "config"


def load_yaml_config(filename: str) -> dict[str, Any]:
    """
    Load YAML configuration file

    Args:
        filename: Config filename (e.g., 'providers.yaml')

    Returns:
        Parsed YAML as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    config_path = get_config_dir() / filename

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f)


def validate_yaml_file(filepath: Path) -> bool:
    """
    Validate YAML file syntax

    Args:
        filepath: Path to YAML file

    Returns:
        True if valid, False otherwise
    """
    try:
        with open(filepath) as f:
            yaml.safe_load(f)
        return True
    except (yaml.YAMLError, FileNotFoundError):
        return False


# Config file constants
PROVIDERS_CONFIG = "providers.yaml"
MAPPINGS_CONFIG = "model-mappings.yaml"
LITELLM_CONFIG = "litellm-unified.yaml"
PORTS_CONFIG = "ports.yaml"
