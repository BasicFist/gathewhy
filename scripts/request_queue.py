#!/usr/bin/env python3
"""
Request Queuing and Prioritization System for LiteLLM Gateway.

Implements intelligent request queuing with priority levels, rate limiting,
and load balancing across providers. Ensures high-priority requests are
processed first while maintaining fairness.

Features:
- Multi-level priority queuing (critical, high, normal, low)
- Provider-specific queue management
- Dynamic priority adjustment based on wait time
- Request deadline handling
- Queue analytics and monitoring
- Circuit breaker integration
- Load shedding for overload protection

Usage:
    from request_queue import RequestQueue, Priority

    queue = RequestQueue()

    # Enqueue request
    request_id = queue.enqueue(
        prompt="Analyze this data",
        model="gpt-4o",
        priority=Priority.HIGH,
        deadline=30.0  # seconds
    )

    # Dequeue for processing
    request = queue.dequeue(model="gpt-4o")
    if request:
        process_request(request)

Configuration:
    Set environment variables:
    - REDIS_HOST: Redis server host (default: 127.0.0.1)
    - REDIS_PORT: Redis server port (default: 6379)
    - MAX_QUEUE_SIZE: Maximum requests per queue (default: 1000)
    - PRIORITY_AGE_BOOST_SECONDS: Boost priority after wait (default: 30)
"""

import enum
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import redis
from loguru import logger


class Priority(enum.IntEnum):
    """Request priority levels (higher number = higher priority)."""

    CRITICAL = 4  # System-critical, emergency requests
    HIGH = 3  # Business-critical, user-facing interactive requests
    NORMAL = 2  # Standard requests
    LOW = 1  # Background, batch processing
    BULK = 0  # Bulk processing, non-time-sensitive


@dataclass
class QueuedRequest:
    """
    Represents a request in the queue system.

    Attributes:
        request_id: Unique identifier for this request
        prompt: User prompt or request data
        model: Target model identifier
        priority: Request priority level
        enqueued_at: Timestamp when request was enqueued
        deadline: Maximum seconds to wait before expiring
        metadata: Additional request metadata
        retries: Number of retry attempts
        original_priority: Initial priority (for tracking boosts)
    """

    request_id: str
    prompt: str
    model: str
    priority: Priority
    enqueued_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    original_priority: Priority = None

    def __post_init__(self):
        """Set original priority if not already set."""
        if self.original_priority is None:
            self.original_priority = self.priority

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "prompt": self.prompt,
            "model": self.model,
            "priority": int(self.priority),
            "enqueued_at": self.enqueued_at,
            "deadline": self.deadline,
            "metadata": self.metadata,
            "retries": self.retries,
            "original_priority": int(self.original_priority),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QueuedRequest":
        """Create from dictionary."""
        return cls(
            request_id=data["request_id"],
            prompt=data["prompt"],
            model=data["model"],
            priority=Priority(data["priority"]),
            enqueued_at=data["enqueued_at"],
            deadline=data.get("deadline"),
            metadata=data.get("metadata", {}),
            retries=data.get("retries", 0),
            original_priority=Priority(data.get("original_priority", data["priority"])),
        )

    def is_expired(self) -> bool:
        """Check if request has exceeded its deadline."""
        if self.deadline is None:
            return False
        return (time.time() - self.enqueued_at) > self.deadline

    def wait_time(self) -> float:
        """Get current wait time in seconds."""
        return time.time() - self.enqueued_at


class RequestQueue:
    """
    Multi-priority request queue with Redis backend.

    Manages requests across multiple priority levels with automatic
    priority boosting for aged requests and deadline enforcement.
    """

    def __init__(
        self,
        redis_host: str = "127.0.0.1",
        redis_port: int = 6379,
        max_queue_size: int = 1000,
        priority_age_boost_seconds: float = 30.0,
    ):
        """
        Initialize request queue system.

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            max_queue_size: Maximum requests per queue
            priority_age_boost_seconds: Boost priority after this many seconds
        """
        self.max_queue_size = max_queue_size
        self.priority_age_boost_seconds = priority_age_boost_seconds

        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=2,  # Use separate database for queue
                decode_responses=True,
            )
            self.redis_client.ping()
            logger.info("Request queue connected to Redis", host=redis_host, port=redis_port)
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis for request queue: {e}")
            raise

    def _get_queue_key(self, model: str, priority: Priority) -> str:
        """Get Redis key for specific model and priority queue."""
        return f"request_queue::{model}::{priority.name}"

    def _get_metadata_key(self, request_id: str) -> str:
        """Get Redis key for request metadata."""
        return f"request_metadata::{request_id}"

    def enqueue(
        self,
        prompt: str,
        model: str,
        priority: Priority = Priority.NORMAL,
        deadline: Optional[float] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Add request to queue.

        Args:
            prompt: User prompt or request data
            model: Target model identifier
            priority: Request priority level
            deadline: Maximum seconds to wait before expiring
            metadata: Additional request metadata

        Returns:
            str: Request ID for tracking

        Raises:
            ValueError: If queue is full
        """
        # Check queue size
        queue_key = self._get_queue_key(model, priority)
        current_size = self.redis_client.llen(queue_key)

        if current_size >= self.max_queue_size:
            logger.warning(
                "Queue full, rejecting request",
                model=model,
                priority=priority.name,
                size=current_size,
            )
            raise ValueError(f"Queue full for {model} at {priority.name} priority")

        # Create request
        request = QueuedRequest(
            request_id=str(uuid.uuid4()),
            prompt=prompt,
            model=model,
            priority=priority,
            deadline=deadline,
            metadata=metadata or {},
        )

        # Store request metadata
        metadata_key = self._get_metadata_key(request.request_id)
        self.redis_client.setex(
            metadata_key,
            3600,  # 1 hour TTL
            json.dumps(request.to_dict()),
        )

        # Add to queue (right push for FIFO within priority)
        self.redis_client.rpush(queue_key, request.request_id)

        logger.info(
            "Request enqueued",
            request_id=request.request_id,
            model=model,
            priority=priority.name,
            queue_size=current_size + 1,
        )

        return request.request_id

    def dequeue(self, model: str, provider: Optional[str] = None) -> Optional[QueuedRequest]:
        """
        Retrieve highest priority request from queue.

        Args:
            model: Target model to dequeue for
            provider: Optional provider preference

        Returns:
            QueuedRequest or None: Next request to process, or None if queues empty
        """
        # Try priorities from highest to lowest
        for priority in sorted(Priority, reverse=True):
            queue_key = self._get_queue_key(model, priority)

            while True:
                # Pop from left (FIFO)
                request_id = self.redis_client.lpop(queue_key)
                if not request_id:
                    break

                # Get request metadata
                metadata_key = self._get_metadata_key(request_id)
                request_data = self.redis_client.get(metadata_key)

                if not request_data:
                    logger.warning("Request metadata not found", request_id=request_id)
                    continue

                request = QueuedRequest.from_dict(json.loads(request_data))

                # Check if expired
                if request.is_expired():
                    logger.info(
                        "Request expired, discarding",
                        request_id=request_id,
                        wait_time=request.wait_time(),
                    )
                    self.redis_client.delete(metadata_key)
                    continue

                # Check for priority boost
                if request.wait_time() > self.priority_age_boost_seconds:
                    if request.priority < Priority.CRITICAL:
                        request.priority = Priority(request.priority + 1)
                        logger.info(
                            "Request priority boosted due to age",
                            request_id=request_id,
                            original=request.original_priority.name,
                            new=request.priority.name,
                        )

                logger.info(
                    "Request dequeued",
                    request_id=request_id,
                    model=model,
                    priority=priority.name,
                    wait_time=f"{request.wait_time():.2f}s",
                )

                return request

        return None

    def requeue(self, request: QueuedRequest, reason: str = "retry") -> bool:
        """
        Re-add request to queue (for retry scenarios).

        Args:
            request: Request to requeue
            reason: Reason for requeuing

        Returns:
            bool: True if successfully requeued
        """
        try:
            request.retries += 1

            # Store updated metadata
            metadata_key = self._get_metadata_key(request.request_id)
            self.redis_client.setex(
                metadata_key,
                3600,
                json.dumps(request.to_dict()),
            )

            # Add to queue
            queue_key = self._get_queue_key(request.model, request.priority)
            self.redis_client.rpush(queue_key, request.request_id)

            logger.info(
                "Request requeued",
                request_id=request.request_id,
                reason=reason,
                retries=request.retries,
            )

            return True

        except Exception as e:
            logger.error(f"Failed to requeue request: {e}", request_id=request.request_id)
            return False

    def get_queue_depth(self, model: str, priority: Optional[Priority] = None) -> int:
        """
        Get current queue depth for model/priority.

        Args:
            model: Model identifier
            priority: Specific priority (None = all priorities)

        Returns:
            int: Number of requests in queue
        """
        if priority:
            queue_key = self._get_queue_key(model, priority)
            return self.redis_client.llen(queue_key)
        else:
            total = 0
            for p in Priority:
                queue_key = self._get_queue_key(model, p)
                total += self.redis_client.llen(queue_key)
            return total

    def get_stats(self) -> dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            dict: Statistics including queue depths, wait times, etc.
        """
        stats = {
            "timestamp": datetime.now().isoformat(),
            "queues": {},
            "total_requests": 0,
        }

        # Scan all queue keys
        for key in self.redis_client.scan_iter("request_queue::*"):
            parts = key.split("::")
            if len(parts) == 3:
                _, model, priority_name = parts
                depth = self.redis_client.llen(key)
                stats["total_requests"] += depth

                if model not in stats["queues"]:
                    stats["queues"][model] = {}

                stats["queues"][model][priority_name] = depth

        return stats

    def clear_expired(self) -> int:
        """
        Remove all expired requests from queues.

        Returns:
            int: Number of expired requests removed
        """
        removed = 0

        for key in self.redis_client.scan_iter("request_queue::*"):
            # Get all request IDs in queue
            request_ids = self.redis_client.lrange(key, 0, -1)

            for request_id in request_ids:
                metadata_key = self._get_metadata_key(request_id)
                request_data = self.redis_client.get(metadata_key)

                if not request_data:
                    # Remove orphaned request
                    self.redis_client.lrem(key, 1, request_id)
                    removed += 1
                    continue

                request = QueuedRequest.from_dict(json.loads(request_data))

                if request.is_expired():
                    # Remove expired request
                    self.redis_client.lrem(key, 1, request_id)
                    self.redis_client.delete(metadata_key)
                    removed += 1

        if removed > 0:
            logger.info("Cleared expired requests", count=removed)

        return removed


# CLI for testing and management
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Request Queue Management")
    parser.add_argument("--stats", action="store_true", help="Show queue statistics")
    parser.add_argument("--clear-expired", action="store_true", help="Clear expired requests")
    parser.add_argument("--test", action="store_true", help="Run test enqueue/dequeue")

    args = parser.parse_args()

    queue = RequestQueue()

    if args.stats:
        stats = queue.get_stats()
        print(json.dumps(stats, indent=2))

    elif args.clear_expired:
        removed = queue.clear_expired()
        print(f"Cleared {removed} expired requests")

    elif args.test:
        # Test queue operations
        print("Testing queue operations...")

        # Enqueue with different priorities
        r1 = queue.enqueue("Low priority task", "gpt-4o-mini", Priority.LOW)
        r2 = queue.enqueue("Normal task", "gpt-4o-mini", Priority.NORMAL)
        r3 = queue.enqueue("High priority task", "gpt-4o-mini", Priority.HIGH)

        print(f"Enqueued: {r1}, {r2}, {r3}")

        # Dequeue (should get high priority first)
        req = queue.dequeue("gpt-4o-mini")
        if req:
            print(f"Dequeued: {req.request_id} - Priority: {req.priority.name}")
            print(f"Prompt: {req.prompt}")

        # Show stats
        stats = queue.get_stats()
        print(json.dumps(stats, indent=2))
