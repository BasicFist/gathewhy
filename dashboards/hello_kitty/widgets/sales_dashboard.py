"""Hello Kitty BubbleTea Shop TUI - Sales Dashboard Widget."""

from __future__ import annotations

from datetime import datetime, timedelta
from collections import defaultdict
from textual.widgets import Static

from .models import SalesMetrics, MenuItem, Order


class SalesDashboard(Static):
    """Sales dashboard with Hello Kitty styling.
    
    Displays sales performance, popular items, revenue trends,
    and business insights with kawaii design elements.
    Features cute charts, colorful indicators, and adorable
    status messages.
    """

    def __init__(self):
        """Initialize sales dashboard widget."""
        super().__init__()
        self.sales_metrics: SalesMetrics | None = None
        self.current_date = datetime.now().date()
        self.show_period: str = "today"  # today, week, month

    def update_metrics(self, sales_metrics: SalesMetrics) -> None:
        """Update sales dashboard with new metrics.
        
        Args:
            sales_metrics: Sales metrics to display
        """
        self.sales_metrics = sales_metrics
        self._render_dashboard()

    def set_period(self, period: str) -> None:
        """Set the time period for dashboard display.
        
        Args:
            period: Time period ('today', 'week', 'month')
        """
        self.show_period = period
        self._render_dashboard()

    def _render_dashboard(self) -> None:
        """Render the sales dashboard display."""
        if not self.sales_metrics:
            dashboard_lines = [
                "[bold bright_magenta]🌸 Sales Dashboard ✨[/]",
                "",
                "[light_pink]💝 Loading sweet sales data...[/]",
                "[light_pink]🎀 Preparing kawaii insights![/]"
            ]
        else:
            dashboard_lines = self._build_dashboard_header()
            dashboard_lines.extend(self._build_metrics_summary())
            dashboard_lines.extend(self._build_popular_items())
            dashboard_lines.extend(self._build_performance_charts())
            dashboard_lines.extend(self._build_insights_footer())

        self.update("\n".join(dashboard_lines))

    def _build_dashboard_header(self) -> list[str]:
        """Build the dashboard header with period selector."""
        # Period buttons
        periods = ["today", "week", "month"]
        period_buttons = []
        
        for period in periods:
            if period == "today":
                label = "🌸 Today"
            elif period == "week":
                label = "📅 This Week"
            else:
                label = "📆 This Month"
            
            if self.show_period == period:
                period_buttons.append(f"[bright_magenta]◈ {label}[/]")
            else:
                period_buttons.append(f"[dim]{label}[/]")

        header = [
            "[bold bright_magenta]🌸 Hello Kitty Sales Dashboard ✨[/]",
            "  ".join(period_buttons),
            ""
        ]

        if self.sales_metrics:
            # Add greeting based on performance
            if self.sales_metrics.total_orders > 0:
                if self.sales_metrics.average_order_value > 15:
                    greeting = "[bright_green]💫 Amazing sales performance today![/]"
                elif self.sales_metrics.average_order_value > 10:
                    greeting = "[yellow]😊 Sweet sales momentum![/]"
                else:
                    greeting = "[light_blue]🌸 Gentle start to the day![/]"
            else:
                greeting = "[dim]✨ New day, new opportunities![/]"
            
            header.append(greeting)
            header.append("")

        return header

    def _build_metrics_summary(self) -> list[str]:
        """Build the main metrics summary."""
        if not self.sales_metrics:
            return []

        metrics = self.sales_metrics
        summary_lines = []

        # Revenue and orders in a cute card
        summary_lines.extend([
            "[light_magenta]┌─{border}─┐[/]".format(border="─" * 50),
            f"[light_magenta]│[/] 💰 [bold]Total Revenue:[/] ${metrics.total_revenue:.2f}        {metrics.total_orders:3} Orders [light_magenta]│[/]",
            f"[light_magenta]│[/] 💝 [bold]Avg Order:[/] ${metrics.average_order_value:.2f}    {metrics.customer_count:3} Customers [light_magenta]│[/]",
            f"[light_magenta]│[/] ✨ [bold]Profit Est:[/] ${metrics.profit_estimate:.2f}         {metrics.refund_rate:5.1f}% Refunds [light_magenta]│[/]",
            "[light_magenta]└─{border}─┘[/]"
        ])

        # Performance indicators
        performance_indicators = []
        
        # Order velocity
        if metrics.total_orders > 0:
            if metrics.total_orders > 50:
                performance_indicators.append("[bright_green]🚀 High Volume![/]")
            elif metrics.total_orders > 20:
                performance_indicators.append("[yellow]😊 Steady Flow[/]")
            else:
                performance_indicators.append("[light_blue]🌸 Building Up[/]")

        # Average order value
        if metrics.average_order_value > 15:
            performance_indicators.append("[bright_green]💎 Premium Orders[/]")
        elif metrics.average_order_value > 10:
            performance_indicators.append("[yellow]💖 Sweet Spot[/]")
        else:
            performance_indicators.append("[light_blue]🌸 Getting Started[/]")

        # Customer satisfaction (inverse of refund rate)
        if metrics.refund_rate < 2:
            performance_indicators.append("[bright_green]⭐ Happy Customers[/]")
        elif metrics.refund_rate < 5:
            performance_indicators.append("[yellow]😊 Good Service[/]")
        else:
            performance_indicators.append("[orange_red1]⚠️ Needs Attention[/]")

        if performance_indicators:
            summary_lines.extend([""])
            summary_lines.extend(performance_indicators)

        summary_lines.append("")

        return summary_lines

    def _build_popular_items(self) -> list[str]:
        """Build the popular items display."""
        if not self.sales_metrics or not self.sales_metrics.popular_items:
            return [
                "[dim]🌸 Popular items will appear here...[/]",
                ""
            ]

        popular_lines = [
            "[bold]🌟 Today's Favorites:[/]",
            ""
        ]

        # Show top 5 popular items
        for i, (item, count) in enumerate(self.sales_metrics.popular_items[:5]):
            # Create a cute item card
            rank_emoji = ["🥇", "🥈", "🥉", "🌟", "✨"][i]
            name = item.name[:25]  # Truncate long names
            
            if item.is_popular:
                popular_label = "[gold3]★ POPULAR[/]"
            else:
                popular_label = ""

            item_line = f"{rank_emoji} [bold]{name}[/] - {count} sold"
            if popular_label:
                item_line += f"  {popular_label}"

            popular_lines.append(item_line)

        popular_lines.append("")
        return popular_lines

    def _build_performance_charts(self) -> list[str]:
        """Build visual performance indicators."""
        if not self.sales_metrics:
            return []

        charts_lines = []
        metrics = self.sales_metrics

        # Mini bar chart for order distribution (simulated)
        if metrics.peak_hours:
            charts_lines.append("[bold]📊 Peak Hours:[/]")
            
            # Create a simple bar chart
            hour_bars = {}
            for hour in range(8, 22):  # Business hours
                if hour in metrics.peak_hours:
                    hour_bars[hour] = "█" * 5  # Busy hour
                else:
                    hour_bars[hour] = "░" * 5  # Quiet hour
            
            # Display hours with bars
            for hour, bar in hour_bars.items():
                time_str = f"{hour:02d}:00"
                if hour in metrics.peak_hours:
                    chart_line = f"[bright_green]{time_str}: {bar}[/] ⭐"
                else:
                    chart_line = f"[dim]{time_str}: {bar}[/]"
                charts_lines.append(chart_line)

            charts_lines.append("")

        # Goal progress (simulated daily goal)
        daily_goal = 200.0  # Could be configurable
        progress = min((metrics.total_revenue / daily_goal) * 100, 100)
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        
        charts_lines.extend([
            "[bold]🎯 Daily Goal Progress:[/]",
            f"[bright_magenta]{progress_bar}[/] {progress:.1f}%",
            f"[dim]Goal: ${daily_goal:.2f} | Current: ${metrics.total_revenue:.2f}[/]",
            ""
        ])

        # Service quality indicators
        charts_lines.extend([
            "[bold]💫 Service Quality:[/]",
            f"[bright_green]✅ Completed Orders:[/] {metrics.total_orders - metrics.refund_count}",
            f"[yellow]🔄 Refunds/Issues:[/] {metrics.refund_count}",
            f"[bright_green]⭐ Customer Satisfaction:[/] {(1 - metrics.refund_rate/100) * 100:.1f}%",
            ""
        ])

        return charts_lines

    def _build_insights_footer(self) -> list[str]:
        """Build footer with insights and recommendations."""
        if not self.sales_metrics:
            return []

        insights = []
        metrics = self.sales_metrics

        # Business insights based on data
        if metrics.average_order_value > 12:
            insights.append("[bright_green]💡 Customers love premium options![/]")
        
        if metrics.refund_rate > 5:
            insights.append("[yellow]💡 Consider staff training on order accuracy[/]")
        
        if metrics.total_orders < 20 and self.show_period == "today":
            insights.append("[light_blue]💡 Try promoting popular items during slow periods[/]")
        
        if metrics.profit_estimate > 50:
            insights.append("[bright_green]💫 Excellent profit margin today![/]")

        # Fun kawaii messages
        kawaii_messages = [
            "🌸 Keep spreading sweetness!",
            "✨ Every cup tells a story!",
            "💝 Kawaii customer service wins hearts!",
            "🥤 Brewing happiness, one bubble tea at a time!",
            "🌈 Making the world sweeter, one sip at a time!"
        ]
        
        import random
        random_message = random.choice(kawaii_messages)
        insights.append(f"[dim italic]{random_message}[/]")

        if insights:
            return [
                "[bold]💡 Sweet Insights:[/]",
                ""
            ] + insights + [""]
        
        return []

    def get_hourly_sales_data(self, orders: list[Order]) -> dict[int, float]:
        """Get hourly sales data from orders.
        
        Args:
            orders: List of orders to analyze
            
        Returns:
            Dictionary mapping hour to revenue
        """
        hourly_revenue = defaultdict(float)
        
        for order in orders:
            if order.created_at.date() == self.current_date:
                hour = order.created_at.hour
                hourly_revenue[hour] += order.total
        
        return dict(hourly_revenue)

    def calculate_trends(self, current_period: SalesMetrics, previous_period: SalesMetrics) -> dict[str, str]:
        """Calculate trends compared to previous period.
        
        Args:
            current_period: Current period metrics
            previous_period: Previous period metrics
            
        Returns:
            Dictionary with trend indicators
        """
        trends = {}
        
        # Revenue trend
        if previous_period.total_revenue > 0:
            revenue_change = ((current_period.total_revenue - previous_period.total_revenue) / 
                            previous_period.total_revenue) * 100
            if revenue_change > 10:
                trends["revenue"] = "[bright_green]↗️ +{:.1f}%[/]".format(revenue_change)
            elif revenue_change < -10:
                trends["revenue"] = "[red]↘️ {:.1f}%[/]".format(revenue_change)
            else:
                trends["revenue"] = "[yellow]→ {:.1f}%[/]".format(revenue_change)
        
        # Order count trend
        if previous_period.total_orders > 0:
            order_change = ((current_period.total_orders - previous_period.total_orders) / 
                          previous_period.total_orders) * 100
            if order_change > 10:
                trends["orders"] = "[bright_green]↗️ +{:.1f}%[/]".format(order_change)
            elif order_change < -10:
                trends["orders"] = "[red]↘️ {:.1f}%[/]".format(order_change)
            else:
                trends["orders"] = "[yellow]→ {:.1f}%[/]".format(order_change)
        
        # Average order value trend
        if previous_period.average_order_value > 0:
            aov_change = ((current_period.average_order_value - previous_period.average_order_value) / 
                         previous_period.average_order_value) * 100
            if aov_change > 5:
                trends["aov"] = "[bright_green]↗️ +{:.1f}%[/]".format(aov_change)
            elif aov_change < -5:
                trends["aov"] = "[red]↘️ {:.1f}%[/]".format(aov_change)
            else:
                trends["aov"] = "[yellow]→ {:.1f}%[/]".format(aov_change)
        
        return trends

    def generate_daily_report(self) -> str:
        """Generate a cute daily sales report.
        
        Returns:
            Formatted daily report string
        """
        if not self.sales_metrics:
            return "No sales data available for today 🌸"
        
        metrics = self.sales_metrics
        
        report_lines = [
            "🌸 Hello Kitty BubbleTea - Daily Report ✨",
            "=" * 40,
            f"📊 Total Revenue: ${metrics.total_revenue:.2f}",
            f"🥤 Orders Completed: {metrics.total_orders}",
            f"💝 Average Order: ${metrics.average_order_value:.2f}",
            f"👥 Unique Customers: {metrics.customer_count}",
            f"💰 Estimated Profit: ${metrics.profit_estimate:.2f}",
            f"⭐ Customer Satisfaction: {(1 - metrics.refund_rate/100) * 100:.1f}%",
            ""
        ]
        
        if metrics.popular_items:
            report_lines.extend([
                "🌟 Most Popular Items:",
                *["  {} {} ({} sold)".format(
                    "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🌟",
                    item[0].name, 
                    item[1]
                ) for i, item in enumerate(metrics.popular_items[:3])]
            ])
        
        report_lines.extend([
            "",
            "🌈 Tomorrow's Goals:",
            f"• Revenue target: ${metrics.total_revenue * 1.1:.2f}",
            f"• Order goal: {int(metrics.total_orders * 1.05)}",
            "",
            "💫 Keep spreading sweetness! 💝"
        ])
        
        return "\n".join(report_lines)

    def export_sales_data(self, format_type: str = "summary") -> dict:
        """Export sales data in various formats.
        
        Args:
            format_type: Type of export ('summary', 'detailed', 'json')
            
        Returns:
            Dictionary with sales data
        """
        if not self.sales_metrics:
            return {"error": "No sales data available"}
        
        if format_type == "summary":
            return {
                "date": self.current_date.isoformat(),
                "total_revenue": self.sales_metrics.total_revenue,
                "total_orders": self.sales_metrics.total_orders,
                "average_order_value": self.sales_metrics.average_order_value,
                "customer_count": self.sales_metrics.customer_count,
                "profit_estimate": self.sales_metrics.profit_estimate
            }
        elif format_type == "detailed":
            return {
                "date": self.current_date.isoformat(),
                "metrics": self.sales_metrics.__dict__,
                "generated_at": datetime.now().isoformat()
            }
        else:  # json format
            return {
                "report": self.generate_daily_report(),
                "data": self.sales_metrics.__dict__
            }
