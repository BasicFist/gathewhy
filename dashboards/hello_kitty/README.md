# Hello Kitty BubbleTea Shop TUI Widgets

A delightful collection of kawaii-themed widgets for bubble tea shop management, inspired by Hello Kitty's adorable aesthetic. This TUI (Terminal User Interface) system provides all the essential components needed to run a bubble tea shop with style and efficiency.

## 🌸 Features

### ✨ Hello Kitty Design System
- **Kawaii Aesthetics**: Rounded borders, pastel colors, and adorable icons
- **Authentic Color Palette**: Based on Hello Kitty's signature pink, red, and yellow
- **Cute Typography**: Friendly fonts and emoji integration
- **Accessible Design**: High contrast and clear visual hierarchy

### 🧋 Bubble Tea Specific Widgets
- **Menu Display**: Beautiful drink cards with categories, pricing, and status indicators
- **Order Queue**: Real-time kitchen order management with priority handling
- **POS Panel**: Point of sale interface for taking orders
- **Inventory Status**: Stock level monitoring with low stock alerts
- **Sales Dashboard**: Performance metrics and business insights

### 🎯 Professional Features
- **Real-time Updates**: Live data refresh and automatic updates
- **Keyboard Navigation**: Vim-style navigation and shortcuts
- **Mobile Friendly**: Responsive design for various terminal sizes
- **Extensible**: Easy to customize and extend with new widgets

## 📦 Widget Components

### 1. MenuDisplay
Displays the bubble tea menu with Hello Kitty styling.

```python
from widgets import MenuDisplay, MenuItem

# Create menu display widget
menu_display = MenuDisplay()

# Add menu items
menu_items = [
    MenuItem(
        id="tarot_milk_tea",
        name="Taro Milk Tea",
        category="milk-tea",
        price=5.99,
        description="Creamy purple taro with chewy pearls",
        toppings=["tapioca", "popping boba", "cheese foam"],
        prep_time=5,
        is_popular=True
    )
]

menu_display.update_menu(menu_items)
```

**Features:**
- Category filtering (All, Milk Tea, Fruit Tea, Fresh Tea, Smoothies, Specialty)
- Visual status indicators (Popular, New, Out of Stock)
- Topping icons using Unicode symbols
- Rounded border cards with kawaii styling

### 2. OrderQueue
Manages kitchen orders with real-time status tracking.

```python
from widgets import OrderQueue, Order, OrderItem

# Create order queue widget
order_queue = OrderQueue()

# Add order
order = Order(
    id="ORD_001",
    customer_name="Alice",
    items=[order_item],
    status="preparing",
    created_at=datetime.now()
)

order_queue.add_order(order)
```

**Features:**
- Priority handling (rush orders first)
- Real-time status updates (pending, preparing, ready, completed)
- Overdue order alerts
- Customer information display
- Order duration tracking

### 3. POSPanel
Point of sale interface for order taking.

```python
from widgets import POSPanel, MenuItem

# Create POS panel
pos_panel = POSPanel()

# Add item to order
pos_panel.add_item_to_order(menu_item, quantity=1, toppings=toppings)

# Calculate total
total = pos_panel.calculate_total()

# Submit order
order = pos_panel.submit_order()
```

**Features:**
- Order item selection and customization
- Customer information management
- Order type selection (dine-in, takeaway, delivery)
- Real-time total calculation
- Order validation and error handling

### 4. InventoryStatus
Monitors inventory levels with alert system.

```python
from widgets import InventoryStatus, InventoryItem

# Create inventory widget
inventory_status = InventoryStatus()

# Add inventory items
inventory = [
    InventoryItem(
        id="taro_powder",
        name="Taro Powder",
        category="tea-base",
        current_stock=15,
        max_capacity=50,
        unit="kg",
        reorder_level=10,
        cost_per_unit=25.00,
        last_restocked=datetime.now()
    )
]

inventory_status.update_inventory(inventory)
```

**Features:**
- Stock level visualization with progress bars
- Low stock and out-of-stock alerts
- Expiry date tracking
- Category organization
- Restocking priority suggestions

### 5. SalesDashboard
Displays sales performance and business insights.

```python
from widgets import SalesDashboard, SalesMetrics

# Create sales dashboard
sales_dashboard = SalesDashboard()

# Update with sales data
sales_metrics = SalesMetrics(
    date=datetime.now(),
    total_orders=35,
    total_revenue=245.50,
    average_order_value=7.01,
    popular_items=[(menu_item, 12)],
    peak_hours=[10, 11, 14, 15, 16, 18, 19],
    customer_count=32,
    refund_count=1
)

sales_dashboard.update_metrics(sales_metrics)
```

**Features:**
- Revenue and order metrics
- Popular items tracking
- Peak hours visualization
- Performance indicators
- Business insights and recommendations

## 🎨 Design System

### Color Palette
Based on Hello Kitty's authentic color scheme:

- **Primary Pink**: `#ED164F` (Spanish Crimson)
- **Accent Yellow**: `#FFE700` (Vivid Yellow)
- **Contour Black**: `#1E181A` (Eerie Black)
- **Background White**: `#FFFFFF`
- **Pastel Variations**: Pink, mint, sky blue, butter yellow, lilac

### Typography
- **Headers**: Bold with hot pink and bright magenta
- **Body Text**: Dark charcoal for readability
- **Accents**: Bright colors for highlights and status indicators
- **Emoji Integration**: Extensive use of cute icons and symbols

### Border Styles
- **Normal**: Clean, minimal lines for subtle sections
- **Rounded**: Soft corners for cards and badges (recommended for kawaii feel)
- **Thick**: High-visibility outlines for important sections
- **Double**: Formal boundaries for primary panels

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/your-repo/hello-kitty-bubbletea-tui.git
cd hello-kitty-bubbletea-tui

# Install dependencies (Textual framework)
pip install textual
```

### Basic Usage
```python
from textual.app import App
from widgets import BubbleTeaShopView, MenuItem

class MyBubbleTeaApp(App):
    def compose(self):
        yield BubbleTeaShopView()

    def on_mount(self):
        # Get the main view
        shop_view = self.query_one(BubbleTeaShopView)
        
        # Load sample data
        menu_items = [...]  # Your menu data
        shop_view.update_menu(menu_items)

if __name__ == "__main__":
    app = MyBubbleTeaApp()
    app.run()
```

### Run Sample Application
```bash
python sample_app.py
```

## 📚 API Reference

### Models

#### MenuItem
```python
@dataclass
class MenuItem:
    id: str
    name: str
    category: Literal["milk-tea", "fruit-tea", "fresh-tea", "smoothies", "specialty", "snacks"]
    price: float
    description: str
    toppings: list[str]
    prep_time: int
    is_popular: bool = False
    is_new: bool = False
    is_out_of_stock: bool = False
```

#### Order
```python
@dataclass
class Order:
    id: str
    customer_name: str
    items: list[OrderItem]
    status: Literal["pending", "preparing", "ready", "completed", "cancelled"]
    created_at: datetime
    estimated_ready_time: Optional[datetime] = None
    total: float = 0.0
    order_type: Literal["dine-in", "takeaway", "delivery"] = "takeaway"
    priority: Literal["normal", "rush"] = "normal"
```

#### InventoryItem
```python
@dataclass
class InventoryItem:
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
```

### Widget Methods

#### BubbleTeaShopView
- `update_menu(menu_items)` - Update menu display
- `update_orders(orders)` - Update order queue
- `update_inventory(inventory)` - Update inventory status
- `update_sales(sales_metrics)` - Update sales dashboard

#### MenuDisplay
- `update_menu(menu_items)` - Load menu items
- `filter_by_category(category)` - Filter by category
- `highlight_item(item_id)` - Highlight specific item

#### OrderQueue
- `update_orders(orders)` - Load orders
- `add_order(order)` - Add new order
- `update_order_status(order_id, status)` - Update order status
- `filter_by_status(status)` - Filter orders by status

#### POSPanel
- `add_item_to_order(menu_item, quantity, toppings)` - Add item to order
- `remove_item_from_order(item_index)` - Remove item from order
- `calculate_total()` - Calculate order total
- `submit_order()` - Submit and create Order object

#### InventoryStatus
- `update_inventory(inventory)` - Load inventory items
- `mark_as_restocked(item_id)` - Mark item as restocked
- `filter_low_stock(show_only_low)` - Filter to low stock items

#### SalesDashboard
- `update_metrics(sales_metrics)` - Update sales data
- `set_period(period)` - Change time period (today, week, month)
- `generate_daily_report()` - Generate formatted report

## 🔧 Customization

### Styling
The widgets use Textual's CSS-like styling system. You can customize the appearance:

```python
from textual.css import Style

# Custom styling
my_widget.styles.background = "#F8BBD0"  # Pastel pink
my_widget.styles.border = ("heavy", "#ED164F")  # Pink border
my_widget.styles.padding = (1, 2)  # Custom padding
```

### Adding Custom Widgets
Extend the system by creating new widgets that follow the kawaii design patterns:

```python
from textual.widgets import Static
from widgets.models import YourModel

class YourCustomWidget(Static):
    def update_data(self, data: YourModel) -> None:
        # Update widget with new data
        pass
    
    def _create_kawaii_card(self, data: YourModel) -> list[str]:
        # Create Hello Kitty styled card
        pass
```

### Theme Configuration
Create a custom theme by overriding the color palette:

```python
class CustomBubbleTeaTheme:
    # Override color constants
    HK_PRIMARY = "#FF69B4"  # Hot pink
    HK_ACCENT = "#FFE4E1"   # Misty rose
    # ... other colors
```

## 🎯 Use Cases

### Small Bubble Tea Shop
- **Menu Display**: Show drinks and prices to customers
- **Order Queue**: Manage kitchen workflow
- **POS Panel**: Take orders at counter
- **Inventory**: Track basic stock levels

### Food Truck
- **Simplified Menu**: Focus on popular items
- **Mobile Order Queue**: Fast order processing
- **Portable POS**: Quick payment processing
- **Essential Inventory**: Monitor critical supplies

### Chain Store
- **Multi-location Support**: Different menus per location
- **Advanced Analytics**: Detailed sales reporting
- **Staff Training**: Standardized order process
- **Central Inventory**: Multi-store stock management

### Franchise Operation
- **Corporate Dashboard**: Multi-store sales overview
- **Standardized Experience**: Consistent kawaii branding
- **Performance Tracking**: Compare store performance
- **Training Materials**: Staff onboarding support

## 🐛 Troubleshooting

### Common Issues

**Widgets not displaying properly:**
- Ensure Textual is installed: `pip install textual`
- Check terminal compatibility (supports 256 colors)
- Verify CSS styling is loaded correctly

**Performance issues with large datasets:**
- Implement data pagination for order queues
- Use data virtualization for large menu lists
- Cache frequently accessed data

**Color rendering problems:**
- Set `TERM=xterm-256color` for better color support
- Check terminal emulator color settings
- Use adaptive colors for light/dark themes

**Layout issues on small terminals:**
- Implement responsive layouts
- Add collapse/expand functionality
- Prioritize most important information

### Debug Mode
Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

app = MyBubbleTeaApp()
app.run()
```

## 🤝 Contributing

We welcome contributions to make this kawaii widget system even better!

### Development Setup
1. Fork the repository
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Run tests: `pytest`
5. Start development server: `python sample_app.py`

### Adding New Features
1. Follow the existing kawaii design patterns
2. Add comprehensive documentation
3. Include unit tests for new functionality
4. Update the sample application
5. Ensure accessibility compliance

### Design Guidelines
- Maintain Hello Kitty aesthetic consistency
- Use pastel colors and rounded elements
- Include cute emoji and icons
- Ensure high contrast for readability
- Test on various terminal backgrounds

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Hello Kitty Design**: Inspired by Sanrio's beloved character
- **Textual Framework**: For providing the excellent TUI foundation
- **Kawaii Culture**: For the adorable design philosophy
- **Bubble Tea Community**: For the wonderful beverage culture
- **Open Source Contributors**: For making this possible

## 📞 Support

For questions, issues, or suggestions:
- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Community support and ideas
- **Documentation**: Comprehensive guides and examples

---

*Made with 💝 and lots of kawaii sparkle! 🌸*

*Keep spreading sweetness, one bubble tea at a time! ✨*
