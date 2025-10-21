#!/usr/bin/env python3
"""
AI Backend - Web UI for Model Testing & Comparison

Interactive Gradio interface for testing LiteLLM unified backend.
Implements Phase 2.1: Web UI (Gradio)
"""

import time

import gradio as gr
import yaml
from database import RequestDatabase
from openai import OpenAI

# Load configuration
with open("web-ui/config.yaml") as f:
    config = yaml.safe_load(f)

# Initialize OpenAI client for LiteLLM
client = OpenAI(
    base_url=config["litellm"]["base_url"],
    api_key=config["litellm"]["api_key"],
    timeout=config["litellm"]["timeout"],
)

# Initialize database
db = RequestDatabase(config["database"]["path"])


def get_available_models() -> list[str]:
    """Fetch available models from LiteLLM gateway."""
    try:
        models_response = client.models.list()
        return sorted([model.id for model in models_response.data])
    except Exception as e:
        print(f"Error fetching models: {e}")
        return ["llama3.1:8b", "qwen-coder"]  # Fallback defaults


def chat_with_model(
    message: str,
    history: list[tuple[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
) -> tuple[list[tuple[str, str]], str]:
    """
    Send a chat message and get response.

    Args:
        message: User message
        history: Chat history [(user, assistant), ...]
        model: Model name
        temperature: Sampling temperature
        max_tokens: Maximum response tokens
        top_p: Nucleus sampling threshold

    Returns:
        Updated history and timing info
    """
    if not message.strip():
        return history, ""

    # Build messages from history
    messages = []
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if assistant_msg:
            messages.append({"role": "assistant", "content": assistant_msg})

    messages.append({"role": "user", "content": message})

    try:
        start_time = time.time()

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        assistant_message = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason

        # Log to database
        db.log_request(
            model=model,
            messages=messages,
            response=assistant_message,
            provider=None,  # LiteLLM doesn't expose this in response
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            response_time_ms=elapsed_ms,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            finish_reason=finish_reason,
        )

        # Update history
        history.append((message, assistant_message))

        # Timing info
        timing_info = (
            f"⏱️ {elapsed_ms}ms | "
            f"📊 {response.usage.prompt_tokens}→{response.usage.completion_tokens} tokens | "
            f"🏁 {finish_reason}"
        )

        return history, timing_info

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"

        # Log error to database
        db.log_request(
            model=model,
            messages=messages,
            error=str(e),
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )

        history.append((message, error_msg))
        return history, ""


def compare_models(
    message: str,
    selected_models: list[str],
    temperature: float,
    max_tokens: int,
    top_p: float,
) -> list[tuple[str, str, str]]:
    """
    Send the same message to multiple models for comparison.

    Returns:
        List of (model_name, response, timing_info) tuples
    """
    if not message.strip():
        return []

    if not selected_models or len(selected_models) < 2:
        return [("Error", "Please select 2-4 models to compare", "")]

    if len(selected_models) > 4:
        return [("Error", "Maximum 4 models for comparison", "")]

    messages = [{"role": "user", "content": message}]
    results = []

    for model in selected_models:
        try:
            start_time = time.time()

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            assistant_message = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            # Log to database
            db.log_request(
                model=model,
                messages=messages,
                response=assistant_message,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                response_time_ms=elapsed_ms,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                finish_reason=finish_reason,
                metadata={"comparison": True, "models": selected_models},
            )

            timing_info = (
                f"⏱️ {elapsed_ms}ms | "
                f"{response.usage.prompt_tokens}→{response.usage.completion_tokens} tokens"
            )

            results.append((model, assistant_message, timing_info))

        except Exception as e:
            # Log error
            db.log_request(
                model=model,
                messages=messages,
                error=str(e),
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                metadata={"comparison": True, "models": selected_models},
            )

            results.append((model, f"❌ Error: {str(e)}", ""))

    return results


def format_comparison_results(results: list[tuple[str, str, str]]) -> str:
    """Format comparison results for display."""
    if not results:
        return ""

    output = []
    for model, response, timing in results:
        output.append(f"### 🤖 {model}")
        if timing:
            output.append(f"*{timing}*\n")
        output.append(response)
        output.append("\n---\n")

    return "\n".join(output)


def get_analytics_summary() -> str:
    """Get analytics summary for the last 7 days."""
    analytics = db.get_analytics(days=7)

    output = ["# 📊 Analytics (Last 7 Days)\n"]

    output.append(f"**Total Requests**: {analytics['total_requests']}")
    output.append(f"**Avg Response Time**: {analytics['avg_response_time_ms']}ms")
    output.append(f"**Error Rate**: {analytics['error_rate']}%\n")

    output.append("## Token Usage")
    tokens = analytics["tokens"]
    output.append(f"- **Total**: {tokens['total']:,}")
    output.append(f"- **Prompt**: {tokens['prompt']:,}")
    output.append(f"- **Completion**: {tokens['completion']:,}")
    output.append(f"- **Avg per Request**: {tokens['avg_per_request']}\n")

    if analytics["by_model"]:
        output.append("## Requests by Model")
        for item in analytics["by_model"][:5]:  # Top 5
            output.append(f"- **{item['model']}**: {item['count']}")

    if analytics["by_provider"]:
        output.append("\n## Requests by Provider")
        for item in analytics["by_provider"]:
            output.append(f"- **{item['provider']}**: {item['count']}")

    return "\n".join(output)


def get_recent_history(limit: int = 20) -> str:
    """Get recent request history."""
    requests = db.get_recent_requests(limit=limit)

    if not requests:
        return "No requests yet."

    output = ["# 📝 Recent Requests\n"]

    for req in requests:
        timestamp = req["timestamp"]
        model = req["model"]
        messages = eval(req["messages"])  # JSON string to list
        user_msg = messages[-1]["content"][:100]  # First 100 chars

        response_time = f"{req['response_time_ms']}ms" if req["response_time_ms"] else "N/A"
        tokens = req["total_tokens"] if req["total_tokens"] else "N/A"

        output.append(f"**{timestamp}** | {model}")
        output.append(f"> {user_msg}...")
        output.append(f"*{response_time} | {tokens} tokens*\n")

    return "\n".join(output)


# Build Gradio Interface
with gr.Blocks(
    title=config["ui"]["title"],
    theme=config["ui"]["theme"],
) as app:
    gr.Markdown(f"# {config['ui']['title']}")
    gr.Markdown(config["ui"]["description"])

    with gr.Tabs():
        # Tab 1: Chat Interface
        with gr.Tab("💬 Chat"):
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        height=500,
                        label="Conversation",
                        show_copy_button=True,
                    )
                    msg = gr.Textbox(
                        label="Your message",
                        placeholder="Type your message here...",
                        lines=3,
                    )
                    with gr.Row():
                        submit = gr.Button("Send", variant="primary")
                        clear = gr.Button("Clear")

                    timing_display = gr.Markdown("", label="Timing")

                with gr.Column(scale=1):
                    model_dropdown = gr.Dropdown(
                        choices=get_available_models(),
                        value=get_available_models()[0] if get_available_models() else None,
                        label="Model",
                    )

                    temperature = gr.Slider(
                        minimum=config["parameters"]["temperature"]["min"],
                        maximum=config["parameters"]["temperature"]["max"],
                        value=config["parameters"]["temperature"]["default"],
                        step=config["parameters"]["temperature"]["step"],
                        label="Temperature",
                    )

                    max_tokens = gr.Slider(
                        minimum=config["parameters"]["max_tokens"]["min"],
                        maximum=config["parameters"]["max_tokens"]["max"],
                        value=config["parameters"]["max_tokens"]["default"],
                        step=config["parameters"]["max_tokens"]["step"],
                        label="Max Tokens",
                    )

                    top_p = gr.Slider(
                        minimum=config["parameters"]["top_p"]["min"],
                        maximum=config["parameters"]["top_p"]["max"],
                        value=config["parameters"]["top_p"]["default"],
                        step=config["parameters"]["top_p"]["step"],
                        label="Top P",
                    )

            submit.click(
                chat_with_model,
                inputs=[msg, chatbot, model_dropdown, temperature, max_tokens, top_p],
                outputs=[chatbot, timing_display],
            )
            msg.submit(
                chat_with_model,
                inputs=[msg, chatbot, model_dropdown, temperature, max_tokens, top_p],
                outputs=[chatbot, timing_display],
            )
            clear.click(lambda: ([], ""), outputs=[chatbot, timing_display])

        # Tab 2: Model Comparison
        with gr.Tab("🔀 Compare Models"):
            gr.Markdown(
                "Send the same prompt to multiple models and compare responses side-by-side."
            )

            compare_models_select = gr.CheckboxGroup(
                choices=get_available_models(),
                label="Select 2-4 models to compare",
            )

            compare_msg = gr.Textbox(
                label="Prompt",
                placeholder="Enter your prompt here...",
                lines=3,
            )

            with gr.Row():
                compare_temperature = gr.Slider(
                    minimum=config["parameters"]["temperature"]["min"],
                    maximum=config["parameters"]["temperature"]["max"],
                    value=config["parameters"]["temperature"]["default"],
                    step=config["parameters"]["temperature"]["step"],
                    label="Temperature",
                )

                compare_max_tokens = gr.Slider(
                    minimum=config["parameters"]["max_tokens"]["min"],
                    maximum=config["parameters"]["max_tokens"]["max"],
                    value=config["parameters"]["max_tokens"]["default"],
                    step=config["parameters"]["max_tokens"]["step"],
                    label="Max Tokens",
                )

                compare_top_p = gr.Slider(
                    minimum=config["parameters"]["top_p"]["min"],
                    maximum=config["parameters"]["top_p"]["max"],
                    value=config["parameters"]["top_p"]["default"],
                    step=config["parameters"]["top_p"]["step"],
                    label="Top P",
                )

            compare_btn = gr.Button("🚀 Run Comparison", variant="primary")

            comparison_output = gr.Markdown(label="Results")

            compare_btn.click(
                lambda msg, models, temp, max_tok, top_p: format_comparison_results(
                    compare_models(msg, models, temp, max_tok, top_p)
                ),
                inputs=[
                    compare_msg,
                    compare_models_select,
                    compare_temperature,
                    compare_max_tokens,
                    compare_top_p,
                ],
                outputs=comparison_output,
            )

        # Tab 3: Analytics & History
        with gr.Tab("📊 Analytics"):
            with gr.Row():
                refresh_analytics = gr.Button("🔄 Refresh Analytics")
                refresh_history = gr.Button("🔄 Refresh History")

            with gr.Row():
                with gr.Column():
                    analytics_output = gr.Markdown(
                        value=get_analytics_summary(), label="Analytics Summary"
                    )

                with gr.Column():
                    history_output = gr.Markdown(
                        value=get_recent_history(20), label="Recent Requests"
                    )

            refresh_analytics.click(get_analytics_summary, outputs=analytics_output)
            refresh_history.click(get_recent_history, outputs=history_output)

# Launch the app
if __name__ == "__main__":
    app.launch(
        server_name=config["server"]["host"],
        server_port=config["server"]["port"],
        share=config["server"]["share"],
    )
