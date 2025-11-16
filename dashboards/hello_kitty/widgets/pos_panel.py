"""Hello Kitty BubbleTea Shop TUI - POS Panel Widget."""

from __future__ import annotations

from datetime import datetime
from textual.widgets import Static, Input, Button
from textual.containers import Vertical, Horizontal

from .models import MenuItem, Order, OrderItem, Topping, Customer


class POSPanel(Static):
    """Point of Sale panel with Hello Kitty styling.
    
    Allows staff to take orders with a beautiful kawaii interface.
    Features item selection, customization options, and order total calculation.
    """

    def __init__(self):
        """Initialize POS panel widget."""
        super().__init__()
        self.selected_items: list[OrderItem] = []
        self.customer_name: str = ""
        self.order_type: str = "takeaway"
        self.current_customer: Customer | None = None

    def update_selection(self, selected_items: list[MenuItem]) -> None:
        """Update POS with currently selected menu items.
        
        Args:
            selected_items: List of menu items currently selected
        """
        # This would typically be called when items are clicked in the menu
        pass

    def add_item_to_order(self, menu_item: MenuItem, quantity: int = 1, toppings: list[Topping] = None) -> None:
        """Add an item to the current order.
        
        Args:
            menu_item: Menu item to add
            quantity: Quantity to add
            toppings: List of toppings to add
        """
        if toppings is None:
            toppings = []

        # Check if item already exists in order (for quantity updates)
        for existing_item in self.selected_items:
            if (existing_item.menu_item.id == menu_item.id and 
                existing_item.toppings == toppings):
                existing_item.quantity += quantity
                break
        else:
            # Add new item
            order_item = OrderItem(
                menu_item=menu_item,
                quantity=quantity,
                toppings=toppings,
                customizations={}
            )
            self.selected_items.append(order_item)
        
        self._render_pos_panel()

    def remove_item_from_order(self, item_index: int) -> None:
        """Remove an item from the current order.
        
        Args:
            item_index: Index of item to remove
        """
        if 0 <= item_index < len(self.selected_items):
            del self.selected_items[item_index]
            self._render_pos_panel()

    def update_item_quantity(self, item_index: int, quantity: int) -> None:
        """Update quantity of an item in the order.
        
        Args:
            item_index: Index of item to update
            quantity: New quantity
        """
        if 0 <= item_index < len(self.selected_items) and quantity > 0:
            self.selected_items[item_index].quantity = quantity
            self._render_pos_panel()

    def set_customer_info(self, name: str, phone: str = "", email: str = "") -> None:
        """Set customer information for the order.
        
        Args:
            name: Customer name
            phone: Customer phone number
            email: Customer email
        """
        self.customer_name = name
        # Create or update customer object
        self.current_customer = Customer(
            id=f"cust_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=name,
            phone=phone if phone else None,
            email=email if email else None
        )
        self._render_pos_panel()

    def set_order_type(self, order_type: str) -> None:
        """Set the order type (dine-in, takeaway, delivery).
        
        Args:
            order_type: Type of order
        """
        self.order_type = order_type
        self._render_pos_panel()

    def calculate_total(self) -> float:
        """Calculate the total cost of the current order.
        
        Returns:
            Total cost of the order
        """
        total = 0.0
        for item in self.selected_items:
            item_total = item.menu_item.price + sum(t.price for t in item.toppings)
            total += item_total * item.quantity
        return total

    def clear_order(self) -> None:
        """Clear the current order."""
        self.selected_items.clear()
        self.customer_name = ""
        self.current_customer = None
        self.order_type = "takeaway"
        self._render_pos_panel()

    def submit_order(self) -> Order | None:
        """Submit the current order and return the Order object.
        
        Returns:
            Order object if order is valid, None otherwise
        """
        if not self.selected_items:
            return None
        
        if not self.customer_name:
            # Could show an error or prompt for customer name
            return None

        # Create order object
        order = Order(
            id=f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            customer_name=self.customer_name,
            items=self.selected_items.copy(),
            status="pending",
            created_at=datetime.now(),
            order_type=self.order_type
        )

        # Clear the current order
        self.clear_order()
        
        return order

    def _render_pos_panel(self) -> None:
        """Render the POS panel display."""
        if not self.selected_items:
            pos_lines = self._build_empty_order_display()
        else:
            pos_lines = self._build_order_display()

        self.update("\n".join(pos_lines))

    def _build_empty_order_display(self) -> list[str]:
        """Build display for when no items are selected."""
        return [
            "[bold hot_pink]🌸 Hello Kitty POS ✨[/]",
            "",
            "[light_pink]🥤 Select drinks from the menu[/]",
            "[light_pink]✨ Click on items to add them![/]",
            "",
            "[dim]💝 Kawaii customer service[/]",
            "[dim]🌸 One sweet treat at a time![/]"
        ]

    def _build_order_display(self) -> list[str]:
        """Build display for the current order."""
        lines = [
            "[bold hot_pink]🌸 Current Order ✨[/]",
            ""
        ]

        # Customer info
        if self.customer_name:
            lines.append(f"[bold]👤 Customer:[/] {self.customer_name}")
            lines.append(f"[dim]📱 Type: {self.order_type.title()}[/]")
        else:
            lines.append("[dim]👤 Customer: Not specified[/]")

        lines.append("")

        # Order items
        lines.append("[bold]Order Items:[/]")
        for i, item in enumerate(self.selected_items):
            item_card = self._create_order_item_card(item, i)
            lines.extend(item_card)
            lines.append("")

        # Total
        total = self.calculate_total()
        lines.append(f"[bold hot_pink]💰 Total: ${total:.2f}[/]")

        # Action buttons info
        lines.append("")
        lines.append("[dim]🔸 [Enter] Submit Order[/]")
        lines.append("[dim]🔸 [Backspace] Remove Item[/]")
        lines.append("[dim]🔸 [C] Clear Order[/]")

        return lines

    def _create_order_item_card(self, item: OrderItem, index: int) -> list[str]:
        """Create a card for an order item.
        
        Args:
            item: Order item to display
            index: Index in the order
            
        Returns:
            List of strings representing the item card
        """
        # Item header with quantity and name
        name = item.menu_item.name
        quantity = item.quantity
        price = item.menu_item.price * quantity
        
        lines = [
            f"[light_pink]┌─{'-' * 40}─┐[/]",
            f"[light_pink]│[/] [{index + 1}] {quantity}× {name[:20]:<20} [bold]${price:.2f}[/] [light_pink]│[/]"
        ]

        # Toppings
        if item.toppings:
            toppings_icons = " ".join([t.name[:8] for t in item.toppings])
            lines.append(f"[light_pink]│[/]    [dim]Toppings: {toppings_icons:<32}[/] [light_pink]│[/]")

        # Customizations
        if item.customizations:
            for key, value in item.customizations.items():
                lines.append(f"[light_pink]│[/]    [dim]{key}: {value:<32}[/] [light_pink]│[/]")

        lines.append(f"[light_pink]└─{'-' * 40}─┘[/]")
        
        return lines

    def apply_loyalty_discount(self, discount_percent: float) -> None:
        """Apply loyalty program discount to current order.
        
        Args:
            discount_percent: Discount percentage to apply
        """
        # This would modify the total calculation
        # Implementation would depend on loyalty program rules
        pass

    def get_popular_suggestions(self) -> list[MenuItem]:
        """Get popular menu items for suggesting to customers.
        
        Returns:
            List of popular menu items
        """
        # This would typically come from sales data
        # For now, return empty list as placeholder
        return []

    def calculate_estimated_time(self) -> int:
        """Calculate estimated preparation time for current order.
        
        Returns:
            Estimated time in minutes
        """
        if not self.selected_items:
            return 0
        
        max_prep_time = max(item.menu_item.prep_time for item in self.selected_items)
        base_time = max_prep_time
        
        # Add time for complexity (number of toppings)
        total_toppings = sum(len(item.toppings) for item in self.selected_items)
        complexity_bonus = total_toppings * 0.5  # 30 seconds per topping
        
        return int(base_time + complexity_bonus)

    def validate_order(self) -> tuple[bool, list[str]]:
        """Validate the current order for completeness.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.selected_items:
            errors.append("No items in order")
        
        if not self.customer_name:
            errors.append("Customer name required")
        
        # Check for out of stock items
        for item in self.selected_items:
            if item.menu_item.is_out_of_stock:
                errors.append(f"{item.menu_item.name} is out of stock")
        
        return len(errors) == 0, errors

    def get_order_summary(self) -> dict:
        """Get summary of current order.
        
        Returns:
            Dictionary with order summary information
        """
        total = self.calculate_total()
        item_count = sum(item.quantity for item in self.selected_items)
        estimated_time = self.calculate_estimated_time()
        
        return {
            "customer": self.customer_name,
            "item_count": item_count,
            "order_type": self.order_type,
            "total": total,
            "estimated_time": estimated_time,
            "loyalty_applicable": self.current_customer is not None
        }
