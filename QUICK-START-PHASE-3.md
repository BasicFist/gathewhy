# Quick Start: Phase 3 Tools & Commands

**New Tools Available**: Configuration management, versioning, audit, and troubleshooting

---

## 🚀 Essential Commands

### Health & Diagnostics
```bash
# Check configuration health
python3 scripts/schema_versioning.py --health-check

# Run comprehensive audit
python3 scripts/config-audit.py

# Quick security + compliance audit
python3 scripts/config-audit.py --quick

# Check schema version
python3 scripts/schema_versioning.py --check-version
```

### Troubleshooting
```bash
# When something breaks, run:
python3 scripts/validate-config-schema.py           # Schema validation
python3 scripts/validate-config-consistency.py      # Cross-file consistency
python3 scripts/schema_versioning.py --health-check # System health
python3 scripts/config-audit.py --quick             # Quick audit

# See detailed error troubleshooting:
cat docs/error-troubleshooting-guide.md
```

### Configuration Management
```bash
# Plan migration between versions
python3 scripts/schema_versioning.py --plan-migration v1.0.0 v1.2.0

# Validate before migration
python3 scripts/schema_versioning.py --validate-migration

# View migration history
python3 scripts/schema_versioning.py --history

# See all available commands
python3 scripts/schema_versioning.py --help
python3 scripts/config-audit.py --help
```

---

## 📊 Common Workflows

### Daily Operations
```bash
#!/bin/bash
# Daily health check (30 seconds)
python3 scripts/schema_versioning.py --health-check
```

### Pre-Deployment Verification
```bash
#!/bin/bash
set -e

echo "Pre-deployment verification..."
python3 scripts/validate-config-schema.py
python3 scripts/validate-config-consistency.py
python3 scripts/schema_versioning.py --health-check
python3 scripts/config-audit.py --quick

echo "✅ Ready to deploy"
```

### Weekly Audit
```bash
#!/bin/bash
echo "Running weekly configuration audit..."
python3 scripts/config-audit.py --format json | jq '.overall_score'
```

### Adding New Provider
```bash
#!/bin/bash
# 1. Edit config/providers.yaml
# 2. Edit config/model-mappings.yaml
# 3. Regenerate LiteLLM config
python3 scripts/generate-litellm-config.py
# 4. Validate
python3 scripts/validate-config-schema.py
python3 scripts/validate-config-consistency.py
# 5. Audit
python3 scripts/config-audit.py --quick
```

---

## 🔧 Troubleshooting Quick Ref

| Issue | Command |
|-------|---------|
| Model not found | `grep "model-name" config/model-mappings.yaml` |
| Provider error | `curl http://localhost:11434/api/tags` |
| Config error | `python3 scripts/validate-config-schema.py` |
| Health check | `python3 scripts/schema_versioning.py --health-check` |
| Audit status | `python3 scripts/config-audit.py` |
| See errors | `cat docs/error-troubleshooting-guide.md` |

---

## 📈 Audit Scoring

**Baseline Score: 71.5/100**

Score Interpretation:
- **80-100**: Excellent ✅
- **60-79**: Good (minor issues) ⚠️
- **<60**: Needs attention 🔴

Common improvements:
- Use HTTPS for remote connections
- Enable authentication for production
- Implement access controls
- Add fallback chains for critical models

---

## 🎯 Key Features

### Schema Versioning
- Current version: 1.2.0
- Migration support: 1.0.0 → 1.2.0
- Automatic backup tracking

### Configuration Audit
- Security assessment
- Compliance validation
- Performance review
- Completeness check

### Error Troubleshooting
- 22+ error scenarios
- Diagnostic procedures
- Common solutions
- Reference tables

### Health Checks
- YAML syntax validation
- File size verification
- Schema compliance
- Version tracking

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `docs/error-troubleshooting-guide.md` | Error diagnosis and solutions |
| `docs/PHASE-3-COMPLETION.md` | Technical details and integration |
| `IMPLEMENTATION-COMPLETE.md` | Project completion summary |
| `config/.schema-version` | Current version tracking |
| `config/.migration-history` | Change history log |

---

## 🔒 Security Reminders

✅ Do:
- Enable authentication for production
- Use HTTPS for remote connections
- Run audits regularly
- Track configuration changes
- Keep backups current

❌ Don't:
- Put credentials in config files
- Use HTTP for remote endpoints
- Skip validation before deploying
- Ignore audit findings
- Skip health checks

---

## 💡 Tips & Tricks

### JSON Output for Automation
```bash
python3 scripts/config-audit.py --format json | jq '.overall_score'
```

### Check Only Security
```bash
python3 scripts/config-audit.py --focus security
```

### Plan Major Migration
```bash
python3 scripts/schema_versioning.py --plan-migration v1.0.0 v1.2.0 | less
```

### Export Audit Report
```bash
python3 scripts/config-audit.py --format json > audit-$(date +%Y%m%d).json
```

---

## 🚨 Emergency Procedures

If something breaks, run this:
```bash
#!/bin/bash
echo "🚨 Emergency diagnostics..."

echo "1. Configuration validation..."
python3 scripts/validate-config-schema.py

echo "2. Consistency check..."
python3 scripts/validate-config-consistency.py

echo "3. Health check..."
python3 scripts/schema_versioning.py --health-check

echo "4. Quick audit..."
python3 scripts/config-audit.py --quick

echo "5. Provider health..."
curl http://localhost:11434/api/tags
curl http://localhost:4000/v1/models

echo "✅ Diagnostics complete - check output above"
```

---

## 📞 Need Help?

1. **Check documentation**: `docs/error-troubleshooting-guide.md`
2. **Run diagnostics**: See Emergency Procedures above
3. **Review audit**: `python3 scripts/config-audit.py`
4. **Check health**: `python3 scripts/schema_versioning.py --health-check`

---

## ✨ Next Steps

1. **Review** all Phase 3 documentation
2. **Run** the health check command
3. **Schedule** weekly audits
4. **Train** your team
5. **Deploy** with confidence

---

**You're all set! All three phases are complete and production-ready.** 🎉
