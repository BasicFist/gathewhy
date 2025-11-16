# Hello Kitty BubbleTea TUI - Data Models

This module contains kawaii-inspired data models for the BubbleTea shop TUI dashboard, designed with patterns adapted from gathewhy's ServiceMetrics and GPUOverview structures.

## Overview

The data models provide comprehensive representations of all aspects of a bubble tea shop operation, with kawaii (cute) visual elements for terminal UI rendering.

## Model Structure

### Menu Models (`menu_models.py`)

**Core Classes:**
- `MenuItem` - Complete drink representation with pricing, ingredients, and kawaii visuals
- `Ingredient` - Base ingredients with allergen information and dietary flags
- `Topping` - Bubble tea toppings with Unicode symbols and texture descriptions
- `DrinkCategory` - Enum with kawaii emojis and color hints for UI styling

**Key Features:**
- Kawaii visual representations for terminal display
- Profit margin calculations
- Allergen tracking and dietary accommodations
- Price calculations with custom toppings
- Seasonal item support

### Order Models (`order_models.py`)

**Core Classes:**
- `Order` - Complete customer order with kawaii status tracking
- `OrderItem` - Individual items within orders with customization support
- `OrderStatus` - Enum with emotional emojis and color hints
- `PaymentMethod` - Enum with kawaii icons for payment types

**Key Features:**
- Kawaii status indicators with emotional emojis
- Real-time progress tracking
- Estimated wait time calculations
- Order customization and special instructions
- Performance metrics (preparation time, etc.)

### Inventory Models (`inventory_models.py`)

**Core Classes:**
- `InventoryItem` - Individual inventory tracking with kawaii stock levels
- `InventoryMetrics` - Aggregated inventory analytics
- `StockLevel` - Enum with emotional states and urgency levels
- `SupplyType` - Enum with kawaii icons and storage requirements

**Key Features:**
- Emotional stock level indicators
- Expiration date tracking and warnings
- Restock recommendations with cost estimates
- Supplier performance analysis
- Waste tracking and turnover rates

### Staff Models (`staff_models.py`)

**Core Classes:**
- `Employee` - Individual staff member with personality traits
- `Shift` - Work shift with kawaii scheduling information
- `StaffMetrics` - Aggregated staff performance analytics
- `StaffRole` - Enum with kawaii icons and responsibility levels

**Key Features:**
- Kawaii personality and mood tracking
- Performance score management
- Skill and certification tracking
- Shift management with status indicators
- Training needs assessment

### Analytics Models (`analytics_models.py`)

**Core Classes:**
- `SalesMetrics` - Sales performance with kawaii insights
- `InventoryMetrics` - Inventory analytics and health scores
- `StaffMetrics` - Staff performance and efficiency metrics
- `DailyReport` - Comprehensive business report with overall mood

**Key Features:**
- Kawaii performance indicators
- Business health scoring
- Trend analysis and forecasting
- Executive summaries with emotional states
- Recommendation engines

## Usage Examples

### Creating a Menu Item

```python
from models import MenuItem, Ingredient, Topping, DrinkCategory

# Create ingredients
tea_base = Ingredient(
    name="Black Tea",
    category="tea_base",
    cost_per_unit=50  # $0.50
)

milk = Ingredient(
    name="Whole Milk",
    category="milk", 
    cost_per_unit=30,
    allergens=["dairy"]
)

# Create toppings
tapioca = Topping(
    name="Tapioca Pearls",
    kawaii_symbol="●",
    category="pearls",
    cost=75,
    calories_per_serving=140
)

# Create menu item
milk_tea = MenuItem(
    id="milk_tea_001",
    name="Classic Milk Tea",
    category=DrinkCategory.MILK_TEA,
    base_price=450,  # $4.50
    ingredients=[tea_base, milk],
    available_toppings=[tapioca],
    caffeine_content_mg=95
)
```

### Processing an Order

```python
from models import Order, OrderItem, OrderStatus, PaymentMethod

# Create order items
item = OrderItem(
    menu_item_id="milk_tea_001",
    menu_item_name="Classic Milk Tea",
    quantity=2,
    toppings=["Tapioca Pearls"],
    unit_price=525,  # $5.25 with topping
    total_price=1050  # $10.50 for 2
)

# Create order
order = Order(
    id="ORD_001",
    customer_name="Hello Kitty",
    items=[item],
    payment_method=PaymentMethod.CREDIT_CARD
)

# Update status
order.update_status(OrderStatus.PREPARING)
```

### Inventory Management

```python
from models import InventoryItem, SupplyType

# Add inventory item
tea_inventory = InventoryItem(
    id="tea_black_001",
    name="Black Tea Bags",
    supply_type=SupplyType.TEA_BASE,
    current_stock=50.0,
    unit_of_measurement="bags",
    cost_per_unit=50,  # $0.50 per bag
    reorder_point=20.0,
    maximum_stock_level=200.0
)

# Use inventory
if tea_inventory.use_stock(5.0):
    print("Stock used successfully")
else:
    print("Insufficient stock!")

# Check status
print(tea_inventory.kawaii_stock_display)
# Output: 😐 Black Tea Bags: 45.0bags (22%)
```

### Staff Scheduling

```python
from models import Employee, Shift, StaffRole

# Create employee
employee = Employee(
    id="EMP_001",
    name="Mimi San",
    role=StaffRole.BARISTA,
    hire_date=time.time() - (180 * 24 * 60 * 60),  # 180 days ago
    hourly_wage=1500,  # $15.00/hour
    skills=["Milk Tea", "Matcha", "Customer Service"]
)

# Create shift
shift = Shift(
    id="SHIFT_001",
    employee_id="EMP_001", 
    employee_name="Mimi San",
    start_time=morning_start,
    end_time=evening_end,
    station_assignment="bar"
)

shift.start_shift()
# Later...
shift.complete_shift()
```

### Analytics and Reporting

```python
from models import SalesMetrics, DailyReport

# Create sales metrics
sales = SalesMetrics(
    date=start_of_day,
    total_revenue=250000,  # $2,500
    total_orders=85,
    hourly_sales={10: 15000, 11: 25000, 12: 45000}
)

# Add hourly sales
sales.add_hourly_sale(13, 35000)
sales.add_payment_method("credit_card")

# Create daily report
report = DailyReport(
    date=start_of_day,
    sales_metrics=sales,
    inventory_metrics=inventory_metrics,
    staff_metrics=staff_metrics
)

report.add_achievement("Beat daily sales record!")
report.add_challenge("Ran out of taro topping")

print(report.kawaii_executive_summary)
# Output: 😊 Daily Report: $2,500.00 revenue, 85/100 health score
```

## Kawaii Design Principles

All models incorporate kawaii design principles:

1. **Emotional States**: Status indicators use emotional emojis
2. **Color Hints**: Each enum provides color hints for UI styling
3. **Visual Representations**: Objects include kawaii_* properties for TUI display
4. **Soft Messaging**: Language and feedback maintain friendly, positive tone
5. **Accessibility**: Visual elements are supplementary to textual information

## JSON Serialization

All models support JSON serialization:

```python
# Convert to JSON
json_data = menu_item.to_json()

# Restore from JSON
restored_item = MenuItem.from_json(json_data)
```

## Integration with TUI

Models are designed for easy integration with terminal UI frameworks:

- Kawaii visual properties provide emoji and color hints
- Status indicators change based on data state
- Formatted display properties for currency, time, etc.
- Summary properties for dashboard widgets

## Patterns Adapted from Gathewhy

These models follow the successful patterns from gathewhy's dashboard:

- **Comprehensive Documentation**: Detailed docstrings for all attributes
- **JSON Serialization**: to_json() and from_json() methods for data persistence
- **Field Defaults**: Sensible defaults using field() and default_factory
- **Derived Properties**: Calculated properties for common display needs
- **Type Hints**: Full type annotations for better code clarity
- **Enum Support**: Rich enums with additional properties and methods
- **Timestamp Tracking**: Automatic timestamp management for data freshness

This design creates a maintainable, extensible foundation for the BubbleTea shop TUI while maintaining the kawaii aesthetic throughout.