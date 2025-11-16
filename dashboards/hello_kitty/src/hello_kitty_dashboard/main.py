#!/usr/bin/env python3
"""
Hello Kitty BubbleTea TUI - Main Entry Point
============================================

A kawaii terminal user interface for managing your Hello Kitty-themed bubble tea shop!
Inspired by gathewhy's AI Backend Unified Infrastructure but adapted for bubble tea shop management.

Features:
- Real-time order tracking with Hello Kitty charm
- Menu management with kawaii aesthetics  
- Inventory monitoring with cute notifications
- Sales analytics with pastel dashboards
- Customer management with friendly interfaces
"""

import asyncio
import sys
import argparse
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label, Button
from textual.binding import Binding

from hello_kitty_dashboard.ui.dashboard import DashboardScreen
from hello_kitty_dashboard.ui.menu import MenuScreen
from hello_kitty_dashboard.ui.orders import OrdersScreen
from hello_kitty_dashboard.ui.inventory import InventoryScreen
from hello_kitty_dashboard.ui.customers import CustomersScreen
from hello_kitty_dashboard.core.theme import HelloKittyTheme
from hello_kitty_dashboard.core.shop_manager import ShopManager
from hello_kitty_dashboard.config.settings import Settings


class HelloKittyBubbleTeaTUI(App):
    """Main TUI application for Hello Kitty BubbleTea shop management."""
    
    CSS = """
    /* Import Hello Kitty theme styles */
    @import "theme.css";
    """
    
    BINDINGS = [
        Binding("d", "show_dashboard", "Dashboard"),
        Binding("m", "show_menu", "Menu"),
        Binding("o", "show_orders", "Orders"),
        Binding("i", "show_inventory", "Inventory"),
        Binding("c", "show_customers", "Customers"),
        Binding("q", "quit", "Quit"),
    ]
    
    def __init__(self, settings: Settings = None):
        super().__init__()
        self.settings = settings or Settings()
        self.hk_theme = HelloKittyTheme()
        self.shop_manager = ShopManager(self.settings)
        self.title = "🌸 Hello Kitty BubbleTea TUI 🌸"
        self.sub_title = "Your kawaii bubble tea shop management system!"
    
    async def on_mount(self) -> None:
        """Initialize the application when mounted."""
        await self.shop_manager.initialize()
        await self.switch_screen("dashboard")
    
    async def switch_screen(self, screen_name: str) -> None:
        """Switch between different screens."""
        screens = {
            "dashboard": DashboardScreen,
            "menu": MenuScreen,
            "orders": OrdersScreen,
            "inventory": InventoryScreen,
            "customers": CustomersScreen,
        }
        
        if screen_name in screens:
            screen = screens[screen_name](self.shop_manager, self.hk_theme)
            await self.view.dock(screen, edge="top", size=1)
    
    # Screen switching actions
    def action_show_dashboard(self) -> None:
        """Show the main dashboard."""
        self.switch_screen("dashboard")
    
    def action_show_menu(self) -> None:
        """Show the menu management screen."""
        self.switch_screen("menu")
    
    def action_show_orders(self) -> None:
        """Show the orders management screen."""
        self.switch_screen("orders")
    
    def action_show_inventory(self) -> None:
        """Show the inventory management screen."""
        self.switch_screen("inventory")
    
    def action_show_customers(self) -> None:
        """Show the customers management screen."""
        self.switch_screen("customers")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Hello Kitty BubbleTea TUI")
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--data-dir", "-d",
        type=Path,
        help="Path to data directory"
    )
    parser.add_argument(
        "--theme", "-t",
        choices=["hello_kitty", "bubble_tea"],
        default="hello_kitty",
        help="Theme to use"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--providers-config",
        type=Path,
        help="Path to LiteLLM providers.yaml (defaults to repo config)"
    )
    parser.add_argument(
        "--disable-litellm-adapter",
        action="store_true",
        help="Disable LiteLLM data bridge (use canned sample data)"
    )
    
    args = parser.parse_args()
    
    # Load settings
    settings = Settings.from_args(args)
    if args.debug:
        settings.debug = True
    
    if args.providers_config:
        settings.providers_config = args.providers_config
    if args.disable_litellm_adapter:
        settings.enable_litellm_adapter = False

    try:
        # Run the application
        app = HelloKittyBubbleTeaTUI(settings)
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Sayonara! Thanks for using Hello Kitty BubbleTea TUI!")
        sys.exit(0)
    except Exception as e:
        if args.debug:
            raise
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
