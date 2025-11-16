"""
Hello Kitty BubbleTea TUI - Menu Screen
======================================

Menu management screen for viewing and managing bubble tea offerings
with kawaii Hello Kitty theming.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, Label, Button, DataTable, Input
from textual.reactive import reactive
from textual.message import Message

from ..core.shop_manager import ShopManager, Drink
from ..core.theme import HelloKittyTheme


class DrinkCard(Static):
    """A kawaii card displaying drink information."""
    
    def __init__(self, drink: Drink, theme: HelloKittyTheme):
        super().__init__()
        self.drink = drink
        self.theme = theme
    
    def compose(self) -> ComposeResult:
        """Compose the drink card."""
        with Container(classes="drink-card"):
            # Drink header with icon and name
            with Container(classes="drink-header"):
                yield Label(f"{self.drink.icon} {self.drink.name}", classes="drink-name")
                yield Label(f"${self.drink.base_price:.2f}", classes="drink-price")
            
            # Drink description
            yield Label(self.drink.description, classes="drink-description")
            
            # Ingredients
            if self.drink.ingredients:
                ingredients_text = "🥄 " + ", ".join(self.drink.ingredients[:3])
                yield Label(ingredients_text, classes="drink-ingredients")
            
            # Status and actions
            with Horizontal(classes="drink-actions"):
                status_text = "✅ Available" if self.drink.is_available else "❌ Unavailable"
                yield Label(status_text, classes=f"availability-{self.drink.is_available}")
                
                if self.drink.is_seasonal:
                    yield Label("🌸 Seasonal", classes="seasonal-badge")
                
                if self.drink.allergens:
                    allergens_text = "⚠️ " + ", ".join(self.drink.allergens)
                    yield Label(allergens_text, classes="allergens")


class MenuScreen(Static):
    """Menu management screen for Hello Kitty BubbleTea."""
    
    def __init__(self, shop_manager: ShopManager, theme: HelloKittyTheme):
        super().__init__()
        self.shop_manager = shop_manager
        self.theme = theme
        self.selected_category = "all"
    
    def compose(self) -> ComposeResult:
        """Compose the menu screen."""
        # Header
        with Container(classes="menu-header"):
            yield Label("🍵 Hello Kitty BubbleTea Menu 🍵", classes="menu-title")
            yield Label("Browse our kawaii collection of bubble tea creations!", classes="menu-subtitle")
        
        # Category filters
        with Container(classes="category-filters"):
            yield Label("Filter by Category:", classes="filter-label")
            with Horizontal(classes="category-buttons"):
                yield Button("🌟 All Drinks", id="filter-all", classes="category-button")
                yield Button("🥛 Milk Teas", id="filter-milk_tea", classes="category-button")
                yield Button("🍓 Fruit Teas", id="filter-fruit_tea", classes="category-button")
                yield Button("🌸 Seasonal", id="filter-seasonal", classes="category-button")
        
        # Menu grid
        with Grid(classes="menu-grid", id="menu-grid"):
            drinks = self._get_filtered_drinks()
            for drink in drinks:
                yield DrinkCard(drink, self.theme)
        
        # Action panel
        with Container(classes="menu-actions"):
            yield Label("Menu Management", classes="actions-title")
            with Horizontal(classes="actions-row"):
                yield Button("➕ Add Drink", id="add-drink", classes="action-button primary")
                yield Button("✏️ Edit Selected", id="edit-drink", classes="action-button")
                yield Button("🗑️ Remove Drink", id="remove-drink", classes="action-button danger")
                yield Button("🔄 Refresh", id="refresh-menu", classes="action-button")
    
    def _get_filtered_drinks(self) -> list[Drink]:
        """Get drinks filtered by the selected category."""
        if self.selected_category == "all":
            return self.shop_manager.get_available_drinks()
        elif self.selected_category == "seasonal":
            return [drink for drink in self.shop_manager.get_available_drinks() if drink.is_seasonal]
        else:
            return self.shop_manager.get_drinks_by_category(self.selected_category)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "filter-all":
            self.selected_category = "all"
            self._refresh_menu_grid()
        elif button_id == "filter-milk_tea":
            self.selected_category = "milk_tea"
            self._refresh_menu_grid()
        elif button_id == "filter-fruit_tea":
            self.selected_category = "fruit_tea"
            self._refresh_menu_grid()
        elif button_id == "filter-seasonal":
            self.selected_category = "seasonal"
            self._refresh_menu_grid()
        elif button_id == "add-drink":
            self._show_add_drink_dialog()
        elif button_id == "edit-drink":
            self._show_edit_drink_dialog()
        elif button_id == "remove-drink":
            self._show_remove_drink_dialog()
        elif button_id == "refresh-menu":
            self._refresh_menu_grid()
    
    def _refresh_menu_grid(self) -> None:
        """Refresh the menu grid with current filters."""
        grid = self.query_one("#menu-grid", Grid)
        grid.remove_children()
        
        drinks = self._get_filtered_drinks()
        for drink in drinks:
            grid.mount(DrinkCard(drink, self.theme))
    
    def _show_add_drink_dialog(self) -> None:
        """Show dialog to add a new drink."""
        # Placeholder for add drink functionality
        self.notify("🆕 Add New Drink feature coming soon! ✨")
    
    def _show_edit_drink_dialog(self) -> None:
        """Show dialog to edit a selected drink."""
        # Placeholder for edit drink functionality  
        self.notify("✏️ Edit Drink feature coming soon! ✨")
    
    def _show_remove_drink_dialog(self) -> None:
        """Show confirmation for removing a drink."""
        # Placeholder for remove drink functionality
        self.notify("🗑️ Remove Drink feature coming soon! ✨")


# CSS styling for menu screen
MENU_CSS = """
/* Hello Kitty Menu Styles */
.menu-header {
    align: center;
    background: $pastel-pink;
    border: solid $hk-primary;
    margin: 1;
    padding: 1;
}

.menu-title {
    color: $hk-text;
    text-align: center;
    text-style: bold;
    font-size: 1.5;
    margin-bottom: 1;
}

.menu-subtitle {
    color: $hk-secondary;
    text-align: center;
    font-size: 1.0;
}

.category-filters {
    background: $pastel-sky;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    height: 4;
}

.filter-label {
    color: $hk-text;
    text-style: bold;
    margin-bottom: 1;
}

.category-buttons {
    spacing: 2;
}

.category-button {
    background: $hk-primary;
    color: $hk-bg;
    border: rounded;
    width: 12;
    height: 2;
}

.category-button:hover, .category-button:pressed {
    background: $hk-secondary;
}

.menu-grid {
    height: 1fr;
    margin: 1;
    grid-gutter: 2;
    grid-columns: 3;
    grid-rows: auto;
}

.drink-card {
    background: $pastel-butter;
    border: rounded $hk-contour;
    padding: 1;
    margin: 1;
    height: auto;
}

.drink-header {
    height: 3;
    background: $pastel-pink;
    border: solid $hk-primary;
    margin-bottom: 1;
    padding: 1;
    align: center middle;
}

.drink-name {
    color: $hk-text;
    text-style: bold;
    font-size: 1.2;
    width: 1fr;
}

.drink-price {
    color: $hk-primary;
    text-style: bold;
    font-size: 1.0;
}

.drink-description {
    color: $hk-text;
    font-size: 0.9;
    margin-bottom: 1;
}

.drink-ingredients {
    color: $hk-secondary;
    font-size: 0.8;
    margin-bottom: 1;
}

.drink-actions {
    spacing: 2;
    align: right middle;
}

.availability-true {
    color: $matcha-green;
    font-size: 0.8;
}

.availability-false {
    color: $thai-orange;
    font-size: 0.8;
}

.seasonal-badge {
    color: $hk-accent;
    background: $pastel-lilac;
    border: rounded;
    font-size: 0.7;
    padding: 0 1;
}

.allergens {
    color: $hk-accent;
    font-size: 0.7;
    text-style: italic;
}

.menu-actions {
    background: $pastel-lilac;
    border: solid $hk-contour;
    margin: 1;
    padding: 1;
    height: 5;
}

.actions-title {
    color: $hk-text;
    text-style: bold;
    margin-bottom: 1;
}

.actions-row {
    align: center middle;
    spacing: 2;
}

.action-button {
    background: $hk-contour;
    color: $hk-bg;
    border: rounded;
    width: 15;
    height: 2;
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
"""