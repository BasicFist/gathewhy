import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from backend.callbacks import RequestContext


class BudgetManager:
    def __init__(
        self,
        config_path: str = "runtime/budget_config.json",
        db_path: str = "runtime/usage/llm_usage.db",
    ):
        self.config_path = Path(config_path)
        self.db_path = Path(db_path)
        self.budgets = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading budget config: {e}")
            return {}

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def check_budget(self, ctx: RequestContext) -> str | None:
        """
        Check if request exceeds any budget.
        Returns warning message if exceeded, None otherwise.
        """
        if not self.budgets:
            return None

        warnings = []

        # Check Provider Budget
        if ctx.provider and ctx.provider in self.budgets.get("providers", {}):
            b = self.budgets["providers"][ctx.provider]
            spent = self._calculate_spend(
                column="provider", value=ctx.provider, window=b.get("budget_window")
            )
            if spent >= b.get("max_budget_usd", float("inf")):
                warnings.append(
                    f"Provider '{ctx.provider}' over budget ({spent:.2f} >= {b['max_budget_usd']})"
                )

        # Check Logical Model Budget
        if ctx.logical_model and ctx.logical_model in self.budgets.get("models", {}):
            b = self.budgets["models"][ctx.logical_model]
            spent = self._calculate_spend(
                column="logical_model", value=ctx.logical_model, window=b.get("budget_window")
            )
            if spent >= b.get("max_budget_usd", float("inf")):
                warnings.append(
                    f"Model '{ctx.logical_model}' over budget ({spent:.2f} >= {b['max_budget_usd']})"
                )

        # Check Capability Budget
        if ctx.capability and ctx.capability in self.budgets.get("capabilities", {}):
            b = self.budgets["capabilities"][ctx.capability]
            spent = self._calculate_spend(
                column="capability", value=ctx.capability, window=b.get("budget_window")
            )
            if spent >= b.get("max_budget_usd", float("inf")):
                warnings.append(
                    f"Capability '{ctx.capability}' over budget ({spent:.2f} >= {b['max_budget_usd']})"
                )

        if warnings:
            return "; ".join(warnings)
        return None

    def _calculate_spend(self, column: str, value: str, window: str) -> float:
        if not self.db_path.exists():
            return 0.0

        start_time = self._window_to_timestamp(window)
        if not start_time:
            return 0.0

        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    f"""
                    SELECT SUM(cost_usd) FROM usage_logs
                    WHERE {column} = ? AND timestamp >= ?
                """,
                    (value, start_time.isoformat()),
                )
                result = cursor.fetchone()
                return result[0] or 0.0
        except Exception as e:
            print(f"Error calculating spend: {e}")
            return 0.0

    def _window_to_timestamp(self, window: str) -> datetime | None:
        if not window:
            return None
        now = datetime.now()
        if window == "1h":
            return now - timedelta(hours=1)
        if window == "1d":
            return now - timedelta(days=1)
        if window == "7d":
            return now - timedelta(days=7)
        if window == "30d":
            return now - timedelta(days=30)
        return None
