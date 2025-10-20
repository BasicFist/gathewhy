# Scripts Directory

Validation and utility scripts for AI Backend Unified Infrastructure.

## Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

## Validation Scripts

### `validate-config-schema.py`
Pydantic-based configuration validation with strong typing and semantic checks.

```bash
python3 scripts/validate-config-schema.py
```

**Validates**:
- YAML syntax and structure
- URL formats and port ranges
- Provider status and model definitions
- Cross-configuration references
- Fallback chain integrity

### `validate-unified-backend.sh`
Comprehensive runtime validation testing all providers and routing logic.

```bash
bash scripts/validate-unified-backend.sh
```

**Tests**:
- Provider health endpoints
- LiteLLM gateway availability
- Model routing and completion
- Streaming responses
- Performance benchmarks

### `check-generated-configs.sh`
Verifies that generated configuration files haven't been manually edited.

```bash
bash scripts/check-generated-configs.sh
```

Used automatically by pre-commit hooks.

## Generation Scripts

### `generate-litellm-config.py`
**Eliminates configuration redundancy** by generating `litellm-unified.yaml` from source files.

**Source Files**:
- `config/providers.yaml`: Provider registry (models, URLs, status)
- `config/model-mappings.yaml`: Routing rules and fallback chains

**Features**:
- ✅ Single source of truth (no manual synchronization)
- ✅ Version tracking (git-based or timestamp)
- ✅ Automatic backup before regeneration
- ✅ Rollback capability
- ✅ Post-generation validation
- ✅ Preserves security settings

**Basic Usage**:
```bash
# Generate configuration
python3 scripts/generate-litellm-config.py

# Validate only (without regenerating)
python3 scripts/generate-litellm-config.py --validate-only

# List available backup versions
python3 scripts/generate-litellm-config.py --list-backups

# Rollback to specific version
python3 scripts/generate-litellm-config.py --rollback 20251020-143022
```

**Workflow**:
1. Edit `config/providers.yaml` or `config/model-mappings.yaml`
2. Run generation script
3. Review generated `config/litellm-unified.yaml`
4. Apply to LiteLLM: `cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml`
5. Restart: `systemctl --user restart litellm.service`

**Output**:
- `config/litellm-unified.yaml`: Generated configuration
- `config/backups/`: Automatic backups (keeps last 10)
- `config/.litellm-version`: Version metadata

## Testing Scripts

### `test-rollback.sh` (coming in Phase 3)
Tests the rollback procedure for configuration changes.

```bash
bash scripts/test-rollback.sh
```

## Pre-commit Integration

All validation scripts run automatically via pre-commit hooks:

```bash
# Run manually on all files
pre-commit run --all-files

# Run on staged files (happens automatically on git commit)
pre-commit run
```

## Troubleshooting

**ModuleNotFoundError: No module named 'yaml'**
```bash
pip install pyyaml pydantic
```

**Permission denied errors**
```bash
chmod +x scripts/*.sh scripts/*.py
```

**YAML syntax errors**
```bash
yamllint config/*.yaml
```
