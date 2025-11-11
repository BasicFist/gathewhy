# CRUSH Development Guidelines

## Build/Lint/Test Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Code quality (auto-fixes issues)
ruff format scripts/ tests/
ruff check scripts/ tests/ --fix

# Type checking (manual, optional)
mypy scripts/

# Run tests
pytest                          # All tests
pytest -m unit                   # Fast unit tests only
pytest tests/unit/test_ai_dashboard.py::test_dashboard_script_syntax  # Single test
pytest -v -s --tb=short      # Verbose with short tracebacks

# Validation scripts
./scripts/validate-all-configs.sh
python3 scripts/validate-config-schema.py
python3 scripts/validate-config-consistency.py
```

## Code Style Guidelines

### Imports & Formatting
- Use ruff for formatting (100-char line length, double quotes, 4-space indent)
- Imports: `import os`, `from pathlib import Path`, `from typing import Any`
- Type hints: Python 3.11+ syntax (`str | None` not `Optional[str]`)
- Order: stdlib → third-party → local imports

### Naming Conventions
- Functions: `snake_case_with_underscores()`
- Classes: `PascalCaseWithCamel`
- Constants: `UPPER_SNAKE_CASE`
- Files: `kebab-case.sh` or `snake_case.py`
- Private: `_leading_underscore`

### Error Handling
- Use structured logging with loguru via `common_utils.py`
- Prefer specific exceptions: `raise ValueError("message")` over generic `Exception`
- Always include context in error messages
- Use try/except with specific exception types

### Documentation
- Module docstrings with examples (Google style)
- Function docstrings for non-obvious functions
- Use `# pragma: allowlist secret` for any hardcoded secrets in examples
- Include type hints for all public functions

### Configuration
- YAML files use 2-space indentation
- Validate with `scripts/validate-config-schema.py`
- Use environment variable references: `${VARIABLE_NAME}`
- Never edit `config/litellm-unified.yaml` (auto-generated)

### Testing
- Test files: `test_*.py` in `tests/unit/`, `tests/integration/`
- Fixtures in `tests/conftest.py`
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`
- Mock external dependencies in unit tests

### Security
- Never commit secrets or API keys
- Use `.secrets.baseline` for detect-secrets
- Validate all user inputs
- Use parameterized queries to prevent injection
