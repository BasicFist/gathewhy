"""Inventory models for BubbleTea shop.

This module defines data structures for representing inventory items,
stock levels, and supply management with kawaii-inspired tracking.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import List, Optional


class SupplyType(Enum):
    """Types of supplies with kawaii visual indicators.
    
    Each supply type includes visual hints for TUI rendering.
    """
    TEA_BASE = "tea_base"
    MILK = "milk"
    SYRUP = "syrup"
    TOPPING = "topping"
    CUPS = "cups"
    LIDS = "lids"
    STRAWS = "straws"
    CLEANING = "cleaning"
    EQUIPMENT = "equipment"
    
    @property
    def kawaii_icon(self) -> str:
        """Kawaii emoji for this supply type.
        
        Returns:
            Emoji representing the supply type
        """
        icons = {
            self.TEA_BASE: "🍵",
            self.MILK: "🥛",
            self.SYRUP: "🍯",
            self.TOPPING: "🧋",
            self.CUPS: "🥤",
            self.LIDS: "🔄",
            self.STRAWS: "🥤",
            self.CLEANING: "🧼",
            self.EQUIPMENT: "⚙️"
        }
        return icons.get(self, "📦")
    
    @property
    def storage_temperature(self) -> str:
        """Recommended storage temperature.
        
        Returns:
            Temperature range for storage
        """
        temps = {
            self.TEA_BASE: "Room temp (20-22°C)",
            self.MILK: "Refrigerated (2-4°C)",
            self.SYRUP: "Room temp (20-22°C)",
            self.TOPPING: "Refrigerated (2-4°C)",
            self.CUPS: "Room temp (20-22°C)",
            self.LIDS: "Room temp (20-22°C)",
            self.STRAWS: "Room temp (20-22°C)",
            self.CLEANING: "Room temp (20-22°C)",
            self.EQUIPMENT: "Room temp (20-22°C)"
        }
        return temps.get(self, "Room temp (20-22°C)")


class StockLevel(Enum):
    """Stock level indicators with kawaii emotion.
    
    Each level includes visual and emotional representation.
    """
    OUT_OF_STOCK = "out_of_stock"  # 😱
    CRITICALLY_LOW = "critically_low"  # 😰
    LOW = "low"  # 😟
    MODERATE = "moderate"  # 😐
    GOOD = "good"  # 🙂
    EXCELLENT = "excellent"  # 😍
    
    @property
    def kawaii_emoji(self) -> str:
        """Kawaii emoji representing the emotional state.
        
        Returns:
            Emoji showing the emotional tone of this stock level
        """
        emojis = {
            self.OUT_OF_STOCK: "😱",
            self.CRITICALLY_LOW: "😰", 
            self.LOW: "😟",
            self.MODERATE: "😐",
            self.GOOD: "😊",
            self.EXCELLENT: "😍"
        }
        return emojis.get(self, "❓")
    
    @property
    def color_hint(self) -> str:
        """Color hint for TUI styling.
        
        Returns:
            Color name or hex for terminal styling
        """
        colors = {
            self.OUT_OF_STOCK: "#FF0000",
            self.CRITICALLY_LOW: "#FF4500",
            self.LOW: "#FFA500", 
            self.MODERATE: "#FFD700",
            self.GOOD: "#32CD32",
            self.EXCELLENT: "#00FF00"
        }
        return colors.get(self, "#FFFFFF")
    
    @property
    def urgency_level(self) -> int:
        """Urgency level for restocking (1=low, 5=critical).
        
        Returns:
            Urgency rating from 1 to 5
        """
        urgency = {
            self.OUT_OF_STOCK: 5,
            self.CRITICALLY_LOW: 5,
            self.LOW: 4,
            self.MODERATE: 3,
            self.GOOD: 2,
            self.EXCELLENT: 1
        }
        return urgency.get(self, 3)


@dataclass
class InventoryItem:
    """Individual inventory item with kawaii tracking.
    
    Attributes:
        id: Unique inventory item identifier
        name: Human-readable item name
        supply_type: Type of supply
        current_stock: Current quantity in stock
        unit_of_measurement: Unit (pieces, kg, liters, etc.)
        minimum_stock_level: Minimum acceptable stock level
        maximum_stock_level: Maximum stock capacity
        reorder_point: Stock level that triggers reordering
        cost_per_unit: Cost per unit in cents
        supplier: Supplier name
        expiration_date: Expiration date (if applicable)
        storage_requirements: Storage requirements description
        last_restocked: Unix timestamp of last restock
        expiry_warning_days: Days before expiration to show warning
        is_seasonal: Whether this is a seasonal item
        location_in_store: Physical location description
        popularity_rank: Popularity ranking (1=most popular)
        kawaii_status: Current status with emoji
        timestamp: Last updated timestamp
    """
    
    id: str
    name: str
    supply_type: SupplyType
    current_stock: float = 0.0
    unit_of_measurement: str = "pieces"
    minimum_stock_level: float = 10.0
    maximum_stock_level: float = 1000.0
    reorder_point: float = 20.0
    cost_per_unit: int = 0  # in cents
    supplier: str = ""
    expiration_date: Optional[float] = None
    storage_requirements: str = ""
    last_restocked: Optional[float] = None
    expiry_warning_days: int = 7
    is_seasonal: bool = False
    location_in_store: str = ""
    popularity_rank: int = 50
    kawaii_status: str = "📦"
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Update kawaii status after initialization."""
        self._update_kawaii_status()
    
    @property
    def stock_level_enum(self) -> StockLevel:
        """Current stock level as enum.
        
        Returns:
            StockLevel enum representing current status
        """
        percentage = (self.current_stock / self.maximum_stock_level) * 100 if self.maximum_stock_level > 0 else 0
        
        if self.current_stock <= 0:
            return StockLevel.OUT_OF_STOCK
        elif self.current_stock <= self.minimum_stock_level * 0.5:
            return StockLevel.CRITICALLY_LOW
        elif self.current_stock <= self.minimum_stock_level:
            return StockLevel.LOW
        elif percentage <= 30:
            return StockLevel.MODERATE
        elif percentage <= 70:
            return StockLevel.GOOD
        else:
            return StockLevel.EXCELLENT
    
    def _update_kawaii_status(self):
        """Update kawaii status based on current stock level."""
        level = self.stock_level_enum
        self.kawaii_status = f"{level.kawaii_emoji} {self.name}"
    
    @property
    def stock_percentage(self) -> float:
        """Current stock as percentage of maximum.
        
        Returns:
            Percentage of maximum stock (0-100)
        """
        if self.maximum_stock_level <= 0:
            return 0.0
        return min(100.0, (self.current_stock / self.maximum_stock_level) * 100)
    
    @property
    def needs_restocking(self) -> bool:
        """Whether item needs restocking.
        
        Returns:
            True if stock is at or below reorder point
        """
        return self.current_stock <= self.reorder_point
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Days until expiration (if applicable).
        
        Returns:
            Number of days until expiration, None if no expiration
        """
        if self.expiration_date is None:
            return None
        days = (self.expiration_date - time.time()) / (24 * 60 * 60)
        return max(0, int(days))
    
    @property
    def is_expired(self) -> bool:
        """Whether item has expired.
        
        Returns:
            True if expiration date has passed
        """
        if self.expiration_date is None:
            return False
        return time.time() > self.expiration_date
    
    @property
    def is_expiring_soon(self) -> bool:
        """Whether item is expiring within warning period.
        
        Returns:
            True if within warning days of expiration
        """
        days = self.days_until_expiry
        return days is not None and days <= self.expiry_warning_days
    
    @property
    def restock_amount_needed(self) -> float:
        """Recommended restock amount.
        
        Returns:
            Suggested quantity to restock to reach maximum
        """
        return max(0, self.maximum_stock_level - self.current_stock)
    
    @property
    def estimated_restock_cost(self) -> int:
        """Estimated cost to restock to maximum.
        
        Returns:
            Cost in cents to restock to maximum level
        """
        return int(self.restock_amount_needed * self.cost_per_unit)
    
    @property
    def kawaii_stock_display(self) -> str:
        """Kawaii stock display for TUI.
        
        Returns:
            String with emoji, stock level, and percentage
        """
        level = self.stock_level_enum
        percentage = self.stock_percentage
        return f"{level.kawaii_emoji} {self.name}: {self.current_stock:.1f}{self.unit_of_measurement} ({percentage:.0f}%)"
    
    def update_stock(self, new_stock: float, timestamp: Optional[float] = None):
        """Update stock level.
        
        Args:
            new_stock: New stock quantity
            timestamp: Timestamp for the update (defaults to now)
        """
        self.current_stock = max(0.0, new_stock)
        self.timestamp = timestamp or time.time()
        self._update_kawaii_status()
    
    def use_stock(self, amount: float, timestamp: Optional[float] = None) -> bool:
        """Use stock and check if successful.
        
        Args:
            amount: Amount to use
            timestamp: Timestamp for the usage (defaults to now)
            
        Returns:
            True if stock was available and used, False if insufficient
        """
        if self.current_stock >= amount:
            self.current_stock -= amount
            self.timestamp = timestamp or time.time()
            self._update_kawaii_status()
            return True
        return False
    
    def add_stock(self, amount: float, timestamp: Optional[float] = None):
        """Add stock to inventory.
        
        Args:
            amount: Amount to add
            timestamp: Timestamp for the addition (defaults to now)
        """
        self.current_stock += amount
        self.last_restocked = timestamp or time.time()
        self.timestamp = self.last_restocked
        self._update_kawaii_status()
    
    def mark_expired(self, timestamp: Optional[float] = None):
        """Mark item as expired and remove from usable stock.
        
        Args:
            timestamp: Timestamp for expiration (defaults to now)
        """
        self.current_stock = 0.0
        self.expiration_date = timestamp or time.time()
        self.timestamp = self.expiration_date
        self._update_kawaii_status()
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        data["supply_type"] = self.supply_type.value
        return data
    
    @classmethod
    def from_json(cls, data: dict) -> InventoryItem:
        """Create instance from JSON-serializable dictionary."""
        data["supply_type"] = SupplyType(data["supply_type"])
        return cls(**data)


@dataclass
class InventoryMetrics:
    """Aggregated inventory metrics with kawaii insights.
    
    Attributes:
        total_items: Total number of distinct inventory items
        items_below_reorder: Number of items below reorder point
        items_out_of_stock: Number of items completely out of stock
        items_expired: Number of expired items
        total_inventory_value: Total value of inventory in cents
        critical_items: List of critical (low stock) items
        expiring_soon_items: List of items expiring within warning period
        top_consumed_today: Most consumed items today
        supplier_performance: Performance metrics by supplier
        timestamp: When metrics were collected
    """
    
    total_items: int
    items_below_reorder: int
    items_out_of_stock: int
    items_expired: int
    total_inventory_value: int  # in cents
    critical_items: List[InventoryItem] = field(default_factory=list)
    expiring_soon_items: List[InventoryItem] = field(default_factory=list)
    top_consumed_today: List[tuple[str, float]] = field(default_factory=list)  # (item_name, amount)
    supplier_performance: dict[str, dict] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    @property
    def kawaii_summary(self) -> str:
        """Kawaii summary of inventory health.
        
        Returns:
            Summary with emoji and key metrics
        """
        if self.items_out_of_stock > 0:
            emoji = "😱"
        elif self.items_below_reorder > 0:
            emoji = "😰"
        else:
            emoji = "😊"
        
        return f"{emoji} Inventory: {self.total_items} items, {self.items_below_reorder} need restock, ${self.total_inventory_value / 100:.2f} value"
    
    @property
    def health_score(self) -> int:
        """Overall inventory health score (0-100).
        
        Returns:
            Health score where 100 is perfect
        """
        if self.total_items == 0:
            return 100
        
        penalty = 0
        penalty += self.items_out_of_stock * 20  # Heavy penalty for out of stock
        penalty += self.items_below_reorder * 10  # Penalty for low stock
        penalty += self.items_expired * 15  # Penalty for expired items
        
        return max(0, 100 - penalty)
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        # Convert InventoryItems to their JSON representations
        data["critical_items"] = [item.to_json() for item in self.critical_items]
        data["expiring_soon_items"] = [item.to_json() for item in self.expiring_soon_items]
        return data