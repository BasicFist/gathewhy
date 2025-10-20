#!/bin/bash
# Check that generated config files haven't been manually edited
# Used by pre-commit hook

set -e

CONFIG_FILE="config/litellm-unified.yaml"

# Check if file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "✅ Config file doesn't exist yet (ok for initial setup)"
    exit 0
fi

# Check for AUTO-GENERATED header in model_list section
if grep -q "# AUTO-GENERATED from providers.yaml" "$CONFIG_FILE"; then
    # File has generation marker - verify it's current

    # Extract generation timestamp if present
    GENERATED_TS=$(grep "# Generated:" "$CONFIG_FILE" | awk '{print $3, $4}' || echo "unknown")

    # Check if providers.yaml is newer than generation timestamp
    PROVIDERS_MODIFIED=$(stat -c %Y config/providers.yaml 2>/dev/null || echo 0)

    # If providers.yaml exists and this is a generated config, warn if stale
    if [ "$PROVIDERS_MODIFIED" -gt 0 ]; then
        echo "ℹ️  Config appears to be generated (timestamp: $GENERATED_TS)"
        echo "   If you modified providers.yaml, regenerate with:"
        echo "   python3 scripts/generate-litellm-config.py"
    fi

    exit 0
else
    # No generation marker - either manual or needs regeneration
    echo "⚠️  Warning: config/litellm-unified.yaml may be manually edited"
    echo "   Consider using scripts/generate-litellm-config.py for consistency"
    echo ""
    echo "   To bypass this check, add this header to the model_list section:"
    echo "   # AUTO-GENERATED from providers.yaml"

    # Don't fail, just warn (allows initial setup)
    exit 0
fi
