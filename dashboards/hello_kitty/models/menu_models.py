"""Menu item models for BubbleTea shop.

This module defines data structures for representing menu items including
drinks, ingredients, and toppings with kawaii-inspired visual properties.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import List, Optional


class DrinkCategory(Enum):
    """Categories of bubble tea drinks with kawaii styling.
    
    Each category includes visual styling hints for TUI rendering.
    """
    MILK_TEA = "milk_tea"
    FRUIT_TEA = "fruit_tea"
    MATCHA = "matcha"
    TARO = "taro"
    THAI_TEA = "thai_tea"
    BROWN_SUGAR = "brown_sugar"
    FRESH_TEA = "fresh_tea"
    SMOOTHIE = "smoothie"
    
    @property
    def kawaii_icon(self) -> str:
        """Kawaii-style emoji/icon for this category.
        
        Returns:
            Emoji character representing the drink category
        """
        icons = {
            self.MILK_TEA: "🥛",
            self.FRUIT_TEA: "🍓",
            self.MATCHA: "🍵",
            self.TARO: "🟣",
            self.THAI_TEA: "🟠",
            self.BROWN_SUGAR: "🟤",
            self.FRESH_TEA: "🌿",
            self.SMOOTHIE: "🥤"
        }
        return icons.get(self, "🧋")
    
    @property
    def color_hint(self) -> str:
        """Color hint for TUI styling.
        
        Returns:
            Color name or hex for terminal styling
        """
        colors = {
            self.MILK_TEA: "#F5F5DC",
            self.FRUIT_TEA: "#FFB6C1", 
            self.MATCHA: "#90EE90",
            self.TARO: "#DDA0DD",
            self.THAI_TEA: "#FFA500",
            self.BROWN_SUGAR: "#8B4513",
            self.FRESH_TEA: "#98FB98",
            self.SMOOTHIE: "#FF69B4"
        }
        return colors.get(self, "#FFFFFF")


@dataclass
class Ingredient:
    """Base ingredient for menu items.
    
    Attributes:
        name: Ingredient name
        category: Type of ingredient (tea_base, milk, syrup, etc.)
        cost_per_unit: Cost per unit in cents
        allergens: List of allergen warnings
        is_vegetarian: Whether ingredient is vegetarian
        is_vegan: Whether ingredient is vegan
        is_gluten_free: Whether ingredient is gluten free
    """
    
    name: str
    category: str
    cost_per_unit: int  # in cents
    allergens: List[str] = field(default_factory=list)
    is_vegetarian: bool = True
    is_vegan: bool = False
    is_gluten_free: bool = True
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)
    
    @classmethod
    def from_json(cls, data: dict) -> Ingredient:
        """Create instance from JSON-serializable dictionary."""
        return cls(**data)


@dataclass 
class Topping:
    """Bubble tea toppings with visual and textural properties.
    
    Attributes:
        name: Topping name
        kawaii_symbol: Unicode symbol representing the topping texture
        category: Type of topping (pearls, jellies, etc.)
        cost: Additional cost for this topping
        calories_per_serving: Calories per serving
        texture_description: Description of texture and mouthfeel
        prep_time_seconds: Time to prepare topping in seconds
    """
    
    name: str
    kawaii_symbol: str
    category: str
    cost: int  # additional cost in cents
    calories_per_serving: int
    texture_description: str = ""
    prep_time_seconds: int = 0
    
    @property
    def visual_representation(self) -> str:
        """Kawaii visual representation for TUI.
        
        Returns:
            Symbol with descriptive text for terminal display
        """
        return f"{self.kawaii_symbol} {self.name}"
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)
    
    @classmethod
    def from_json(cls, data: dict) -> Topping:
        """Create instance from JSON-serializable dictionary."""
        return cls(**data)


@dataclass
class MenuItem:
    """Complete menu item representing a drink.
    
    Attributes:
        id: Unique menu item identifier
        name: Human-readable drink name
        category: Drink category for kawaii styling
        base_price: Base price in cents
        ingredients: List of ingredients required
        available_toppings: List of available toppings for this drink
        prep_time_seconds: Preparation time in seconds
        is_seasonal: Whether this is a seasonal special
        description: Detailed description of the drink
        serving_size_ml: Volume in milliliters
        caffeine_content_mg: Caffeine content in milligrams
        popularity_score: Popularity rating (1-10)
        is_available: Whether currently available
        kawaii_visual: Pre-rendered visual for TUI display
        timestamp: When this menu item was last updated
    """
    
    id: str
    name: str
    category: DrinkCategory
    base_price: int  # in cents
    ingredients: List[Ingredient] = field(default_factory=list)
    available_toppings: List[Topping] = field(default_factory=list)
    prep_time_seconds: int = 120
    is_seasonal: bool = False
    description: str = ""
    serving_size_ml: int = 500
    caffeine_content_mg: int = 0
    popularity_score: int = 5
    is_available: bool = True
    kawaii_visual: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Generate kawaii visual representation after initialization."""
        if not self.kawaii_visual:
            icon = self.category.kawaii_icon
            color = self.category.color_hint
            self.kawaii_visual = f"{icon} {self.name} [{color}]"
    
    @property
    def formatted_price(self) -> str:
        """Formatted price for display.
        
        Returns:
            Price formatted as currency string
        """
        return f"${self.base_price / 100:.2f}"
    
    @property 
    def total_cost(self) -> int:
        """Total ingredient cost in cents.
        
        Returns:
            Sum of all ingredient costs
        """
        return sum(ingredient.cost_per_unit for ingredient in self.ingredients)
    
    @property
    def profit_margin(self) -> float:
        """Profit margin as percentage.
        
        Returns:
            Profit margin percentage (0-100)
        """
        if self.total_cost == 0:
            return 0.0
        return ((self.base_price - self.total_cost) / self.base_price) * 100
    
    @property
    def allergen_warnings(self) -> List[str]:
        """List of allergen warnings for this drink.
        
        Returns:
            Combined list of all ingredient allergens
        """
        warnings = []
        for ingredient in self.ingredients:
            warnings.extend(ingredient.allergens)
        return list(set(warnings))  # Remove duplicates
    
    def calculate_price_with_toppings(self, topping_ids: List[str]) -> int:
        """Calculate total price including selected toppings.
        
        Args:
            topping_ids: List of topping IDs to include
            
        Returns:
            Total price in cents
        """
        total = self.base_price
        topping_map = {t.name: t for t in self.available_toppings}
        
        for topping_id in topping_ids:
            if topping_id in topping_map:
                total += topping_map[topping_id].cost
                
        return total
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        data["category"] = self.category.value
        return data
    
    @classmethod 
    def from_json(cls, data: dict) -> MenuItem:
        """Create instance from JSON-serializable dictionary."""
        # Convert category enum back
        data["category"] = DrinkCategory(data["category"])
        
        # Convert ingredients and toppings
        if "ingredients" in data:
            data["ingredients"] = [Ingredient.from_json(ing) for ing in data["ingredients"]]
        if "available_toppings" in data:
            data["available_toppings"] = [Topping.from_json(t) for t in data["available_toppings"]]
            
        return cls(**data)