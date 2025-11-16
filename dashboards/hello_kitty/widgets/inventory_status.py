"""Hello Kitty BubbleTea Shop TUI - Inventory Status Widget."""

from __future__ import annotations

from datetime import datetime, timedelta
from textual.widgets import Static

from .models import InventoryItem


class InventoryStatus(Static):
    """Inventory status display with Hello Kitty styling.
    
    Shows current stock levels, alerts for low stock items,
    expiry dates, and supplier information. Features kawaii design
    with cute icons and color-coded status indicators.
    """

    def __init__(self):
        """Initialize inventory status widget."""
        super().__init__()
        self.inventory_items: list[InventoryItem] = []
        self.show_low_stock_only: bool = False

    def update_inventory(self, inventory: list[InventoryItem]) -> None:
        """Update inventory with new stock levels.
        
        Args:
            inventory: List of inventory items with current stock
        """
        self.inventory_items = inventory
        self._render_inventory()

    def filter_low_stock(self, show_only_low: bool = True) -> None:
        """Filter to show only low stock items.
        
        Args:
            show_only_low: Whether to filter to low stock only
        """
        self.show_low_stock_only = show_only_low
        self._render_inventory()

    def mark_as_restocked(self, item_id: str) -> None:
        """Mark an item as restocked.
        
        Args:
            item_id: ID of item to mark as restocked
        """
        for item in self.inventory_items:
            if item.id == item_id:
                item.last_restocked = datetime.now()
                break
        self._render_inventory()

    def update_stock_level(self, item_id: str, new_stock: int) -> None:
        """Update stock level for a specific item.
        
        Args:
            item_id: ID of item to update
            new_stock: New stock level
        """
        for item in self.inventory_items:
            if item.id == item_id:
                item.current_stock = new_stock
                break
        self._render_inventory()

    def _render_inventory(self) -> None:
        """Render the inventory display."""
        if not self.inventory_items:
            inventory_lines = [
                "[light_green]🌸 Inventory Loading... 🌸[/]",
                "[dim]✨ Checking stock levels ✨[/]"
            ]
        else:
            inventory_lines = self._build_inventory_header()
            inventory_lines.extend(self._build_inventory_list())
            inventory_lines.extend(self._build_inventory_footer())

        self.update("\n".join(inventory_lines))

    def _build_inventory_header(self) -> list[str]:
        """Build the inventory header section."""
        # Filter toggle button
        if self.show_low_stock_only:
            filter_text = "[bright_green]◈ Low Stock Only[/]  [dim](Click to show all)[/]"
        else:
            filter_text = "[dim]Show All  [/]  [bright_green]◈ Low Stock Only[/]"

        # Count items by status
        low_stock_count = sum(1 for item in self.inventory_items if item.is_low_stock)
        critical_stock_count = sum(1 for item in self.inventory_items if item.current_stock == 0)
        expiring_soon_count = sum(1 for item in self.inventory_items 
                                if item.days_until_expiry is not None and item.days_until_expiry <= 7)

        header = [
            "[bold light_green]🌸 Hello Kitty Inventory 🌸[/]",
            filter_text,
            ""
        ]

        if low_stock_count > 0 or critical_stock_count > 0 or expiring_soon_count > 0:
            alerts = []
            if critical_stock_count > 0:
                alerts.append(f"[red]❌ {critical_stock_count} Out of Stock[/]")
            if low_stock_count > 0:
                alerts.append(f"[yellow]⚠️ {low_stock_count} Low Stock[/]")
            if expiring_soon_count > 0:
                alerts.append(f"[orange_red1]⏰ {expiring_soon_count} Expiring Soon[/]")
            
            header.append("  ".join(alerts))
            header.append("")

        return header

    def _build_inventory_list(self) -> list[str]:
        """Build the list of inventory items."""
        items_to_show = self.inventory_items
        if self.show_low_stock_only:
            items_to_show = [item for item in self.inventory_items if item.is_low_stock]

        if not items_to_show:
            if self.show_low_stock_only:
                return ["[dim]🌸 All items are well stocked! ✨[/]", ""]
            else:
                return ["[dim]Loading inventory...[/]", ""]

        items_to_show.sort(key=lambda x: (
            x.current_stock == 0,  # Out of stock first
            x.get_stock_status() == "low",  # Low stock next
            x.name.lower()
        ))

        inventory_lines = []
        
        for item in items_to_show:
            item_card = self._create_inventory_card(item)
            inventory_lines.extend(item_card)
            inventory_lines.append("")  # Spacing between items

        return inventory_lines

    def _build_inventory_footer(self) -> list[str]:
        """Build the inventory footer with summary."""
        if not self.inventory_items:
            return []

        # Calculate totals
        total_items = len(self.inventory_items)
        total_value = sum(item.current_stock * item.cost_per_unit for item in self.inventory_items)
        
        # Category breakdown
        categories = {}
        for item in self.inventory_items:
            cat = item.category.replace("-", " ").title()
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        footer = [
            f"[dim]Total Items: {total_items} | Inventory Value: ${total_value:.2f}[/]",
            f"[dim]Categories: {', '.join(f'{cat} ({count})' for cat, count in categories.items())}[/]"
        ]

        return footer

    def _create_inventory_card(self, item: InventoryItem) -> list[str]:
        """Create a Hello Kitty styled inventory card.
        
        Args:
            item: Inventory item to create card for
            
        Returns:
            List of strings representing the card display
        """
        # Status indicators
        status_icons = []
        status_color = "white"
        
        if item.current_stock == 0:
            status_icons.append("[red]❌[/]")
            status_color = "red"
        elif item.is_low_stock:
            status_icons.append("[yellow]⚠️[/]")
            status_color = "yellow"
        else:
            status_icons.append("[green]✅[/]")
            status_color = "green"

        # Expiry warning
        if item.days_until_expiry is not None:
            if item.days_until_expiry <= 0:
                status_icons.append("[red]⏰[/]")  # Expired
            elif item.days_until_expiry <= 3:
                status_icons.append("[orange_red1]⏰[/]")  # Expiring soon
            elif item.days_until_expiry <= 7:
                status_icons.append("[yellow]⏰[/]")  # Expiring this week

        status_line = " ".join(status_icons) if status_icons else ""

        # Stock level bar
        stock_percentage = item.stock_percentage
        if stock_percentage >= 80:
            bar_color = "green"
        elif stock_percentage >= 50:
            bar_color = "yellow"
        elif stock_percentage >= 25:
            bar_color = "orange_red1"
        else:
            bar_color = "red"

        bar_filled = int(stock_percentage / 10)  # 10-character bar
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        stock_bar = f"[{bar_color}]{bar}[/]"

        # Item name and category
        category_icon = self._get_category_icon(item.category)
        name_line = f"{category_icon} [bold]{item.name}[/] ({item.category.replace('-', ' ').title()})"

        # Stock info
        stock_line = f"[{status_color}]Current: {item.current_stock}/{item.max_capacity} {item.unit}[/]"
        percentage_line = f"[{status_color}]{stock_percentage:.0f}%[/]"
        
        # Days since restocked
        days_since_restocked = (datetime.now() - item.last_restocked).days
        if days_since_restocked == 0:
            restock_info = "[dim]Restocked today[/]"
        elif days_since_restocked == 1:
            restock_info = "[dim]Restocked yesterday[/]"
        else:
            restock_info = f"[dim]Restocked {days_since_restocked} days ago[/]"

        # Expiry info
        if item.days_until_expiry is not None:
            if item.days_until_expiry <= 0:
                expiry_info = "[red]EXPIRED[/]"
            elif item.days_until_expiry == 1:
                expiry_info = "[orange_red1]Expires tomorrow[/]"
            elif item.days_until_expiry <= 7:
                expiry_info = f"[yellow]Expires in {item.days_until_expiry} days[/]"
            else:
                days = item.days_until_expiry
                expiry_info = f"[dim]Expires in {days} days[/]"
        else:
            expiry_info = "[dim]No expiry date[/]"

        # Build card
        card = [
            "[light_blue]┌─{border}─┐[/]".format(border="─" * 60),
            f"[light_blue]│[/] {status_line:8} {name_line:48} [light_blue]│[/]",
            f"[light_blue]│[/] {stock_line:25} {percentage_line:8} {stock_bar:12} [light_blue]│[/]",
            f"[light_blue]│[/] {restock_info:25} {expiry_info:30} [light_blue]│[/]"
        ]

        # Add supplier info if available
        if item.supplier:
            supplier_line = f"[dim]Supplier: {item.supplier}[/]"
            card.append(f"[light_blue]│[/] {supplier_line:60} [light_blue]│[/]")

        card.append("[light_blue]└─{border}─┘[/]".format(border="─" * 60))
        
        return card

    def _get_category_icon(self, category: str) -> str:
        """Get icon for inventory category.
        
        Args:
            category: Category name
            
        Returns:
            Icon string for the category
        """
        icons = {
            "tea-base": "🍵",
            "milk": "🥛",
            "syrup": "🍯",
            "topping": "●",
            "supplies": "📦"
        }
        return icons.get(category, "📦")

    def get_inventory_alerts(self) -> dict[str, list[InventoryItem]]:
        """Get inventory alerts organized by type.
        
        Returns:
            Dictionary with different types of alerts
        """
        alerts = {
            "out_of_stock": [],
            "low_stock": [],
            "expiring_soon": [],
            "expired": []
        }
        
        for item in self.inventory_items:
            if item.current_stock == 0:
                alerts["out_of_stock"].append(item)
            elif item.is_low_stock:
                alerts["low_stock"].append(item)
            
            if item.days_until_expiry is not None:
                if item.days_until_expiry <= 0:
                    alerts["expired"].append(item)
                elif item.days_until_expiry <= 7:
                    alerts["expiring_soon"].append(item)
        
        return alerts

    def calculate_restock_urgency(self, item: InventoryItem) -> int:
        """Calculate restock urgency score (1-10, 10 = most urgent).
        
        Args:
            item: Inventory item to calculate urgency for
            
        Returns:
            Urgency score from 1 to 10
        """
        score = 0
        
        # Base score from stock level
        if item.current_stock == 0:
            score += 10
        elif item.stock_percentage < 10:
            score += 8
        elif item.stock_percentage < 25:
            score += 6
        elif item.stock_percentage < 50:
            score += 3
        
        # Expiry adjustment
        if item.days_until_expiry is not None:
            if item.days_until_expiry <= 0:
                score += 10
            elif item.days_until_expiry <= 3:
                score += 7
            elif item.days_until_expiry <= 7:
                score += 4
        
        # Days since restocked (if very old, might need freshness check)
        days_old = (datetime.now() - item.last_restocked).days
        if days_old > 30:
            score += 2
        
        return min(score, 10)  # Cap at 10

    def get_restock_priority_list(self) -> list[tuple[InventoryItem, int]]:
        """Get list of items that need restocking, sorted by urgency.
        
        Returns:
            List of (item, urgency_score) tuples sorted by urgency
        """
        priority_items = []
        for item in self.inventory_items:
            urgency = self.calculate_restock_urgency(item)
            if urgency >= 5:  # Only include items that need attention
                priority_items.append((item, urgency))
        
        # Sort by urgency score (highest first)
        priority_items.sort(key=lambda x: x[1], reverse=True)
        return priority_items
