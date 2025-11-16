"""
Hello Kitty BubbleTea TUI - Dashboard Screen
===========================================

Main dashboard showing key metrics, current orders, and shop status
with kawaii Hello Kitty theming.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, Label, Button, DataTable
from textual.reactive import reactive
from textual.message import Message
from datetime import datetime, timedelta

from ..core.shop_manager import ShopManager
from ..core.theme import HelloKittyTheme


class MetricCard(Static):
    """A kawaii-themed metric display card."""
    
    def __init__(self, title: str, value: str, icon: str = "", color_token: str = "pastel_sky"):
        super().__init__()
        self.title = title
        self.value = value
        self.icon = icon
        self.color_token = color_token
    
    def compose(self) -> ComposeResult:
        """Compose the metric card."""
        with Container(classes="metric-card"):
            if self.icon:
                yield Label(f"{self.icon} {self.title}", classes="metric-title")
            else:
                yield Label(self.title, classes="metric-title")
            yield Label(self.value, classes="metric-value")


class OrderStatusWidget(Static):
    """Widget showing current order statuses."""
    
    def __init__(self, shop_manager: ShopManager, theme: HelloKittyTheme):
        super().__init__()
        self.shop_manager = shop_manager
        self.theme = theme
    
    def compose(self) -> ComposeResult:
        """Compose the order status widget."""
        with Container(classes="order-status-widget"):
            yield Label("🍵 Current Orders", classes="widget-title")
            
            # Get recent orders
            recent_orders = list(self.shop_manager.orders.values())[-5:]  # Last 5 orders
            if not recent_orders:
                yield Label("No recent orders ✨", classes="no-orders")
                return
            
            for order in recent_orders:
                status_emoji = self._get_status_emoji(order.status.value)
                customer_name = order.customer.name if order.customer else "Guest"
                
                order_info = f"{status_emoji} Order #{order.id[:8]} - {customer_name} - ${order.total_amount:.2f}"
                yield Label(order_info, classes=f"order-item status-{order.status.value}")


class InventoryAlertWidget(Static):
    """Widget showing inventory alerts."""
    
    def __init__(self, shop_manager: ShopManager, theme: HelloKittyTheme):
        super().__init__()
        self.shop_manager = shop_manager
        self.theme = theme
    
    def compose(self) -> ComposeResult:
        """Compose the inventory alert widget."""
        with Container(classes="inventory-widget"):
            yield Label("📦 Inventory Alerts", classes="widget-title")
            
            inventory_status = self.shop_manager.get_inventory_status()
            low_stock_items = inventory_status["low_stock_items"]
            
            if not low_stock_items:
                yield Label("All items well stocked! ✨", classes="no-alerts")
                return
            
            yield Label(f"⚠️ {len(low_stock_items)} items low on stock:", classes="alert-count")
            
            for item in low_stock_items[:5]:  # Show top 5
                yield Label(f"• {item['item']}: {item['quantity']} remaining", classes="low-stock-item")


class DashboardScreen(Static):
    """Main dashboard screen for the Hello Kitty BubbleTea TUI."""
    
    def __init__(self, shop_manager: ShopManager, theme: HelloKittyTheme):
        super().__init__()
        self.shop_manager = shop_manager
        self.theme = theme
    
    def compose(self) -> ComposeResult:
        """Compose the dashboard screen."""
        # Header
        with Container(classes="dashboard-header"):
            yield Label("🌸 Hello Kitty BubbleTea Dashboard 🌸", classes="main-title")
            yield Label(self._get_greeting(), classes="sub-title")
        
        # Top metrics row
        with Horizontal(classes="metrics-row"):
            yield MetricCard("Daily Revenue", self._get_daily_revenue(), "💰", "pastel_butter")
            yield MetricCard("Orders Today", self._get_orders_today(), "🍵", "pastel_pink")
            yield MetricCard("Active Orders", self._get_active_orders(), "⚡", "pastel_mint")
            yield MetricCard("Low Stock Items", self._get_low_stock_count(), "⚠️", "pastel_lilac")
        
        # Main content area
        with Horizontal(classes="content-row"):
            # Left column
            with Vertical(classes="left-column"):
                yield self._create_popular_drinks_widget()
            
            # Right column  
            with Vertical(classes="right-column"):
                yield OrderStatusWidget(self.shop_manager, self.theme)
                yield InventoryAlertWidget(self.shop_manager, self.theme)
        
        # Quick actions
        with Container(classes="quick-actions"):
            yield Label("✨ Quick Actions ✨", classes="actions-title")
            with Horizontal(classes="actions-row"):
                yield Button("🆕 New Order", id="new-order", classes="action-button")
                yield Button("📋 View Menu", id="view-menu", classes="action-button")
                yield Button("📦 Inventory", id="view-inventory", classes="action-button")
                yield Button("👥 Customers", id="view-customers", classes="action-button")
    
    def _get_greeting(self) -> str:
        """Get a kawaii greeting based on time of day."""
        hour = datetime.now().hour
        if hour < 12:
            return "☀️ Good Morning! Ready to serve some kawaii bubble tea?"
        elif hour < 18:
            return "🌞 Good Afternoon! Hope you're having a purr-fect day!"
        else:
            return "🌙 Good Evening! Time for some cozy bubble tea vibes!"
    
    def _get_daily_revenue(self) -> str:
        """Get today's revenue formatted for display."""
        summary = self.shop_manager.get_daily_sales_summary()
        revenue = summary["total_revenue"]
        return f"${revenue:.2f}"
    
    def _get_orders_today(self) -> str:
        """Get number of orders today."""
        summary = self.shop_manager.get_daily_sales_summary()
        return str(summary["total_orders"])
    
    def _get_active_orders(self) -> str:
        """Get number of active (non-completed) orders."""
        from ..core.shop_manager import OrderStatus
        active_orders = [
            order for order in self.shop_manager.orders.values()
            if order.status not in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]
        ]
        return str(len(active_orders))
    
    def _get_low_stock_count(self) -> str:
        """Get count of low stock items."""
        inventory_status = self.shop_manager.get_inventory_status()
        return str(inventory_status["low_stock_count"])
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for order status."""
        status_emojis = {
            "pending": "⏳",
            "in_progress": "🌀",
            "ready": "✅",
            "completed": "💕",
            "cancelled": "❌"
        }
        return status_emojis.get(status, "❓")
    
    def _create_popular_drinks_widget(self) -> Static:
        """Create the popular drinks widget."""
        summary = self.shop_manager.get_daily_sales_summary()
        popular_drinks = summary["popular_drinks"]

        children: list[Static] = [Label("🔥 Popular Drinks Today", classes="widget-title")]

        if not popular_drinks:
            children.append(Label("No orders yet today ✨", classes="no-orders"))
        else:
            for drink_name, count in popular_drinks:
                drink_icon = next(
                    (drink.icon for drink in self.shop_manager.drinks.values() if drink.name == drink_name),
                    "🍵",
                )
                drink_info = f"{drink_icon} {drink_name}: {count} sold"
                children.append(Label(drink_info, classes="popular-drink-item"))

        return Container(*children, classes="popular-drinks-widget")


# CSS styling for kawaii Hello Kitty theme
DASHBOARD_CSS = """
/* Hello Kitty Dashboard Styles */
.dashboard-header {
    align: center;
    height: 4;
    background: $pastel-pink;
    border: solid $hk-primary;
    margin: 1;
    padding: 1;
}

.main-title {
    color: $hk-text;
    text-align: center;
    text-style: bold;
    font-size: 1.5;
}

.sub-title {
    color: $hk-secondary;
    text-align: center;
    font-size: 1.0;
}

.metrics-row {
    height: 6;
    margin: 1;
}

.metric-card {
    background: $pastel-sky;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    width: 1fr;
    align: center middle;
}

.metric-title {
    color: $hk-text;
    text-align: center;
    font-size: 0.8;
}

.metric-value {
    color: $hk-primary;
    text-align: center;
    text-style: bold;
    font-size: 1.5;
}

.content-row {
    height: 1fr;
    margin: 1;
}

.left-column, .right-column {
    width: 1fr;
    height: 1fr;
    margin: 1;
}

.widget-title {
    color: $hk-primary;
    text-style: bold;
    font-size: 1.0;
    margin-bottom: 1;
}

.order-status-widget, .inventory-widget, .popular-drinks-widget {
    background: $pastel-butter;
    border: rounded $hk-contour;
    margin: 1;
    padding: 1;
    height: 1fr;
}

.order-item {
    margin: 0 0 1 0;
    font-size: 0.8;
}

.status-pending { color: $hk-accent; }
.status-in_progress { color: $hk-secondary; }
.status-ready { color: $hk-primary; }
.status-completed { color: $matcha-green; }
.status-cancelled { color: $thai-orange; }

.low-stock-item {
    color: $hk-accent;
    font-size: 0.8;
}

.alert-count {
    color: $hk-primary;
    text-style: bold;
    font-size: 0.9;
}

.no-orders, .no-alerts {
    color: $hk-contour;
    text-align: center;
    text-style: italic;
}

.popular-drink-item {
    color: $hk-text;
    margin: 0 0 1 0;
    font-size: 0.8;
}

.quick-actions {
    background: $pastel-lilac;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    height: 5;
}

.actions-title {
    color: $hk-text;
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
}

.actions-row {
    align: center middle;
    spacing: 2;
}

.action-button {
    background: $hk-primary;
    color: $hk-bg;
    border: rounded;
    width: 15;
    height: 2;
}

.action-button:hover {
    background: $hk-secondary;
}
"""
