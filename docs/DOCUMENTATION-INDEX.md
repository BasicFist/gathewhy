# AI Unified Backend - Documentation Index

**Navigation guide for all project documentation and knowledge resources**

Last Updated: 2025-10-30

---

## 🚀 Quick Start Paths

### I Want To...

- **Use the unified backend** → [Quick Start Guide](docs/quick-start.md) → [Consuming API](docs/consuming-api.md)
- **Add a new provider** → [Adding Providers Guide](docs/adding-providers.md) → [Provider Registry Memory](.serena/memories/02-provider-registry.md)
- **Understand the architecture** → [Architecture Overview](docs/architecture.md) → [Architecture Memory](.serena/memories/01-architecture.md)
- **Configure model routing** → [Model Selection Guide](docs/model-selection-guide.md) → [Routing Config Memory](.serena/memories/03-routing-config.md)
- **Troubleshoot issues** → [Troubleshooting Guide](docs/troubleshooting.md) → [Troubleshooting Patterns Memory](.serena/memories/06-troubleshooting-patterns.md)
- **Monitor the system** → [Observability Guide](docs/observability.md) → [Monitoring Setup](monitoring/)
- **Deploy/operate the system** → [Runtime Operations](docs/runtime-operations.md) → [Operational Runbooks Memory](.serena/memories/07-operational-runbooks.md)

---

## 📚 Documentation Structure

### Core Documentation (`docs/`)

#### Getting Started
- **[README.md](README.md)** - Project overview, architecture diagram, quick start
- **[docs/quick-start.md](docs/quick-start.md)** - Fastest path to using the unified backend
- **[docs/consuming-api.md](docs/consuming-api.md)** - How LAB projects consume the API

#### Architecture & Design
- **[docs/architecture.md](docs/architecture.md)** - Detailed system architecture
- **[docs/local-vs-cloud-routing.md](docs/local-vs-cloud-routing.md)** - Routing strategies and decision logic
- **[CONFIG-SCHEMA.md](CONFIG-SCHEMA.md)** - Configuration file schemas and validation

#### Configuration
- **[docs/adding-providers.md](docs/adding-providers.md)** - Step-by-step provider addition guide
- **[docs/model-selection-guide.md](docs/model-selection-guide.md)** - Choosing the right model/provider
- **[docs/vllm-model-switching.md](docs/vllm-model-switching.md)** - vLLM-specific configuration
- **[docs/ollama-cloud-setup.md](docs/ollama-cloud-setup.md)** - Ollama Cloud integration guide

#### Operations & Maintenance
- **[docs/runtime-operations.md](docs/runtime-operations.md)** - Day-to-day operations guide
- **[docs/recovery-procedures.md](docs/recovery-procedures.md)** - Disaster recovery and rollback
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment procedures and checklists
- **[docs/security-setup.md](docs/security-setup.md)** - Security hardening and authentication

#### Monitoring & Observability
- **[docs/observability.md](docs/observability.md)** - Prometheus + Grafana setup
- **[docs/ai-dashboard.md](docs/ai-dashboard.md)** - AI-powered monitoring dashboard
- **[monitoring/](monitoring/)** - Prometheus config, Grafana dashboards

#### Troubleshooting
- **[docs/troubleshooting.md](docs/troubleshooting.md)** - Common issues and solutions
- **[docs/error-troubleshooting-guide.md](docs/error-troubleshooting-guide.md)** - Error codes and remediation
- **[docs/VLLM-DEPLOYMENT-REQUIREMENTS.md](docs/VLLM-DEPLOYMENT-REQUIREMENTS.md)** - vLLM-specific troubleshooting

#### Reference
- **[docs/COMMAND-REFERENCE.md](docs/COMMAND-REFERENCE.md)** - CLI commands and scripts
- **[docs/AGENTS.md](docs/AGENTS.md)** - Agent coordination patterns
- **[docs/DEVELOPMENT-HISTORY.md](docs/DEVELOPMENT-HISTORY.md)** - Project evolution timeline

---

## 🧠 Knowledge Base (Serena Memories)

Located in `.serena/memories/` - Comprehensive knowledge preserved by Serena MCP

### Architecture & Design
1. **[01-architecture.md](.serena/memories/01-architecture.md)**
   - Complete system architecture with diagrams
   - Component responsibilities and interactions
   - Request flow patterns and data flows
   - Performance optimization strategies
   - Security considerations

2. **[02-provider-registry.md](.serena/memories/02-provider-registry.md)**
   - Complete provider catalog with specifications
   - Model capabilities and performance characteristics
   - Integration locations and service management
   - Provider selection criteria and best practices

3. **[03-routing-config.md](.serena/memories/03-routing-config.md)**
   - LiteLLM routing configuration patterns
   - Exact matching, pattern matching, capability-based routing
   - Load balancing strategies and fallback chains
   - Configuration generation workflow

4. **[04-model-mappings.md](.serena/memories/04-model-mappings.md)**
   - Model-to-provider routing rules
   - Capability-based model selection
   - Fallback chain configurations
   - Routing strategy decision trees

### Operations & Integration
5. **[05-integration-guide.md](.serena/memories/05-integration-guide.md)**
   - How LAB projects consume the unified backend
   - OpenAI SDK integration patterns
   - MCP protocol usage
   - Example code for Python, JavaScript, Go, R

6. **[06-troubleshooting-patterns.md](.serena/memories/06-troubleshooting-patterns.md)**
   - Common failure modes and diagnostics
   - Provider-specific issues and resolutions
   - Performance troubleshooting methodology
   - Error pattern catalog

7. **[07-operational-runbooks.md](.serena/memories/07-operational-runbooks.md)**
   - Step-by-step operational procedures
   - Adding providers and models
   - Configuration management workflow
   - Rollback and recovery procedures
   - Performance tuning and security hardening

8. **[08-testing-patterns.md](.serena/memories/08-testing-patterns.md)**
   - Test strategy and coverage targets
   - Unit, integration, contract testing patterns
   - Validation workflow and automated testing
   - Quality assurance procedures

---

## ⚙️ Configuration Files

### Source of Truth
- **[config/providers.yaml](config/providers.yaml)** - Master provider registry
  - All provider definitions and metadata
  - Health check endpoints and service files
  - Model catalogs and capabilities

- **[config/model-mappings.yaml](config/model-mappings.yaml)** - Routing rules
  - Exact model name matching
  - Pattern-based routing
  - Capability-based routing
  - Load balancing and fallback chains

### Generated Configuration
- **[config/litellm-unified.yaml](config/litellm-unified.yaml)** - LiteLLM gateway config
  - **AUTO-GENERATED** - Do not edit directly
  - Generated by `scripts/generate-litellm-config.py`
  - Extended with observability and security settings

### Schemas & Validation
- **[config/schemas/](config/schemas/)** - Pydantic validation schemas
  - Provider schema validation
  - Model mapping schema validation
  - Configuration consistency checks

---

## 🔧 Scripts & Tools

### Validation & Testing
- **[scripts/validate-unified-backend.sh](scripts/validate-unified-backend.sh)** - Complete system validation
- **[scripts/validate-all-configs.sh](scripts/validate-all-configs.sh)** - Configuration validation
- **[scripts/generate-litellm-config.py](scripts/generate-litellm-config.py)** - Config generation

### Debugging & Analysis (Phase 2)
- **[scripts/debugging/tail-requests.py](scripts/debugging/tail-requests.py)** - Real-time request monitoring
- **[scripts/debugging/analyze-logs.py](scripts/debugging/analyze-logs.py)** - Log analysis and search
- **[scripts/debugging/test-routing.sh](scripts/debugging/test-routing.sh)** - Routing decision testing

### Profiling & Optimization (Phase 2)
- **[scripts/profiling/analyze-latency.py](scripts/profiling/analyze-latency.py)** - Latency analysis
- **[scripts/profiling/analyze-token-usage.py](scripts/profiling/analyze-token-usage.py)** - Token usage tracking
- **[scripts/profiling/compare-providers.py](scripts/profiling/compare-providers.py)** - Provider benchmarking

### Operational Tools
- **[scripts/vllm-model-switch.sh](scripts/vllm-model-switch.sh)** - vLLM model switching
- **[scripts/backup-config.sh](scripts/backup-config.sh)** - Configuration backup
- **[scripts/health-check-all.sh](scripts/health-check-all.sh)** - All-provider health check

---

## 📊 Monitoring & Observability

### Prometheus Metrics
- **Location**: [monitoring/prometheus/](monitoring/prometheus/)
- **Scrape Config**: `prometheus.yml`
- **Metrics Endpoint**: `http://localhost:9090` (when monitoring stack is running)

### Grafana Dashboards (Phase 2)
Located in [monitoring/grafana/dashboards/](monitoring/grafana/dashboards/):

1. **litellm-overview.json** - System-wide metrics and health
2. **provider-performance.json** - Per-provider latency and throughput
3. **model-usage.json** - Model selection patterns and popularity
4. **cache-efficiency.json** - Redis cache hit rates and performance
5. **error-analysis.json** - Error rates and failure patterns

### Dashboard Access
- **Grafana UI**: `http://localhost:3000` (when monitoring stack is running)
- **Prometheus UI**: `http://localhost:9090`

---

## 🧪 Testing

### Test Structure
```
tests/
├── unit/                   # Unit tests for individual components
├── integration/            # Provider integration tests
├── contract/              # API contract tests
└── rollback/              # Configuration rollback tests
```

### Running Tests
```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests (requires providers running)
pytest tests/integration/

# With coverage
pytest --cov=. tests/
```

### Test Documentation
- **[tests/README.md](tests/README.md)** - Testing strategy and guidelines
- **Memory**: [08-testing-patterns.md](.serena/memories/08-testing-patterns.md)

---

## 📝 Status & Planning Documents

### Current Status
- **[STATUS-CURRENT.md](STATUS-CURRENT.md)** - Current project status
- **[CLOUD_MODELS_READY.md](CLOUD_MODELS_READY.md)** - Ollama Cloud integration status
- **[P0-FIXES-APPLIED.md](P0-FIXES-APPLIED.md)** - Critical fixes applied

### Planning & History
- **[CONSOLIDATION-PLAN.md](CONSOLIDATION-PLAN.md)** - Consolidation strategy
- **[CONSOLIDATION-SUMMARY.md](CONSOLIDATION-SUMMARY.md)** - Consolidation results
- **[FINAL-P0-FIXES-SUMMARY.md](FINAL-P0-FIXES-SUMMARY.md)** - P0 completion summary

### Archive
- **[archive/](archive/)** - Historical documents and phase reports
  - Phase reports (1-4)
  - Workflow implementation docs
  - Status reports and completion summaries

---

## 🔗 Cross-Reference Guide

### By Task Type

#### Adding a New Provider
1. Read: [docs/adding-providers.md](docs/adding-providers.md)
2. Reference: [.serena/memories/02-provider-registry.md](.serena/memories/02-provider-registry.md)
3. Update: [config/providers.yaml](config/providers.yaml)
4. Update: [config/model-mappings.yaml](config/model-mappings.yaml)
5. Generate: Run `scripts/generate-litellm-config.py`
6. Validate: Run `scripts/validate-unified-backend.sh`
7. Runbook: [.serena/memories/07-operational-runbooks.md](.serena/memories/07-operational-runbooks.md) → "Adding a New Provider"

#### Troubleshooting Provider Issues
1. Check: [docs/troubleshooting.md](docs/troubleshooting.md) → Provider-specific section
2. Logs: `scripts/debugging/tail-requests.py` or `journalctl --user -u litellm.service`
3. Health: Run `scripts/health-check-all.sh`
4. Patterns: [.serena/memories/06-troubleshooting-patterns.md](.serena/memories/06-troubleshooting-patterns.md)
5. Recovery: [docs/recovery-procedures.md](docs/recovery-procedures.md)

#### Configuring Model Routing
1. Understand: [docs/model-selection-guide.md](docs/model-selection-guide.md)
2. Routing Logic: [docs/local-vs-cloud-routing.md](docs/local-vs-cloud-routing.md)
3. Memory: [.serena/memories/03-routing-config.md](.serena/memories/03-routing-config.md)
4. Edit: [config/model-mappings.yaml](config/model-mappings.yaml)
5. Test: `scripts/debugging/test-routing.sh model-name`

#### Setting Up Monitoring
1. Guide: [docs/observability.md](docs/observability.md)
2. Start Stack: `cd monitoring && docker-compose up -d`
3. Configure: [monitoring/prometheus/prometheus.yml](monitoring/prometheus/prometheus.yml)
4. Dashboards: Import from [monitoring/grafana/dashboards/](monitoring/grafana/dashboards/)
5. Dashboard Guide: [docs/ai-dashboard.md](docs/ai-dashboard.md)

#### Consuming the API
1. Quick Start: [docs/quick-start.md](docs/quick-start.md)
2. API Guide: [docs/consuming-api.md](docs/consuming-api.md)
3. Examples: [.serena/memories/05-integration-guide.md](.serena/memories/05-integration-guide.md)
4. Architecture: [docs/architecture.md](docs/architecture.md)

---

## 🎯 Documentation Maintenance

### Keeping Documentation Current

**When adding a provider:**
1. Update `config/providers.yaml`
2. Update `.serena/memories/02-provider-registry.md`
3. Add to `docs/adding-providers.md` if new provider type

**When changing routing logic:**
1. Update `config/model-mappings.yaml`
2. Update `.serena/memories/03-routing-config.md`
3. Update `docs/model-selection-guide.md` if decision criteria changed

**When encountering new issues:**
1. Document in `docs/troubleshooting.md`
2. Update `.serena/memories/06-troubleshooting-patterns.md`
3. Add to runbooks if operational procedure needed

### Documentation Standards
- Use Markdown for all documentation
- Include diagrams for complex concepts (ASCII art or Mermaid)
- Cross-reference related documents
- Keep examples up-to-date with current configuration
- Update "Last Updated" dates when making changes

---

## 🔍 Search Tips

### Finding Specific Information

**Provider configuration:**
```bash
grep -r "provider_name" config/
```

**Model routing:**
```bash
grep -r "model-name" config/model-mappings.yaml
```

**Error patterns:**
```bash
grep -r "error message" docs/troubleshooting.md .serena/memories/
```

**Operational procedures:**
```bash
grep -r "runbook" .serena/memories/07-operational-runbooks.md
```

---

## 📞 Getting Help

### Documentation Navigation
- Start with this index for navigation
- Use cross-references to find related topics
- Check Serena memories for comprehensive details
- Refer to runbooks for step-by-step procedures

### Common Questions
- **"How do I add a provider?"** → [docs/adding-providers.md](docs/adding-providers.md)
- **"Why isn't my model routing correctly?"** → [docs/troubleshooting.md](docs/troubleshooting.md)
- **"How do I monitor the system?"** → [docs/observability.md](docs/observability.md)
- **"What's the architecture?"** → [docs/architecture.md](docs/architecture.md)

---

**Project**: AI Unified Backend Infrastructure
**Documentation Version**: 1.0
**Last Major Update**: 2025-10-30
**Maintainer**: LAB Infrastructure Team
