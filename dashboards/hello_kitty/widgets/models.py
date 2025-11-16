"""Data models for Hello Kitty BubbleTea Shop TUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


# Menu and Items
@dataclass
class MenuItem:
    """Represents a bubble tea menu item."""
    id: str
    name: str
    category: Literal[
        "milk-tea", "fruit-tea", "fresh-tea", "smoothies", "specialty", "snacks"
    ]
    price: float
    description: str
    toppings: list[str]
    prep_time: int  # minutes
    is_popular: bool = False
    is_new: bool = False
    is_out_of_stock: bool = False
    
    def __post_init__(self):
        """Add category-specific styling info."""
        self.category_icons = {
            "milk-tea": "🥛",
            "fruit-tea": "🍓", 
            "fresh-tea": "🍵",
            "smoothies": "🥤",
            "specialty": "✨",
            "snacks": "🍪"
        }
        self.category_colors = {
            "milk-tea": "light_pink",
            "fruit-tea": "light_blue", 
            "fresh-tea": "light_green",
            "smoothies": "light_magenta",
            "specialty": "gold3",
            "snacks": "light_yellow"
        }


# Toppings
@dataclass
class Topping:
    """Replies a bubble tea topping."""
    id: str
    name: str
    price: float
    category: Literal["pearls", "jelly", "pudding", "fruit", "cream", "other"]
    
    def __post_init__(self):
        self.category_icons = {
            "pearls": "●",  # Tapioca pearls
            "jelly": "▮",  # Grass jelly
            "pudding": "▢",  # Pudding
            "fruit": "🍓",  # Fruit pieces
            "cream": "~",  # Cheese foam
            "other": "✨"
        }


# Orders
@dataclass
class OrderItem:
    """Represents an item in an order."""
    menu_item: MenuItem
    quantity: int
    toppings: list[Topping]
    customizations: dict[str, str]
    subtotal: float


@dataclass
class Order:
    """Represents a customer order."""
    id: str
    customer_name: str
    items: list[OrderItem]
    status: Literal["pending", "preparing", "ready", "completed", "cancelled"]
    created_at: datetime
    estimated_ready_time: Optional[datetime] = None
    total: float = 0.0
    order_type: Literal["dine-in", "takeaway", "delivery"] = "takeaway"
    priority: Literal["normal", "rush"] = "normal"
    
    def __post_init__(self):
        """Calculate order total and estimate ready time."""
        if not self.total:
            self.total = sum(
                (item.menu_item.price + sum(t.price for t in item.toppings)) * item.quantity
                for item in self.items
            )
        
        if not self.estimated_ready_time:
            max_prep_time = max(
                (item.menu_item.prep_time for item in self.items), default=5
            )
            self.estimated_ready_time = self.created_at.replace(
                minute=self.created_at.minute + max_prep_time
            )
    
    @property
    def is_overdue(self) -> bool:
        """Check if order is overdue."""
        return datetime.now() > self.estimated_ready_time and self.status in ["pending", "preparing"]
    
    @property
    def order_duration_minutes(self) -> int:
        """Get order duration in minutes."""
        return int((datetime.now() - self.created_at).total_seconds() / 60)
    
    def get_status_icon(self) -> str:
        """Get status icon for display."""
        icons = {
            "pending": "⏳",
            "preparing": "🥤",
            "ready": "✨",
            "completed": "✅",
            "cancelled": "❌"
        }
        return icons.get(self.status, "❓")


# Inventory
@dataclass
class InventoryItem:
    """Represents an inventory item."""
    id: str
    name: str
    category: Literal["tea-base", "milk", "syrup", "topping", "supplies"]
    current_stock: int
    max_capacity: int
    unit: str
    reorder_level: int
    cost_per_unit: float
    last_restocked: datetime
    expiry_date: Optional[datetime] = None
    supplier: Optional[str] = None
    
    @property
    def stock_percentage(self) -> float:
        """Get stock as percentage of capacity."""
        return (self.current_stock / self.max_capacity) * 100 if self.max_capacity > 0 else 0
    
    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below reorder level."""
        return self.current_stock <= self.reorder_level
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get days until expiry."""
        if not self.expiry_date:
            return None
        return (self.expiry_date - datetime.now()).days
    
    def get_stock_status(self) -> Literal["critical", "low", "normal", "full"]:
        """Get stock status category."""
        if self.current_stock == 0:
            return "critical"
        elif self.current_stock <= self.reorder_level:
            return "low"
        elif self.stock_percentage >= 90:
            return "full"
        else:
            return "normal"


# Sales Metrics
@dataclass
class SalesMetrics:
    """Daily sales metrics and statistics."""
    date: datetime
    total_orders: int
    total_revenue: float
    average_order_value: float
    popular_items: list[tuple[MenuItem, int]]  # (menu_item, count)
    peak_hours: list[int]  # hours of the day
    customer_count: int
    refund_count: int
    
    @property
    def profit_estimate(self) -> float:
        """Estimate profit (revenue * 0.3 for simplicity)."""
        return self.total_revenue * 0.3
    
    @property
    def refund_rate(self) -> float:
        """Calculate refund rate percentage."""
        if self.total_orders == 0:
            return 0.0
        return (self.refund_count / self.total_orders) * 100


# Customer
@dataclass
class Customer:
    """Represents a customer."""
    id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    favorite_drinks: list[str] = None
    loyalty_points: int = 0
    total_orders: int = 0
    
    def __post_init__(self):
        if self.favorite_drinks is None:
            self.favorite_drinks = []


# Store Settings
@dataclass
class StoreSettings:
    """Store configuration settings."""
    store_name: str = "Hello Kitty BubbleTea"
    opening_hours: dict[str, tuple[int, int]]  # day -> (open_hour, close_hour)
    default_prep_time: int = 5  # minutes
    loyalty_points_per_dollar: float = 1.0
    enable_loyalty_program: bool = True
    enable_online_orders: bool = True
    auto_accept_orders: bool = False
    max_order_queue: int = 20
    low_stock_threshold: float = 20.0  # percentage
    
    @property
    def is_open_now(self) -> bool:
        """Check if store is currently open."""
        now = datetime.now()
        weekday = now.strftime("%A").lower()
        current_hour = now.hour
        
        if weekday in self.opening_hours:
            open_hour, close_hour = self.opening_hours[weekday]
            return open_hour <= current_hour < close_hour
        return False
