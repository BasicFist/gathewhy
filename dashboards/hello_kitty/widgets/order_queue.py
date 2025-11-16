"""Hello Kitty BubbleTea Shop TUI - Order Queue Widget."""

from __future__ import annotations

from datetime import datetime, timedelta
from textual.widgets import Static
from textual.containers import Vertical, Horizontal

from .models import Order, OrderItem


class OrderQueue(Static):
    """Order queue display with Hello Kitty styling.
    
    Shows current orders with status indicators, estimated ready times,
    and priority handling. Features kawaii design with rounded borders
    and pastel colors.
    """

    def __init__(self):
        """Initialize order queue widget."""
        super().__init__()
        self.orders: list[Order] = []
        self.filter_status: str = "all"  # all, pending, preparing, ready

    def update_orders(self, orders: list[Order]) -> None:
        """Update the order queue with new orders.
        
        Args:
            orders: List of current orders
        """
        self.orders = sorted(orders, key=lambda x: (
            x.priority == "rush",  # Rush orders first
            x.status == "pending",  # Pending first
            x.created_at  # Then by creation time
        ), reverse=True)
        self._render_queue()

    def add_order(self, order: Order) -> None:
        """Add a new order to the queue.
        
        Args:
            order: Order to add
        """
        self.orders.append(order)
        self.orders.sort(key=lambda x: (
            x.priority == "rush",
            x.status == "pending", 
            x.created_at
        ), reverse=True)
        self._render_queue()

    def update_order_status(self, order_id: str, new_status: str) -> None:
        """Update status of a specific order.
        
        Args:
            order_id: ID of order to update
            new_status: New status for the order
        """
        for order in self.orders:
            if order.id == order_id:
                order.status = new_status
                break
        self._render_queue()

    def filter_by_status(self, status: str) -> None:
        """Filter orders by status.
        
        Args:
            status: Status to filter by ('all', 'pending', 'preparing', 'ready')
        """
        self.filter_status = status
        self._render_queue()

    def _render_queue(self) -> None:
        """Render the order queue display."""
        if not self.orders:
            queue_lines = [
                "[light_green]🌸 Order Queue is Empty 🌸[/]",
                "[dim]✨ All orders completed! ✨[/]"
            ]
        else:
            queue_lines = self._build_queue_header()
            queue_lines.extend(self._build_order_list())
            queue_lines.extend(self._build_queue_footer())

        self.update("\n".join(queue_lines))

    def _build_queue_header(self) -> list[str]:
        """Build the queue header section."""
        # Filter buttons
        filter_buttons = []
        for status in ["all", "pending", "preparing", "ready"]:
            if status == "all":
                label = "✨ All Orders"
            elif status == "pending":
                label = "⏳ Pending"
            elif status == "preparing":
                label = "🥤 Preparing"
            else:
                label = "✨ Ready"

            if self.filter_status == status:
                filter_buttons.append(f"[bright_green]◈ {label}[/]")
            else:
                filter_buttons.append(f"[dim]{label}[/]")

        header = [
            "[bold bright_green]🌸 Hello Kitty Order Queue 🌸[/]",
            "  ".join(filter_buttons),
            ""
        ]
        return header

    def _build_order_list(self) -> list[str]:
        """Build the list of orders."""
        orders_to_show = self.orders
        if self.filter_status != "all":
            orders_to_show = [o for o in self.orders if o.status == self.filter_status]

        if not orders_to_show:
            return ["[dim]No orders with selected filter...[/]", ""]

        order_lines = []
        
        for order in orders_to_show[:10]:  # Show max 10 orders
            order_card = self._create_order_card(order)
            order_lines.extend(order_card)

        if len(self.orders) > 10:
            order_lines.append(f"[dim]... and {len(self.orders) - 10} more orders[/]")

        return order_lines

    def _build_queue_footer(self) -> list[str]:
        """Build the queue footer with summary."""
        if not self.orders:
            return []

        # Count orders by status
        pending_count = sum(1 for o in self.orders if o.status == "pending")
        preparing_count = sum(1 for o in self.orders if o.status == "preparing")
        ready_count = sum(1 for o in self.orders if o.status == "ready")
        
        # Find oldest pending order
        oldest_pending = None
        for order in self.orders:
            if order.status == "pending":
                oldest_pending = order
                break
        
        footer = [""]  # Empty line before footer
        
        if oldest_pending:
            wait_time = oldest_pending.order_duration_minutes
            wait_color = "red" if wait_time > 15 else "yellow" if wait_time > 10 else "green"
            footer.append(f"[bold dim]Oldest pending: {wait_time}min ago [as {wait_color}]({oldest_pending.customer_name})[/]")
        
        footer.append(f"[dim]Queue: {pending_count} pending, {preparing_count} preparing, {ready_count} ready[/]")
        return footer

    def _create_order_card(self, order: Order) -> list[str]:
        """Create a Hello Kitty styled order card.
        
        Args:
            order: Order to create card for
            
        Returns:
            List of strings representing the card display
        """
        # Status and priority indicators
        status_parts = [order.get_status_icon()]
        if order.priority == "rush":
            status_parts.append("[red]⚡[/]")
        if order.is_overdue:
            status_parts.append("[red]⏰[/]")

        status_line = "".join(status_parts)

        # Customer and order info
        customer_line = f"👤 [bold]{order.customer_name}[/]"
        order_id_line = f"#{order.id[:6].upper()}"

        # Time info
        now = datetime.now()
        time_ago = order.order_duration_minutes
        time_color = "red" if time_ago > 15 else "yellow" if time_ago > 10 else "green"
        time_line = f"[{time_color}]{time_ago}min ago[/]"

        # Items summary
        item_summaries = []
        for item in order.items[:3]:  # Show first 3 items
            qty = item.quantity
            name = item.menu_item.name
            if len(name) > 15:
                name = name[:12] + "..."
            item_summaries.append(f"{qty}×{name}")

        if len(order.items) > 3:
            item_summaries.append(f"+{len(order.items) - 3} more")

        items_line = " • ".join(item_summaries)

        # Build card
        card = [
            "[light_blue]┌─{border}─┐[/]".format(border="─" * 50),
            f"[light_blue]│[/] {status_line:2} {customer_line:20} {order_id_line:12} {time_line:12} [light_blue]│[/]",
            f"[light_blue]│[/] {items_line:48} [light_blue]│[/]"
        ]

        # Add toppings info if any
        all_toppings = []
        for item in order.items:
            for topping in item.toppings:
                all_toppings.append(topping.name)
        
        if all_toppings:
            toppings_icons = " ".join([self._get_topping_icon(t) for t in all_toppings[:8]])
            if len(all_toppings) > 8:
                toppings_icons += "..."
            card.append(f"[light_blue]│[/] [dim]Toppings: {toppings_icons:40}[/] [light_blue]│[/]")

        card.append("[light_blue]└─{border}─┘[/]".format(border="─" * 50))
        
        return card

    def _get_topping_icon(self, topping: str) -> str:
        """Get icon for topping.
        
        Args:
            topping: Topping name
            
        Returns:
            Icon string for the topping
        """
        topping_icons = {
            "tapioca": "●",
            "golden pearls": "◎",
            "popping boba": "◉",
            "grass jelly": "▮",
            "aloe vera": "▯",
            "pudding": "▢",
            "red bean": "●",
            "taro balls": "◎",
            "cheese foam": "~",
            "coconut jelly": "♦",
            "ice": "❄️",
            "brown sugar": "🍯"
        }
        
        topping_lower = topping.lower()
        for key, icon in topping_icons.items():
            if key in topping_lower:
                return icon
        
        return "✨"

    def mark_order_ready(self, order_id: str) -> None:
        """Mark an order as ready for pickup.
        
        Args:
            order_id: ID of order to mark ready
        """
        self.update_order_status(order_id, "ready")

    def complete_order(self, order_id: str) -> None:
        """Mark an order as completed.
        
        Args:
            order_id: ID of order to complete
        """
        self.update_order_status(order_id, "completed")

    def get_queue_summary(self) -> dict[str, int]:
        """Get summary of orders by status.
        
        Returns:
            Dictionary with status counts
        """
        summary = {"pending": 0, "preparing": 0, "ready": 0, "completed": 0}
        for order in self.orders:
            if order.status in summary:
                summary[order.status] += 1
        return summary
