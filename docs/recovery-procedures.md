# Configuration Recovery Procedures

This document describes procedures for recovering from configuration issues or failed deployments.

## Table of Contents

1. [Quick Recovery](#quick-recovery)
2. [Manual Rollback](#manual-rollback)
3. [Backup Verification](#backup-verification)
4. [Recovery Scenarios](#recovery-scenarios)
5. [Preventive Measures](#preventive-measures)

---

## Quick Recovery

### Automatic Rollback (Recommended)

The `reload-litellm-config.sh` script includes automatic rollback on failure:

```bash
# Normal reload with automatic rollback on failure
./scripts/reload-litellm-config.sh

# The script will automatically:
# 1. Create a backup before deployment
# 2. Deploy the new configuration
# 3. Reload the service
# 4. Verify service health
# 5. Rollback automatically if health check fails
```

**Rollback Triggers**:
- Service fails to start after reload
- Health endpoint not responding within 30 seconds
- Configuration validation errors during reload

---

## Manual Rollback

### Step 1: List Available Backups

```bash
# View all backups (sorted by date, newest first)
ls -lt ../openwebui/backups/litellm.yaml.backup-*

# Example output:
# -rw-r--r-- 1 miko miko 12345 Oct 21 14:30 litellm.yaml.backup-20251021_143000
# -rw-r--r-- 1 miko miko 12340 Oct 21 13:15 litellm.yaml.backup-20251021_131500
# -rw-r--r-- 1 miko miko 12335 Oct 21 12:00 litellm.yaml.backup-20251021_120000
```

### Step 2: Verify Backup

```bash
# Verify specific backup before restoring
./scripts/verify-backup.sh ../openwebui/backups/litellm.yaml.backup-20251021_143000

# Expected output:
# === Backup Verification ===
#
# Verifying: litellm.yaml.backup-20251021_143000
# [✓] YAML syntax valid
# [✓] Required fields present
# [INFO] Size: 12K
# [INFO] Created: 2025-10-21 14:30:00
# [✓] Backup valid
```

### Step 3: Restore Backup

```bash
# Copy backup to deployment location
cp ../openwebui/backups/litellm.yaml.backup-20251021_143000 \
   ../openwebui/config/litellm.yaml

# Reload service
systemctl --user restart litellm.service

# Verify service health
curl -f http://localhost:4000/health

# Check logs if needed
journalctl --user -u litellm.service -f
```

---

## Backup Verification

### Verify Latest Backup

```bash
./scripts/verify-backup.sh
```

### Verify All Backups

```bash
# Comprehensive verification of all backups
./scripts/verify-backup.sh --all

# Example output:
# === Backup Verification ===
#
# [INFO] Found 15 backups
#
# Verifying: litellm.yaml.backup-20251021_143000
# [✓] YAML syntax valid
# [✓] Required fields present
# ... (for each backup)
#
# === Summary ===
# [✓] Verified: 15
# [✓] All backups valid
```

### Verify Specific Backup

```bash
./scripts/verify-backup.sh ../openwebui/backups/litellm.yaml.backup-YYYYMMDD_HHMMSS
```

---

## Recovery Scenarios

### Scenario 1: Service Won't Start After Config Change

**Symptoms**:
- `systemctl --user status litellm.service` shows failed state
- Service logs show configuration errors

**Solution**:
```bash
# 1. Check service status and logs
systemctl --user status litellm.service
journalctl --user -u litellm.service -n 50

# 2. Identify the error (common issues):
#    - YAML syntax error
#    - Invalid model name
#    - Missing required field
#    - Port conflict

# 3. Rollback to last known good configuration
LATEST_BACKUP=$(ls -t ../openwebui/backups/litellm.yaml.backup-* | head -1)
cp "$LATEST_BACKUP" ../openwebui/config/litellm.yaml

# 4. Restart service
systemctl --user restart litellm.service

# 5. Verify recovery
curl -f http://localhost:4000/health
```

### Scenario 2: Gradual Performance Degradation

**Symptoms**:
- Service running but requests timing out
- High memory usage or CPU spikes
- Unexpected error rates

**Solution**:
```bash
# 1. Check current configuration date
ls -l ../openwebui/config/litellm.yaml

# 2. Identify when degradation started
journalctl --user -u litellm.service --since "2 hours ago" | grep ERROR

# 3. Find backup from before degradation
ls -lt ../openwebui/backups/ | head -10

# 4. Rollback to pre-degradation backup
cp ../openwebui/backups/litellm.yaml.backup-YYYYMMDD_HHMMSS \
   ../openwebui/config/litellm.yaml

# 5. Restart and monitor
systemctl --user restart litellm.service
watch -n 2 'systemctl --user status litellm.service'
```

### Scenario 3: Corrupted Configuration File

**Symptoms**:
- YAML parsing errors in logs
- Service fails to start with syntax errors

**Solution**:
```bash
# 1. Verify corruption
python3 -c "import yaml; yaml.safe_load(open('../openwebui/config/litellm.yaml'))"

# 2. If corrupted, restore from backup
LATEST_BACKUP=$(ls -t ../openwebui/backups/litellm.yaml.backup-* | head -1)

# 3. Verify backup before restoring
./scripts/verify-backup.sh "$LATEST_BACKUP"

# 4. Restore verified backup
cp "$LATEST_BACKUP" ../openwebui/config/litellm.yaml

# 5. Restart service
systemctl --user restart litellm.service
```

### Scenario 4: All Backups Are Old/Stale

**Symptoms**:
- Need to recover but all backups are outdated
- Current configuration lost without recent backup

**Prevention**:
```bash
# This scenario should not occur due to automatic backups!
# Every reload creates a backup automatically.

# If it does occur, reconstruct from source files:

# 1. Regenerate from source configurations
cd /home/miko/LAB/ai/backend/ai-backend-unified
python3 scripts/generate-litellm-config.py

# 2. Validate generated config
./scripts/validate-config-consistency.py

# 3. Deploy cautiously
./scripts/reload-litellm-config.sh --validate-only
./scripts/reload-litellm-config.sh
```

---

## Preventive Measures

### Backup Retention Policy

The system automatically maintains:
- **Last 10 backups**: Most recent configuration changes
- **7 daily backups**: One per day for the last week
- **4 weekly backups**: One per week for the last month

This provides ~40 days of rollback history.

### Pre-Deployment Checklist

Before deploying configuration changes:

```bash
# 1. Validate configuration syntax
python3 -c "import yaml; yaml.safe_load(open('config/litellm-unified.yaml'))"

# 2. Validate model consistency
./scripts/validate-config-consistency.py

# 3. Use validation-only mode first
./scripts/reload-litellm-config.sh --validate-only

# 4. Deploy during low-traffic period if possible

# 5. Monitor service logs during deployment
journalctl --user -u litellm.service -f
```

### Health Monitoring

```bash
# Continuous health monitoring
watch -n 5 'curl -s http://localhost:4000/health | jq'

# Check all providers
./scripts/validate-unified-backend.sh

# Monitor service status
systemctl --user status litellm.service
```

### Configuration Version Control

```bash
# Commit configuration changes to git
cd /home/miko/LAB/ai/backend/ai-backend-unified
git add config/
git commit -m "Update LiteLLM configuration: <description>"

# Create tags for major changes
git tag -a v1.2-prod -m "Production deployment October 2025"

# This provides additional rollback capability via git
```

---

## Emergency Contact

For critical production issues:

1. **Immediate Rollback**: Use latest verified backup
2. **Check Logs**: `journalctl --user -u litellm.service -n 100`
3. **Verify Providers**: `./scripts/validate-unified-backend.sh`
4. **Document Issue**: Save logs and error messages for analysis

---

## Backup Locations

- **Primary Backups**: `../openwebui/backups/litellm.yaml.backup-*`
- **Git History**: `/home/miko/LAB/ai/backend/ai-backend-unified/.git`
- **Source Configs**: `config/providers.yaml`, `config/model-mappings.yaml`

---

## Additional Resources

- **Configuration Hot-Reload**: `README.md` - Configuration Hot-Reload section
- **Validation Scripts**: `scripts/validate-config-consistency.py`
- **Architecture Documentation**: `docs/architecture.md`
- **Troubleshooting Guide**: `docs/troubleshooting.md`
