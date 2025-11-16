"""
Hello Kitty BubbleTea TUI - Customers Screen
===========================================

Customer management screen for viewing and managing customer information
with kawaii Hello Kitty theming.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, Label, Button, DataTable, Input
from textual.reactive import reactive
from textual.message import Message

from ..core.shop_manager import ShopManager, Customer
from ..core.theme import HelloKittyTheme


class CustomerCard(Static):
    """A card displaying customer information."""
    
    def __init__(self, customer: Customer, theme: HelloKittyTheme):
        super().__init__()
        self.customer = customer
        self.theme = theme
    
    def compose(self) -> ComposeResult:
        """Compose the customer card."""
        with Container(classes="customer-card"):
            # Customer header
            with Container(classes="customer-header"):
                yield Label(self._get_customer_avatar(), classes="customer-avatar")
                with Vertical(classes="customer-info"):
                    yield Label(self.customer.name, classes="customer-name")
                    yield Label(self._get_customer_status(), classes="customer-status")
            
            # Contact information
            with Container(classes="contact-info"):
                yield Label(f"📱 {self.customer.phone}", classes="contact-item")
                if self.customer.email:
                    yield Label(f"✉️ {self.customer.email}", classes="contact-item")
            
            # Order statistics
            with Horizontal(classes="stats-row"):
                yield Label(f"🛍️ Orders: {self.customer.total_orders}", classes="stat-item")
                yield Label(f"💖 Points: {self.customer.loyalty_points}", classes="stat-item")
                if self.customer.is_vip:
                    yield Label("⭐ VIP", classes="vip-badge")
            
            # Favorite drinks
            if self.customer.favorite_drinks:
                yield Label("❤️  Favorites:", classes="favorites-header")
                favorite_names = []
                for drink_id in self.customer.favorite_drinks[:3]:
                    # Get drink name from shop manager (would need to be passed in)
                    favorite_names.append("🍵")  # Placeholder
                yield Label(" ".join(favorite_names), classes="favorite-drinks")
            
            # Last order date
            if self.customer.last_order_date:
                days_since = (self.customer.last_order_date.date()).days
                if days_since == 0:
                    last_order_text = "Today!"
                elif days_since == 1:
                    last_order_text = "Yesterday"
                else:
                    last_order_text = f"{days_since} days ago"
                yield Label(f"🕐 Last order: {last_order_text}", classes="last-order")
            
            # Action buttons
            with Horizontal(classes="customer-actions"):
                yield Button("📞 Call", id=f"call-{self.customer.id}", classes="action-button small")
                yield Button("📝 Edit", id=f"edit-{self.customer.id}", classes="action-button small")
                yield Button("🍵 New Order", id=f"order-{self.customer.id}", classes="action-button small primary")
    
    def _get_customer_avatar(self) -> str:
        """Get avatar emoji for customer."""
        # Could add logic to choose different avatars
        # For now, use Hello Kitty as default
        return "🌸"
    
    def _get_customer_status(self) -> str:
        """Get customer status text."""
        if self.customer.is_vip:
            return "⭐ VIP Customer"
        elif self.customer.total_orders >= 5:
            return "💖 Loyalty Member"
        else:
            return "🌟 New Customer"


class AddCustomerForm(Static):
    """Form for adding new customers."""
    
    def compose(self) -> ComposeResult:
        """Compose the add customer form."""
        with Container(classes="add-customer-form"):
            yield Label("👤 Add New Customer", classes="form-title")
            
            # Name
            yield Label("Name:", classes="form-label")
            yield Input(placeholder="Customer name...", id="name-input", classes="form-input")
            
            # Phone
            yield Label("Phone:", classes="form-label")
            yield Input(placeholder="Phone number...", id="phone-input", classes="form-input")
            
            # Email (optional)
            yield Label("Email (optional):", classes="form-label")
            yield Input(placeholder="Email address...", id="email-input", classes="form-input")
            
            # VIP status
            yield Label("Customer Type:", classes="form-label")
            yield Button("🌟 Regular Customer", id="regular-customer", classes="customer-type-button")
            yield Button("⭐ VIP Customer", id="vip-customer", classes="customer-type-button")
            
            # Submit button
            with Horizontal(classes="form-actions"):
                yield Button("💕 Create Customer", id="submit-customer", classes="action-button primary")
                yield Button("❌ Cancel", id="cancel-form", classes="action-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle form button presses."""
        button_id = event.button.id
        
        if button_id == "submit-customer":
            self._create_customer()
        elif button_id == "cancel-form":
            self.app.action_back()
        elif button_id in ["regular-customer", "vip-customer"]:
            self._select_customer_type(button_id)
    
    def _create_customer(self) -> None:
        """Create a new customer from form data."""
        # This would be implemented to actually create a customer
        self.notify("👤 Customer creation coming soon! ✨")
    
    def _select_customer_type(self, button_id: str) -> None:
        """Handle customer type selection."""
        self.notify(f"💫 Selected {button_id.replace('-customer', '').replace('_', ' ')}! ✨")


class CustomersScreen(Static):
    """Customer management screen for Hello Kitty BubbleTea."""
    
    def __init__(self, shop_manager: ShopManager, theme: HelloKittyTheme):
        super().__init__()
        self.shop_manager = shop_manager
        self.theme = theme
        self.show_add_form = False
        self.search_query = ""
    
    def compose(self) -> ComposeResult:
        """Compose the customers screen."""
        if self.show_add_form:
            yield AddCustomerForm()
            return
        
        # Header
        with Container(classes="customers-header"):
            yield Label("👥 Customer Management 👥", classes="customers-title")
            yield Label("Manage your kawaii customer relationships!", classes="customers-subtitle")
        
        # Customer controls
        with Container(classes="customer-controls"):
            with Horizontal(classes="controls-row"):
                yield Button("➕ Add Customer", id="add-customer", classes="control-button primary")
                yield Button("📊 Analytics", id="customer-analytics", classes="control-button")
                yield Button("🔄 Refresh", id="refresh-customers", classes="control-button")
                yield Button("💎 Export VIPs", id="export-vips", classes="control-button")
        
        # Search and filters
        with Container(classes="search-filters"):
            yield Label("Search Customers:", classes="search-label")
            with Horizontal(classes="search-row"):
                yield Input(placeholder="Search by name or phone...", id="search-input", classes="search-input")
                yield Button("🔍 Search", id="search-btn", classes="search-button")
                yield Button("🌟 All", id="filter-all", classes="filter-button")
                yield Button("⭐ VIP Only", id="filter-vip", classes="filter-button")
        
        # Customer statistics
        with Container(classes="customer-stats"):
            stats = self._get_customer_stats()
            with Horizontal(classes="stats-row"):
                yield Label(f"👥 Total: {stats['total']}", classes="stat-item")
                yield Label(f"⭐ VIP: {stats['vip']}", classes="stat-item")
                yield Label(f"💖 Active: {stats['active']}", classes="stat-item")
                yield Label(f"🌟 New: {stats['new']}", classes="stat-item")
        
        # Customers grid
        with Container(classes="customers-container"):
            customers = self._get_filtered_customers()
            if not customers:
                yield Label("No customers found ✨", classes="no-customers")
            else:
                with Grid(classes="customers-grid"):
                    for customer in customers:
                        yield CustomerCard(customer, self.theme)
    
    def _get_customer_stats(self) -> dict:
        """Get customer statistics."""
        customers = self.shop_manager.get_all_customers()
        
        total = len(customers)
        vip = sum(1 for c in customers if c.is_vip)
        
        # Active customers (ordered in last 30 days)
        active_date_threshold = (self.customer_created_date if hasattr(self, 'customer_created_date') else None)
        active = sum(1 for c in customers if c.last_order_date and 
                    (c.last_order_date.date() >= active_date_threshold))
        
        # New customers (created in last 30 days)
        new_date_threshold = active_date_threshold
        new = sum(1 for c in customers if 
                 c.created_at.date() >= new_date_threshold)
        
        return {
            "total": total,
            "vip": vip, 
            "active": active,
            "new": new
        }
    
    def _get_filtered_customers(self) -> list[Customer]:
        """Get customers filtered by search and category."""
        customers = self.shop_manager.get_all_customers()
        
        # Apply search filter
        if self.search_query:
            customers = self.shop_manager.search_customers(self.search_query)
        
        # Sort by name
        customers.sort(key=lambda c: c.name)
        
        return customers
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "add-customer":
            self.show_add_form = True
            self.refresh()
        elif button_id == "customer-analytics":
            self._show_analytics()
        elif button_id == "refresh-customers":
            self._refresh_customers()
        elif button_id == "export-vips":
            self._export_vip_customers()
        elif button_id == "search-btn":
            self._perform_search()
        elif button_id.startswith("call-"):
            customer_id = button_id[5:]
            self._call_customer(customer_id)
        elif button_id.startswith("edit-"):
            customer_id = button_id[5:]
            self._edit_customer(customer_id)
        elif button_id.startswith("order-"):
            customer_id = button_id[6:]
            self._create_order_for_customer(customer_id)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission events."""
        if event.input.id == "search-input":
            self._perform_search()
    
    def _show_analytics(self) -> None:
        """Show customer analytics."""
        self.notify("📊 Customer Analytics coming soon! ✨")
    
    def _refresh_customers(self) -> None:
        """Refresh the customers display."""
        self.refresh()
        self.notify("🔄 Customers refreshed! ✨")
    
    def _export_vip_customers(self) -> None:
        """Export VIP customer list."""
        self.notify("💎 VIP Export coming soon! ✨")
    
    def _perform_search(self) -> None:
        """Perform customer search."""
        search_input = self.query_one("#search-input", Input)
        self.search_query = search_input.value
        self.refresh()
    
    def _call_customer(self, customer_id: str) -> None:
        """Handle calling a customer."""
        customer = self.shop_manager.get_customer_by_id(customer_id)
        if customer:
            self.notify(f"📞 Calling {customer.name} at {customer.phone}! 📞")
    
    def _edit_customer(self, customer_id: str) -> None:
        """Handle editing a customer."""
        self.notify("📝 Edit Customer coming soon! ✨")
    
    def _create_order_for_customer(self, customer_id: str) -> None:
        """Handle creating an order for a customer."""
        self.notify("🍵 New Order for Customer coming soon! ✨")


# CSS styling for customers screen
CUSTOMERS_CSS = """
/* Hello Kitty Customers Styles */
.customers-header {
    align: center;
    background: $pastel-pink;
    border: solid $hk-primary;
    margin: 1;
    padding: 1;
}

.customers-title {
    color: $hk-text;
    text-align: center;
    text-style: bold;
    font-size: 1.5;
    margin-bottom: 1;
}

.customers-subtitle {
    color: $hk-secondary;
    text-align: center;
    font-size: 1.0;
}

.customer-controls {
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

.search-filters {
    background: $pastel-butter;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    height: 4;
}

.search-label {
    color: $hk-text;
    text-style: bold;
    margin-bottom: 1;
}

.search-row {
    spacing: 1;
}

.search-input {
    background: $hk-bg;
    border: solid $hk-contour;
    width: 30;
}

.search-button, .filter-button {
    background: $hk-contour;
    color: $hk-bg;
    border: rounded;
    width: 10;
    height: 2;
}

.search-button:hover, .filter-button:hover {
    background: $hk-secondary;
}

.customer-stats {
    background: $pastel-lilac;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    height: 3;
}

.stats-row {
    align: center middle;
    spacing: 3;
}

.stat-item {
    color: $hk-text;
    text-style: bold;
}

.customers-container {
    height: 1fr;
    margin: 1;
}

.no-customers {
    color: $hk-contour;
    text-align: center;
    text-style: italic;
    font-size: 1.2;
}

.customers-grid {
    height: 1fr;
    grid-gutter: 2;
    grid-columns: 2;
    grid-rows: auto;
}

.customer-card {
    background: $pastel-sky;
    border: rounded $hk-contour;
    padding: 1;
    margin: 1;
    height: auto;
}

.customer-header {
    background: $pastel-pink;
    border: solid $hk-primary;
    margin-bottom: 1;
    padding: 1;
    align: center middle;
}

.customer-avatar {
    font-size: 2.0;
    width: 1;
}

.customer-info {
    width: 1fr;
}

.customer-name {
    color: $hk-text;
    text-style: bold;
    font-size: 1.1;
}

.customer-status {
    color: $hk-secondary;
    font-size: 0.8;
}

.contact-info {
    margin: 1 0;
}

.contact-item {
    color: $hk-text;
    font-size: 0.8;
    margin-bottom: 0;
}

.stats-row {
    spacing: 2;
    margin: 1 0;
}

.stat-item {
    color: $hk-text;
    font-size: 0.8;
}

.vip-badge {
    color: $hk-accent;
    background: $pastel-butter;
    border: rounded;
    font-size: 0.8;
    padding: 0 1;
}

.favorites-header {
    color: $hk-primary;
    text-style: bold;
    font-size: 0.8;
    margin: 1 0 0 0;
}

.favorite-drinks {
    color: $hk-secondary;
    font-size: 0.8;
    margin-bottom: 1;
}

.last-order {
    color: $hk-contour;
    font-size: 0.7;
    margin-bottom: 1;
}

.customer-actions {
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

.action-button:hover {
    background: $hk-secondary;
}

.add-customer-form {
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

.form-input {
    background: $hk-bg;
    border: solid $hk-contour;
    margin-bottom: 1;
}

.customer-type-button {
    background: $pastel-lilac;
    color: $hk-text;
    border: rounded;
    width: 15;
    height: 2;
    margin: 0 1 1 0;
}

.form-actions {
    spacing: 2;
    align: center middle;
    margin-top: 2;
}
"""