"""
Hello Kitty BubbleTea TUI - Orders Screen
========================================

Orders management screen for viewing, creating, and updating bubble tea orders
with kawaii Hello Kitty theming.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, Label, Button, DataTable, Input, Select
from textual.reactive import reactive
from textual.message import Message

from ..core.shop_manager import ShopManager, Order, OrderStatus, DrinkSize
from ..core.theme import HelloKittyTheme


class OrderCard(Static):
    """A card displaying order information."""
    
    def __init__(self, order: Order, theme: HelloKittyTheme):
        super().__init__()
        self.order = order
        self.theme = theme
    
    def compose(self) -> ComposeResult:
        """Compose the order card."""
        with Container(classes="order-card"):
            # Order header
            with Container(classes="order-header"):
                yield Label(f"🧾 Order #{self.order.id[:8]}", classes="order-id")
                yield Label(self._get_status_emoji(), classes="order-status-emoji")
                yield Label(self.order.status.value.replace("_", " ").title(), classes="order-status")
            
            # Customer info
            customer_name = self.order.customer.name if self.order.customer else "Guest"
            pickup_delivery = "🍽️ Pickup" if self.order.is_pickup else "🚚 Delivery"
            yield Label(f"👤 {customer_name} • {pickup_delivery}", classes="order-customer")
            
            # Order items
            yield Label("🍵 Items:", classes="items-header")
            for i, item in enumerate(self.order.items, 1):
                item_info = f"  {i}. {item.drink.icon} {item.drink.name} ({item.size.value})"
                if item.toppings:
                    toppings_list = ", ".join([t.icon + " " + t.name for t in item.toppings])
                    item_info += f" + {toppings_list}"
                item_info += f" x{item.quantity}"
                yield Label(item_info, classes="order-item")
            
            # Order details
            with Horizontal(classes="order-details"):
                yield Label(f"💰 ${self.order.total_amount:.2f}", classes="order-total")
                yield Label(f"🕐 {self.order.created_at.strftime('%H:%M')}", classes="order-time")
                if self.order.estimated_completion:
                    eta = self.order.estimated_completion.strftime('%H:%M')
                    yield Label(f"⏰ ETA: {eta}", classes="order-eta")
            
            # Order notes
            if self.order.notes:
                yield Label(f"📝 Notes: {self.order.notes}", classes="order-notes")
            
            # Action buttons
            with Horizontal(classes="order-actions"):
                if self.order.status == OrderStatus.PENDING:
                    yield Button("▶️ Start", id=f"start-{self.order.id}", classes="action-button small")
                elif self.order.status == OrderStatus.IN_PROGRESS:
                    yield Button("✅ Ready", id=f"ready-{self.order.id}", classes="action-button small")
                elif self.order.status == OrderStatus.READY:
                    yield Button("💕 Complete", id=f"complete-{self.order.id}", classes="action-button small primary")
                
                yield Button("❌ Cancel", id=f"cancel-{self.order.id}", classes="action-button small danger")
    
    def _get_status_emoji(self) -> str:
        """Get emoji for order status."""
        status_emojis = {
            OrderStatus.PENDING: "⏳",
            OrderStatus.IN_PROGRESS: "🌀", 
            OrderStatus.READY: "✅",
            OrderStatus.COMPLETED: "💕",
            OrderStatus.CANCELLED: "❌"
        }
        return status_emojis.get(self.order.status, "❓")


class NewOrderForm(Static):
    """Form for creating new orders."""
    
    def __init__(self, shop_manager: ShopManager, theme: HelloKittyTheme):
        super().__init__()
        self.shop_manager = shop_manager
        self.theme = theme
    
    def compose(self) -> ComposeResult:
        """Compose the new order form."""
        with Container(classes="new-order-form"):
            yield Label("🆕 Create New Order", classes="form-title")
            
            # Customer selection
            yield Label("Select Customer:", classes="form-label")
            customer_options = [(c.name, c.id) for c in self.shop_manager.get_all_customers()]
            # Fallback entry when no customer list is available
            customer_options.append(("Guest (No Account)", "guest"))
            yield Select(customer_options, id="customer-select", classes="form-select")
            
            # Drink selection
            yield Label("Select Drink:", classes="form-label")
            drink_options = [(f"{d.icon} {d.name} - ${d.base_price:.2f}", d.id) 
                           for d in self.shop_manager.get_available_drinks()]
            yield Select(drink_options, id="drink-select", classes="form-select")
            
            # Size selection
            yield Label("Select Size:", classes="form-label")
            size_options = [(size.value.title(), size.value) for size in DrinkSize]
            yield Select(size_options, id="size-select", value="medium", classes="form-select")
            
            # Toppings selection
            yield Label("Select Toppings:", classes="form-label")
            topping_options = [(f"{t.icon} {t.name} (+${t.price:.2f})", t.id)
                             for t in self.shop_manager.get_available_toppings()]
            yield Select(topping_options, id="toppings-select", classes="form-select")
            
            # Quantity
            yield Label("Quantity:", classes="form-label")
            yield Input(value="1", id="quantity-input", classes="form-input")
            
            # Order type
            yield Label("Order Type:", classes="form-label")
            order_type_options = [("Pickup", "pickup"), ("Delivery", "delivery")]
            yield Select(order_type_options, id="order-type-select", value="pickup", classes="form-select")
            
            # Notes
            yield Label("Special Notes:", classes="form-label")
            yield Input(placeholder="Any special requests...", id="notes-input", classes="form-input")
            
            # Submit button
            with Horizontal(classes="form-actions"):
                yield Button("💕 Create Order", id="submit-order", classes="action-button primary")
                yield Button("❌ Cancel", id="cancel-form", classes="action-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle form button presses."""
        button_id = event.button.id
        
        if button_id == "submit-order":
            self._create_order()
        elif button_id == "cancel-form":
            self._reset_form()
    
    def _create_order(self) -> None:
        """Create a new order from form data."""
        # Get form values
        customer_select = self.query_one("#customer-select", Select)
        drink_select = self.query_one("#drink-select", Select)
        size_select = self.query_one("#size-select", Select)
        toppings_select = self.query_one("#toppings-select", Select)
        quantity_input = self.query_one("#quantity-input", Input)
        order_type_select = self.query_one("#order-type-select", Select)
        notes_input = self.query_one("#notes-input", Input)
        
        try:
            # Validate inputs
            if not drink_select.value:
                self.notify("🍵 Please select a drink!", severity="warning")
                return
            
            # Get selected values
            customer_id = customer_select.value if customer_select.value != "guest" else None
            drink_id = drink_select.value
            size = DrinkSize(size_select.value or "medium")
            quantity = int(quantity_input.value or "1")
            is_pickup = order_type_select.value == "pickup"
            notes = notes_input.value or ""
            
            # Get drink and toppings
            drink = self.shop_manager.get_drink_by_id(drink_id)
            if not drink:
                self.notify("❌ Selected drink not found!", severity="error")
                return
            
            toppings = []
            if toppings_select.value:
                topping = self.shop_manager.get_topping_by_id(topping_select.value)
                if topping:
                    toppings = [topping]
            
            # Create order
            customer = self.shop_manager.get_customer_by_id(customer_id) if customer_id else None
            
            # This would need to be implemented in the ShopManager
            self.notify("🆕 Order creation coming soon! ✨")
            
        except ValueError:
            self.notify("❌ Please enter a valid quantity!", severity="error")
    
    def _reset_form(self) -> None:
        """Reset the form to default values."""
        # Reset form inputs
        inputs = self.query(Input)
        for input_widget in inputs:
            if input_widget.id == "quantity-input":
                input_widget.value = "1"
            else:
                input_widget.value = ""


class OrdersScreen(Static):
    """Orders management screen for Hello Kitty BubbleTea."""
    
    def __init__(self, shop_manager: ShopManager, theme: HelloKittyTheme):
        super().__init__()
        self.shop_manager = shop_manager
        self.theme = theme
        self.show_new_order_form = False
    
    def compose(self) -> ComposeResult:
        """Compose the orders screen."""
        if self.show_new_order_form:
            yield NewOrderForm(self.shop_manager, self.theme)
            return
        
        # Header
        with Container(classes="orders-header"):
            yield Label("🍵 Order Management 🍵", classes="orders-title")
            yield Label("Manage orders with kawaii efficiency!", classes="orders-subtitle")
        
        # Order controls
        with Container(classes="order-controls"):
            with Horizontal(classes="controls-row"):
                yield Button("➕ New Order", id="new-order", classes="control-button primary")
                yield Button("🔄 Refresh", id="refresh-orders", classes="control-button")
                yield Button("📊 Analytics", id="order-analytics", classes="control-button")
        
        # Order filters
        with Container(classes="order-filters"):
            yield Label("Filter by Status:", classes="filter-label")
            with Horizontal(classes="status-buttons"):
                yield Button("🌟 All", id="filter-all", classes="status-button active")
                yield Button("⏳ Pending", id="filter-pending", classes="status-button")
                yield Button("🌀 In Progress", id="filter-progress", classes="status-button")
                yield Button("✅ Ready", id="filter-ready", classes="status-button")
                yield Button("💕 Completed", id="filter-completed", classes="status-button")
        
        # Orders list
        with Container(classes="orders-container"):
            orders = self._get_filtered_orders()
            if not orders:
                yield Label("No orders found ✨", classes="no-orders")
            else:
                with Grid(classes="orders-grid"):
                    for order in orders:
                        yield OrderCard(order, self.theme)
    
    def _get_filtered_orders(self) -> list[Order]:
        """Get orders filtered by current selection."""
        all_orders = list(self.shop_manager.orders.values())
        
        # Sort by creation time (newest first)
        all_orders.sort(key=lambda x: x.created_at, reverse=True)
        
        return all_orders  # Could add filtering logic here
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "new-order":
            self.show_new_order_form = True
            self.refresh()
        elif button_id == "refresh-orders":
            self._refresh_orders()
        elif button_id == "order-analytics":
            self._show_analytics()
        elif button_id.startswith("start-"):
            order_id = button_id[6:]  # Remove "start-" prefix
            self._update_order_status(order_id, OrderStatus.IN_PROGRESS)
        elif button_id.startswith("ready-"):
            order_id = button_id[6:]  # Remove "ready-" prefix
            self._update_order_status(order_id, OrderStatus.READY)
        elif button_id.startswith("complete-"):
            order_id = button_id[8:]  # Remove "complete-" prefix
            self._update_order_status(order_id, OrderStatus.COMPLETED)
        elif button_id.startswith("cancel-"):
            order_id = button_id[7:]  # Remove "cancel-" prefix
            self._update_order_status(order_id, OrderStatus.CANCELLED)
    
    def _refresh_orders(self) -> None:
        """Refresh the orders display."""
        self.refresh()
        self.notify("🔄 Orders refreshed! ✨")
    
    def _show_analytics(self) -> None:
        """Show order analytics."""
        self.notify("📊 Analytics feature coming soon! ✨")
    
    async def _update_order_status(self, order_id: str, new_status: OrderStatus) -> None:
        """Update an order's status."""
        success = await self.shop_manager.update_order_status(order_id, new_status)
        if success:
            self.refresh()
            self.notify(f"💕 Order #{order_id[:8]} updated to {new_status.value}!")
        else:
            self.notify("❌ Failed to update order status!", severity="error")


# CSS styling for orders screen
ORDERS_CSS = """
/* Hello Kitty Orders Styles */
.orders-header {
    align: center;
    background: $pastel-pink;
    border: solid $hk-primary;
    margin: 1;
    padding: 1;
}

.orders-title {
    color: $hk-text;
    text-align: center;
    text-style: bold;
    font-size: 1.5;
    margin-bottom: 1;
}

.orders-subtitle {
    color: $hk-secondary;
    text-align: center;
    font-size: 1.0;
}

.order-controls {
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

.order-filters {
    background: $pastel-butter;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    height: 3;
}

.filter-label {
    color: $hk-text;
    text-style: bold;
    margin-bottom: 1;
}

.status-buttons {
    spacing: 1;
}

.status-button {
    background: $hk-contour;
    color: $hk-bg;
    border: rounded;
    width: 12;
    height: 2;
}

.status-button.active {
    background: $hk-primary;
    text-style: bold;
}

.status-button:hover {
    background: $hk-secondary;
}

.orders-container {
    height: 1fr;
    margin: 1;
}

.orders-grid {
    height: 1fr;
    grid-gutter: 2;
    grid-columns: 2;
    grid-rows: auto;
}

.no-orders {
    color: $hk-contour;
    text-align: center;
    text-style: italic;
    font-size: 1.2;
}

.order-card {
    background: $pastel-lilac;
    border: rounded $hk-contour;
    padding: 1;
    margin: 1;
    height: auto;
}

.order-header {
    background: $pastel-pink;
    border: solid $hk-primary;
    margin-bottom: 1;
    padding: 1;
    align: center middle;
}

.order-id {
    color: $hk-text;
    text-style: bold;
    width: 1fr;
}

.order-status-emoji {
    font-size: 1.2;
}

.order-status {
    color: $hk-secondary;
    text-style: bold;
}

.order-customer {
    color: $hk-text;
    font-size: 0.9;
    margin-bottom: 1;
}

.items-header {
    color: $hk-primary;
    text-style: bold;
    margin-bottom: 1;
}

.order-item {
    color: $hk-text;
    font-size: 0.8;
    margin-bottom: 0;
}

.order-details {
    spacing: 2;
    margin: 1 0;
}

.order-total {
    color: $hk-primary;
    text-style: bold;
}

.order-time, .order-eta {
    color: $hk-secondary;
    font-size: 0.8;
}

.order-notes {
    color: $hk-accent;
    font-style: italic;
    font-size: 0.8;
    margin-top: 1;
}

.order-actions {
    spacing: 1;
    align: right middle;
    margin-top: 1;
}

.action-button {
    background: $hk-contour;
    color: $hk-bg;
    border: rounded;
    padding: 0 1;
    height: 2;
}

.action-button.small {
    width: 8;
    font-size: 0.8;
}

.action-button.primary {
    background: $hk-primary;
}

.action-button.danger {
    background: $thai-orange;
}

.action-button:hover {
    background: $hk-secondary;
}

.new-order-form {
    background: $pastel-sky;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    height: 1fr;
}

.form-title {
    color: $hk-primary;
    text-style: bold;
    text-align: center;
    font-size: 1.3;
    margin-bottom: 2;
}

.form-label {
    color: $hk-text;
    text-style: bold;
    margin: 1 0 0 0;
}

.form-select, .form-input {
    background: $hk-bg;
    border: solid $hk-contour;
    margin-bottom: 1;
}

.form-actions {
    spacing: 2;
    align: center middle;
    margin-top: 2;
}
"""
