"""Analytics models for BubbleTea shop.

This module defines data structures for representing sales metrics,
inventory analytics, and staff analytics with kawaii-inspired insights.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SalesMetrics:
    """Sales performance metrics with kawaii insights.
    
    Attributes:
        date: Date for these metrics (Unix timestamp at start of day)
        total_revenue: Total revenue in cents
        total_orders: Number of orders placed
        average_order_value: Average order value in cents
        total_items_sold: Total number of menu items sold
        hourly_sales: Sales breakdown by hour
        payment_methods: Breakdown by payment method
        popular_items: Most popular menu items
        peak_hours: Busiest hours of the day
        slow_hours: Slowest hours of the day
        customer_count: Number of unique customers
        repeat_customers: Number of repeat customers
        new_customers: Number of new customers
        average_prep_time: Average order preparation time in minutes
        order_queue_length: Current queue length
        kawaii_performance: Overall performance rating with emoji
        timestamp: When metrics were calculated
    """
    
    date: float
    total_revenue: int  # in cents
    total_orders: int
    average_order_value: int  # in cents
    total_items_sold: int
    hourly_sales: Dict[int, int] = field(default_factory=dict)  # hour -> revenue
    payment_methods: Dict[str, int] = field(default_factory=dict)  # method -> count
    popular_items: List[tuple[str, int]] = field(default_factory=list)  # (item_name, count)
    peak_hours: List[int] = field(default_factory=list)  # Hours with highest sales
    slow_hours: List[int] = field(default_factory=list)  # Hours with lowest sales
    customer_count: int = 0
    repeat_customers: int = 0
    new_customers: int = 0
    average_prep_time: float = 0.0
    order_queue_length: int = 0
    kawaii_performance: str = "📊"
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Calculate derived metrics after initialization."""
        if self.total_orders > 0:
            self.average_order_value = self.total_revenue // self.total_orders
        self._update_kawaii_performance()
    
    def _update_kawaii_performance(self):
        """Update kawaii performance indicator based on metrics."""
        if self.total_revenue == 0:
            self.kawaii_performance = "😴"
            return
        
        # Performance based on revenue per hour
        hours_with_sales = len([h for h in self.hourly_sales.values() if h > 0])
        if hours_with_sales == 0:
            self.kawaii_performance = "😴"
            return
        
        avg_hourly_revenue = self.total_revenue / hours_with_sales
        
        if avg_hourly_revenue >= 10000:  # $100/hour
            self.kawaii_performance = "😍"
        elif avg_hourly_revenue >= 5000:   # $50/hour
            self.kawaii_performance = "😄"
        elif avg_hourly_revenue >= 2500:   # $25/hour
            self.kawaii_performance = "😊"
        else:
            self.kawaii_performance = "😐"
    
    @property
    def formatted_total_revenue(self) -> str:
        """Formatted total revenue for display.
        
        Returns:
            Revenue formatted as currency string
        """
        return f"${self.total_revenue / 100:.2f}"
    
    @property
    def formatted_average_order_value(self) -> str:
        """Formatted average order value for display.
        
        Returns:
            Average order value formatted as currency string
        """
        return f"${self.average_order_value / 100:.2f}"
    
    @property
    def revenue_per_hour(self) -> float:
        """Average revenue per hour of operation.
        
        Returns:
            Revenue per hour in cents
        """
        hours_with_sales = len([h for h in self.hourly_sales.values() if h > 0])
        if hours_with_sales == 0:
            return 0.0
        return self.total_revenue / hours_with_sales
    
    @property
    def orders_per_hour(self) -> float:
        """Average orders per hour of operation.
        
        Returns:
            Orders per hour
        """
        hours_with_sales = len([h for h in self.hourly_sales.values() if h > 0])
        if hours_with_sales == 0:
            return 0.0
        return self.total_orders / hours_with_sales
    
    @property
    def customer_retention_rate(self) -> float:
        """Customer retention rate as percentage.
        
        Returns:
            Percentage of repeat customers
        """
        if self.customer_count == 0:
            return 0.0
        return (self.repeat_customers / self.customer_count) * 100
    
    @property
    def peak_hour_display(self) -> str:
        """Display the peak hour in a friendly format.
        
        Returns:
            Peak hour as formatted string
        """
        if not self.peak_hours:
            return "No data"
        
        peak_hour = max(self.peak_hours, key=lambda h: self.hourly_sales.get(h, 0))
        return f"{peak_hour:02d}:00"
    
    @property
    def kawaii_summary(self) -> str:
        """Kawaii summary for dashboard display.
        
        Returns:
            Summary with emoji and key metrics
        """
        return f"{self.kawaii_performance} Sales: {self.total_orders} orders, {self.formatted_total_revenue} revenue, avg ${self.average_order_value / 100:.2f}"
    
    def add_hourly_sale(self, hour: int, revenue: int):
        """Add revenue for a specific hour.
        
        Args:
            hour: Hour (0-23)
            revenue: Revenue in cents
        """
        self.hourly_sales[hour] = self.hourly_sales.get(hour, 0) + revenue
        self.total_revenue += revenue
        self.timestamp = time.time()
        self._update_kawaii_performance()
    
    def add_payment_method(self, method: str):
        """Record a payment method usage.
        
        Args:
            method: Payment method used
        """
        self.payment_methods[method] = self.payment_methods.get(method, 0) + 1
        self.timestamp = time.time()
    
    def add_popular_item(self, item_name: str, count: int = 1):
        """Add to popular items count.
        
        Args:
            item_name: Name of the menu item
            count: Number of times ordered
        """
        # Find existing entry or add new one
        for i, (name, cnt) in enumerate(self.popular_items):
            if name == item_name:
                self.popular_items[i] = (name, cnt + count)
                break
        else:
            self.popular_items.append((item_name, count))
        
        # Keep only top 10 items
        self.popular_items.sort(key=lambda x: x[1], reverse=True)
        self.popular_items = self.popular_items[:10]
        
        self.timestamp = time.time()
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        return data


@dataclass
class InventoryMetrics:
    """Inventory analytics and insights.
    
    Attributes:
        total_inventory_value: Total value of all inventory in cents
        items_below_minimum: Count of items below minimum stock level
        items_out_of_stock: Count of items completely out of stock
        slow_moving_items: Items with low turnover rate
        fast_moving_items: Items with high turnover rate
        waste_percentage: Estimated waste percentage
        restock_urgency: Items requiring immediate restock
        upcoming_expirations: Items expiring soon
        supplier_analysis: Analysis by supplier
        cost_analysis: Cost breakdown by category
        turnover_rate: Average inventory turnover rate
        days_of_supply: Average days of supply remaining
        kawaii_inventory_health: Overall inventory health indicator
        timestamp: When metrics were calculated
    """
    
    total_inventory_value: int  # in cents
    items_below_minimum: int
    items_out_of_stock: int
    slow_moving_items: List[tuple[str, int]] = field(default_factory=list)  # (item_name, turnover_days)
    fast_moving_items: List[tuple[str, int]] = field(default_factory=list)  # (item_name, daily_usage)
    waste_percentage: float = 0.0
    restock_urgency: List[str] = field(default_factory=list)  # Item names needing restock
    upcoming_expirations: List[tuple[str, int]] = field(default_factory=list)  # (item_name, days_until_expiry)
    supplier_analysis: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    cost_analysis: Dict[str, int] = field(default_factory=dict)  # category -> cost
    turnover_rate: float = 0.0
    days_of_supply: float = 0.0
    kawaii_inventory_health: str = "📦"
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Update kawaii inventory health after initialization."""
        self._update_kawaii_health()
    
    def _update_kawaii_health(self):
        """Update kawaii health indicator based on inventory status."""
        if self.items_out_of_stock > 5:
            self.kawaii_inventory_health = "😱"
        elif self.items_below_minimum > 10:
            self.kawaii_inventory_health = "😰"
        elif self.items_below_minimum > 5:
            self.kawaii_inventory_health = "😟"
        elif self.waste_percentage > 10:
            self.kawaii_inventory_health = "🤔"
        else:
            self.kawaii_inventory_health = "😊"
    
    @property
    def inventory_health_score(self) -> int:
        """Overall inventory health score (0-100).
        
        Returns:
            Health score where 100 is perfect
        """
        score = 100
        
        # Deduct for out of stock items
        score -= self.items_out_of_stock * 10
        
        # Deduct for low stock items
        score -= self.items_below_minimum * 2
        
        # Deduct for waste
        score -= self.waste_percentage * 2
        
        return max(0, score)
    
    @property
    def formatted_total_value(self) -> str:
        """Formatted total inventory value.
        
        Returns:
            Value formatted as currency string
        """
        return f"${self.total_inventory_value / 100:.2f}"
    
    @property
    def kawaii_summary(self) -> str:
        """Kawaii summary for dashboard display.
        
        Returns:
            Summary with emoji and key metrics
        """
        return f"{self.kawaii_inventory_health} Inventory: {self.formatted_total_value} value, {self.items_below_minimum} low stock"
    
    def add_restock_urgency(self, item_name: str):
        """Add item to restock urgency list.
        
        Args:
            item_name: Name of item needing restock
        """
        if item_name not in self.restock_urgency:
            self.restock_urgency.append(item_name)
            self.timestamp = time.time()
            self._update_kawaii_health()
    
    def add_upcoming_expiration(self, item_name: str, days_until_expiry: int):
        """Add item to upcoming expirations.
        
        Args:
            item_name: Name of item
            days_until_expiry: Days until expiration
        """
        # Remove if already exists
        self.upcoming_expirations = [
            (name, days) for name, days in self.upcoming_expirations if name != item_name
        ]
        
        # Add with new data
        self.upcoming_expirations.append((item_name, days_until_expiry))
        
        # Sort by days until expiry (most urgent first)
        self.upcoming_expirations.sort(key=lambda x: x[1])
        
        self.timestamp = time.time()
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        return data


@dataclass
class StaffMetrics:
    """Staff performance and scheduling analytics.
    
    Attributes:
        total_scheduled_hours: Total scheduled staff hours
        total_actual_hours: Total actual hours worked
        overtime_hours: Total overtime hours worked
        shift_completion_rate: Percentage of completed shifts
        no_show_rate: Percentage of no-show shifts
        average_performance_score: Average staff performance
        staff_utilization: Percentage of scheduled time actually worked
        training_completion_rate: Percentage of required training completed
        staff_satisfaction: Estimated staff satisfaction score
        peak_hour_coverage: Staffing coverage during peak hours
        skills_gaps: Areas where skills are lacking
        top_performers: Highest performing staff members
        scheduling_efficiency: How efficiently shifts are scheduled
        cost_per_hour: Labor cost per hour of operation
        kawaii_staff_satisfaction: Overall staff satisfaction indicator
        timestamp: When metrics were calculated
    """
    
    total_scheduled_hours: float
    total_actual_hours: float
    overtime_hours: float
    shift_completion_rate: float
    no_show_rate: float
    average_performance_score: float
    staff_utilization: float
    training_completion_rate: float
    staff_satisfaction: float
    peak_hour_coverage: float
    skills_gaps: List[str] = field(default_factory=list)
    top_performers: List[str] = field(default_factory=list)  # Employee names
    scheduling_efficiency: float = 0.0
    cost_per_hour: float = 0.0  # in cents
    kawaii_staff_satisfaction: str = "👥"
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Calculate derived metrics after initialization."""
        self._update_kawaii_satisfaction()
    
    def _update_kawaii_satisfaction(self):
        """Update kawaii satisfaction indicator based on metrics."""
        if self.staff_satisfaction >= 8.5:
            self.kawaii_staff_satisfaction = "😍"
        elif self.staff_satisfaction >= 7.0:
            self.kawaii_staff_satisfaction = "😊"
        elif self.staff_satisfaction >= 5.5:
            self.kawaii_staff_satisfaction = "😐"
        elif self.staff_satisfaction >= 4.0:
            self.kawaii_staff_satisfaction = "😟"
        else:
            self.kawaii_staff_satisfaction = "😰"
    
    @property
    def formatted_cost_per_hour(self) -> str:
        """Formatted cost per hour.
        
        Returns:
            Cost formatted as currency string per hour
        """
        return f"${self.cost_per_hour / 100:.2f}/hr"
    
    @property
    def labor_efficiency(self) -> float:
        """Labor efficiency score (0-100).
        
        Returns:
            Efficiency based on utilization and performance
        """
        efficiency = self.staff_utilization
        efficiency += (self.average_performance_score - 5) * 10  # Performance bonus/penalty
        efficiency -= self.no_show_rate * 5  # No-show penalty
        return max(0, min(100, efficiency))
    
    @property
    def kawaii_summary(self) -> str:
        """Kawaii summary for dashboard display.
        
        Returns:
            Summary with emoji and key metrics
        """
        return f"{self.kawaii_staff_satisfaction} Staff: {self.shift_completion_rate:.0f}% completion, {self.staff_utilization:.0f}% utilization"
    
    def add_skill_gap(self, skill: str):
        """Add a skill gap to the list.
        
        Args:
            skill: Missing skill area
        """
        if skill not in self.skills_gaps:
            self.skills_gaps.append(skill)
            self.timestamp = time.time()
    
    def add_top_performer(self, employee_name: str):
        """Add employee to top performers list.
        
        Args:
            employee_name: Name of top performing employee
        """
        if employee_name not in self.top_performers:
            self.top_performers.append(employee_name)
            # Keep only top 5
            self.top_performers = self.top_performers[:5]
            self.timestamp = time.time()
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        return data


@dataclass
class DailyReport:
    """Comprehensive daily business report with kawaii insights.
    
    Attributes:
        date: Date for this report (Unix timestamp at start of day)
        sales_metrics: Sales performance metrics
        inventory_metrics: Inventory analytics
        staff_metrics: Staff performance metrics
        weather_impact: Weather impact on business (if applicable)
        special_events: Special events that may have affected business
        achievements: Daily achievements and milestones
        challenges: Challenges encountered
        recommendations: Recommendations for improvement
        kawaii_mood_today: Overall business mood for the day
        timestamp: When report was generated
    """
    
    date: float
    sales_metrics: SalesMetrics
    inventory_metrics: InventoryMetrics
    staff_metrics: StaffMetrics
    weather_impact: str = "No data"
    special_events: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    kawaii_mood_today: str = "📊"
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Update overall kawaii mood after initialization."""
        self._update_overall_mood()
    
    def _update_overall_mood(self):
        """Update overall business mood based on all metrics."""
        # Score based on multiple factors
        mood_score = 0
        count = 0
        
        # Sales performance
        if self.sales_metrics.total_revenue > 0:
            mood_score += 1
            count += 1
        
        # Inventory health
        if self.inventory_metrics.items_out_of_stock == 0:
            mood_score += 1
        count += 1
        
        # Staff performance
        if self.staff_metrics.shift_completion_rate >= 90:
            mood_score += 1
        count += 1
        
        if count > 0:
            mood_percentage = mood_score / count
            
            if mood_percentage >= 0.9:
                self.kawaii_mood_today = "😍"
            elif mood_percentage >= 0.75:
                self.kawaii_mood_today = "😊"
            elif mood_percentage >= 0.5:
                self.kawaii_mood_today = "😐"
            else:
                self.kawaii_mood_today = "😔"
    
    @property
    def total_revenue(self) -> int:
        """Total revenue for the day.
        
        Returns:
            Revenue in cents
        """
        return self.sales_metrics.total_revenue
    
    @property
    def formatted_total_revenue(self) -> str:
        """Formatted total revenue.
        
        Returns:
            Revenue formatted as currency string
        """
        return f"${self.total_revenue / 100:.2f}"
    
    @property
    def business_health_score(self) -> int:
        """Overall business health score (0-100).
        
        Returns:
            Health score based on all metrics
        """
        scores = []
        
        # Sales score (0-100 based on revenue)
        if self.sales_metrics.total_revenue > 0:
            scores.append(min(100, (self.sales_metrics.total_revenue / 50000) * 100))
        
        # Inventory health score
        scores.append(self.inventory_metrics.inventory_health_score)
        
        # Staff efficiency score
        scores.append(self.staff_metrics.labor_efficiency)
        
        return int(sum(scores) / len(scores)) if scores else 0
    
    @property
    def kawaii_executive_summary(self) -> str:
        """Executive summary with kawaii mood.
        
        Returns:
            Brief summary of the day's performance
        """
        return f"{self.kawaii_mood_today} Daily Report: {self.formatted_total_revenue} revenue, {self.business_health_score}/100 health score"
    
    def add_achievement(self, achievement: str):
        """Add a daily achievement.
        
        Args:
            achievement: Achievement to record
        """
        if achievement not in self.achievements:
            self.achievements.append(achievement)
            self.timestamp = time.time()
    
    def add_challenge(self, challenge: str):
        """Add a daily challenge.
        
        Args:
            challenge: Challenge encountered
        """
        if challenge not in self.challenges:
            self.challenges.append(challenge)
            self.timestamp = time.time()
    
    def add_recommendation(self, recommendation: str):
        """Add a recommendation for improvement.
        
        Args:
            recommendation: Recommendation to add
        """
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
            self.timestamp = time.time()
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        return data