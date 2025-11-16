# Codex Guardrails (LAB)

When you need AI configs or prompts on this machine:
1. Use the canonical directories under `~/LAB/config/<agent>/` (configs, prompts, secrets live there).
2. Shared behavior docs live under `~/LAB/docs/ai/shared/` — start with `MASTER-INDEX.md`.
3. Native paths such as `~/.codex`, `~/.config/qwen-code`, `~/.config/kimi`, `~/.ollama`, and `~/.copilot` are symlinks into that LAB tree. If you add files, place them under LAB first and symlink if needed.
4. Never treat anything inside `~/LAB/archive/**` (Claude/Serena/other legacy) as live config unless the operator explicitly pastes content.
5. Log structural moves in `~/LAB/config/MIGRATION_LOG.md`.

--- project-doc ---

# Repository Guidelines

## Project Structure & Module Organization
- `config/` holds provider registries (`providers.yaml`), routing tables (`model-mappings.yaml`), and LiteLLM gateway settings; treat these as the single source of truth when adding capacity.
- `scripts/` groups operational tooling (`validate-unified-backend.sh`, `test-rollback.sh`, profiling/load-test helpers) that double as smoke tests—run the matching script before touching its subsystem.
- `tests/` mirrors the validation pyramid: `unit/` for pure routing logic, `integration/` for live provider paths, `contract/` for API compliance, and `fixtures/` for canned models.
- `docs/` plus top-level guides (README, CONFIGURATION-QUICK-REFERENCE, etc.) explain architecture and deployment; keep new docs alongside the closest topic.
- `ai-dashboard/`, `monitoring/`, and `wth-widgets/` provide operational UX—update these when changing telemetry fields.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` — sync Python dependencies (Python 3.11).
- `pre-commit run --all-files` — apply lint, format, YAML, and secret scans before pushing.
- `ruff check scripts tests && ruff format scripts tests` — enforce lint/format baselines.
- `mypy --config-file mypy.ini scripts` — type-check operational Python code.
- `pytest tests/unit -v` (fast) and `pytest -m "not slow"` (CI-safe) — primary regression nets.
- `bash tests/contract/test_provider_contracts.sh --provider ollama` — provider contract smoke test.
- `bash scripts/validate-unified-backend.sh` — end-to-end health (LiteLLM gateway + providers).

## Coding Style & Naming Conventions
- Python: 4-space indent, double quotes, 100-char lines enforced via Ruff; prefer dataclasses/Pydantic models for config payloads.
- YAML: keep keys kebab-cased (`lite-llm`, `routing-mode`); validate with `yamllint` (config in `.yamllint.yaml`).
- Scripts follow `snake_case.py` names; shell utilities use verb-first kebab case (e.g., `test-rollback.sh`).
- Type hints are mandatory for new public helpers; upgrade existing modules opportunistically (`mypy.ini` enables incremental mode).

## Testing Guidelines
- Tests live beside their layer; name files `test_<feature>.py`.
- Mark scope with `@pytest.mark.unit`, `integration`, `contract`, `slow`, and provider-specific markers so CI selectors stay reliable.
- Require coverage when touching routing or config generation: `pytest tests/unit --cov=scripts --cov-report=term`.
- Contract and integration suites expect local services (`systemctl --user status litellm.service`, `ollama.service`) before execution.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`type(scope): summary`) as seen in recent history (`feat(config): …`, `test(dashboard): …`).
- Keep commits scoped to one concern with updated docs/tests in the same change.
- PRs must link the relevant Linear/Jira issue, describe config or routing impacts, include validation commands run, and attach screenshots or log excerpts for dashboard or monitoring work.
- When altering provider configs, mention rollback steps (`scripts/test-rollback.sh --dry-run`) in the PR checklist to help release managers.
