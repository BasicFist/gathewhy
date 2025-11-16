"""Order models for BubbleTea shop.

This module defines data structures for representing customer orders
with kawaii-inspired tracking and status management.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import List, Optional


class OrderStatus(Enum):
    """Order status with kawaii visual indicators.
    
    Each status includes visual hints for TUI rendering and emotional tone.
    """
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    @property
    def kawaii_emoji(self) -> str:
        """Kawaii emoji for this status.
        
        Returns:
            Emoji representing the emotional tone of the status
        """
        emojis = {
            self.PENDING: "⏳",
            self.CONFIRMED: "✨",
            self.PREPARING: "🥤",
            self.READY: "🎉",
            self.COMPLETED: "💕",
            self.CANCELLED: "😔"
        }
        return emojis.get(self, "❓")
    
    @property
    def color_hint(self) -> str:
        """Color hint for TUI styling.
        
        Returns:
            Color name or hex for terminal styling
        """
        colors = {
            self.PENDING: "#FFE4B5",
            self.CONFIRMED: "#98FB98", 
            self.PREPARING: "#87CEEB",
            self.READY: "#FFD700",
            self.COMPLETED: "#FF69B4",
            self.CANCELLED: "#D3D3D3"
        }
        return colors.get(self, "#FFFFFF")
    
    @property
    def is_terminal(self) -> bool:
        """Whether this is a terminal (final) state.
        
        Returns:
            True if order is completed or cancelled
        """
        return self in [self.COMPLETED, self.CANCELLED]


class PaymentMethod(Enum):
    """Payment methods with visual indicators."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_PAY = "mobile_pay"
    GIFT_CARD = "gift_card"
    
    @property
    def kawaii_icon(self) -> str:
        """Kawaii icon for this payment method.
        
        Returns:
            Emoji character for the payment method
        """
        icons = {
            self.CASH: "💰",
            self.CREDIT_CARD: "💳",
            self.DEBIT_CARD: "🏦",
            self.MOBILE_PAY: "📱",
            self.GIFT_CARD: "🎁"
        }
        return icons.get(self, "💳")


@dataclass
class OrderItem:
    """Individual item within an order.
    
    Attributes:
        menu_item_id: Reference to menu item
        menu_item_name: Human-readable name for display
        quantity: Number of this item ordered
        customizations: List of customization notes
        toppings: List of selected toppings
        unit_price: Price per item in cents
        total_price: Total price for this line item in cents
        special_instructions: Any special preparation instructions
    """
    
    menu_item_id: str
    menu_item_name: str
    quantity: int = 1
    customizations: List[str] = field(default_factory=list)
    toppings: List[str] = field(default_factory=list)  # topping names
    unit_price: int = 0  # in cents
    total_price: int = 0  # in cents
    special_instructions: str = ""
    
    def __post_init__(self):
        """Calculate total price if not provided."""
        if self.total_price == 0:
            self.total_price = self.unit_price * self.quantity
    
    @property
    def formatted_unit_price(self) -> str:
        """Formatted unit price for display.
        
        Returns:
            Price formatted as currency string
        """
        return f"${self.unit_price / 100:.2f}"
    
    @property
    def formatted_total_price(self) -> str:
        """Formatted total price for display.
        
        Returns:
            Price formatted as currency string
        """
        return f"${self.total_price / 100:.2f}"
    
    @property
    def kawaii_representation(self) -> str:
        """Kawaii representation for TUI display.
        
        Returns:
            String with emoji and item details
        """
        topping_str = ", ".join(self.toppings) if self.toppings else "no toppings"
        return f"🧋 {self.quantity}x {self.menu_item_name} ({topping_str})"
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)
    
    @classmethod
    def from_json(cls, data: dict) -> OrderItem:
        """Create instance from JSON-serializable dictionary."""
        return cls(**data)


@dataclass
class Order:
    """Complete customer order with kawaii tracking.
    
    Attributes:
        id: Unique order identifier
        customer_name: Customer name for personalization
        customer_phone: Customer phone number (optional)
        items: List of items in the order
        status: Current order status
        payment_method: Payment method used
        subtotal: Order subtotal in cents
        tax_amount: Tax amount in cents
        tip_amount: Tip amount in cents
        total_amount: Total order amount in cents
        order_time: Unix timestamp when order was placed
        estimated_completion_time: Estimated completion time
        actual_completion_time: Actual completion time (if completed)
        pickup_name: Name for pickup identification
        order_type: Type of order (dine_in, takeout, delivery)
        special_requests: Any special requests or notes
        assigned_barista: Barista assigned to this order
        priority_level: Priority level (1=normal, 2=high, 3=urgent)
        kawaii_progress: Visual progress indicator
        timestamp: Last updated timestamp
    """
    
    id: str
    customer_name: str
    customer_phone: Optional[str] = None
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    payment_method: PaymentMethod = PaymentMethod.CASH
    subtotal: int = 0  # in cents
    tax_amount: int = 0  # in cents
    tip_amount: int = 0  # in cents
    total_amount: int = 0  # in cents
    order_time: float = field(default_factory=time.time)
    estimated_completion_time: Optional[float] = None
    actual_completion_time: Optional[float] = None
    pickup_name: str = ""
    order_type: str = "takeout"  # dine_in, takeout, delivery
    special_requests: str = ""
    assigned_barista: str = ""
    priority_level: int = 1
    kawaii_progress: str = "⏳"
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Calculate totals and set default pickup name."""
        if not self.pickup_name:
            self.pickup_name = self.customer_name or f"Customer_{self.id[:6]}"
        
        if self.subtotal == 0:
            self.subtotal = sum(item.total_price for item in self.items)
        
        if self.total_amount == 0:
            self.total_amount = self.subtotal + self.tax_amount + self.tip_amount
        
        # Set estimated completion time if not provided
        if self.estimated_completion_time is None:
            total_prep_time = sum(120 for _ in self.items)  # 2 minutes per item
            self.estimated_completion_time = self.order_time + total_prep_time
        
        # Update kawaii progress
        self._update_kawaii_progress()
    
    def _update_kawaii_progress(self):
        """Update kawaii progress indicator based on status."""
        self.kawaii_progress = self.status.kawaii_emoji
    
    @property
    def formatted_subtotal(self) -> str:
        """Formatted subtotal for display.
        
        Returns:
            Price formatted as currency string
        """
        return f"${self.subtotal / 100:.2f}"
    
    @property
    def formatted_tax_amount(self) -> str:
        """Formatted tax amount for display.
        
        Returns:
            Price formatted as currency string
        """
        return f"${self.tax_amount / 100:.2f}"
    
    @property
    def formatted_tip_amount(self) -> str:
        """Formatted tip amount for display.
        
        Returns:
            Price formatted as currency string
        """
        return f"${self.tip_amount / 100:.2f}"
    
    @property
    def formatted_total_amount(self) -> str:
        """Formatted total amount for display.
        
        Returns:
            Price formatted as currency string
        """
        return f"${self.total_amount / 100:.2f}"
    
    @property
    def estimated_wait_minutes(self) -> int:
        """Estimated wait time in minutes.
        
        Returns:
            Minutes until estimated completion
        """
        if self.status == OrderStatus.COMPLETED:
            return 0
        if self.estimated_completion_time is None:
            return 0
        return max(0, int((self.estimated_completion_time - time.time()) / 60))
    
    @property
    def actual_duration_minutes(self) -> int:
        """Actual duration in minutes (if completed).
        
        Returns:
            Minutes from order to completion, or 0 if not completed
        """
        if self.status != OrderStatus.COMPLETED or self.actual_completion_time is None:
            return 0
        return int((self.actual_completion_time - self.order_time) / 60)
    
    @property
    def kawaii_status_display(self) -> str:
        """Kawaii status display for TUI.
        
        Returns:
            Status with emoji and color hint
        """
        return f"{self.status.kawaii_emoji} {self.status.value.title()}"
    
    @property
    def kawaii_summary(self) -> str:
        """Kawaii summary of the order.
        
        Returns:
            Short summary with emoji and key info
        """
        item_count = sum(item.quantity for item in self.items)
        return f"{self.kawaii_progress} Order #{self.id[:8]} - {item_count} items - {self.formatted_total_amount}"
    
    def update_status(self, new_status: OrderStatus, timestamp: Optional[float] = None):
        """Update order status and related fields.
        
        Args:
            new_status: New order status
            timestamp: Timestamp for the status change (defaults to now)
        """
        self.status = new_status
        self.timestamp = timestamp or time.time()
        
        # Set completion time if moving to completed
        if new_status == OrderStatus.COMPLETED:
            self.actual_completion_time = self.timestamp
        
        self._update_kawaii_progress()
    
    def add_item(self, item: OrderItem):
        """Add an item to the order.
        
        Args:
            item: OrderItem to add
        """
        self.items.append(item)
        self.subtotal += item.total_price
        self.total_amount = self.subtotal + self.tax_amount + self.tip_amount
        self.timestamp = time.time()
    
    def remove_item(self, item_index: int) -> bool:
        """Remove an item from the order.
        
        Args:
            item_index: Index of item to remove
            
        Returns:
            True if item was removed, False if index was invalid
        """
        if 0 <= item_index < len(self.items):
            removed_item = self.items.pop(item_index)
            self.subtotal -= removed_item.total_price
            self.total_amount = self.subtotal + self.tax_amount + self.tip_amount
            self.timestamp = time.time()
            return True
        return False
    
    def calculate_tip_percentage(self) -> float:
        """Calculate tip as percentage of subtotal.
        
        Returns:
            Tip percentage (0-100)
        """
        if self.subtotal == 0:
            return 0.0
        return (self.tip_amount / self.subtotal) * 100
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        data["payment_method"] = self.payment_method.value
        # Convert OrderItems
        data["items"] = [asdict(item) for item in self.items]
        return data
    
    @classmethod
    def from_json(cls, data: dict) -> Order:
        """Create instance from JSON-serializable dictionary."""
        # Convert enums
        data["status"] = OrderStatus(data["status"])
        data["payment_method"] = PaymentMethod(data["payment_method"])
        
        # Convert OrderItems
        if "items" in data:
            data["items"] = [OrderItem.from_json(item) for item in data["items"]]
            
        return cls(**data)