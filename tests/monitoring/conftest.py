"""
Pytest configuration for monitoring tests
"""

import pytest
from playwright.sync_api import Browser, BrowserContext


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for monitoring tests"""
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "ignore_https_errors": True,
        "record_video_dir": "tests/monitoring/videos" if False else None,  # Enable for debugging
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configure browser launch arguments"""
    import os

    return {
        **browser_type_launch_args,
        "headless": os.getenv("PLAYWRIGHT_HEADED") != "1",
        "slow_mo": int(os.getenv("PLAYWRIGHT_SLOWMO", "0")),
    }


@pytest.fixture(scope="function")
def context(browser: Browser, browser_context_args):
    """Create a new browser context for each test"""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """Create a new page for each test"""
    page = context.new_page()
    yield page
    page.close()
