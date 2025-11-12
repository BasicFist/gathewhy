#!/usr/bin/env bash
# Install WTH LiteLLM dashboard assets into the current user’s home directory.
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
WIDGET_SRC="$REPO_ROOT/wth-widgets"
WIDGET_DEST=${WTH_WIDGET_DEST:-$HOME/.local/share/wth-widgets}
CONFIG_DEST=${WTH_CONFIG_DEST:-$HOME/.config/wth}
ALIAS_NAME=${WTH_ALIAS_NAME:-wth-lite}

detect_alias_file() {
    if [[ -n "${WTH_ALIAS_FILE:-}" ]]; then
        printf '%s' "$WTH_ALIAS_FILE"
    else
        case "${SHELL:-}" in
            *zsh)
                printf '%s' "$HOME/.zshrc"
                ;;
            *)
                printf '%s' "$HOME/.bashrc"
                ;;
        esac
    fi
}

mkdir -p "$WIDGET_DEST" "$CONFIG_DEST"
rsync -a --delete "$WIDGET_SRC/" "$WIDGET_DEST/"

if [[ ! -f "$CONFIG_DEST/wth.yaml" ]]; then
    cp "$WIDGET_DEST/litellm/config/wth-lite-dashboard.yaml" "$CONFIG_DEST/wth.yaml"
    echo "Created $CONFIG_DEST/wth.yaml"
else
    echo "Config file already exists at $CONFIG_DEST/wth.yaml — merge in litellm config manually."
fi

ALIAS_FILE=$(detect_alias_file)
mkdir -p "$(dirname "$ALIAS_FILE")"
touch "$ALIAS_FILE"
ALIAS_CMD="alias $ALIAS_NAME='WTH_WIDGET_DIR=$WIDGET_DEST wth run --config $CONFIG_DEST/wth.yaml'"
if ! grep -F "$ALIAS_CMD" "$ALIAS_FILE" >/dev/null 2>&1; then
    {
        echo ""
        echo "# WTH LiteLLM dashboard"
        echo "$ALIAS_CMD"
    } >> "$ALIAS_FILE"
    echo "Added alias '$ALIAS_NAME' to $ALIAS_FILE (reload your shell to use it)."
else
    echo "Alias '$ALIAS_NAME' already present in $ALIAS_FILE."
fi

echo "Widgets installed to $WIDGET_DEST"
echo "Launch with: WTH_WIDGET_DIR=$WIDGET_DEST wth run --config $CONFIG_DEST/wth.yaml"
