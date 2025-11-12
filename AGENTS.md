# Repository Guidelines

## Project Structure & Module Organization
Configuration drives the gateway: edit provider metadata in `config/providers.yaml`, routing in `config/model-mappings.yaml`, and regenerate `config/litellm-unified.yaml` when done. Operational tooling sits in `scripts/` (validation, load, profiling) and `monitoring/` (Prometheus + Grafana stack). Dashboards live in `ai-dashboard/`, and runtime helpers live in `runtime/`. Tests are separated into `tests/unit`, `tests/integration`, and `tests/contract`; co-locate fixtures with the suite they serve.

## Build, Test, and Development Commands
Set up Python 3.11 with `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Essential workflows:
- `ruff check scripts tests` — linting + formatting validation.
- `pytest -m unit` or `pytest -m "integration and not slow"` — targeted suites.
- `./scripts/validate-unified-backend.sh` — end-to-end provider smoke test.
- `python scripts/validate-config-consistency.py` — ensure routing files agree.
- `./scripts/check-port-conflicts.sh --required` — verify LiteLLM/Ollama/vLLM ports.

## Coding Style & Naming Conventions
Follow Ruff defaults: 4-space indentation, double quotes, max line length 100, and modern Python 3.11 syntax (dataclasses, pattern matching, rich type hints). Use snake_case for modules, functions, and file names; reserve UPPER_SNAKE_CASE for constants. YAML keys stay lowercase-with-dashes to satisfy `CONFIG-SCHEMA.md`. CLI scripts should expose a `main()` guard and document usage near the top.

## Testing Guidelines
Pytest discovers `test_*.py` files and `test_*` functions as configured in `pytest.ini`. Place pure logic tests under `tests/unit`, multi-service flows in `tests/integration`, and API/schema guarantees in `tests/contract`. Decorate expensive cases with `@pytest.mark.slow` or provider markers (`requires_ollama`, `requires_vllm`, `requires_redis`) so CI can filter them. Any change touching routing or config must run `pytest -m "unit or contract"` plus `./scripts/validate-unified-backend.sh`.

## Commit & Pull Request Guidelines
Recent history blends Conventional Commit prefixes (`docs:`, `fix(dashboard):`) with short imperative subjects (“Add llama.cpp model catalog”). Match that tone: keep subjects under ~70 characters, explain the why in the body, and group related config edits in a single commit. PRs should link issues or status entries, summarize provider impact, include screenshots for dashboard changes, and list which validation commands ran. Avoid mixing large refactors with urgent fixes so rollback stays simple.

## Configuration & Operational Tips
Treat `config/litellm-unified.yaml` as generated—edit the source YAMLs and run `python scripts/generate-litellm-config.py`. Before merging runtime changes, run `./scripts/check-port-conflicts.sh --all`, `./scripts/monitor-redis-cache.sh --watch`, and, when applicable, `python scripts/profile-latency.py` to baseline performance. Keep secrets in environment variables and document any new ones in `DEPLOYMENT.md`. Capture rollback or feature-flag steps in the PR whenever touching monitoring, routing, or deployment assets.
