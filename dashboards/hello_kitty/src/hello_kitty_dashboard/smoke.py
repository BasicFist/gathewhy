from pathlib import Path
import sys

from hello_kitty_dashboard.core.shop_manager import ShopManager
from hello_kitty_dashboard.config.settings import Settings


def main():
    settings = Settings()
    # Prefer repo providers.yaml
    repo_root = Path(__file__).resolve().parents[4]
    settings.providers_config = repo_root / "config" / "providers.yaml"
    settings.enable_litellm_adapter = True
    sm = ShopManager(settings)
    sm._load_litellm_data()
    print(f"Loaded providers: {len(sm.drinks)} drinks, {len(sm.inventory)} inventory entries, {len(sm.orders)} orders")
    # basic sanity: no crash and objects populated or empty gracefully
    sys.exit(0)


if __name__ == "__main__":
    main()
