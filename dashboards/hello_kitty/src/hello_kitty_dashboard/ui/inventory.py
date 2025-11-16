"""
Hello Kitty BubbleTea TUI - Inventory Screen
===========================================

Inventory management screen for monitoring and managing stock levels
with kawaii Hello Kitty theming.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, Label, Button, DataTable, ProgressBar
from textual.reactive import reactive
from textual.message import Message

from ..core.shop_manager import ShopManager
from ..core.theme import HelloKittyTheme


class InventoryItemCard(Static):
    """A card displaying inventory item information."""
    
    def __init__(self, item_name: str, quantity: int, threshold: int = 50):
        super().__init__()
        self.item_name = item_name
        self.quantity = quantity
        self.threshold = threshold
        self.is_low_stock = quantity <= threshold
    
    def compose(self) -> ComposeResult:
        """Compose the inventory item card."""
        stock_level = min(self.quantity / (self.threshold * 2), 1.0)  # Normalize to 0-1
        
        with Container(classes="inventory-card"):
            # Item header
            with Container(classes="item-header"):
                yield Label(self._get_item_icon(), classes="item-icon")
                yield Label(self.item_name, classes="item-name")
                yield Label(f"{self.quantity}", classes="item-quantity")
            
            # Stock level bar
            with Container(classes="stock-level-container"):
                yield ProgressBar(total=1.0, show_percentage=False)
            
            # Stock status
            status_text = self._get_status_text()
            yield Label(status_text, classes=f"stock-status status-{self._get_status_type()}")
            
            # Low stock indicator
            if self.is_low_stock:
                yield Label("⚠️ Low Stock", classes="low-stock-alert")
    
    def _get_item_icon(self) -> str:
        """Get icon for the inventory item."""
        # Map common bubble tea ingredients to icons
        icon_map = {
            "tapioca": "●",
            "boba": "◉",
            "milk": "🥛", 
            "tea": "🍵",
            "sugar": "🍯",
            "strawberry": "🍓",
            "matcha": "🟢",
            "taro": "🟣"
        }
        
        for key, icon in icon_map.items():
            if key in self.item_name.lower():
                return icon
        return "📦"
    
    def _get_status_text(self) -> str:
        """Get status text based on quantity."""
        if self.quantity == 0:
            return "Out of Stock"
        elif self.quantity <= self.threshold // 2:
            return "Very Low"
        elif self.quantity <= self.threshold:
            return "Low Stock"
        else:
            return "In Stock"
    
    def _get_status_type(self) -> str:
        """Get status type for styling."""
        if self.quantity == 0:
            return "out"
        elif self.quantity <= self.threshold:
            return "low"
        else:
            return "good"


class InventoryScreen(Static):
    """Inventory management screen for Hello Kitty BubbleTea."""
    
    def __init__(self, shop_manager: ShopManager, theme: HelloKittyTheme):
        super().__init__()
        self.shop_manager = shop_manager
        self.theme = theme
        self.filter_category = "all"
    
    def compose(self) -> ComposeResult:
        """Compose the inventory screen."""
        # Header
        with Container(classes="inventory-header"):
            yield Label("📦 Inventory Management 📦", classes="inventory-title")
            yield Label("Keep track of your kawaii bubble tea supplies!", classes="inventory-subtitle")
        
        # Inventory controls
        with Container(classes="inventory-controls"):
            with Horizontal(classes="controls-row"):
                yield Button("➕ Add Stock", id="add-stock", classes="control-button primary")
                yield Button("📉 Update Stock", id="update-stock", classes="control-button")
                yield Button("🔄 Refresh", id="refresh-inventory", classes="control-button")
                yield Button("📊 Report", id="inventory-report", classes="control-button")
        
        # Inventory status summary
        with Container(classes="inventory-summary"):
            status = self.shop_manager.get_inventory_status()
            with Horizontal(classes="summary-row"):
                yield Label(f"📦 Total Items: {status['total_items']}", classes="summary-item")
                yield Label(f"⚠️ Low Stock: {status['low_stock_count']}", classes="summary-item")
                yield Label(f"🕐 Updated: {status['last_updated'][:16]}", classes="summary-item")
        
        # Inventory items grid
        with Container(classes="inventory-container"):
            yield Label("🗃️ Stock Levels", classes="items-header")
            
            with Grid(classes="inventory-grid"):
                inventory_items = self._get_inventory_items()
                for item_name, quantity in inventory_items:
                    yield InventoryItemCard(item_name, quantity)
        
        # Low stock alerts
        if status["low_stock_items"]:
            with Container(classes="low-stock-section"):
                yield Label("🚨 Low Stock Alerts", classes="alerts-title")
                for item in status["low_stock_items"]:
                    yield Label(f"⚠️ {item['item']}: {item['quantity']} remaining", classes="alert-item")
    
    def _get_inventory_items(self) -> list[tuple[str, int]]:
        """Get inventory items, filtered by category."""
        items = list(self.shop_manager.inventory.items())
        
        # Could add filtering logic here based on self.filter_category
        # For now, return all items sorted by quantity (lowest first)
        return sorted(items, key=lambda x: x[1])
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "add-stock":
            self._show_add_stock_dialog()
        elif button_id == "update-stock":
            self._show_update_stock_dialog()
        elif button_id == "refresh-inventory":
            self._refresh_inventory()
        elif button_id == "inventory-report":
            self._show_inventory_report()
    
    def _show_add_stock_dialog(self) -> None:
        """Show dialog to add stock."""
        self.notify("➕ Add Stock feature coming soon! ✨")
    
    def _show_update_stock_dialog(self) -> None:
        """Show dialog to update stock levels."""
        self.notify("📉 Update Stock feature coming soon! ✨")
    
    def _refresh_inventory(self) -> None:
        """Refresh the inventory display."""
        self.refresh()
        self.notify("🔄 Inventory refreshed! ✨")
    
    def _show_inventory_report(self) -> None:
        """Show inventory report."""
        self.notify("📊 Inventory Report coming soon! ✨")


# CSS styling for inventory screen
INVENTORY_CSS = """
/* Hello Kitty Inventory Styles */
.inventory-header {
    align: center;
    background: $pastel-pink;
    border: solid $hk-primary;
    margin: 1;
    padding: 1;
}

.inventory-title {
    color: $hk-text;
    text-align: center;
    text-style: bold;
    font-size: 1.5;
    margin-bottom: 1;
}

.inventory-subtitle {
    color: $hk-secondary;
    text-align: center;
    font-size: 1.0;
}

.inventory-controls {
    background: $pastel-sky;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    height: 4;
}

.controls-row {
    align: center middle;
    spacing: 2;
}

.control-button {
    background: $hk-primary;
    color: $hk-bg;
    border: rounded;
    width: 12;
    height: 2;
}

.control-button.primary {
    background: $hk-primary;
    text-style: bold;
}

.control-button:hover {
    background: $hk-secondary;
}

.inventory-summary {
    background: $pastel-butter;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    height: 3;
}

.summary-row {
    align: center middle;
    spacing: 3;
}

.summary-item {
    color: $hk-text;
    text-style: bold;
}

.inventory-container {
    height: 1fr;
    margin: 1;
}

.items-header {
    color: $hk-primary;
    text-style: bold;
    font-size: 1.2;
    margin-bottom: 1;
}

.inventory-grid {
    height: 1fr;
    grid-gutter: 2;
    grid-columns: 3;
    grid-rows: auto;
}

.inventory-card {
    background: $pastel-lilac;
    border: rounded $hk-contour;
    padding: 1;
    margin: 1;
    height: auto;
}

.item-header {
    background: $pastel-pink;
    border: solid $hk-primary;
    margin-bottom: 1;
    padding: 1;
    align: center middle;
}

.item-icon {
    font-size: 1.5;
    width: 1;
}

.item-name {
    color: $hk-text;
    text-style: bold;
    width: 1fr;
    text-align: left;
}

.item-quantity {
    color: $hk-primary;
    text-style: bold;
    font-size: 1.2;
}

.stock-level-container {
    background: $pastel-butter;
    border: solid $hk-contour;
    height: 2;
    margin: 1 0;
}

ProgressBar {
    background: $pastel-mint;
    color: $hk-primary;
}

.stock-status {
    text-align: center;
    text-style: bold;
    font-size: 0.9;
}

.status-out {
    color: $thai-orange;
    background: $hk-accent;
    border: rounded;
    padding: 0 1;
}

.status-low {
    color: $hk-primary;
    background: $pastel-butter;
    border: rounded;
    padding: 0 1;
}

.status-good {
    color: $matcha-green;
    background: $pastel-mint;
    border: rounded;
    padding: 0 1;
}

.low-stock-alert {
    color: $hk-primary;
    background: $hk-accent;
    border: rounded;
    text-align: center;
    font-size: 0.8;
    margin-top: 1;
}

.low-stock-section {
    background: $pastel-butter;
    border: solid $hk-accent;
    margin: 1;
    padding: 1;
    height: 5;
}

.alerts-title {
    color: $hk-primary;
    text-style: bold;
    margin-bottom: 1;
}

.alert-item {
    color: $hk-text;
    font-size: 0.9;
    margin-bottom: 0;
}
"""
