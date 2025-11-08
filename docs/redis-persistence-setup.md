# Redis Persistence Configuration

**Status**: AOF enabled via runtime config, RDB already active
**Date**: 2025-10-30
**Context**: Phase 2 Production Hardening - LiteLLM Gateway

## Current Configuration

### RDB (Redis Database) - Snapshots
✅ **ACTIVE** - Configured and working
- Save policy: `3600 1 300 100 60 10000`
  - Save after 3600s if ≥1 key changed
  - Save after 300s if ≥100 keys changed
  - Save after 60s if ≥10000 keys changed
- Last save: Working (`rdb_last_bgsave_status:ok`)
- Save count: 22 successful saves
- Data directory: `/var/lib/redis`

### AOF (Append-Only File) - Write Log
✅ **ENABLED** (runtime) - Via redis-cli CONFIG SET
- `appendonly yes` - Enabled
- `appendfsync everysec` - Fsync every second (recommended)
- Status: Active and working

## Persistence Strategy

**Dual persistence** (RDB + AOF) provides:
1. **RDB**: Fast restarts with point-in-time snapshots
2. **AOF**: Durability with write-ahead logging (max 1 second data loss)

This is the recommended production configuration for Redis.

## Making AOF Configuration Permanent

⚠️ **Current limitation**: AOF enabled via `redis-cli CONFIG SET` but not persisted to `/etc/redis/redis.conf`.
This means AOF will be disabled if Redis restarts.

### To make permanent (requires sudo):

```bash
# Option 1: Edit config file
sudo sed -i 's/^appendonly no/appendonly yes/' /etc/redis/redis.conf
sudo sed -i 's/^# appendfsync everysec/appendfsync everysec/' /etc/redis/redis.conf
sudo systemctl restart redis-server

# Option 2: Use redis-cli CONFIG REWRITE (if permissions allow)
redis-cli CONFIG REWRITE

# Verify persistence
redis-cli INFO persistence | grep aof_enabled
```

### Config file location:
- **Path**: `/etc/redis/redis.conf`
- **Service**: `redis-server.service` (systemd)
- **User**: `redis`
- **Data directory**: `/var/lib/redis`

### Required changes in `/etc/redis/redis.conf`:

```conf
# Enable AOF persistence
appendonly yes

# AOF sync policy (everysec is recommended)
# Options: always (slow, most durable), everysec (recommended), no (fast, least durable)
appendfsync everysec

# AOF rewrite configuration (optional tuning)
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

## Verification

### Check runtime configuration:
```bash
redis-cli CONFIG GET appendonly
redis-cli CONFIG GET appendfsync
redis-cli INFO persistence
```

### Check persistence files:
```bash
sudo ls -lh /var/lib/redis/
# Should show:
# - dump.rdb (RDB snapshot)
# - appendonly.aof (AOF log)
```

## Current Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| RDB Persistence | ✅ Active | Configured in redis.conf, working |
| AOF Persistence | ⚠️ Active (runtime) | Enabled via redis-cli, not in config file |
| Persistence Files | ✅ Working | Both dump.rdb and appendonly.aof being created |
| Durability | ✅ Good | Max 1s data loss with everysec fsync |

## Recommendations

1. **Immediate**: AOF is now active for current session ✅
2. **Follow-up**: Update `/etc/redis/redis.conf` to persist AOF across restarts
3. **Monitoring**: Add Redis persistence metrics to Grafana dashboards
4. **Backup**: Regular backups of `/var/lib/redis/dump.rdb`

## Testing Persistence

```bash
# Write test data
redis-cli SET test:persistence "$(date)"

# Verify it's written
redis-cli GET test:persistence

# Check RDB save
redis-cli BGSAVE
redis-cli LASTSAVE

# Check AOF
redis-cli INFO persistence | grep aof
```

## Related Documentation

- **LiteLLM Config**: `config/litellm-unified.yaml` (router_settings.redis_*)
- **Systemd Service**: `/usr/lib/systemd/system/redis-server.service`
- **Redis Data**: `/var/lib/redis/`
- **Official Docs**: https://redis.io/docs/management/persistence/

---

**Phase 2 Task**: Configure Redis persistence (RDB + AOF) ✅
**Next Steps**: Update config file for permanent persistence, monitor in Grafana
