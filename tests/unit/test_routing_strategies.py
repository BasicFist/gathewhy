from pathlib import Path

import pytest
import yaml

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
MAPPINGS_FILE = CONFIG_DIR / "model-mappings.yaml"


@pytest.fixture
def mappings():
    with open(MAPPINGS_FILE) as f:
        return yaml.safe_load(f)


def test_capabilities_structure(mappings):
    """Verify the 8 canonical capabilities are present."""
    caps = mappings.get("capabilities", {})
    expected = {
        "code",
        "analytical",
        "reasoning",
        "creative",
        "chat",
        "high_throughput",
        "low_latency",
        "large_context",
    }
    assert set(caps.keys()) == expected


def test_code_capability_strategy(mappings):
    """Verify code capability uses complexity-based routing."""
    code_cap = mappings["capabilities"]["code"]
    assert code_cap["routing_strategy"] == "complexity_based"
    assert "complexity_thresholds" in code_cap
    assert "high" in code_cap["complexity_thresholds"]


def test_fallback_chains_structure(mappings):
    """Verify fallback chains are defined for key models."""
    chains = mappings.get("fallback_chains", {})
    assert "llama3.1:latest" in chains
    assert "qwen2.5-coder:7b" in chains
    assert "default" in chains

    # Verify local chain structure
    llama_chain = chains["llama3.1:latest"]["chain"]
    assert isinstance(llama_chain, list)
    assert len(llama_chain) > 0


def test_load_balancing_strategies(mappings):
    """Verify load balancing strategies."""
    lb = mappings.get("load_balancing", {})
    assert "llama3.1:latest" in lb
    assert lb["llama3.1:latest"]["strategy"] == "weighted_round_robin"

    assert "code-generation" in lb
    assert lb["code-generation"]["strategy"] == "adaptive_weighted"


def test_pattern_routing(mappings):
    """Verify regex patterns exist."""
    patterns = mappings.get("patterns", [])
    assert any("Qwen" in p["pattern"] for p in patterns)
    assert any("gguf" in p["pattern"] for p in patterns)
