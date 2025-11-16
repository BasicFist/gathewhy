# Security Setup Guide

**Target**: Local network deployment with production-ready security foundations
**Last Updated**: 2025-10-20

## Overview

The AI Backend Unified Infrastructure implements multiple security layers:
1. **CORS Restrictions**: Localhost-only by default
2. **Rate Limiting**: Per-model request and token limits
3. **Encryption**: Salt key for database encryption (when persistence is used)
4. **Operational Isolation**: Services bind to loopback interfaces and are accessed via SSH tunnels or VPN when remote access is required

## Current Security Posture

### ✅ Implemented (Phase 1)

**CORS Restrictions**
- Allowed origins: `localhost`, `127.0.0.1`, `[::1]`
- Blocks cross-origin requests from external domains
- Configuration: `config/litellm-unified.yaml:cors`

**Rate Limiting**
- Enabled with sensible per-model defaults
- Prevents DoS attacks via local network
- Configuration: `config/litellm-unified.yaml:rate_limit_settings`

**Security Documentation**
- CORS enforcement playbook
- Salt key encryption guidance
- Environment variable patterns

### ⏳ Available for Production (Not Yet Enabled)

**Database Encryption**
- Salt key for encrypting stored data
- Protects sensitive model configurations

## Security Setup Instructions

### 1. CORS Configuration (Already Applied)

Current configuration restricts access to localhost:

```yaml
cors:
  enabled: true
  allowed_origins:
    - "http://localhost:*"
    - "http://127.0.0.1:*"
    - "http://[::1]:*"
```

**To Add External Domain**:
```yaml
cors:
  enabled: true
  allowed_origins:
    - "http://localhost:*"
    - "http://127.0.0.1:*"
    - "https://yourdomain.com"  # Add specific domain
```

### 2. Rate Limiting (Already Enabled)

Current limits per model:

| Model | RPM | TPM | Use Case |
|-------|-----|-----|----------|
| llama3.1:8b | 100 | 50,000 | General chat |
| qwen-coder | 80 | 40,000 | Code generation |
| llama2-13b-vllm | 50 | 100,000 | High-throughput |
| llama-cpp-native | 150 | 75,000 | Fast inference |

**To Adjust Limits**:
```yaml
rate_limit_settings:
  enabled: true
  limits:
    model-name:
      rpm: 200  # Increase requests per minute
      tpm: 100000  # Increase tokens per minute
```

### 3. Gateway Exposure (Keyless by Design)

LiteLLM intentionally exposes a keyless OpenAI-compatible endpoint. Access control is enforced by network topology:

- Bind services to `127.0.0.1`/`[::1]`.
- Require SSH tunnelling, WireGuard, or VPN for remote operators.
- Keep provider API keys (e.g., `OLLAMA_API_KEY`) in systemd environment files so the gateway can reach upstream APIs without handing secrets to clients.

If you must share the API beyond localhost, terminate TLS and authentication at a reverse proxy (Caddy, Nginx, Tailscale) while leaving LiteLLM itself keyless.

### 4. Salt Key for Encryption (Optional)

**If using database storage**:

```bash
# Generate salt key
LITELLM_SALT_KEY="$(openssl rand -hex 32)"
echo "export LITELLM_SALT_KEY='$LITELLM_SALT_KEY'" >> ~/.bashrc

# Add to systemd
systemctl --user edit litellm.service

[Service]
Environment="LITELLM_SALT_KEY=your-salt-key-here"

# Enable in config
general_settings:
  salt_key: ${LITELLM_SALT_KEY}
```

**IMPORTANT**: Never change salt key after adding models to database!

## Production Readiness Checklist

### Current State: Local Development ✅

- ✅ CORS restricted to localhost
- ✅ Rate limiting enabled
- ✅ Security documentation complete
- ✅ Configuration validation enforced

### For Production Deployment: ⏳

- [ ] **SSL/TLS Certificates**
  - Obtain certificates (Let's Encrypt recommended)
  - Configure reverse proxy (nginx/traefik)
  - Redirect HTTP → HTTPS

- [ ] **Authenticated Reverse Proxy**
  - Terminate TLS + auth (OAuth, mTLS, VPN, or network ACLs)
  - Keep LiteLLM bound to loopback interfaces

- [ ] **Audit Logging**
  - Enable detailed request logging
  - Configure log aggregation (Loki/ELK)
  - Set up log retention policy
  - Monitor for suspicious patterns

- [ ] **Network Security**
  - Use reverse proxy with rate limiting
  - Enable firewall rules (UFW/iptables)
  - Restrict port access to known IPs
  - Consider VPN for remote access

- [ ] **Secrets Management**
  - Use systemd `LoadCredential=` for encrypted secrets
  - Never commit secrets to git
  - Rotate provider/API keys regularly (quarterly)
  - Document key rotation procedures

- [ ] **Monitoring & Alerting**
  - Set up Prometheus alerts
  - Configure PagerDuty/Slack notifications
  - Monitor provider quota errors
  - Track rate limit violations

- [ ] **Compliance**
  - SOC 2 compliance validation
  - GDPR data handling review
  - Security audit by third party
  - Penetration testing

## Security Best Practices

### Development

1. **Never commit secrets**: Use `.gitignore` for sensitive files
2. **Use environment variables**: Never hardcode keys in config
3. **Validate all configs**: Run `validate-config-schema.py` before applying
4. **Test security**: Verify CORS and rate limits work

### Operation

1. **Regular updates**: Keep LiteLLM and providers updated
2. **Monitor logs**: Watch for unexpected 4xx responses or spikes in rejected requests
3. **Rotate keys**: Change provider API keys quarterly
4. **Backup configs**: Version control all configuration changes
5. **Incident response**: Have rollback plan ready

### Deployment

1. **Principle of least privilege**: Minimum necessary permissions
2. **Defense in depth**: Multiple security layers
3. **Fail secure**: Security failures should deny access
4. **Audit everything**: Log all security-relevant events

## Security Incident Response

### Suspected Unauthorized Access

1. **Immediate containment**:
   ```bash
   # Restrict exposure to localhost-only
   sudo ufw deny 4000/tcp

   # Restart gateway to drop existing sessions
   systemctl --user restart litellm.service
   ```

2. **Investigate**:
   ```bash
   # Check logs for suspicious activity
   journalctl --user -u litellm.service --since "1 day ago" | grep "401\|403"

   # Identify leaked provider keys / quota spikes
   journalctl --user -u litellm.service | grep "invalid_api_key"
   ```

3. **Remediate**:
   - Rotate provider keys in the secrets store and reload systemd units
   - Review and tighten CORS policies
   - Add VPN or proxy authentication before re-exposing the service

### Rate Limit Violations

1. **Detect**:
   ```bash
   # Check for rate limit triggers
   journalctl --user -u litellm.service | grep "rate_limit"
   ```

2. **Analyze**:
   - Legitimate spike vs attack?
   - Which model/client affected?
   - Pattern of requests

3. **Respond**:
   - Temporarily lower limits if attack
   - Block offending IP at firewall level
   - Raise limits if legitimate growth

## Security Monitoring

### Daily Checks
```bash
# Upstream auth or quota errors
journalctl --user -u litellm.service --since "1 day ago" | grep "401\|invalid_api_key" | wc -l

# Rate limit violations
journalctl --user -u litellm.service --since "1 day ago" | grep "rate_limit" | wc -l

# Error rate
journalctl --user -u litellm.service --since "1 day ago" | grep "ERROR" | wc -l
```

### Weekly Checks
```bash
# Run full validation
bash scripts/validate-unified-backend.sh

# Review configuration changes
git log --since="1 week ago" --oneline config/
```

### Monthly Checks
- Review rate limit appropriateness
- Rotate provider API keys (where supported by upstream services)
- Update security documentation
- Audit log access patterns

## Additional Resources

- **LiteLLM Security Docs**: https://docs.litellm.ai/docs/data_security
- **OWASP API Security**: https://owasp.org/www-project-api-security/
- **systemd Security**: https://www.freedesktop.org/software/systemd/man/systemd.exec.html

---

**Security Contact**: Document security incidents and response procedures
**Last Security Audit**: 2025-10-20 (Initial setup)
**Next Review Due**: 2025-11-20
