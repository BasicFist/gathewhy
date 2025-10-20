# CI/CD Pipeline Documentation

This directory contains GitHub Actions workflows and Dependabot configuration for automated validation and dependency management.

## Workflows

### `validate-config.yml` - Configuration Validation Pipeline

**Triggers:**
- Push to main/master (config/, scripts/, docs/ changes)
- Pull requests to main/master
- Manual dispatch (workflow_dispatch)

**Stages:**

1. **YAML Syntax Validation**
   - Runs yamllint with custom rules (.yamllint.yaml)
   - Validates YAML can be parsed with Python yaml module
   - Fast fail on syntax errors

2. **Pydantic Schema Validation**
   - Runs `scripts/validate-config-schema.py`
   - Strong typing validation (provider types, status values)
   - URL format validation
   - Port range validation (1-65535)
   - Cross-configuration consistency:
     - Provider references exist
     - Fallback chains valid
     - Model references correct
     - Load balancing weights sum to 1.0

3. **Secret Scanning**
   - Uses detect-secrets to find credentials
   - Compares against baseline (.secrets.baseline)
   - Fails on new unreviewed secrets
   - Scans config/, scripts/, docs/ directories

4. **Documentation Sync Check**
   - Validates active providers documented in architecture.md
   - Ensures all 8 required Serena memories present:
     - 01-architecture.md
     - 02-provider-registry.md
     - 03-routing-config.md
     - 04-model-mappings.md
     - 05-integration-guide.md
     - 06-troubleshooting-patterns.md
     - 07-operational-runbooks.md
     - 08-testing-patterns.md

5. **Generated Config Verification**
   - Runs `scripts/check-generated-configs.sh`
   - Ensures AUTO-GENERATED markers present
   - Prevents manual edits to generated files

6. **Integration Tests (Optional)**
   - Dry-run provider health checks
   - Full tests require active providers
   - Can be triggered manually with input flag

**Usage:**

```bash
# Automatically runs on push/PR

# Manual trigger with integration tests:
gh workflow run validate-config.yml -f run_integration_tests=true
```

---

### `pr-validation.yml` - Pull Request Validation

**Triggers:**
- Pull request events (opened, synchronize, reopened, edited)

**Additional Checks:**

1. **PR Metadata Validation**
   - Conventional commit format for PR title:
     - `feat(routing): add fallback for Ollama models`
     - `fix(config): correct vLLM port mapping`
     - `docs(security): update master key setup`
   - PR description presence (warning only)

2. **Configuration Change Analysis**
   - Detects changed config files
   - Shows line additions/deletions
   - Identifies breaking changes:
     - status: disabled
     - base_url changes
     - removed/deprecated fields
   - Provides migration checklist

3. **Security Impact Assessment**
   - Flags security-sensitive file changes:
     - security, auth, cors files
     - rate limiting configs
     - master/salt key settings
     - .env files
   - Reminds of security review requirements

4. **Performance Impact Check**
   - Identifies performance-related changes:
     - routing configuration
     - cache settings
     - timeout/retry values
   - Suggests performance testing

5. **Changelog Check**
   - Reminds to update CHANGELOG.md (warning only)
   - Only for PRs to main/master

**Usage:**

PR validation runs automatically. Ensure:
- PR title follows conventional commit format
- Breaking changes are documented
- Security changes reviewed
- Performance impact assessed

---

### `dependabot.yml` - Automated Dependency Updates

**Ecosystems:**

1. **Python Dependencies (requirements.txt)**
   - Weekly updates (Mondays 09:00)
   - Max 5 open PRs
   - Ignores pydantic major version updates (manual review)
   - Labels: dependencies, python
   - Commit prefix: `chore(deps)`

2. **GitHub Actions**
   - Weekly updates (Mondays 09:00)
   - Max 3 open PRs
   - Labels: dependencies, github-actions
   - Commit prefix: `chore(ci)`

3. **Pre-commit Hooks**
   - Monthly updates
   - Max 2 open PRs
   - Only tracks: pre-commit, yamllint, detect-secrets
   - Labels: dependencies, pre-commit
   - Commit prefix: `chore(hooks)`

**Usage:**

Dependabot automatically creates PRs. Review and merge:

```bash
# List open Dependabot PRs
gh pr list --author app/dependabot

# Review specific PR
gh pr view <PR-number>

# Merge after validation passes
gh pr merge <PR-number> --squash
```

---

## Workflow Integration

```
Push/PR → validate-config.yml (6 stages)
       ↓
    [YAML] → [Schema] → [Secrets] → [Docs] → [Generated] → [Integration]
       ↓
   All Pass → ✅ Ready for merge
       ↓
   Any Fail → ❌ Fix and retry

PR Opened → pr-validation.yml (5 checks)
       ↓
    [Metadata] → [Config Diff] → [Security] → [Performance] → [Changelog]
       ↓
   Warnings/Errors → Review and address
```

---

## Local Development

Run validation locally before pushing:

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Pre-commit runs automatically on git commit
git add .
git commit -m "feat(routing): add new provider"

# Manual pre-commit run
pre-commit run --all-files

# Individual validations
yamllint -c .yamllint.yaml config/
python3 scripts/validate-config-schema.py
detect-secrets scan --baseline .secrets.baseline
bash scripts/check-generated-configs.sh
```

---

## CI/CD Best Practices

### 1. Fast Feedback
- YAML validation runs first (fast fail)
- Parallel jobs where possible
- Schema validation after syntax check

### 2. Fail-Safe
- Multiple validation layers
- Breaking change detection
- Security scanning on every commit

### 3. Documentation-Driven
- Documentation sync enforced
- Serena memories completeness checked
- Configuration changes analyzed

### 4. Security-First
- Secret scanning baseline
- Security-sensitive file detection
- No hardcoded credentials allowed

### 5. Dependency Hygiene
- Automated weekly updates
- Grouped by ecosystem
- Manual review for major versions

---

## Troubleshooting

### Validation Failures

**YAML Syntax Error:**
```bash
# Check with yamllint locally
yamllint -c .yamllint.yaml config/providers.yaml

# Fix and retry
```

**Schema Validation Error:**
```bash
# Run locally for detailed output
python3 scripts/validate-config-schema.py

# Common issues:
# - Invalid provider type (must be: ollama, llama_cpp, vllm, openai, anthropic, openai_compatible)
# - Invalid status (must be: active, disabled, pending_integration, template)
# - Malformed URL (must start with http:// or https://)
# - Invalid port range (must be 1-65535)
# - Load balancing weights don't sum to 1.0
```

**Secret Detected:**
```bash
# Audit new secrets
detect-secrets audit .secrets.baseline

# If false positive, mark as safe and update baseline:
detect-secrets scan --baseline .secrets.baseline > .secrets.baseline.new
mv .secrets.baseline.new .secrets.baseline
git add .secrets.baseline
```

**Documentation Out of Sync:**
```bash
# Update docs/architecture.md with new provider information
# Ensure all 8 Serena memories present in .serena/memories/
```

**Generated Config Modified:**
```bash
# Don't manually edit files with AUTO-GENERATED marker
# Regenerate instead:
python3 scripts/generate-litellm-config.py  # When implemented in Phase 2
```

---

## Adding New Workflows

To add a new workflow:

1. Create `.github/workflows/<name>.yml`
2. Define triggers (on:)
3. Add jobs with meaningful names
4. Use appropriate actions from marketplace
5. Test with `act` or manual trigger
6. Document in this README

Example structure:
```yaml
name: My Workflow

on:
  push:
    branches: [main]

jobs:
  my-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: My step
        run: echo "Hello"
```

---

## Maintenance

### Monthly Tasks
- Review Dependabot PRs and merge
- Check for outdated GitHub Actions
- Validate workflow efficiency (execution times)
- Update baseline for secret scanning if needed

### Quarterly Tasks
- Review and update validation rules
- Assess need for additional checks
- Performance optimization of CI/CD pipeline
- Update this documentation

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Dependabot Configuration](https://docs.github.com/en/code-security/dependabot)
- [Pre-commit Framework](https://pre-commit.com/)
- [detect-secrets](https://github.com/Yelp/detect-secrets)
- [yamllint](https://yamllint.readthedocs.io/)
- [Pydantic](https://docs.pydantic.dev/)

---

**Last Updated:** 2025-10-20
**Maintained By:** AI Backend Unified Infrastructure Team
