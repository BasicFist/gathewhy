"""Entry point for running dashboard as a module.

This allows running the dashboard using:
    python3 -m dashboard
"""

import logging

from .app import DashboardApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
