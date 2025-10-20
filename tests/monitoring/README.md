# Monitoring Stack Tests

Automated browser tests using Playwright to validate the Grafana monitoring dashboard.

## What It Tests

1. **Grafana Login**: Verifies you can log in to Grafana
2. **Datasources**: Checks Prometheus and Loki datasources are configured
3. **Dashboard Exists**: Confirms "AI Backend Unified Infrastructure" dashboard is present
4. **Dashboard Panels**: Validates all 11 expected panels are visible:
   - Request Rate
   - Response Time (P95)
   - Error Rate
   - Provider Health
   - Cache Hit Rate
   - Rate Limit Usage
   - Fallback Triggers
   - System CPU Usage
   - System Memory Usage
   - Request Distribution by Model
   - Active Alerts
5. **Panel Data**: Checks panels aren't showing "No data" errors
6. **Datasource Health**: Tests Prometheus datasource connectivity
7. **Query Execution**: Runs a test Prometheus query
8. **Alert Rules**: Verifies alert rules are visible

## Prerequisites

### 1. Install Dependencies

```bash
cd ai-backend-unified
pip install -r requirements.txt
```

This installs:
- `pytest-playwright` - Pytest plugin for Playwright
- `playwright` - Browser automation library

### 2. Install Playwright Browsers

```bash
# Option 1: Via test script
./scripts/test-monitoring.sh --install

# Option 2: Manually
python3 -m playwright install chromium
```

### 3. Start Monitoring Stack

```bash
# Start all monitoring services
systemctl --user start prometheus grafana loki promtail

# Verify they're running
systemctl --user status prometheus grafana
```

### 4. Import Dashboard

```bash
# In Grafana (http://localhost:3000):
# 1. Login (admin/admin)
# 2. Dashboards → Import
# 3. Upload: monitoring/grafana/litellm-dashboard.json
# 4. Select Prometheus datasource
# 5. Click Import
```

## Running the Tests

### Quick Test (Headless)

```bash
./scripts/test-monitoring.sh
```

### Watch Browser (Headed Mode)

```bash
./scripts/test-monitoring.sh --headed
```

This opens a visible browser window so you can see what's being tested.

### Run with Pytest Directly

```bash
# All monitoring tests
pytest -m monitoring -v

# Specific test
pytest tests/monitoring/test_grafana_dashboard.py::TestGrafanaDashboard::test_dashboard_panels -v

# With browser visible
PLAYWRIGHT_HEADED=1 pytest tests/monitoring/test_grafana_dashboard.py -v -s
```

## Output

### Console Output

```
======================================================================
1. Testing Grafana login...
   ✓ Successfully logged in to Grafana

2. Testing datasources configuration...
   ✓ Prometheus datasource found
   ✓ Loki datasource found

3. Testing dashboard exists...
   ✓ Dashboard 'AI Backend Unified Infrastructure' found

4. Testing dashboard panels...
   ✓ Found panel: Request Rate
   ✓ Found panel: Response Time (P95)
   ✓ Found panel: Error Rate
   ...
   ✓ Dashboard screenshot saved: tests/monitoring/screenshots/dashboard.png
   ✓ All 11 expected panels found

5. Testing panels for data...
   ✓ All panels have data

6. Testing datasource health...
   ✓ Prometheus datasource is healthy

7. Testing panel creation with Prometheus query...
   ✓ Prometheus query executed, screenshot: prometheus_query.png

8. Testing alert rules...
   ✓ Alert rules section is visible
======================================================================
```

### Screenshots

Screenshots are automatically saved to `tests/monitoring/screenshots/`:

- `dashboard.png` - Full dashboard view
- `prometheus_query.png` - Prometheus query results
- `alert_rules.png` - Alert rules configuration

Use these screenshots to:
- Verify dashboard layout
- Debug test failures
- Document monitoring setup
- Include in reports/documentation

## Troubleshooting

### "Grafana is not accessible on :3000"

```bash
# Check if Grafana is running
systemctl --user status grafana

# Start if not running
systemctl --user start grafana

# Check logs if failing
journalctl --user -u grafana -n 50
```

### "Prometheus is not accessible on :9090"

```bash
# Check if Prometheus is running
systemctl --user status prometheus

# Start if not running
systemctl --user start prometheus
```

### "playwright not installed"

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install browsers
python3 -m playwright install chromium
```

### "No data" Warnings in Tests

This is expected if:
- Monitoring stack just started (metrics not collected yet)
- No requests have been made to LiteLLM (:4000)
- Prometheus hasn't scraped metrics yet (wait 30 seconds)

**Solution**: Generate some test traffic:

```bash
# Send a few test requests
for i in {1..5}; do
  curl -X POST http://localhost:4000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "llama3.1:8b", "messages": [{"role": "user", "content": "Test"}], "max_tokens": 5}'
  sleep 1
done

# Wait for Prometheus to scrape (15 seconds)
sleep 15

# Re-run tests
./scripts/test-monitoring.sh
```

### Dashboard Not Found

```bash
# Import the dashboard manually:
# 1. Open http://localhost:3000
# 2. Login: admin/admin
# 3. Dashboards → Import
# 4. Upload: monitoring/grafana/litellm-dashboard.json
# 5. Select Prometheus datasource
# 6. Click Import
```

### Test Hangs or Times Out

```bash
# Check if browser can be launched
python3 -m playwright install --dry-run chromium

# If not installed:
python3 -m playwright install chromium

# Run with headed mode to see what's happening
./scripts/test-monitoring.sh --headed
```

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Setup monitoring tests
  run: |
    pip install -r requirements.txt
    python3 -m playwright install chromium --with-deps

- name: Start monitoring stack
  run: |
    # Start Grafana and Prometheus in CI environment
    docker-compose up -d grafana prometheus

- name: Run monitoring tests
  run: |
    ./scripts/test-monitoring.sh
```

## Development

### Adding New Tests

```python
@pytest.mark.monitoring
def test_new_feature(page: Page):
    """Test: Description of what this tests"""
    print("\n9. Testing new feature...")

    page.goto("http://localhost:3000/...")
    # Your test logic

    print("   ✓ New feature works")
```

### Debugging Tests

```bash
# Run with Python debugger
pytest tests/monitoring/test_grafana_dashboard.py --pdb

# Slow down automation (for debugging)
PLAYWRIGHT_SLOWMO=1000 pytest tests/monitoring/test_grafana_dashboard.py -v

# Headed + slow motion
PLAYWRIGHT_HEADED=1 PLAYWRIGHT_SLOWMO=500 pytest tests/monitoring/test_grafana_dashboard.py -v
```

### Taking Additional Screenshots

```python
# In any test
page.screenshot(path="tests/monitoring/screenshots/my_screenshot.png")
page.screenshot(path="full_page.png", full_page=True)
```

## Expected Test Duration

- **Setup**: 2-3 seconds (Grafana health check)
- **Login**: 1-2 seconds
- **Datasources**: 2-3 seconds
- **Dashboard validation**: 5-7 seconds
- **Query execution**: 3-5 seconds
- **Total**: ~20-30 seconds

## Best Practices

1. **Run regularly**: After dashboard changes or Grafana updates
2. **Generate traffic first**: Ensure panels have data before testing
3. **Use screenshots**: Visual confirmation is valuable
4. **Test in CI**: Automate monitoring validation in deployment pipeline
5. **Keep updated**: Update tests when adding new panels

## Related Documentation

- [Monitoring README](../../monitoring/README.md) - Complete monitoring stack documentation
- [Grafana Documentation](https://grafana.com/docs/)
- [Playwright Documentation](https://playwright.dev/python/)
- [pytest-playwright](https://github.com/microsoft/playwright-pytest)
