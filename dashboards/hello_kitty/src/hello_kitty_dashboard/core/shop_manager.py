"""
Hello Kitty BubbleTea TUI - Shop Manager
========================================

Core business logic for managing the bubble tea shop operations,
including orders, inventory, menu, and customer management.
"""

import asyncio
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import yaml


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DrinkSize(Enum):
    """Bubble tea size options."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class Drink:
    """Represents a bubble tea drink."""
    id: str
    name: str
    description: str
    base_price: float
    category: str
    color_token: str
    icon: str
    ingredients: List[str]
    allergens: List[str]
    is_seasonal: bool = False
    is_available: bool = True
    

@dataclass
class Topping:
    """Represents a bubble tea topping."""
    id: str
    name: str
    price: float
    icon: str
    category: str
    calories: int
    allergens: List[str]
    is_available: bool = True


@dataclass
class OrderItem:
    """Represents an item in an order."""
    drink: Drink
    size: DrinkSize
    toppings: List[Topping]
    quantity: int
    customizations: Dict[str, Any]
    
    @property
    def total_price(self) -> float:
        """Calculate total price for this order item."""
        base_price = self.drink.base_price
        topping_price = sum(topping.price for topping in self.toppings)
        size_multiplier = {"small": 0.9, "medium": 1.0, "large": 1.2}[self.size.value]
        return (base_price + topping_price) * size_multiplier * self.quantity


@dataclass
class Customer:
    """Represents a customer."""
    id: str
    name: str
    phone: str
    email: Optional[str]
    favorite_drinks: List[str]
    loyalty_points: int
    total_orders: int
    created_at: datetime
    last_order_date: Optional[datetime]
    is_vip: bool = False


@dataclass
class Order:
    """Represents a complete order."""
    id: str
    customer: Optional[Customer]
    items: List[OrderItem]
    status: OrderStatus
    total_amount: float
    created_at: datetime
    estimated_completion: Optional[datetime]
    notes: str
    is_pickup: bool = True


REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_PROVIDERS_PATH = REPO_ROOT / "config" / "providers.yaml"


class ShopManager:
    """Main shop management class."""
    
    def __init__(self, settings):
        self.settings = settings
        self.orders: Dict[str, Order] = {}
        self.customers: Dict[str, Customer] = {}
        self.drinks: Dict[str, Drink] = {}
        self.toppings: Dict[str, Topping] = {}
        self.inventory: Dict[str, int] = {}
        self._load_sample_data()
        if getattr(self.settings, "enable_litellm_adapter", False):
            self._load_litellm_data()
    
    async def initialize(self) -> None:
        """Initialize the shop manager with data."""
        await self.load_data()
        self._ensure_sample_data()
    
    def _load_sample_data(self) -> None:
        """Load sample data for demonstration."""
        # Sample drinks
        sample_drinks = [
            Drink(
                id="taro_milk_tea",
                name="Taro Milk Tea",
                description="Creamy taro with milk",
                base_price=4.50,
                category="milk_tea",
                color_token="taro_purple",
                icon="🟣",
                ingredients=["taro powder", "milk", "tea", "sugar"],
                allergens=["milk"]
            ),
            Drink(
                id="matcha_milk_tea", 
                name="Matcha Milk Tea",
                description="Premium Japanese matcha",
                base_price=5.00,
                category="milk_tea",
                color_token="matcha_green",
                icon="🟢",
                ingredients=["matcha powder", "milk", "tea", "honey"],
                allergens=["milk"]
            ),
            Drink(
                id="thai_tea",
                name="Thai Tea",
                description="Traditional spiced Thai tea",
                base_price=4.25,
                category="milk_tea",
                color_token="thai_orange", 
                icon="🟠",
                ingredients=["thai tea", "condensed milk", "sugar"],
                allergens=["milk"]
            ),
            Drink(
                id="brown_sugar_milk",
                name="Brown Sugar Milk Tea",
                description="Caramelized brown sugar goodness",
                base_price=5.25,
                category="milk_tea",
                color_token="brown_sugar",
                icon="🟤",
                ingredients=["brown sugar", "milk", "tea"],
                allergens=["milk"]
            ),
            Drink(
                id="strawberry_green_tea",
                name="Strawberry Green Tea",
                description="Fresh strawberries with green tea",
                base_price=4.75,
                category="fruit_tea",
                color_token="pastel_pink",
                icon="🍓",
                ingredients=["strawberry", "green tea", "honey"],
                allergens=[]
            ),
        ]
        
        # Sample toppings
        sample_toppings = [
            Topping(
                id="tapioca_pearls",
                name="Tapioca Pearls",
                price=0.75,
                icon="●",
                category="pearls",
                calories=120,
                allergens=[]
            ),
            Topping(
                id="popping_boba_strawberry",
                name="Strawberry Popping Boba",
                price=1.00,
                icon="◉",
                category="boba",
                calories=80,
                allergens=[]
            ),
            Topping(
                id="cheese_foam",
                name="Cheese Foam",
                price=1.25,
                icon="~",
                category="foam",
                calories=100,
                allergens=["dairy"]
            ),
            Topping(
                id="grass_jelly",
                name="Grass Jelly",
                price=0.50,
                icon="▮",
                category="jelly",
                calories=40,
                allergens=[]
            ),
        ]
        
        # Load into dictionaries
        for drink in sample_drinks:
            self.drinks[drink.id] = drink
        
        for topping in sample_toppings:
            self.toppings[topping.id] = topping
        
        # Sample inventory
        self.inventory = {
            "tapioca_pearls": 1000,
            "popping_boba_strawberry": 500,
            "cheese_foam": 200,
            "grass_jelly": 300,
            "taro_powder": 50,
            "matcha_powder": 30,
            "thai_tea": 100,
            "brown_sugar": 75,
            "strawberry": 200,
            "green_tea": 80
        }
    
    def _ensure_sample_data(self) -> None:
        """Ensure we have sample data for demonstration."""
        if not self.drinks:
            self._load_sample_data()
        
        # Create sample customers
        if not self.customers:
            sample_customer = Customer(
                id=str(uuid.uuid4()),
                name="Hello Kitty",
                phone="555-KITTEN",
                email="hello@kitty.com",
                favorite_drinks=["taro_milk_tea", "matcha_milk_tea"],
                loyalty_points=250,
                total_orders=15,
                created_at=datetime.now() - timedelta(days=30),
                last_order_date=datetime.now() - timedelta(days=1),
                is_vip=True
            )
            self.customers[sample_customer.id] = sample_customer
    
    async def load_data(self) -> None:
        """Load data from disk."""
        data_dir = self.settings.data_dir or Path.home() / ".hello_kitty_dashboard"
        data_dir.mkdir(exist_ok=True)
        
        # Load orders
        orders_file = data_dir / "orders.json"
        if orders_file.exists():
            try:
                with open(orders_file, 'r') as f:
                    orders_data = json.load(f)
                # Convert back to Order objects
                # (Implementation details omitted for brevity)
            except Exception as e:
                print(f"⚠️  Could not load orders: {e}")
    
    async def save_data(self) -> None:
        """Save data to disk."""
        data_dir = self.settings.data_dir or Path.home() / ".hello_kitty_dashboard"
        data_dir.mkdir(exist_ok=True)
        
        # Save orders
        orders_file = data_dir / "orders.json"
        orders_data = {order_id: asdict(order) for order_id, order in self.orders.items()}
        try:
            with open(orders_file, 'w') as f:
                json.dump(orders_data, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Could not save orders: {e}")
    
    # Order management methods
    async def create_order(self, customer: Optional[Customer], items: List[OrderItem], 
                          is_pickup: bool = True, notes: str = "") -> Order:
        """Create a new order."""
        order_id = str(uuid.uuid4())
        total_amount = sum(item.total_price for item in items)
        created_at = datetime.now()
        estimated_completion = created_at + timedelta(minutes=15)
        
        order = Order(
            id=order_id,
            customer=customer,
            items=items,
            status=OrderStatus.PENDING,
            total_amount=total_amount,
            created_at=created_at,
            estimated_completion=estimated_completion,
            notes=notes,
            is_pickup=is_pickup
        )
        
        self.orders[order_id] = order
        
        # Update customer loyalty points
        if customer:
            customer.loyalty_points += int(total_amount)
            customer.total_orders += 1
            customer.last_order_date = created_at
            if customer.total_orders >= 10:
                customer.is_vip = True
        
        # Update inventory
        await self._deduct_inventory(items)
        
        return order

    def _load_litellm_data(self) -> None:
        """Load LiteLLM provider data into the kawaii domain."""
        config_path = self.settings.providers_config or DEFAULT_PROVIDERS_PATH
        if not config_path.exists():
            return

        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except Exception as exc:
            if getattr(self.settings, "debug", False):
                print(f"⚠️  LiteLLM adapter failed to read {config_path}: {exc}")
            return

        providers = data.get("providers", {})
        if not providers:
            return

        color_cycle = [
            "pastel_pink",
            "pastel_mint",
            "pastel_sky",
            "pastel_lilac",
            "pastel_butter",
            "matcha_green",
            "taro_purple",
        ]

        for idx, (provider_key, provider_cfg) in enumerate(providers.items()):
            models = provider_cfg.get("models", [])
            if not models:
                continue

            color_token = color_cycle[idx % len(color_cycle)]
            provider_icon = self._pick_provider_icon(provider_cfg.get("type"))

            for model in models:
                drink = self._create_drink_from_model(
                    provider_key, provider_cfg, model, color_token, provider_icon
                )
                self.drinks[drink.id] = drink
                self.inventory.setdefault(drink.id, random.randint(40, 180))

            self._create_provider_orders(provider_key, provider_cfg, models)

    def _create_drink_from_model(
        self,
        provider_key: str,
        provider_cfg: Dict[str, Any],
        model_cfg: Dict[str, Any],
        color_token: str,
        provider_icon: str,
    ) -> Drink:
        """Create a kawaii drink representation from a LiteLLM model."""
        model_name = model_cfg.get("name", "unknown-model")
        size_hint = str(model_cfg.get("size", "")).upper()
        base_price = self._derive_price_from_size(size_hint)

        description = model_cfg.get("description") or provider_cfg.get("description") or ""
        category = provider_cfg.get("type", "provider")

        return Drink(
            id=f"{provider_key}:{model_name}",
            name=model_name,
            description=description[:120],
            base_price=base_price,
            category=category,
            color_token=color_token,
            icon=provider_icon,
            ingredients=model_cfg.get("tags", [provider_key]),
            allergens=[],
            is_seasonal=model_cfg.get("status") == "beta",
            is_available=provider_cfg.get("status", "active") == "active",
        )

    def _derive_price_from_size(self, size_hint: str) -> float:
        """Map model size to a cute price for display."""
        if size_hint.endswith("B"):
            try:
                value = float(size_hint[:-1] or "0")
                return round(4.0 + value * 0.25, 2)
            except ValueError:
                pass
        return round(4.5 + random.random(), 2)

    def _pick_provider_icon(self, provider_type: Optional[str]) -> str:
        """Choose an icon based on provider type."""
        mapping = {
            "ollama": "🧋",
            "llama_cpp": "🦙",
            "vllm": "⚡",
            "openai": "🌐",
            "anthropic": "✨",
        }
        return mapping.get(provider_type or "", "🤖")

    def _create_provider_orders(
        self, provider_key: str, provider_cfg: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> None:
        """Generate synthetic orders to power the dashboard metrics."""
        if not models:
            return

        drink_id = f"{provider_key}:{models[0].get('name', 'model')}"
        drink = self.drinks.get(drink_id)
        if not drink:
            return

        status_map = {
            "active": OrderStatus.IN_PROGRESS,
            "degraded": OrderStatus.PENDING,
            "maintenance": OrderStatus.PENDING,
            "inactive": OrderStatus.CANCELLED,
        }
        provider_status = provider_cfg.get("status", "active").lower()
        live_status = status_map.get(provider_status, OrderStatus.PENDING)

        # Active order representing current provider status
        active_order = Order(
            id=f"litellm_{provider_key}_active",
            customer=None,
            items=[
                OrderItem(
                    drink=drink,
                    size=DrinkSize.MEDIUM,
                    toppings=[],
                    quantity=1,
                    customizations={"provider": provider_key},
                )
            ],
            status=live_status,
            total_amount=drink.base_price,
            created_at=datetime.now() - timedelta(minutes=random.randint(1, 30)),
            estimated_completion=datetime.now() + timedelta(minutes=random.randint(5, 20)),
            notes=provider_cfg.get("description", ""),
            is_pickup=True,
        )
        self.orders[active_order.id] = active_order

        # Completed order to feed revenue metrics
        completed_order = Order(
            id=f"litellm_{provider_key}_completed",
            customer=None,
            items=active_order.items,
            status=OrderStatus.COMPLETED,
            total_amount=drink.base_price * random.randint(2, 5),
            created_at=datetime.now() - timedelta(hours=random.randint(1, 4)),
            estimated_completion=datetime.now() - timedelta(hours=1),
            notes="Auto-generated from LiteLLM snapshot",
            is_pickup=True,
        )
        self.orders[completed_order.id] = completed_order
    
    async def update_order_status(self, order_id: str, new_status: OrderStatus) -> bool:
        """Update order status."""
        if order_id in self.orders:
            self.orders[order_id].status = new_status
            await self.save_data()
            return True
        return False
    
    async def _deduct_inventory(self, items: List[OrderItem]) -> None:
        """Deduct ingredients from inventory based on order items."""
        for item in items:
            # Deduct base ingredients
            for ingredient in item.drink.ingredients:
                if ingredient in self.inventory:
                    self.inventory[ingredient] -= item.quantity
            
            # Deduct toppings
            for topping in item.toppings:
                topping_key = f"{topping.category}_{topping.id}"
                if topping_key in self.inventory:
                    self.inventory[topping_key] -= item.quantity
    
    # Menu management methods
    def get_drink_by_id(self, drink_id: str) -> Optional[Drink]:
        """Get a drink by ID."""
        return self.drinks.get(drink_id)
    
    def get_topping_by_id(self, topping_id: str) -> Optional[Topping]:
        """Get a topping by ID."""
        return self.toppings.get(topping_id)
    
    def get_available_drinks(self) -> List[Drink]:
        """Get all available drinks."""
        return [drink for drink in self.drinks.values() if drink.is_available]
    
    def get_available_toppings(self) -> List[Topping]:
        """Get all available toppings."""
        return [topping for topping in self.toppings.values() if topping.is_available]
    
    def get_drinks_by_category(self, category: str) -> List[Drink]:
        """Get drinks by category."""
        return [drink for drink in self.drinks.values() 
                if drink.category == category and drink.is_available]
    
    # Customer management methods
    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get a customer by ID."""
        return self.customers.get(customer_id)
    
    def get_all_customers(self) -> List[Customer]:
        """Get all customers."""
        return list(self.customers.values())
    
    def search_customers(self, query: str) -> List[Customer]:
        """Search customers by name or phone."""
        query_lower = query.lower()
        return [customer for customer in self.customers.values()
                if query_lower in customer.name.lower() or query_lower in customer.phone.lower()]
    
    # Analytics and reporting methods
    def get_daily_sales_summary(self, date: datetime = None) -> Dict[str, Any]:
        """Get daily sales summary."""
        if date is None:
            date = datetime.now().date()
        
        daily_orders = [
            order for order in self.orders.values()
            if order.created_at.date() == date and order.status == OrderStatus.COMPLETED
        ]
        
        total_revenue = sum(order.total_amount for order in daily_orders)
        total_orders = len(daily_orders)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Popular drinks
        drink_counts = {}
        for order in daily_orders:
            for item in order.items:
                drink_name = item.drink.name
                drink_counts[drink_name] = drink_counts.get(drink_name, 0) + item.quantity
        
        popular_drinks = sorted(drink_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "date": date.isoformat(),
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": average_order_value,
            "popular_drinks": popular_drinks
        }
    
    def get_inventory_status(self) -> Dict[str, Any]:
        """Get current inventory status."""
        low_stock_threshold = 50
        low_stock_items = [
            {"item": ingredient, "quantity": qty}
            for ingredient, qty in self.inventory.items()
            if qty < low_stock_threshold
        ]
        
        total_items = sum(self.inventory.values())
        
        return {
            "total_items": total_items,
            "low_stock_count": len(low_stock_items),
            "low_stock_items": low_stock_items,
            "last_updated": datetime.now().isoformat()
        }
