#!/usr/bin/env python3
"""
Model Routing Visualizer - Interactive visualization of model-to-provider routing
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_config():
    """Load the unified configuration"""
    config_dir = Path("/home/miko/LAB/ai/backend/ai-backend-unified/config")
    providers_file = config_dir / "providers.yaml"
    mappings_file = config_dir / "model-mappings.yaml"

    if not providers_file.exists():
        print(f"❌ Provider config not found: {providers_file}")
        return None, None

    if not mappings_file.exists():
        print(f"❌ Model mappings not found: {mappings_file}")
        return None, None

    with open(providers_file) as f:
        providers = yaml.safe_load(f).get("providers", {})

    with open(mappings_file) as f:
        mappings = yaml.safe_load(f)

    return providers, mappings


def generate_visualization(providers, mappings):
    """Generate ASCII visualization of routing"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║               MODEL ROUTING VISUALIZER                      ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Legend:                                                    ║")
    print("║    🟢 = Active Provider     🔴 = Inactive Provider          ║")
    print("║    🔄 = Primary Route        ↪️  = Fallback Route            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Show provider status
    print("/providers")
    print("├─ Active Providers:")
    for provider_name, provider_data in providers.items():
        if provider_data.get("status") == "active":
            emoji = "🟢" if provider_data.get("status") == "active" else "🔴"
            print(f"│  ├─ {emoji} {provider_name} ({provider_data.get('type', 'unknown')})")
            models = provider_data.get("models", [])
            if models:
                for model in models[:3]:  # Show first 3 models
                    model_name = model if isinstance(model, str) else model.get("name", "unknown")
                    print(f"│  │  └─ {model_name}")
                if len(models) > 3:
                    print(f"│  │  └─ ... and {len(models)-3} more")

    print("├─ Inactive Providers:")
    for provider_name, provider_data in providers.items():
        if provider_data.get("status") != "active":
            emoji = "🔴"
            print(f"│  └─ {emoji} {provider_name} ({provider_data.get('type', 'unknown')})")

    print()

    # Show model routing
    print("/model-routing")
    if mappings:
        exact_matches = mappings.get("exact_matches", {})
        if exact_matches:
            print("├─ Exact Model Matches:")
            for model, route_info in list(exact_matches.items())[:10]:  # Show first 10
                provider = route_info.get("provider", "unknown")
                fallback = route_info.get("fallback", "none")
                provider_status = providers.get(provider, {}).get("status", "unknown")

                status_emoji = "🟢" if provider_status == "active" else "🔴"
                fallback_arrow = "↪️" if fallback != "none" and fallback else ""
                fallback_text = (
                    f" {fallback_arrow} {fallback}" if fallback and fallback != "none" else ""
                )

                print(f"│  ├─ {model} → {status_emoji} {provider}{fallback_text}")

        patterns = []
        if "patterns" in mappings:
            patterns = mappings.get("patterns", [])
        elif "routing_rules" in mappings:
            patterns = mappings.get("routing_rules", [])
        elif isinstance(mappings, dict) and any(isinstance(v, list) for v in mappings.values()):
            # Fallback: find any list value that might contain patterns
            for _, value in mappings.items():
                if (
                    isinstance(value, list)
                    and value
                    and isinstance(value[0], dict)
                    and "pattern" in value[0]
                ):
                    patterns = value
                    break

        if patterns:
            print("├─ Pattern-Based Routing:")
            for pattern in patterns[:5]:  # Show first 5
                if isinstance(pattern, dict):
                    pattern_str = pattern.get("pattern", "unknown")
                    provider_str = pattern.get("provider", "unknown")
                    print(f"│  ├─ {pattern_str} → {provider_str}")
                else:
                    print(f"│  ├─ {pattern}")
            if len(patterns) > 5:
                print(f"│  └─ ... and {len(patterns)-5} more patterns")

    print()

    # Show routing statistics
    active_providers = [p for p, data in providers.items() if data.get("status") == "active"]
    print(".routing-stats")
    print(f"├─ Total Active Providers: {len(active_providers)}")
    print(f"├─ Total Model Routes: {len(exact_matches)}")
    print(f"├─ Total Pattern Routes: {len(patterns)}")
    print()

    # Show usage recommendations
    print(".usage")
    print("├─ Use unified endpoint: http://localhost:4000")
    print("├─ Request models by name (e.g., 'llama3.1:8b')")
    print("├─ LiteLLM will route to appropriate provider automatically")
    print("└─ Fallback chains provide redundancy for unavailable models")
    print()


def generate_dot_graph(providers, mappings, output_file="model-routing.dot"):
    """Generate DOT graph for visualization"""
    with open(output_file, "w") as f:
        f.write("digraph ModelRouting {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=box, style=rounded];\n")
        f.write("  edge [fontname=Arial, fontsize=10];\n\n")

        # Add providers
        for provider_name, provider_data in providers.items():
            status = provider_data.get("status", "unknown")
            color = "green" if status == "active" else "red"
            f.write(f'  "{provider_name}" [color={color}, fillcolor=lightgray, style=filled];\n')

        # Add models and connections
        if mappings:
            exact_matches = mappings.get("exact_matches", {})
            for model, route_info in exact_matches.items():
                provider = route_info.get("provider", "unknown")
                fallback = route_info.get("fallback", "none")

                f.write(f'  "{model}" -> "{provider}" [label="primary"];\n')

                if fallback != "none" and fallback:
                    f.write(
                        f'  "{model}" -> "{fallback}" [label="fallback", style=dashed, color=orange];\n'
                    )

        f.write("}\n")

    print(f"_DOT graph generated: {output_file}")
    print(f"  To visualize: dot -Tpng {output_file} -o model-routing.png")
    print("  Or use online DOT viewer (e.g., https://dreampuf.github.io/GraphvizOnline/)")
    print()


def main():
    parser = argparse.ArgumentParser(description="Model Routing Visualizer")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--dot", action="store_true", help="Generate DOT graph")
    parser.add_argument("--output", "-o", help="Output file for DOT graph")

    args = parser.parse_args()

    providers, mappings = load_config()

    if providers is None or mappings is None:
        print("❌ Failed to load configuration")
        sys.exit(1)

    if args.json:
        # Output in JSON format
        result = {
            "providers": providers,
            "mappings": mappings,
            "visualization": "ASCII diagram available in normal mode",
        }
        print(json.dumps(result, indent=2))
    elif args.dot:
        # Generate DOT graph
        output_file = args.output or "model-routing.dot"
        generate_dot_graph(providers, mappings, output_file)
    else:
        # Generate ASCII visualization
        generate_visualization(providers, mappings)


if __name__ == "__main__":
    main()
