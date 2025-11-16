"""Hello Kitty BubbleTea Shop TUI - Main layout widget."""

from __future__ import annotations

from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from .menu_display import MenuDisplay
from .order_queue import OrderQueue
from .pos_panel import POSPanel
from .inventory_status import InventoryStatus
from .sales_dashboard import SalesDashboard
from .models import Order, MenuItem, InventoryItem, SalesMetrics


class BubbleTeaShopView(Vertical):
    """High-level container that assembles all BubbleTea shop widgets with Hello Kitty styling."""

    def compose(self):
        # Welcome header with Hello Kitty styling
        yield Static(
            "[pink1]🌸 Hello Kitty BubbleTea Shop ✨[/]\n"
            "[yellow]◦•●◉ Welcome to Kawaii's Sweetest Tea Experience! ◉●•◦[/]",
            id="welcome-header",
            classes="kawaii-header"
        )
        
        # Main content area with 3-column layout
        with Horizontal(id="main-content"):
            # Left column - Menu and POS
            with Vertical(id="left-column"):
                yield MenuDisplay(id="menu-display")
                yield POSPanel(id="pos-panel")
            
            # Center column - Order queue and inventory
            with Vertical(id="center-column"):
                yield OrderQueue(id="order-queue")
                yield InventoryStatus(id="inventory-status")
            
            # Right column - Sales dashboard
            with Vertical(id="right-column"):
                yield SalesDashboard(id="sales-dashboard")

    def on_mount(self) -> None:
        """Initialize references to all child widgets."""
        self.menu_display = self.query_one(MenuDisplay)
        self.pos_panel = self.query_one(POSPanel)
        self.order_queue = self.query_one(OrderQueue)
        self.inventory_status = self.query_one(InventoryStatus)
        self.sales_dashboard = self.query_one(SalesDashboard)

    # ----- update helpers ------------------------------------------------
    def update_menu(self, menu_items: list[MenuItem]) -> None:
        """Update the menu display with new items."""
        self.menu_display.update_menu(menu_items)

    def update_orders(self, orders: list[Order]) -> None:
        """Update the order queue with new orders."""
        self.order_queue.update_orders(orders)

    def update_inventory(self, inventory: list[InventoryItem]) -> None:
        """Update the inventory status."""
        self.inventory_status.update_inventory(inventory)

    def update_sales(self, sales_metrics: SalesMetrics) -> None:
        """Update the sales dashboard."""
        self.sales_dashboard.update_metrics(sales_metrics)

    def add_order(self, order: Order) -> None:
        """Add a new order to the queue."""
        self.order_queue.add_order(order)

    def update_pos_selection(self, selected_items: list[MenuItem]) -> None:
        """Update POS panel with current selection."""
        self.pos_panel.update_selection(selected_items)
