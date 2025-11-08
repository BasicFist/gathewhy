"""Configuration management for AI backend dashboard.

This module handles loading and validation of dashboard configuration from
environment variables and YAML configuration files.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def load_env_config() -> tuple[float, int, int]:
    """Load and validate configuration from environment variables.

    Security: Validates all inputs to prevent injection attacks.

    Environment Variables:
        AI_DASH_HTTP_TIMEOUT: HTTP request timeout in seconds (0.5-30, default: 3.0)
        AI_DASH_REFRESH_INTERVAL: Dashboard refresh interval in seconds (1-60, default: 5)
        AI_DASH_LOG_HEIGHT: Event log display height in lines (5-50, default: 12)

    Returns:
        Tuple of (http_timeout, refresh_interval, log_height)

    Raises:
        ValueError: If any configuration value is invalid
    """
    try:
        http_timeout = float(os.getenv("AI_DASH_HTTP_TIMEOUT", "3.0"))
        if not 0.5 <= http_timeout <= 30:
            raise ValueError(f"HTTP_TIMEOUT must be 0.5-30 seconds, got {http_timeout}")
    except ValueError as e:
        logger.error(f"Invalid AI_DASH_HTTP_TIMEOUT: {e}")
        raise ValueError(f"Invalid AI_DASH_HTTP_TIMEOUT: {e}") from None

    try:
        refresh_interval = int(os.getenv("AI_DASH_REFRESH_INTERVAL", "5"))
        if not 1 <= refresh_interval <= 60:
            raise ValueError(f"REFRESH_INTERVAL must be 1-60 seconds, got {refresh_interval}")
    except ValueError as e:
        logger.error(f"Invalid AI_DASH_REFRESH_INTERVAL: {e}")
        raise ValueError(f"Invalid AI_DASH_REFRESH_INTERVAL: {e}") from None

    try:
        log_height = int(os.getenv("AI_DASH_LOG_HEIGHT", "12"))
        if not 5 <= log_height <= 50:
            raise ValueError(f"LOG_HEIGHT must be 5-50 lines, got {log_height}")
    except ValueError as e:
        logger.error(f"Invalid AI_DASH_LOG_HEIGHT: {e}")
        raise ValueError(f"Invalid AI_DASH_LOG_HEIGHT: {e}") from None

    return http_timeout, refresh_interval, log_height


def load_providers_config(config_path: Path | None = None) -> dict | None:
    """Load provider configuration from YAML file.

    Args:
        config_path: Path to providers.yaml file. If None, uses default location
                    relative to package directory.

    Returns:
        Provider configuration dictionary or None if file not found or invalid
    """
    if config_path is None:
        # Default: config/providers.yaml relative to project root
        package_dir = Path(__file__).parent
        config_path = package_dir.parent.parent / "config" / "providers.yaml"

    if not config_path.exists():
        logger.debug(f"Provider config not found at {config_path}")
        return None

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded provider config from {config_path}")
            return config
    except Exception as e:
        logger.warning(f"Failed to load provider config: {type(e).__name__}: {e}")
        return None
