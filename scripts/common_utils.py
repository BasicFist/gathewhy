"""
Common utilities for AI Backend Python scripts.

This module provides shared functionality across all backend scripts including:
- Structured logging with Loguru for production-grade output
- Path utilities for accessing project directories and configs
- YAML configuration loading with comprehensive error handling
- Validation utilities for configuration files

Import with: from common_utils import *

Examples:
    >>> config = load_yaml_config('providers.yaml')
    >>> logger.info("Configuration loaded", file_path=str(PROVIDERS_FILE))
    >>> log_success("Validation completed")
"""

import sys
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

# Configure structured logging
# Remove default handler and add custom one with better formatting
logger.remove()
logger.add(
    sys.stderr,
    format="<level>[{level: <8}]</level> {message}",
    level="INFO",
    colorize=True,
)
logger.add(
    sys.stdout,
    format="<level>{level: <8}</level> | {message}",
    level="DEBUG",
    colorize=True,
    filter=lambda record: record["level"].name in ("SUCCESS", "INFO", "DEBUG"),
)

# ANSI color codes (legacy support for backward compatibility)
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def log_info(message: str, **kwargs: Any) -> None:
    """
    Log info level message with structured logging support.

    Args:
        message: The message to log
        **kwargs: Additional structured fields for logging context

    Example:
        >>> log_info("Configuration loaded", file_path="config.yaml", count=5)
    """
    logger.info(message, **kwargs)


def log_success(message: str, **kwargs: Any) -> None:
    """
    Log success level message with structured logging support.

    Args:
        message: The message to log
        **kwargs: Additional structured fields for logging context

    Example:
        >>> log_success("Validation completed", duration_ms=1234)
    """
    logger.opt(colors=True).success(message, **kwargs)


def log_warn(message: str, **kwargs: Any) -> None:
    """
    Log warning level message with structured logging support.

    Args:
        message: The message to log
        **kwargs: Additional structured fields for logging context

    Example:
        >>> log_warn("Provider unreachable", provider="vllm", retry_count=3)
    """
    logger.warning(message, **kwargs)


def log_error(message: str, **kwargs: Any) -> None:
    """
    Log error level message with structured logging support.

    Args:
        message: The message to log
        **kwargs: Additional structured fields for logging context

    Example:
        >>> log_error("Configuration validation failed", error_code="SCHEMA_ERR")
    """
    logger.error(message, **kwargs)


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path: Absolute path to project root (parent of scripts directory)

    Example:
        >>> root = get_project_root()
        >>> config_dir = root / "config"
    """
    return Path(__file__).parent.parent


def get_config_dir() -> Path:
    """
    Get the configuration directory path.

    Returns:
        Path: Absolute path to config/ directory

    Example:
        >>> config_dir = get_config_dir()
        >>> providers_file = config_dir / "providers.yaml"
    """
    return get_project_root() / "config"


def load_yaml_config(filename: str) -> dict[str, Any]:
    """
    Load and parse a YAML configuration file with error handling.

    Uses yaml.safe_load() to securely parse YAML without executing arbitrary code.
    Provides detailed error messages for troubleshooting.

    Args:
        filename (str): Configuration filename (e.g., 'providers.yaml').
            Path is relative to the config/ directory.

    Returns:
        dict[str, Any]: Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If the configuration file doesn't exist.
        yaml.YAMLError: If YAML syntax is invalid.
        Exception: For other unexpected errors with context.

    Example:
        >>> config = load_yaml_config('providers.yaml')
        >>> providers = config.get('providers', {})

    See Also:
        validate_yaml_file: For validating YAML without loading content
    """
    config_path = get_config_dir() / filename

    if not config_path.exists():
        log_error(
            f"Configuration file not found: {config_path}",
            filename=filename,
            path=str(config_path),
        )
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path) as f:
            content = yaml.safe_load(f)
            logger.debug(
                f"Loaded configuration from {filename}",
                file_path=str(config_path),
                keys=list(content.keys()) if isinstance(content, dict) else None,
            )
            return content
    except yaml.YAMLError as e:
        log_error(
            f"YAML parsing error in {filename}: {e}",
            filename=filename,
            error=str(e),
            line_number=getattr(e, "problem_mark", {}).line if hasattr(e, "problem_mark") else None,
        )
        raise
    except Exception as e:
        log_error(
            f"Unexpected error loading {filename}: {e}",
            filename=filename,
            error_type=type(e).__name__,
        )
        raise


def validate_yaml_file(filepath: Path) -> bool:
    """
    Validate YAML file syntax without loading full content.

    Performs safe validation using yaml.safe_load() to detect syntax errors,
    structure issues, and malformed YAML.

    Args:
        filepath (Path): Path to the YAML file to validate.

    Returns:
        bool: True if YAML is valid and readable, False otherwise.

    Example:
        >>> if validate_yaml_file(Path("config/providers.yaml")):
        ...     config = load_yaml_config("providers.yaml")
        ... else:
        ...     log_error("Invalid YAML")

    Note:
        This function does NOT validate schema or content, only YAML syntax.
        Use Pydantic models for semantic validation.
    """
    try:
        with open(filepath) as f:
            yaml.safe_load(f)
        logger.debug(f"YAML syntax valid: {filepath}", file_path=str(filepath))
        return True
    except yaml.YAMLError as e:
        log_warn(
            f"YAML syntax error in {filepath}: {e}",
            file_path=str(filepath),
            error=str(e),
        )
        return False
    except FileNotFoundError:
        log_warn(f"File not found: {filepath}", file_path=str(filepath))
        return False
    except Exception as e:
        log_error(
            f"Unexpected error validating {filepath}: {e}",
            file_path=str(filepath),
            error_type=type(e).__name__,
        )
        return False


# Config file constants
PROVIDERS_CONFIG = "providers.yaml"
MAPPINGS_CONFIG = "model-mappings.yaml"
LITELLM_CONFIG = "litellm-unified.yaml"
PORTS_CONFIG = "ports.yaml"
