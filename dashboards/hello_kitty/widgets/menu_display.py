"""Hello Kitty BubbleTea Shop TUI - Menu Display Widget."""

from __future__ import annotations

from textual.widgets import Static
from textual.containers import Vertical, Horizontal
from textual.css.query import NoMatches

from .models import MenuItem


class MenuDisplay(Static):
    """Beautiful menu display with Hello Kitty styled drink cards.
    
    Shows menu items with kawaii design elements including rounded borders,
    pastel colors, and cute icons. Features category filtering and
    visual indicators for popular items.
    """

    def __init__(self):
        """Initialize menu display widget."""
        super().__init__()
        self.menu_items: list[MenuItem] = []
        self.selected_category: str | None = None
        self.filtered_items: list[MenuItem] = []

    def update_menu(self, menu_items: list[MenuItem]) -> None:
        """Update the menu with new items.
        
        Args:
            menu_items: List of menu items to display
        """
        self.menu_items = menu_items
        self.filtered_items = menu_items
        self._render_menu()

    def filter_by_category(self, category: str | None) -> None:
        """Filter menu items by category.
        
        Args:
            category: Category to filter by, None for all items
        """
        self.selected_category = category
        if category:
            self.filtered_items = [
                item for item in self.menu_items 
                if item.category == category
            ]
        else:
            self.filtered_items = self.menu_items
        self._render_menu()

    def _render_menu(self) -> None:
        """Render the menu display with current filtered items."""
        if not self.filtered_items:
            self.update(
                "[light_pink]🌸 Menu is being refreshed... 🌸[/]\n"
                "[dim]Please check back in a moment![/]"
            )
            return

        # Category filter buttons
        categories = ["all", "milk-tea", "fruit-tea", "fresh-tea", "smoothies", "specialty"]
        category_buttons = []
        
        for category in categories:
            if category == "all":
                label = "✨ All Items"
            else:
                cat_name = category.replace("-", " ").title()
                label = f"{self._get_category_icon(category)} {cat_name}"
            
            if self.selected_category == category or (category == "all" and self.selected_category is None):
                category_buttons.append(f"[hot_pink]◈ {label}[/]")
            else:
                category_buttons.append(f"[dim]{label}[/]")

        category_bar = "  ".join(category_buttons)

        # Menu items display
        menu_lines = [category_bar, ""]
        
        # Group items by category for better organization
        items_by_category = {}
        for item in self.filtered_items:
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            items_by_category[item.category].append(item)

        for category, items in items_by_category.items():
            # Category header
            icon = self._get_category_icon(category)
            category_name = category.replace("-", " ").title()
            menu_lines.append(f"[bold hot_pink]{icon} {category_name}[/]")
            
            # Items in this category
            for item in items:
                card = self._create_drink_card(item)
                menu_lines.extend(card)
            
            menu_lines.append("")  # Spacing between categories

        # Update the widget
        self.update("\n".join(menu_lines))

    def _create_drink_card(self, item: MenuItem) -> list[str]:
        """Create a Hello Kitty styled drink card.
        
        Args:
            item: Menu item to create card for
            
        Returns:
            List of strings representing the card display
        """
        # Status indicators
        indicators = []
        if item.is_popular:
            indicators.append("[gold3]★ POPULAR[/]")
        if item.is_new:
            indicators.append("[bright_green]🆕 NEW[/]")
        if item.is_out_of_stock:
            indicators.append("[red]❌ OUT OF STOCK[/]")

        status_line = "  ".join(indicators) if indicators else ""

        # Toppings display
        if item.toppings:
            toppings_icons = " ".join([self._get_topping_icon(t) for t in item.toppings[:5]])
            toppings_line = f"[dim]Toppings: {toppings_icons}[/]"
        else:
            toppings_line = ""

        # Price and prep time
        price_line = f"[bold hot_pink]${item.price:.2f}[/]  [dim]⏱ {item.prep_time}min[/]"

        # Stock status coloring
        if item.is_out_of_stock:
            name_line = f"[strike red]🥤 {item.name}[/]"
            desc_line = f"[dim red]{item.description}[/]"
        else:
            name_line = f"🥤 [bold]{item.name}[/]"
            desc_line = f"[dim]{item.description}[/]"

        card = [
            f"[light_pink]╭─{'-' * 45}─╮[/]",
            f"[light_pink]│[/] {name_line:45} [light_pink]│[/]",
            f"[light_pink]│[/] {desc_line:45} [light_pink]│[/]",
        ]
        
        if status_line:
            card.append(f"[light_pink]│[/] {status_line:45} [light_pink]│[/]")
        
        if toppings_line:
            card.append(f"[light_pink]│[/] {toppings_line:45} [light_pink]│[/]")
        
        card.append(f"[light_pink]│[/] {price_line:45} [light_pink]│[/]")
        card.append(f"[light_pink]╰─{'-' * 45}─╯[/]")
        
        return card

    def _get_category_icon(self, category: str) -> str:
        """Get icon for menu category.
        
        Args:
            category: Category name
            
        Returns:
            Icon string for the category
        """
        icons = {
            "milk-tea": "🥛",
            "fruit-tea": "🍓", 
            "fresh-tea": "🍵",
            "smoothies": "🥤",
            "specialty": "✨",
            "all": "🌸"
        }
        return icons.get(category, "🍵")

    def _get_topping_icon(self, topping: str) -> str:
        """Get icon for topping.
        
        Args:
            topping: Topping name
            
        Returns:
            Icon string for the topping
        """
        topping_icons = {
            "tapioca": "●",  # Black pearls
            "golden pearls": "◎",  # Golden pearls
            "popping boba": "◉",  # Colored spheres
            "grass jelly": "▮",  # Dark cubes
            "aloe vera": "▯",  # Light blocks
            "pudding": "▢",  # Soft squares
            "red bean": "●",  # Reddish brown
            "taro balls": "◎",  # Purple
            "cheese foam": "~",  # Wavy cream
            "coconut jelly": "♦",  # Clear squares
            "ice": "❄️",  # Ice cubes
            "brown sugar": "🍯"  # Brown sugar syrup
        }
        
        topping_lower = topping.lower()
        for key, icon in topping_icons.items():
            if key in topping_lower:
                return icon
        
        return "✨"  # Default sparkle

    def highlight_item(self, item_id: str) -> None:
        """Highlight a specific menu item.
        
        Args:
            item_id: ID of item to highlight
        """
        # This could be used to highlight items when selected in POS
        # Implementation would depend on POS panel selection
        pass
