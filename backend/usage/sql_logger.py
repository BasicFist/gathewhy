import json
import sqlite3
from pathlib import Path

from backend.callbacks import Callback, RequestContext


class SQLUsageLoggerCallback(Callback):
    def __init__(self, db_path: str = "runtime/usage/llm_usage.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    provider TEXT,
                    logical_model TEXT,
                    concrete_model TEXT,
                    capability TEXT,
                    tags_json TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    cost_usd REAL,
                    latency_ms REAL,
                    status TEXT,
                    error_type TEXT
                )
            """
            )
            # Index for querying
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_provider ON usage_logs(provider)")

    def on_request(self, ctx: RequestContext) -> None:
        # We log at end of request
        pass

    def on_success(self, ctx: RequestContext) -> None:
        self._log(ctx)

    def on_error(self, ctx: RequestContext) -> None:
        self._log(ctx)

    def _log(self, ctx: RequestContext):
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO usage_logs (
                        timestamp, provider, logical_model, concrete_model, capability,
                        tags_json, prompt_tokens, completion_tokens, total_tokens,
                        cost_usd, latency_ms, status, error_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        ctx.started_at.isoformat(),
                        ctx.provider,
                        ctx.logical_model,
                        ctx.concrete_model,
                        ctx.capability,
                        json.dumps(ctx.tags) if ctx.tags else "{}",
                        ctx.prompt_tokens,
                        ctx.completion_tokens,
                        ctx.total_tokens,
                        ctx.cost_usd,
                        ctx.latency_ms,
                        ctx.status,
                        ctx.error_type,
                    ),
                )
        except Exception as e:
            print(f"Failed to log to SQLite: {e}")
