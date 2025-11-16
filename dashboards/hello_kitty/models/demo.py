#!/usr/bin/env python3
"""
Example usage of Hello Kitty BubbleTea TUI data models.

This script demonstrates how to use all the data models together
to create a complete bubble tea shop management system.
"""

import sys
import time
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.insert(0, '.')

from menu_models import MenuItem, Ingredient, Topping, DrinkCategory
from order_models import Order, OrderItem, OrderStatus, PaymentMethod
from inventory_models import InventoryItem, StockLevel, SupplyType
from staff_models import Employee, Shift, StaffRole
from analytics_models import SalesMetrics, InventoryMetrics, StaffMetrics, DailyReport


def create_sample_data():
    """Create sample data for demonstration."""
    
    print("🧋 Creating Hello Kitty BubbleTea Shop Data... 🧋\n")
    
    # ========================================
    # CREATE MENU ITEMS
    # ========================================
    print("📋 Creating Menu Items...")
    
    # Create ingredients
    black_tea = Ingredient(
        name="Black Tea",
        category="tea_base",
        cost_per_unit=50
    )
    
    milk = Ingredient(
        name="Whole Milk",
        category="milk",
        cost_per_unit=30,
        allergens=["dairy"]
    )
    
    taro_powder = Ingredient(
        name="Taro Powder",
        category="powder",
        cost_per_unit=100
    )
    
    # Create toppings
    tapioca_pearls = Topping(
        name="Tapioca Pearls",
        kawaii_symbol="●",
        category="pearls",
        cost=75,
        calories_per_serving=140,
        texture_description="Chewy and sweet",
        prep_time_seconds=10
    )
    
    popping_boba = Topping(
        name="Popping Boba",
        kawaii_symbol="◉",
        category="boba",
        cost=100,
        calories_per_serving=80,
        texture_description="Bursting with fruit flavor",
        prep_time_seconds=5
    )
    
    # Create menu items
    milk_tea = MenuItem(
        id="milk_tea_001",
        name="Classic Milk Tea",
        category=DrinkCategory.MILK_TEA,
        base_price=450,  # $4.50
        ingredients=[black_tea, milk],
        available_toppings=[tapioca_pearls, popping_boba],
        description="Traditional black tea with fresh milk",
        popularity_score=9
    )
    
    taro_milk_tea = MenuItem(
        id="taro_milk_tea_001",
        name="Taro Milk Tea",
        category=DrinkCategory.TARO,
        base_price=500,  # $5.00
        ingredients=[taro_powder, milk],
        available_toppings=[tapioca_pearls],
        description="Creamy taro with chewy pearls",
        popularity_score=8
    )
    
    print(f"  ✨ Created: {milk_tea.name} - {milk_tea.kawaii_visual}")
    print(f"  ✨ Created: {taro_milk_tea.name} - {taro_milk_tea.kawaii_visual}")
    
    # ========================================
    # CREATE INVENTORY
    # ========================================
    print("\n📦 Creating Inventory...")
    
    tea_inventory = InventoryItem(
        id="tea_black_001",
        name="Black Tea Bags",
        supply_type=SupplyType.TEA_BASE,
        current_stock=50.0,
        unit_of_measurement="bags",
        cost_per_unit=50,
        reorder_point=20.0,
        maximum_stock_level=200.0,
        location_in_store="Tea Storage"
    )
    
    milk_inventory = InventoryItem(
        id="milk_whole_001",
        name="Whole Milk Cartons",
        supply_type=SupplyType.MILK,
        current_stock=15.0,
        unit_of_measurement="cartons",
        cost_per_unit=300,  # $3.00
        reorder_point=10.0,
        maximum_stock_level=50.0,
        storage_requirements="Refrigerated 2-4°C",
        expiration_date=time.time() + (5 * 24 * 60 * 60)  # 5 days from now
    )
    
    cups_inventory = InventoryItem(
        id="cups_large_001",
        name="Large Cups (500ml)",
        supply_type=SupplyType.CUPS,
        current_stock=100.0,
        unit_of_measurement="pieces",
        cost_per_unit=25,
        reorder_point=50.0,
        maximum_stock_level=500.0
    )
    
    print(f"  🟢 {tea_inventory.kawaii_stock_display}")
    print(f"  🟢 {milk_inventory.kawaii_stock_display}")
    print(f"  🟢 {cups_inventory.kawaii_stock_display}")
    
    # ========================================
    # CREATE STAFF
    # ========================================
    print("\n👥 Creating Staff...")
    
    # Create employees
    manager = Employee(
        id="EMP_001",
        name="Hello Kitty",
        role=StaffRole.MANAGER,
        hire_date=time.time() - (365 * 24 * 60 * 60),  # 1 year ago
        hourly_wage=2500,  # $25.00/hour
        skills=["Management", "Customer Service", "Training"],
        performance_score=9
    )
    
    barista = Employee(
        id="EMP_002",
        name="Mimi San",
        role=StaffRole.BARISTA,
        hire_date=time.time() - (180 * 24 * 60 * 60),  # 6 months ago
        hourly_wage=1800,  # $18.00/hour
        skills=["Milk Tea", "Matcha", "Customer Service"],
        performance_score=8
    )
    
    trainee = Employee(
        id="EMP_003",
        name="Badtz-Maru",
        role=StaffRole.TRAINEE,
        hire_date=time.time() - (30 * 24 * 60 * 60),  # 1 month ago
        hourly_wage=1500,  # $15.00/hour
        skills=["Basic Tea Preparation"],
        performance_score=6
    )
    
    print(f"  👑 {manager.kawaii_profile}")
    print(f"  🧋 {barista.kawaii_profile}")
    print(f"  📚 {trainee.kawaii_profile}")
    
    # ========================================
    # CREATE ORDERS
    # ========================================
    print("\n🧾 Creating Orders...")
    
    # Create order items
    item1 = OrderItem(
        menu_item_id="milk_tea_001",
        menu_item_name="Classic Milk Tea",
        quantity=2,
        toppings=["Tapioca Pearls"],
        unit_price=525,  # $5.25 with topping
        total_price=1050  # $10.50 for 2
    )
    
    item2 = OrderItem(
        menu_item_id="taro_milk_tea_001",
        menu_item_name="Taro Milk Tea",
        quantity=1,
        toppings=["Popping Boba"],
        unit_price=600,  # $6.00 with topping
        total_price=600
    )
    
    # Create orders
    order1 = Order(
        id="ORD_001",
        customer_name="Kiki",
        customer_phone="555-0123",
        items=[item1],
        payment_method=PaymentMethod.CREDIT_CARD,
        pickup_name="Kiki",
        special_requests="Less ice please!"
    )
    
    order2 = Order(
        id="ORD_002",
        customer_name="Lala",
        items=[item2],
        payment_method=PaymentMethod.CASH,
        pickup_name="Lala",
        order_type="dine_in"
    )
    
    print(f"  ✨ {order1.kawaii_summary}")
    print(f"  ✨ {order2.kawaii_summary}")
    
    # Update order status
    order1.update_status(OrderStatus.PREPARING)
    print(f"  🥤 Updated: {order1.kawaii_status_display}")
    
    return {
        'menu_items': [milk_tea, taro_milk_tea],
        'inventory': [tea_inventory, milk_inventory, cups_inventory],
        'staff': [manager, barista, trainee],
        'orders': [order1, order2]
    }


def create_analytics_sample(data):
    """Create sample analytics data."""
    
    print("\n📊 Creating Analytics...")
    
    # Create sales metrics
    average_order_value = 125000 // 45  # $1,250 / 45 orders
    total_items_sold = 65  # Estimated items sold
    
    sales_metrics = SalesMetrics(
        date=time.time() - (24 * 60 * 60),  # Yesterday
        total_revenue=125000,  # $1,250
        total_orders=45,
        average_order_value=average_order_value,
        total_items_sold=total_items_sold,
        customer_count=42,
        repeat_customers=8,
        new_customers=34
    )
    
    # Add hourly sales
    sales_metrics.add_hourly_sale(10, 15000)  # 10 AM: $150
    sales_metrics.add_hourly_sale(11, 25000)  # 11 AM: $250
    sales_metrics.add_hourly_sale(12, 45000)  # 12 PM: $450
    sales_metrics.add_hourly_sale(13, 35000)  # 1 PM: $350
    
    # Add payment methods
    sales_metrics.add_payment_method("credit_card")
    sales_metrics.add_payment_method("cash")
    sales_metrics.add_payment_method("mobile_pay")
    
    # Add popular items
    sales_metrics.add_popular_item("Classic Milk Tea", 25)
    sales_metrics.add_popular_item("Taro Milk Tea", 18)
    sales_metrics.add_popular_item("Matcha Milk Tea", 12)
    
    # Create inventory metrics
    inventory_metrics = InventoryMetrics(
        total_inventory_value=250000,  # $2,500
        items_below_minimum=2,
        items_out_of_stock=0,
        waste_percentage=2.5,
        turnover_rate=5.2,
        days_of_supply=15.0
    )
    
    inventory_metrics.add_restock_urgency("Whole Milk Cartons")
    inventory_metrics.add_restock_urgency("Tapioca Pearls")
    
    # Create staff metrics
    staff_metrics = StaffMetrics(
        total_scheduled_hours=32.0,
        total_actual_hours=30.5,
        overtime_hours=2.5,
        shift_completion_rate=92.5,
        no_show_rate=5.0,
        average_performance_score=7.8,
        staff_utilization=95.3,
        training_completion_rate=85.0,
        staff_satisfaction=8.2,
        peak_hour_coverage=88.0
    )
    
    staff_metrics.add_skill_gap("Advanced latte art")
    staff_metrics.add_top_performer("Hello Kitty")
    staff_metrics.add_top_performer("Mimi San")
    
    # Create daily report
    daily_report = DailyReport(
        date=time.time() - (24 * 60 * 60),
        sales_metrics=sales_metrics,
        inventory_metrics=inventory_metrics,
        staff_metrics=staff_metrics,
        weather_impact="Sunny - good for takeout orders",
        special_events=["Hello Kitty Birthday Special"]
    )
    
    daily_report.add_achievement("Beat yesterday's sales by 15%")
    daily_report.add_achievement("Perfect customer service ratings")
    daily_report.add_challenge("Ran low on milk during lunch rush")
    daily_report.add_recommendation("Order more milk for tomorrow")
    daily_report.add_recommendation("Consider expanding taro milk tea marketing")
    
    print(f"  📈 {sales_metrics.kawaii_summary}")
    print(f"  📦 {inventory_metrics.kawaii_summary}")
    print(f"  👥 {staff_metrics.kawaii_summary}")
    print(f"  📋 {daily_report.kawaii_executive_summary}")
    
    return {
        'sales_metrics': sales_metrics,
        'inventory_metrics': inventory_metrics,
        'staff_metrics': staff_metrics,
        'daily_report': daily_report
    }


def demonstrate_json_serialization(data, analytics):
    """Demonstrate JSON serialization."""
    
    print("\n💾 Demonstrating JSON Serialization...")
    
    # Serialize menu item
    menu_item = data['menu_items'][0]
    json_data = menu_item.to_json()
    print(f"  📄 Menu item JSON: {json_data['name']}")
    
    # Deserialize menu item
    restored_item = MenuItem.from_json(json_data)
    print(f"  ✨ Restored: {restored_item.name} - {restored_item.kawaii_visual}")
    
    # Serialize order
    order = data['orders'][0]
    order_json = order.to_json()
    print(f"  📄 Order JSON: {order_json['id']} - {order_json['customer_name']}")
    
    # Deserialize order
    restored_order = Order.from_json(order_json)
    print(f"  ✨ Restored: Order {restored_order.id} for {restored_order.customer_name}")


def demonstrate_kawaii_features(data, analytics):
    """Demonstrate kawaii features."""
    
    print("\n😍 Demonstrating Kawaii Features...")
    
    # Show status emotions
    order = data['orders'][0]
    print(f"  😊 Order status: {order.kawaii_status_display}")
    
    # Show inventory emotions
    for item in data['inventory']:
        print(f"  {item.kawaii_stock_display}")
    
    # Show staff moods
    for employee in data['staff']:
        print(f"  {employee.kawaii_profile}")
    
    # Show performance indicators
    sales = analytics['sales_metrics']
    inventory = analytics['inventory_metrics']
    staff = analytics['staff_metrics']
    
    print(f"\n  📊 Performance Summary:")
    print(f"    Sales: {sales.kawaii_summary}")
    print(f"    Inventory: {inventory.kawaii_summary}")
    print(f"    Staff: {staff.kawaii_summary}")
    print(f"    Overall: {analytics['daily_report'].kawaii_executive_summary}")


def main():
    """Main demonstration function."""
    
    print("=" * 60)
    print("🧋 Hello Kitty BubbleTea TUI - Data Models Demo 🧋")
    print("=" * 60)
    
    # Create sample data
    data = create_sample_data()
    
    # Create analytics
    analytics = create_analytics_sample(data)
    
    # Demonstrate JSON serialization
    demonstrate_json_serialization(data, analytics)
    
    # Demonstrate kawaii features
    demonstrate_kawaii_features(data, analytics)
    
    print("\n" + "=" * 60)
    print("✨ Demo Complete! Ready for TUI Integration! ✨")
    print("=" * 60)


if __name__ == "__main__":
    main()