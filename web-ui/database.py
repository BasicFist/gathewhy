"""
Database operations for request tracking and analytics.

Implements Phase 2.2: Request History & Analytics
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class RequestDatabase:
    """SQLite database for tracking all LiteLLM requests."""

    def __init__(self, db_path: str = "web-ui/requests.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """Create database schema if tables don't exist."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model TEXT NOT NULL,
                    provider TEXT,
                    messages TEXT NOT NULL,  -- JSON array
                    temperature REAL,
                    max_tokens INTEGER,
                    top_p REAL,
                    response TEXT,
                    response_time_ms INTEGER,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    finish_reason TEXT,
                    error TEXT,
                    metadata TEXT  -- JSON object
                )
            """
            )

            # Indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_model ON requests(model)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON requests(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_provider ON requests(provider)")

            conn.commit()

    def log_request(
        self,
        model: str,
        messages: list[dict[str, str]],
        response: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        response_time_ms: int | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        finish_reason: str | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Log a request to the database.

        Returns:
            Request ID of the inserted row
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO requests (
                    model, provider, messages, temperature, max_tokens, top_p,
                    response, response_time_ms, prompt_tokens, completion_tokens,
                    total_tokens, finish_reason, error, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model,
                    provider,
                    json.dumps(messages),
                    temperature,
                    max_tokens,
                    top_p,
                    response,
                    response_time_ms,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    finish_reason,
                    error,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_requests(
        self, limit: int = 50, model: str | None = None
    ) -> list[dict[str, Any]]:
        """Get recent requests, optionally filtered by model."""
        query = "SELECT * FROM requests"
        params = []

        if model:
            query += " WHERE model = ?"
            params.append(model)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def get_request_by_id(self, request_id: int) -> dict[str, Any] | None:
        """Get a specific request by ID."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()

        return dict(row) if row else None

    def search_requests(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        model: str | None = None,
        provider: str | None = None,
        has_error: bool | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Search requests with filters."""
        query = "SELECT * FROM requests WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        if model:
            query += " AND model = ?"
            params.append(model)

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        if has_error is not None:
            if has_error:
                query += " AND error IS NOT NULL"
            else:
                query += " AND error IS NULL"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def get_analytics(self, days: int = 7) -> dict[str, Any]:
        """Get analytics for the last N days."""
        cutoff = datetime.now() - timedelta(days=days)

        with self._get_connection() as conn:
            # Total requests
            total_requests = conn.execute(
                "SELECT COUNT(*) FROM requests WHERE timestamp >= ?",
                (cutoff.isoformat(),),
            ).fetchone()[0]

            # Requests by model
            by_model = conn.execute(
                """
                SELECT model, COUNT(*) as count
                FROM requests
                WHERE timestamp >= ?
                GROUP BY model
                ORDER BY count DESC
                """,
                (cutoff.isoformat(),),
            ).fetchall()

            # Requests by provider
            by_provider = conn.execute(
                """
                SELECT provider, COUNT(*) as count
                FROM requests
                WHERE timestamp >= ? AND provider IS NOT NULL
                GROUP BY provider
                ORDER BY count DESC
                """,
                (cutoff.isoformat(),),
            ).fetchall()

            # Average response time
            avg_response_time = conn.execute(
                """
                SELECT AVG(response_time_ms) as avg_ms
                FROM requests
                WHERE timestamp >= ? AND response_time_ms IS NOT NULL
                """,
                (cutoff.isoformat(),),
            ).fetchone()[0]

            # Token usage
            token_stats = conn.execute(
                """
                SELECT
                    SUM(prompt_tokens) as total_prompt,
                    SUM(completion_tokens) as total_completion,
                    SUM(total_tokens) as total_all,
                    AVG(total_tokens) as avg_per_request
                FROM requests
                WHERE timestamp >= ? AND total_tokens IS NOT NULL
                """,
                (cutoff.isoformat(),),
            ).fetchone()

            # Error rate
            error_count = conn.execute(
                """
                SELECT COUNT(*) FROM requests
                WHERE timestamp >= ? AND error IS NOT NULL
                """,
                (cutoff.isoformat(),),
            ).fetchone()[0]

        return {
            "total_requests": total_requests,
            "by_model": [{"model": row[0], "count": row[1]} for row in by_model],
            "by_provider": [{"provider": row[0], "count": row[1]} for row in by_provider],
            "avg_response_time_ms": (round(avg_response_time, 2) if avg_response_time else 0),
            "tokens": {
                "prompt": token_stats[0] or 0,
                "completion": token_stats[1] or 0,
                "total": token_stats[2] or 0,
                "avg_per_request": (round(token_stats[3], 2) if token_stats[3] else 0),
            },
            "error_count": error_count,
            "error_rate": (
                round(error_count / total_requests * 100, 2) if total_requests > 0 else 0
            ),
        }

    def cleanup_old_requests(self, days: int = 30) -> int:
        """Delete requests older than N days. Returns number deleted."""
        cutoff = datetime.now() - timedelta(days=days)

        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM requests WHERE timestamp < ?", (cutoff.isoformat(),))
            conn.commit()
            return cursor.rowcount

    def export_to_csv(self, output_path: str, days: int | None = None):
        """Export requests to CSV file."""
        import csv

        query = "SELECT * FROM requests"
        params = []

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            query += " WHERE timestamp >= ?"
            params.append(cutoff.isoformat())

        query += " ORDER BY timestamp DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        with open(output_path, "w", newline="") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows([dict(row) for row in rows])

    def export_to_json(self, output_path: str, days: int | None = None):
        """Export requests to JSON file."""
        query = "SELECT * FROM requests"
        params = []

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            query += " WHERE timestamp >= ?"
            params.append(cutoff.isoformat())

        query += " ORDER BY timestamp DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        with open(output_path, "w") as f:
            json.dump([dict(row) for row in rows], f, indent=2, default=str)
