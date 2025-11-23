from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol


@dataclass
class RequestContext:
    logical_model: str | None = None
    concrete_model: str | None = None
    provider: str | None = None
    capability: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: float | None = None
    status: Literal["success", "error"] | None = None
    error_type: str | None = None
    user_id: str | None = None


class Callback(Protocol):
    def on_request(self, ctx: RequestContext) -> None:
        ...

    def on_success(self, ctx: RequestContext) -> None:
        ...

    def on_error(self, ctx: RequestContext) -> None:
        ...


class CallbackManager:
    def __init__(self):
        self.callbacks: list[Callback] = []

    def register(self, callback: Callback):
        self.callbacks.append(callback)

    def emit_request(self, ctx: RequestContext):
        for cb in self.callbacks:
            try:
                cb.on_request(ctx)
            except Exception as e:
                print(f"Error in callback {cb} on_request: {e}")

    def emit_success(self, ctx: RequestContext):
        for cb in self.callbacks:
            try:
                cb.on_success(ctx)
            except Exception as e:
                print(f"Error in callback {cb} on_success: {e}")

    def emit_error(self, ctx: RequestContext):
        for cb in self.callbacks:
            try:
                cb.on_error(ctx)
            except Exception as e:
                print(f"Error in callback {cb} on_error: {e}")
