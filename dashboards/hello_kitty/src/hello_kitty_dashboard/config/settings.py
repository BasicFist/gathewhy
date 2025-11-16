"""
Hello Kitty BubbleTea TUI - Settings and Configuration
=====================================================

Configuration management system with sensible defaults and Hello Kitty theming.
"""

import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from argparse import Namespace


@dataclass
class Settings:
    """Application settings with Hello Kitty defaults."""
    
    # Theme settings
    theme: str = "hello_kitty"
    enable_kawaii_mode: bool = True
    color_profile: str = "auto"  # auto, truecolor, ansi256, ansi16, monochrome
    
    # UI settings
    show_sparkles: bool = True
    show_hearts: bool = True
    refresh_interval: float = 5.0
    enable_animations: bool = True
    
    # Data storage
    data_dir: Optional[Path] = None
    auto_save: bool = True
    save_interval: float = 30.0
    
    # Shop settings  
    shop_name: str = "Hello Kitty BubbleTea"
    default_currency: str = "USD"
    tax_rate: float = 0.0875  # 8.75% default tax
    loyalty_points_rate: float = 0.1  # 10% of order value
    
    # Business hours
    business_hours_start: str = "10:00"
    business_hours_end: str = "22:00"
    timezone: str = "America/New_York"
    
    # Notification settings
    enable_sound_notifications: bool = False
    show_order_notifications: bool = True
    show_inventory_alerts: bool = True
    notify_low_stock_threshold: int = 50
    
    # Debug and development
    debug: bool = False
    log_level: str = "INFO"
    enable_debug_logging: bool = False
    
    # API settings (if integrating with external systems)
    api_enabled: bool = False
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    
    # Database settings
    database_url: Optional[str] = None
    use_sqlite: bool = True

    # LiteLLM bridge
    enable_litellm_adapter: bool = True
    providers_config: Optional[Path] = None
    
    @classmethod
    def from_args(cls, args: Namespace) -> 'Settings':
        """Create settings from command line arguments."""
        settings = cls()
        
        # Apply command line overrides
        if hasattr(args, 'config') and args.config:
            settings.load_from_file(args.config)
        
        if hasattr(args, 'data_dir') and args.data_dir:
            settings.data_dir = args.data_dir
        
        if hasattr(args, 'theme') and args.theme:
            settings.theme = args.theme
        
        if hasattr(args, 'debug') and args.debug:
            settings.debug = True
            settings.log_level = "DEBUG"
            settings.enable_debug_logging = True
        
        return settings
    
    @classmethod
    def default_config_file(cls) -> Path:
        """Get the default configuration file path."""
        return Path.home() / ".hello_kitty_dashboard" / "config.yaml"
    
    def save_to_file(self, config_file: Optional[Path] = None) -> None:
        """Save settings to configuration file."""
        if config_file is None:
            config_file = self.default_config_file()
        
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False, indent=2)
    
    def load_from_file(self, config_file: Path) -> None:
        """Load settings from configuration file."""
        if not config_file.exists():
            # Create default config if it doesn't exist
            self.save_to_file(config_file)
            return
        
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Update settings from file
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not load config file {config_file}: {e}")
            print("   Using default settings instead.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return asdict(self)
    
    def get_hello_kitty_defaults(self) -> Dict[str, Any]:
        """Get Hello Kitty themed default settings."""
        return {
            "shop_name": "🌸 Hello Kitty BubbleTea 🌸",
            "theme": "hello_kitty",
            "show_sparkles": True,
            "show_hearts": True,
            "enable_kawaii_mode": True,
            "color_profile": "auto",
            "default_currency": "💝",  # Using heart as currency symbol
            "tax_rate": 0.088,  # Cute tax rate
            "refresh_interval": 3.0  # Quick refresh for kawaii responsiveness
        }
    
    def apply_hello_kitty_theme(self) -> None:
        """Apply Hello Kitty themed settings."""
        hk_defaults = self.get_hello_kitty_defaults()
        for key, value in hk_defaults.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def validate(self) -> Dict[str, Any]:
        """Validate settings and return validation results."""
        errors = []
        warnings = []
        
        # Validate required settings
        if not self.shop_name.strip():
            errors.append("Shop name cannot be empty")
        
        if not 0 <= self.tax_rate <= 1:
            errors.append("Tax rate must be between 0 and 1")
        
        if not 0 <= self.loyalty_points_rate <= 1:
            errors.append("Loyalty points rate must be between 0 and 1")
        
        if self.refresh_interval < 0.5:
            warnings.append("Refresh interval is very fast, may impact performance")
        
        if self.refresh_interval > 60:
            warnings.append("Refresh interval is very slow, may impact responsiveness")
        
        # Validate directory paths
        if self.data_dir:
            try:
                self.data_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                errors.append(f"Cannot create data directory: {self.data_dir}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def __str__(self) -> str:
        """String representation of settings."""
        return f"HelloKittyBubbleTea Settings (Theme: {self.theme})"


def create_default_config() -> Settings:
    """Create settings with Hello Kitty defaults."""
    settings = Settings()
    settings.apply_hello_kitty_theme()
    return settings


def load_or_create_config(config_file: Optional[Path] = None) -> Settings:
    """Load existing config or create default one."""
    if config_file is None:
        config_file = Settings.default_config_file()
    
    settings = create_default_config()
    
    if config_file.exists():
        settings.load_from_file(config_file)
    else:
        # Save default config for future use
        settings.save_to_file(config_file)
        print(f"📝 Created default configuration at: {config_file}")
    
    return settings
