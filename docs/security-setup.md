# Security Setup Guide

**Target**: Local network deployment with production-ready security foundations
**Last Updated**: 2025-10-20

## Overview

The AI Backend Unified Infrastructure implements multiple security layers:
1. **CORS Restrictions**: Localhost-only by default
2. **Rate Limiting**: Per-model request and token limits
3. **Authentication**: Master key support (optional)
4. **Encryption**: Salt key for database encryption

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
- Master key setup instructions
- Salt key encryption guidance
- Environment variable patterns

### ⏳ Available for Production (Not Yet Enabled)

**Master Key Authentication**
- JWT-based request authentication
- Requires `Authorization: Bearer sk-...` header
- Setup documented in config file

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

### 3. Master Key Authentication (Optional)

**Generate Master Key**:
```bash
# Generate secure key
LITELLM_MASTER_KEY="sk-$(openssl rand -hex 16)"
echo "export LITELLM_MASTER_KEY='$LITELLM_MASTER_KEY'" >> ~/.bashrc
source ~/.bashrc
```

**Configure systemd Service**:
```bash
# Edit service
systemctl --user edit litellm.service

# Add environment variable
[Service]
Environment="LITELLM_MASTER_KEY=sk-your-generated-key-here"

# Reload and restart
systemctl --user daemon-reload
systemctl --user restart litellm.service
```

**Enable in Configuration**:
```yaml
# In config/litellm-unified.yaml
general_settings:
  master_key: ${LITELLM_MASTER_KEY}  # Uncomment this line
```

**Apply Configuration**:
```bash
cp config/litellm-unified.yaml ../openwebui/config/litellm.yaml
systemctl --user restart litellm.service
```

**Test Authentication**:
```bash
# Without key - should fail
curl http://localhost:4000/v1/models

# With key - should work
curl -H "Authorization: Bearer sk-your-key" http://localhost:4000/v1/models
```

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

- [ ] **Enable Master Key Authentication**
  - Generate strong master key
  - Store in secure vault (not in files)
  - Enable in configuration
  - Update client applications

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
  - Rotate keys regularly (quarterly)
  - Document key rotation procedures

- [ ] **Monitoring & Alerting**
  - Set up Prometheus alerts
  - Configure PagerDuty/Slack notifications
  - Monitor failed authentication attempts
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
2. **Monitor logs**: Watch for authentication failures
3. **Rotate keys**: Change master key quarterly
4. **Backup configs**: Version control all configuration changes
5. **Incident response**: Have rollback plan ready

### Deployment

1. **Principle of least privilege**: Minimum necessary permissions
2. **Defense in depth**: Multiple security layers
3. **Fail secure**: Security failures should deny access
4. **Audit everything**: Log all security-relevant events

## Security Incident Response

### Suspected Unauthorized Access

1. **Immediate**:
   ```bash
   # Rotate master key immediately
   LITELLM_MASTER_KEY="sk-$(openssl rand -hex 16)"

   # Update systemd service
   systemctl --user edit litellm.service
   # Update Environment= line

   # Restart
   systemctl --user daemon-reload
   systemctl --user restart litellm.service
   ```

2. **Investigate**:
   ```bash
   # Check logs for suspicious activity
   journalctl --user -u litellm.service --since "1 day ago" | grep "401\|403"

   # Check failed authentication attempts
   journalctl --user -u litellm.service | grep "authentication failed"
   ```

3. **Remediate**:
   - Update all client applications with new key
   - Review and tighten CORS policies
   - Consider additional access restrictions

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
# Failed authentications
journalctl --user -u litellm.service --since "1 day ago" | grep "401" | wc -l

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
- Rotate master key (if enabled)
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
