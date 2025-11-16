#!/usr/bin/env python3
"""Hello Kitty BubbleTea Shop TUI - Sample Application.

Demonstrates how to use the Hello Kitty themed widgets for a bubble tea shop.
This is a sample application showing all the kawaii widgets in action.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import list
import random

from textual.app import App, ComposeResult
from textual.binding import Binding

# Import our Hello Kitty widgets
from widgets import (
    BubbleTeaShopView, MenuItem, Order, InventoryItem, SalesMetrics,
    Topping, OrderItem, Customer
)


class HelloKittyBubbleTeaApp(App[None]):
    """Hello Kitty BubbleTea Shop TUI Application.
    
    A cute and functional bubble tea shop management interface
    with kawaii design elements inspired by Hello Kitty.
    """

    CSS = """
    /* Hello Kitty themed styling */
    .kawaii-header {
        text-align: center;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #left-column, #center-column, #right-column {
        width: 1fr;
        height: auto;
        margin: 1;
        border: solid $primary;
        padding: 1;
    }
    
    #menu-display {
        height: 15;
        border: solid $accent;
        padding: 1;
        background: $panel;
    }
    
    #pos-panel {
        height: 20;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }
    
    #order-queue {
        height: 25;
        border: solid $secondary;
        padding: 1;
        background: $panel;
    }
    
    #inventory-status {
        height: 15;
        border: solid $accent;
        padding: 1;
        background: $surface;
    }
    
    #sales-dashboard {
        height: 40;
        border: solid $primary;
        padding: 1;
        background: $panel;
    }
    
    .kawaii-card {
        border: solid $primary;
        padding: 1;
        margin: 1;
        background: $surface;
    }
    
    .kawaii-button {
        border: solid $accent;
        padding: 0 1;
        margin: 0;
        background: $primary;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("q", "quit", "Quit", priority=True),
        Binding("m", "toggle_menu", "Toggle Menu", priority=True),
        Binding("o", "toggle_orders", "Toggle Orders", priority=True),
        Binding("i", "toggle_inventory", "Toggle Inventory", priority=True),
        Binding("s", "toggle_sales", "Toggle Sales", priority=True),
        Binding("p", "add_sample_order", "Add Order", priority=True),
        Binding("?", "toggle_help", "Help", priority=True),
    ]

    def __init__(self):
        """Initialize the Hello Kitty BubbleTea app."""
        super().__init__()
        self.title = "🌸 Hello Kitty BubbleTea Shop ✨"
        self.sub_title = "Kawaii Customer Service • Sweet Tea Experience"

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield BubbleTeaShopView()

    def on_mount(self) -> None:
        """Initialize the app with sample data."""
        # Get the main view
        self.shop_view = self.query_one(BubbleTeaShopView)
        
        # Load sample data
        self._load_sample_menu()
        self._load_sample_inventory()
        self._load_sample_sales_data()
        
        # Start with some sample orders
        self._create_sample_orders()
        
        # Set up periodic updates
        self.set_interval(5.0, self._refresh_all_data, pause=False)

    def action_refresh(self) -> None:
        """Refresh all data."""
        self._refresh_all_data()

    def action_toggle_menu(self) -> None:
        """Toggle menu display focus."""
        pass  # Placeholder for menu interaction

    def action_toggle_orders(self) -> None:
        """Toggle order queue focus."""
        pass  # Placeholder for order interaction

    def action_toggle_inventory(self) -> None:
        """Toggle inventory focus."""
        pass  # Placeholder for inventory interaction

    def action_toggle_sales(self) -> None:
        """Toggle sales dashboard focus."""
        pass  # Placeholder for sales interaction

    def action_add_sample_order(self) -> None:
        """Add a sample order to demonstrate functionality."""
        self._create_random_order()
        self._refresh_order_data()

    def action_toggle_help(self) -> None:
        """Show help overlay."""
        help_text = """
[bold hot_pink]🌸 Hello Kitty BubbleTea Shop Help ✨[/]

[bold]Key Bindings:[/]
• [yellow]r[/] - Refresh all data
• [yellow]m[/] - Toggle menu focus
• [yellow]o[/] - Toggle order queue focus
• [yellow]i[/] - Toggle inventory focus
• [yellow]s[/] - Toggle sales dashboard focus
• [yellow]p[/] - Add sample order
• [yellow]?[/] - Show this help
• [yellow]q[/] - Quit application

[bold]Features:[/]
• Kawaii menu display with drink cards
• Real-time order queue management
• Inventory tracking with alerts
• Sales dashboard with insights
• Hello Kitty themed design

[bold]Tips:[/]
• Watch the order queue fill up automatically
• Check inventory for low stock alerts
• Monitor sales performance
• Enjoy the kawaii experience!
        """
        
        # Show help in a simple way (could be improved with a modal)
        self.bell()  # Attention sound
        print(help_text)

    # ===== Sample Data Methods =====

    def _load_sample_menu(self) -> None:
        """Load sample menu items."""
        menu_items = [
            MenuItem(
                id="tarot_milk_tea",
                name="Taro Milk Tea",
                category="milk-tea",
                price=5.99,
                description="Creamy purple taro with chewy pearls",
                toppings=["tapioca", "popping boba", "cheese foam"],
                prep_time=5,
                is_popular=True
            ),
            MenuItem(
                id="matcha_latte",
                name="Matcha Green Tea Latte",
                category="milk-tea",
                price=6.49,
                description="Premium Japanese matcha with milk",
                toppings=["tapioca", "red bean"],
                prep_time=6,
                is_new=True
            ),
            MenuItem(
                id="strawberry_tea",
                name="Strawberry Fruit Tea",
                category="fruit-tea",
                price=4.99,
                description="Fresh strawberries with green tea",
                toppings=["popping boba", "aloe vera"],
                prep_time=4,
                is_popular=True
            ),
            MenuItem(
                id="brown_sugar_boba",
                name="Brown Sugar Boba Milk",
                category="specialty",
                price=7.99,
                description="Caramel brown sugar with golden pearls",
                toppings=["golden pearls"],
                prep_time=7
            ),
            MenuItem(
                id="mango_smoothie",
                name="Mango Smoothie",
                category="smoothies",
                price=6.99,
                description="Fresh mango blended to perfection",
                toppings=["coconut jelly", "popping boba"],
                prep_time=5
            ),
            MenuItem(
                id="oolong_tea",
                name="Fresh Oolong Tea",
                category="fresh-tea",
                price=3.99,
                description="Traditional Chinese oolong tea",
                toppings=["tapioca", "grass jelly"],
                prep_time=3
            )
        ]
        
        self.shop_view.update_menu(menu_items)

    def _load_sample_inventory(self) -> None:
        """Load sample inventory data."""
        inventory_items = [
            InventoryItem(
                id="taro_powder",
                name="Taro Powder",
                category="tea-base",
                current_stock=15,
                max_capacity=50,
                unit="kg",
                reorder_level=10,
                cost_per_unit=25.00,
                last_restocked=datetime.now() - timedelta(days=2),
                expiry_date=datetime.now() + timedelta(days=180)
            ),
            InventoryItem(
                id="matcha_powder",
                name="Premium Matcha",
                category="tea-base",
                current_stock=5,
                max_capacity=20,
                unit="kg",
                reorder_level=8,
                cost_per_unit=45.00,
                last_restocked=datetime.now() - timedelta(days=1),
                expiry_date=datetime.now() + timedelta(days=365)
            ),
            InventoryItem(
                id="tapioca_pearls",
                name="Tapioca Pearls",
                category="topping",
                current_stock=25,
                max_capacity=100,
                unit="kg",
                reorder_level=20,
                cost_per_unit=8.00,
                last_restocked=datetime.now() - timedelta(days=3)
            ),
            InventoryItem(
                id="fresh_milk",
                name="Fresh Milk",
                category="milk",
                current_stock=2,
                max_capacity=20,
                unit="L",
                reorder_level=5,
                cost_per_unit=3.50,
                last_restocked=datetime.now() - timedelta(days=1),
                expiry_date=datetime.now() + timedelta(days=3)
            ),
            InventoryItem(
                id="strawberries",
                name="Fresh Strawberries",
                category="fruit",
                current_stock=8,
                max_capacity=30,
                unit="kg",
                reorder_level=10,
                cost_per_unit=12.00,
                last_restocked=datetime.now() - timedelta(hours=6),
                expiry_date=datetime.now() + timedelta(days=2)
            ),
            InventoryItem(
                id="brown_sugar",
                name="Brown Sugar Syrup",
                category="syrup",
                current_stock=0,
                max_capacity=10,
                unit="L",
                reorder_level=2,
                cost_per_unit=15.00,
                last_restocked=datetime.now() - timedelta(days=5),
                expiry_date=datetime.now() + timedelta(days=90)
            )
        ]
        
        self.shop_view.update_inventory(inventory_items)

    def _load_sample_sales_data(self) -> None:
        """Load sample sales metrics."""
        # Create some popular items for the sales data
        popular_items = [
            (MenuItem("tarot_milk_tea", "Taro Milk Tea", "milk-tea", 5.99, "", [], 5), 12),
            (MenuItem("matcha_latte", "Matcha Latte", "milk-tea", 6.49, "", [], 6), 8),
            (MenuItem("strawberry_tea", "Strawberry Tea", "fruit-tea", 4.99, "", [], 4), 15)
        ]
        
        sales_metrics = SalesMetrics(
            date=datetime.now(),
            total_orders=35,
            total_revenue=245.50,
            average_order_value=7.01,
            popular_items=popular_items,
            peak_hours=[10, 11, 14, 15, 16, 18, 19],
            customer_count=32,
            refund_count=1
        )
        
        self.shop_view.update_sales(sales_metrics)

    def _create_sample_orders(self) -> None:
        """Create some sample orders to populate the queue."""
        sample_orders = [
            self._create_order("Alice", ["tarot_milk_tea"], "pending"),
            self._create_order("Bob", ["strawberry_tea"], "preparing"),
            self._create_order("Carol", ["matcha_latte", "brown_sugar_boba"], "ready"),
            self._create_order("David", ["mango_smoothie"], "pending"),
            self._create_order("Eve", ["oolong_tea"], "preparing")
        ]
        
        for order in sample_orders:
            self.shop_view.add_order(order)

    def _create_order(self, customer_name: str, items: list[str], status: str) -> Order:
        """Create a sample order.
        
        Args:
            customer_name: Name of the customer
            items: List of item IDs to include
            status: Initial status for the order
            
        Returns:
            Order object
        """
        # Get sample menu items (in real app, would query menu)
        menu_map = {
            "tarot_milk_tea": MenuItem("tarot_milk_tea", "Taro Milk Tea", "milk-tea", 5.99, "", [], 5),
            "strawberry_tea": MenuItem("strawberry_tea", "Strawberry Tea", "fruit-tea", 4.99, "", [], 4),
            "matcha_latte": MenuItem("matcha_latte", "Matcha Latte", "milk-tea", 6.49, "", [], 6),
            "brown_sugar_boba": MenuItem("brown_sugar_boba", "Brown Sugar Boba", "specialty", 7.99, "", [], 7),
            "mango_smoothie": MenuItem("mango_smoothie", "Mango Smoothie", "smoothies", 6.99, "", [], 5),
            "oolong_tea": MenuItem("oolong_tea", "Oolong Tea", "fresh-tea", 3.99, "", [], 3)
        }
        
        order_items = []
        for item_id in items:
            if item_id in menu_map:
                menu_item = menu_map[item_id]
                order_item = OrderItem(
                    menu_item=menu_item,
                    quantity=1,
                    toppings=[],
                    customizations={}
                )
                order_items.append(order_item)
        
        return Order(
            id=f"ORD_{len(items)}_{customer_name}_{datetime.now().strftime('%H%M%S')}",
            customer_name=customer_name,
            items=order_items,
            status=status,
            created_at=datetime.now() - timedelta(minutes=random.randint(1, 30))
        )

    def _create_random_order(self) -> None:
        """Create a random order for demonstration."""
        customers = ["Sarah", "Mike", "Emma", "Jack", "Lisa", "Tom", "Anna", "Sam"]
        items = ["tarot_milk_tea", "strawberry_tea", "matcha_latte", "mango_smoothie", "oolong_tea"]
        
        customer = random.choice(customers)
        item_count = random.randint(1, 2)
        selected_items = random.sample(items, item_count)
        
        order = self._create_order(customer, selected_items, "pending")
        self.shop_view.add_order(order)

    # ===== Data Refresh Methods =====

    def _refresh_all_data(self) -> None:
        """Refresh all data displays."""
        self._refresh_order_data()
        self._refresh_inventory_alerts()
        self._update_sales_trends()

    def _refresh_order_data(self) -> None:
        """Refresh order queue with current data."""
        # In a real app, this would query actual order data
        pass

    def _refresh_inventory_alerts(self) -> None:
        """Check and update inventory alerts."""
        # In a real app, this would check stock levels
        pass

    def _update_sales_trends(self) -> None:
        """Update sales metrics and trends."""
        # In a real app, this would calculate real sales data
        pass


def main():
    """Run the Hello Kitty BubbleTea app."""
    app = HelloKittyBubbleTeaApp()
    app.run()


if __name__ == "__main__":
    main()
