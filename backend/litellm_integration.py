try:
    from litellm.integrations.custom_logger import CustomLogger
except ImportError:
    # Fallback for when running in environments without litellm (e.g. just testing dashboard)
    class CustomLogger:
        pass


from backend.callbacks import CallbackManager, RequestContext
from backend.observability.metrics import PrometheusCallback
from backend.usage.budgets import BudgetManager
from backend.usage.sql_logger import SQLUsageLoggerCallback


class BackendIntegration(CustomLogger):
    def __init__(self):
        self.callback_manager = CallbackManager()
        self.callback_manager.register(SQLUsageLoggerCallback())
        self.prometheus = PrometheusCallback()
        self.callback_manager.register(self.prometheus)
        self.budget_manager = BudgetManager()

    def log_pre_api_call(self, model, messages, kwargs):
        try:
            ctx = self._build_context(kwargs, model, start=True)
            self.callback_manager.emit_request(ctx)

            # Check budgets
            warning = self.budget_manager.check_budget(ctx)
            if warning:
                print(f"BUDGET WARNING: {warning}")
                # Record metric
                if ctx.provider:
                    self.prometheus.on_budget_exceeded("provider", ctx.provider)
                # We could parse the warning to be more specific but this is a start

            # Save ctx in kwargs to retrieve it in success/failure if needed
            # But LiteLLM might not persist kwargs modifications across calls perfectly in all versions.
            # We'll reconstruct what we can.
        except Exception as e:
            print(f"BackendIntegration pre_call error: {e}")

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        try:
            ctx = self._build_context(kwargs, kwargs.get("model"), start=False)
            ctx.started_at = start_time
            ctx.ended_at = end_time

            if start_time and end_time:
                ctx.latency_ms = (end_time - start_time).total_seconds() * 1000.0

            ctx.status = "success"

            # Extract usage
            usage = getattr(response_obj, "usage", None)
            if usage:
                ctx.prompt_tokens = getattr(usage, "prompt_tokens", 0)
                ctx.completion_tokens = getattr(usage, "completion_tokens", 0)
                ctx.total_tokens = getattr(usage, "total_tokens", 0)

            # Cost (LiteLLM might calculate it, or we calculate it)
            # response_obj._hidden_params might have it
            ctx.cost_usd = kwargs.get("response_cost", 0.0)

            self.callback_manager.emit_success(ctx)
        except Exception as e:
            print(f"BackendIntegration success error: {e}")

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        try:
            ctx = self._build_context(kwargs, kwargs.get("model"), start=False)
            ctx.started_at = start_time
            ctx.ended_at = end_time
            ctx.status = "error"
            # response_obj might be an Exception object in failure event
            ctx.error_type = type(response_obj).__name__ if response_obj else "Unknown"

            self.callback_manager.emit_error(ctx)
        except Exception as e:
            print(f"BackendIntegration failure error: {e}")

    def _build_context(self, kwargs, model, start=True) -> RequestContext:
        # Attempt to extract metadata
        # LiteLLM metadata is often in kwargs.get('litellm_params', {}).get('metadata', {})
        metadata = kwargs.get("litellm_params", {}).get("metadata", {})

        ctx = RequestContext()
        ctx.logical_model = model  # The model requested by user
        # concrete_model is usually model unless mapped.
        # We might find 'model_info' if available.

        ctx.provider = kwargs.get("litellm_params", {}).get("custom_llm_provider")

        # Extract tags/capabilities if passed in metadata
        if isinstance(metadata, dict):
            ctx.capability = metadata.get("capability")
            ctx.tags = metadata.get("tags", {})
            ctx.user_id = metadata.get("user_id")

        return ctx
