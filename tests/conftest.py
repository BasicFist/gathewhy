"""
Pytest configuration and shared fixtures for AI Backend Unified Infrastructure tests
"""

import pytest
import yaml
from pathlib import Path
from typing import Dict, Any

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
PROVIDERS_FILE = CONFIG_DIR / "providers.yaml"
MAPPINGS_FILE = CONFIG_DIR / "model-mappings.yaml"
LITELLM_FILE = CONFIG_DIR / "litellm-unified.yaml"


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Project root directory"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def config_dir() -> Path:
    """Configuration directory"""
    return CONFIG_DIR


@pytest.fixture(scope="session")
def providers_config() -> Dict[str, Any]:
    """Load providers.yaml configuration"""
    with open(PROVIDERS_FILE, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def mappings_config() -> Dict[str, Any]:
    """Load model-mappings.yaml configuration"""
    with open(MAPPINGS_FILE, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def litellm_config() -> Dict[str, Any]:
    """Load litellm-unified.yaml configuration"""
    with open(LITELLM_FILE, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def active_providers(providers_config: Dict) -> Dict[str, Dict]:
    """Get all active providers"""
    return {
        name: config
        for name, config in providers_config['providers'].items()
        if config.get('status') == 'active'
    }


@pytest.fixture(scope="session")
def exact_matches(mappings_config: Dict) -> Dict[str, Dict]:
    """Get exact model matches from mappings"""
    return mappings_config.get('exact_matches', {})


@pytest.fixture(scope="session")
def fallback_chains(mappings_config: Dict) -> Dict[str, Dict]:
    """Get fallback chains from mappings"""
    return mappings_config.get('fallback_chains', {})


@pytest.fixture(scope="session")
def capability_routing(mappings_config: Dict) -> Dict[str, Dict]:
    """Get capability-based routing from mappings"""
    return mappings_config.get('capability_routing', {})


@pytest.fixture(scope="session")
def litellm_url() -> str:
    """LiteLLM gateway URL"""
    return "http://localhost:4000"


@pytest.fixture(scope="session")
def provider_urls(providers_config: Dict) -> Dict[str, str]:
    """Map of provider names to their base URLs"""
    return {
        name: config['base_url']
        for name, config in providers_config['providers'].items()
        if config.get('status') == 'active'
    }


# Mock providers for unit testing (no external dependencies)
@pytest.fixture
def mock_providers():
    """Mock provider configuration for unit tests"""
    return {
        'providers': {
            'test_ollama': {
                'type': 'ollama',
                'base_url': 'http://localhost:11434',
                'status': 'active',
                'models': [
                    {'name': 'test-model:7b', 'size': '7B', 'specialty': 'general'}
                ]
            },
            'test_vllm': {
                'type': 'vllm',
                'base_url': 'http://localhost:8001',
                'status': 'active',
                'models': [
                    {'name': 'test-vllm-model', 'size': '13B', 'specialty': 'chat'}
                ]
            },
            'test_disabled': {
                'type': 'ollama',
                'base_url': 'http://localhost:9999',
                'status': 'disabled',
                'models': []
            }
        }
    }


@pytest.fixture
def mock_mappings():
    """Mock model mappings for unit tests"""
    return {
        'exact_matches': {
            'test-model:7b': {
                'provider': 'test_ollama',
                'priority': 'primary',
                'description': 'Test model'
            },
            'test-vllm-model': {
                'provider': 'test_vllm',
                'priority': 'primary',
                'description': 'Test vLLM model'
            }
        },
        'pattern_matches': [
            {
                'pattern': 'test-.*',
                'provider': 'test_ollama',
                'priority': 'secondary'
            }
        ],
        'capability_routing': {
            'test_capability': {
                'models': ['test-model:7b', 'test-vllm-model'],
                'strategy': 'round_robin'
            }
        },
        'fallback_chains': {
            'test-model:7b': {
                'chain': ['test-vllm-model'],
                'strategy': 'immediate'
            }
        },
        'load_balancing': {
            'test-redundant': {
                'providers': [
                    {'provider': 'test_ollama', 'weight': 0.7},
                    {'provider': 'test_vllm', 'weight': 0.3}
                ]
            }
        }
    }


# Helper functions available to all tests
def load_yaml_file(file_path: Path) -> Dict:
    """Helper to load YAML file"""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def validate_url_format(url: str) -> bool:
    """Helper to validate URL format"""
    import re
    pattern = r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$'
    return bool(re.match(pattern, url))


def validate_port_range(port: int) -> bool:
    """Helper to validate port is in valid range"""
    return 1 <= port <= 65535
