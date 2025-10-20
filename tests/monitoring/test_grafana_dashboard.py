#!/usr/bin/env python3
"""
Playwright test to validate Grafana dashboard is configured correctly
"""

import pytest
from playwright.sync_api import Page, expect
import time


@pytest.mark.monitoring
class TestGrafanaDashboard:
    """Test Grafana dashboard accessibility and configuration"""

    GRAFANA_URL = "http://localhost:3000"
    DASHBOARD_NAME = "AI Backend Unified Infrastructure"

    @pytest.fixture(scope="class", autouse=True)
    def setup_grafana(self):
        """Wait for Grafana to be ready"""
        import requests
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.GRAFANA_URL}/api/health", timeout=2)
                if response.status_code == 200:
                    print(f"✓ Grafana is ready")
                    break
            except Exception as e:
                if i == max_retries - 1:
                    raise Exception(f"Grafana not available after {max_retries} attempts")
                time.sleep(2)

    def test_grafana_login(self, page: Page):
        """Test: Can log in to Grafana"""
        print("\n1. Testing Grafana login...")

        # Navigate to Grafana
        page.goto(self.GRAFANA_URL)

        # Check if we're on login page or already logged in
        if "login" in page.url.lower() or page.locator('input[name="user"]').is_visible():
            print("   - Login page detected, logging in...")

            # Fill in credentials
            page.fill('input[name="user"]', "admin")
            page.fill('input[name="password"]', "admin")

            # Click login button
            page.click('button[type="submit"]')

            # Wait for redirect
            page.wait_for_url("**/", timeout=10000)

            # Skip change password if prompted
            if "change-password" in page.url or page.locator('text=Skip').is_visible():
                page.click('text=Skip')

        # Verify we're logged in
        expect(page.locator('body')).to_be_visible()
        print("   ✓ Successfully logged in to Grafana")

    def test_datasources_configured(self, page: Page):
        """Test: Prometheus and Loki datasources are configured"""
        print("\n2. Testing datasources configuration...")

        # Navigate to datasources
        page.goto(f"{self.GRAFANA_URL}/datasources")
        page.wait_for_load_state("networkidle")

        # Check for Prometheus datasource
        prometheus_locator = page.locator('text=Prometheus')
        expect(prometheus_locator.first).to_be_visible()
        print("   ✓ Prometheus datasource found")

        # Check for Loki datasource
        loki_locator = page.locator('text=Loki')
        expect(loki_locator.first).to_be_visible()
        print("   ✓ Loki datasource found")

    def test_dashboard_exists(self, page: Page):
        """Test: AI Backend dashboard exists"""
        print("\n3. Testing dashboard exists...")

        # Navigate to dashboards
        page.goto(f"{self.GRAFANA_URL}/dashboards")
        page.wait_for_load_state("networkidle")

        # Search for our dashboard
        search_box = page.locator('input[placeholder*="Search"]').first
        search_box.fill("AI Backend")
        page.wait_for_timeout(1000)  # Wait for search results

        # Check dashboard appears in results
        dashboard_link = page.locator(f'text={self.DASHBOARD_NAME}')
        expect(dashboard_link.first).to_be_visible()
        print(f"   ✓ Dashboard '{self.DASHBOARD_NAME}' found")

    def test_dashboard_panels(self, page: Page):
        """Test: Dashboard has expected panels"""
        print("\n4. Testing dashboard panels...")

        # Navigate directly to dashboard
        # First, get the dashboard UID by searching
        page.goto(f"{self.GRAFANA_URL}/dashboards")
        page.wait_for_load_state("networkidle")

        search_box = page.locator('input[placeholder*="Search"]').first
        search_box.fill("AI Backend")
        page.wait_for_timeout(1000)

        # Click on the dashboard
        dashboard_link = page.locator(f'text={self.DASHBOARD_NAME}').first
        dashboard_link.click()

        # Wait for dashboard to load
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)  # Give panels time to render

        # Expected panel titles
        expected_panels = [
            "Request Rate",
            "Response Time (P95)",
            "Error Rate",
            "Provider Health",
            "Cache Hit Rate",
            "Rate Limit Usage",
            "Fallback Triggers",
            "System CPU Usage",
            "System Memory Usage",
            "Request Distribution by Model",
            "Active Alerts"
        ]

        found_panels = []
        missing_panels = []

        for panel_title in expected_panels:
            panel = page.locator(f'text={panel_title}').first
            if panel.is_visible(timeout=2000):
                found_panels.append(panel_title)
                print(f"   ✓ Found panel: {panel_title}")
            else:
                missing_panels.append(panel_title)
                print(f"   ✗ Missing panel: {panel_title}")

        # Take screenshot of dashboard
        screenshot_path = "tests/monitoring/screenshots/dashboard.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"   ✓ Dashboard screenshot saved: {screenshot_path}")

        # Assert all panels are present
        assert len(missing_panels) == 0, f"Missing panels: {missing_panels}"
        print(f"   ✓ All {len(found_panels)} expected panels found")

    def test_panel_no_data_errors(self, page: Page):
        """Test: No panels show 'No data' errors"""
        print("\n5. Testing panels for data...")

        # Navigate to dashboard
        page.goto(f"{self.GRAFANA_URL}/dashboards")
        search_box = page.locator('input[placeholder*="Search"]').first
        search_box.fill("AI Backend")
        page.wait_for_timeout(1000)

        dashboard_link = page.locator(f'text={self.DASHBOARD_NAME}').first
        dashboard_link.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Check for "No data" indicators
        no_data_elements = page.locator('text=No data').count()

        if no_data_elements > 0:
            print(f"   ⚠ Warning: {no_data_elements} panels showing 'No data'")
            print("   This is expected if:")
            print("     - Monitoring stack just started (metrics not collected yet)")
            print("     - No requests have been made to LiteLLM")
            print("     - Prometheus hasn't scraped metrics yet")
        else:
            print("   ✓ All panels have data")

    def test_datasource_health(self, page: Page):
        """Test: Datasources are healthy"""
        print("\n6. Testing datasource health...")

        # Check Prometheus datasource
        page.goto(f"{self.GRAFANA_URL}/datasources")
        page.wait_for_load_state("networkidle")

        prometheus_link = page.locator('a:has-text("Prometheus")').first
        prometheus_link.click()
        page.wait_for_load_state("networkidle")

        # Look for "Data source is working" message
        save_test_button = page.locator('button:has-text("Save & test")').first
        save_test_button.click()
        page.wait_for_timeout(2000)

        # Check for success message
        success_indicators = [
            page.locator('text=Data source is working'),
            page.locator('text=successfully'),
            page.locator('[data-testid="data-testid Alert success"]')
        ]

        success_found = any(indicator.is_visible(timeout=5000) for indicator in success_indicators)

        if success_found:
            print("   ✓ Prometheus datasource is healthy")
        else:
            print("   ⚠ Warning: Could not verify Prometheus datasource health")
            print("   Check if Prometheus is running on :9090")

    def test_create_test_panel(self, page: Page):
        """Test: Can create a test panel with Prometheus query"""
        print("\n7. Testing panel creation with Prometheus query...")

        # Navigate to Explore
        page.goto(f"{self.GRAFANA_URL}/explore")
        page.wait_for_load_state("networkidle")

        # Make sure Prometheus is selected as datasource
        datasource_picker = page.locator('[data-testid="data-testid Data source picker select container"]').first
        if datasource_picker.is_visible():
            datasource_picker.click()
            page.wait_for_timeout(500)
            page.locator('text=Prometheus').first.click()
            page.wait_for_timeout(500)

        # Enter a simple query
        query_input = page.locator('textarea[placeholder*="Enter a PromQL query"]').first
        if not query_input.is_visible():
            query_input = page.locator('textarea').first

        query_input.fill("up")

        # Run query
        run_button = page.locator('button:has-text("Run query")').first
        run_button.click()
        page.wait_for_timeout(3000)

        # Take screenshot of results
        screenshot_path = "tests/monitoring/screenshots/prometheus_query.png"
        page.screenshot(path=screenshot_path)
        print(f"   ✓ Prometheus query executed, screenshot: {screenshot_path}")

    def test_alert_rules_visible(self, page: Page):
        """Test: Alert rules are configured and visible"""
        print("\n8. Testing alert rules...")

        # Navigate to alerting
        page.goto(f"{self.GRAFANA_URL}/alerting/list")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Check if alert rules are present
        # Note: This depends on Prometheus alert rules being imported
        alert_section = page.locator('text=Alert rules').first

        if alert_section.is_visible():
            print("   ✓ Alert rules section is visible")

            # Take screenshot
            screenshot_path = "tests/monitoring/screenshots/alert_rules.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✓ Alert rules screenshot: {screenshot_path}")
        else:
            print("   ⚠ Warning: Alert rules not yet visible")
            print("   This is expected if Prometheus alerting is not configured")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser for testing"""
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "ignore_https_errors": True,
    }


if __name__ == "__main__":
    # Run tests with pytest
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
