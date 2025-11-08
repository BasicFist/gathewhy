"""
Configuration Schema Version Management
========================================

Tracks schema versions for configuration files to detect breaking changes
and enable migrations between versions.

Version Format: MAJOR.MINOR.PATCH (SemVer)
- MAJOR: Breaking changes that require migration
- MINOR: Backward-compatible additions
- PATCH: Bug fixes and clarifications

Usage:
    from config.schemas.version import SCHEMA_VERSION, validate_version

    current_version = get_config_version(config)
    validate_version(current_version, SCHEMA_VERSION)
"""

# Current schema version
SCHEMA_VERSION = "2.0.0"

# Version history with breaking changes
VERSION_HISTORY = {
    "2.0.0": {
        "date": "2025-11-08",
        "changes": [
            "Added vLLM single instance mutual exclusion constraint",
            "Removed unimplemented features (request_metadata_routing, model_size_routing)",
            "Added atomic configuration generation with validation",
            "Marked special routing cases as PLANNED",
        ],
        "breaking": True,
        "migration_required": False,  # Backward compatible with warnings
    },
    "1.0.0": {
        "date": "2025-10-20",
        "changes": [
            "Initial schema definition",
            "providers.yaml structure",
            "model-mappings.yaml routing rules",
            "litellm-unified.yaml generation",
        ],
        "breaking": False,
    },
}

# Required fields for each configuration file
REQUIRED_FIELDS = {
    "providers.yaml": {
        "providers": dict,
        "metadata": dict,
    },
    "model-mappings.yaml": {
        "exact_matches": dict,
        "patterns": list,
        "capabilities": dict,
        "fallback_chains": dict,
    },
    "litellm-unified.yaml": {
        "model_list": list,
        "litellm_settings": dict,
        "router_settings": dict,
    },
}

# Deprecated fields (will be removed in future versions)
DEPRECATED_FIELDS = {
    "2.1.0": {
        "model-mappings.yaml": [
            "routing_rules.request_metadata_routing",
            "routing_rules.model_size_routing",
            "special_cases.first_request_routing",
            "special_cases.error_based_routing",
            "special_cases.geographic_routing",
        ]
    }
}


def get_version_tuple(version_str: str) -> tuple[int, int, int]:
    """Parse version string to tuple"""
    try:
        major, minor, patch = version_str.split('.')
        return (int(major), int(minor), int(patch))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def is_compatible(current: str, required: str) -> bool:
    """Check if current version is compatible with required version"""
    current_tuple = get_version_tuple(current)
    required_tuple = get_version_tuple(required)

    # Major version must match for compatibility
    if current_tuple[0] != required_tuple[0]:
        return False

    # Minor version of current must be >= required
    if current_tuple[1] < required_tuple[1]:
        return False

    return True


def validate_version(config_version: str, expected_version: str = SCHEMA_VERSION) -> tuple[bool, str]:
    """
    Validate configuration version against expected version

    Returns:
        (is_valid, message)
    """
    if not config_version:
        return False, "Configuration missing version field"

    if config_version == expected_version:
        return True, f"Version {config_version} matches expected {expected_version}"

    if is_compatible(config_version, expected_version):
        return True, f"Version {config_version} compatible with {expected_version}"

    current_tuple = get_version_tuple(config_version)
    expected_tuple = get_version_tuple(expected_version)

    if current_tuple[0] < expected_tuple[0]:
        return False, (
            f"Major version mismatch: config is v{config_version} but schema requires v{expected_version}. "
            f"Breaking changes detected. Migration required."
        )

    if current_tuple[0] > expected_tuple[0]:
        return False, (
            f"Configuration version ({config_version}) is newer than schema version ({expected_version}). "
            f"Update application to support newer schema."
        )

    return False, f"Version {config_version} incompatible with {expected_version}"


def get_breaking_changes(from_version: str, to_version: str) -> list[str]:
    """Get list of breaking changes between two versions"""
    from_tuple = get_version_tuple(from_version)
    to_tuple = get_version_tuple(to_version)

    breaking_changes = []

    for version, info in VERSION_HISTORY.items():
        version_tuple = get_version_tuple(version)

        if from_tuple < version_tuple <= to_tuple:
            if info.get("breaking", False):
                breaking_changes.extend([
                    f"v{version} ({info['date']}): {change}"
                    for change in info['changes']
                ])

    return breaking_changes


if __name__ == "__main__":
    print(f"Current Schema Version: {SCHEMA_VERSION}")
    print(f"\nVersion History:")
    for version, info in sorted(VERSION_HISTORY.items(), reverse=True):
        breaking = " [BREAKING]" if info.get("breaking") else ""
        print(f"  {version} ({info['date']}){breaking}")
        for change in info['changes']:
            print(f"    - {change}")
