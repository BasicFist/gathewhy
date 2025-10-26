# Repository Guidelines

## Project Structure & Module Organization
- Core automation lives in `scripts/`, with validation (`validate-unified-backend.sh`), config reload (`reload-litellm-config.sh`), monitoring, and load testing helpers. Import shared bash helpers from `scripts/common.sh` when extending shell tooling.
- Provider and routing source of truth is in `config/` (`providers.yaml`, `model-mappings.yaml`, `litellm-unified.yaml`). Keep backups in `config/backups/` intact; they are rotated by the tooling.
- Python services, assets, and templates for the admin UI sit in `web-ui/`. Configuration for that UI lives in `web-ui/config.yaml`.
- Tests are grouped under `tests/` by pyramid level (`unit/`, `integration/`, `contract/`, `monitoring/`) and share fixtures via `tests/conftest.py`.
- Documentation references live in `docs/`; operational dashboards and compose files are under `monitoring/`.

## Build, Test & Development Commands
- Bootstrap dependencies: `pip install -r requirements.txt` (Python 3.11 expected).
- Fast validation of the gateway stack: `./scripts/validate-unified-backend.sh`.
- Type check Python tooling: `mypy scripts/`.
- Format and lint: `ruff format scripts tests` followed by `ruff check scripts tests`.
- Run tests selectively:
  - Unit: `pytest tests/unit/ -v`.
  - Integration (providers required): `pytest tests/integration/ -m "not slow"`.
  - Contract shell suite: `bash tests/contract/test_provider_contracts.sh --provider ollama`.

## Coding Style & Naming Conventions
- Python code targets 3.11. Use 4-space indentation, line length ≤100, and prefer double quotes (`ruff` enforces this).
- Module names stay snake_case; pytest files follow `test_*.py`, and fixtures go in `tests/fixtures/`.
- Keep shell scripts POSIX-compliant, sourcing `scripts/common.sh` for shared helpers. Name new scripts with hyphen-separated verbs (`sync-configs.sh`).
- Before committing Python changes, run `ruff format`, `ruff check`, and `mypy` to match CI expectations.

## Testing Guidelines
- Pytest markers are defined in `pytest.ini`; apply `@pytest.mark.integration`, `@pytest.mark.requires_ollama`, etc., so suites can filter reliably.
- Aim to accompany feature work with unit coverage; integration tests should document provider prerequisites in docstrings.
- Contract and rollback validation use shell harnesses—ensure they remain idempotent and exit non-zero on failure.
- Generate coverage when touching routing logic: `pytest tests/unit/ --cov=scripts --cov-report=term`.

## Commit & Pull Request Guidelines
- Follow the Conventional Commits pattern visible in history (`type(scope): short summary`), e.g., `feat(ptui): add provider dashboard bulk actions`. Scope should match top-level directories when possible.
- PRs should describe the change, list validation commands run, and link any tracked issues. Include configuration diffs or screenshots when touching `web-ui/`.
- Expect reviewers to request evidence of `./scripts/validate-unified-backend.sh` and focused pytest suites; paste the command output summary in the PR body.

## Configuration & Deployment Safety
- Always dry-run config changes with `./scripts/reload-litellm-config.sh --validate-only`; follow with the confirmed reload once diff review is complete.
- Run `python3 scripts/validate-config-consistency.py` after editing provider mappings to keep routing coherent.
- For monitoring updates, refresh the Prometheus/Grafana stack via `./scripts/test-monitoring.sh` and note any dashboard migrations in PR notes.
