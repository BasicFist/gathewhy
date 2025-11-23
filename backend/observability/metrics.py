try:
    from prometheus_client import Counter, Histogram
except ImportError:
    print("prometheus_client not found, metrics disabled")
    Counter = None
    Histogram = None

from backend.callbacks import Callback, RequestContext


class PrometheusCallback(Callback):
    def __init__(self):
        if not Counter:
            self.enabled = False
            return
        self.enabled = True

        # Define metrics if not already registered (singleton check roughly)        # We use a prefix to avoid collision with native LiteLLM metrics
        try:
            self.requests_total = Counter(
                "backend_llm_requests_total",
                "Total LLM requests",
                ["provider", "logical_model", "capability", "status"],
            )
            self.latency = Histogram(
                "backend_llm_latency_seconds",
                "LLM Latency",
                ["provider", "logical_model", "capability"],
            )
            self.tokens = Counter(
                "backend_llm_tokens_total",
                "Total Tokens",
                ["provider", "logical_model", "capability", "type"],
            )
            self.cost = Counter(
                "backend_llm_cost_usd_total",
                "Total Cost USD",
                ["provider", "logical_model", "capability"],
            )
            self.budget_exceeded = Counter(
                "backend_llm_budget_exceeded_total", "Budget Exceeded Events", ["scope", "target"]
            )
        except ValueError:
            # Already registered
            pass

    def on_request(self, ctx: RequestContext) -> None:
        pass

    def on_success(self, ctx: RequestContext) -> None:
        if not self.enabled:
            return

        labels = {
            "provider": ctx.provider or "unknown",
            "logical_model": ctx.logical_model or "unknown",
            "capability": ctx.capability or "unknown",
        }

        self.requests_total.labels(**labels, status="success").inc()

        if ctx.latency_ms:
            self.latency.labels(**labels).observe(ctx.latency_ms / 1000.0)

        if ctx.prompt_tokens:
            self.tokens.labels(**labels, type="prompt").inc(ctx.prompt_tokens)
        if ctx.completion_tokens:
            self.tokens.labels(**labels, type="completion").inc(ctx.completion_tokens)

        if ctx.cost_usd:
            self.cost.labels(**labels).inc(ctx.cost_usd)

    def on_error(self, ctx: RequestContext) -> None:
        if not self.enabled:
            return

        labels = {
            "provider": ctx.provider or "unknown",
            "logical_model": ctx.logical_model or "unknown",
            "capability": ctx.capability or "unknown",
        }
        self.requests_total.labels(**labels, status="error").inc()

    def on_budget_exceeded(self, scope: str, target: str) -> None:
        if not self.enabled:
            return
        self.budget_exceeded.labels(scope=scope, target=target).inc()
