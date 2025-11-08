# AI Unified Backend - Documentation Index

**Complete navigation guide for all project documentation**

Last Updated: 2025-11-08

---

## 🚀 Quick Access

**Essential Files (Project Root):**
- **[README.md](README.md)** - Project overview and architecture
- **[CLAUDE.md](CLAUDE.md)** - AI assistant instructions and project guide

**Quick References:**
- **[Configuration Quick Reference](docs/reference/CONFIGURATION-QUICK-REFERENCE.md)** - Common configuration tasks
- **[API Reference](docs/API-REFERENCE.md)** - Complete API documentation

---

## 📂 Documentation Structure

```
gathewhy/
├── README.md                    # Project overview
├── CLAUDE.md                    # Claude AI instructions
│
├── docs/
│   ├── guides/                  # User guides
│   ├── reference/               # API and configuration reference
│   ├── operations/              # Operations and troubleshooting
│   ├── reports/                 # Audit reports and implementation summaries
│   └── archive/                 # Historical documents
│
├── config/                      # Configuration files
├── scripts/                     # Automation scripts
├── tests/                       # Test suite
├── monitoring/                  # Monitoring and dashboards
└── .serena/memories/            # Knowledge base
```

---

## 📖 Documentation by Category

### 🎯 Getting Started

**New Users:**
1. [README.md](README.md) - Start here
2. [Quick Start Guide](docs/quick-start.md) - Get running in 5 minutes
3. [Consuming API](docs/consuming-api.md) - Use the unified endpoint

**Developers:**
1. [Architecture](docs/architecture.md) - System design
2. [Adding Providers](docs/adding-providers.md) - Extend the system
3. [Development History](docs/DEVELOPMENT-HISTORY.md) - Project evolution

---

### 📚 User Guides

**Core Guides:**
- [Quick Start](docs/quick-start.md) - Fastest path to using the system
- [Consuming API](docs/consuming-api.md) - How LAB projects use the API
- [Model Selection Guide](docs/model-selection-guide.md) - Choose the right model

**Provider-Specific:**
- [Adding Providers](docs/adding-providers.md) - Step-by-step provider integration
- [vLLM Model Switching](docs/vllm-model-switching.md) - vLLM configuration
- [vLLM Single Instance Management](docs/vllm-single-instance-management.md) - vLLM constraints
- [Ollama Cloud Setup](docs/ollama-cloud-setup.md) - Cloud integration

**Advanced:**
- [Local vs Cloud Routing](docs/local-vs-cloud-routing.md) - Routing strategies
- [Redis Persistence Setup](docs/redis-persistence-setup.md) - Cache configuration

---

### 🔧 Reference Documentation

**API & Commands:**
- [API Reference](docs/API-REFERENCE.md) - Complete API documentation
- [Command Reference](docs/COMMAND-REFERENCE.md) - All CLI commands
- [Configuration Quick Reference](docs/reference/CONFIGURATION-QUICK-REFERENCE.md) - Common tasks
- [Config Schema](docs/reference/CONFIG-SCHEMA.md) - Configuration file structure

**Technical Specifications:**
- [Architecture](docs/architecture.md) - Detailed system architecture
- [Schema Versioning](config/schemas/version.py) - Configuration versions
- [vLLM Deployment Requirements](docs/VLLM-DEPLOYMENT-REQUIREMENTS.md) - vLLM specs

---

### ⚙️ Operations & Maintenance

**Daily Operations:**
- [Runtime Operations](docs/runtime-operations.md) - Day-to-day operations
- [Deployment](docs/operations/DEPLOYMENT.md) - Deployment procedures
- [Status & Monitoring](docs/operations/STATUS-CURRENT.md) - Current system status

**Troubleshooting:**
- [Troubleshooting Guide](docs/troubleshooting.md) - Common issues and solutions
- [Error Troubleshooting Guide](docs/error-troubleshooting-guide.md) - Detailed error analysis
- [Recovery Procedures](docs/recovery-procedures.md) - Disaster recovery

**Monitoring:**
- [Observability Guide](docs/observability.md) - Prometheus + Grafana setup
- [Grafana Dashboards](monitoring/grafana/dashboards/) - Pre-configured dashboards
- [AI Dashboard](docs/ai-dashboard.md) - TUI dashboard guide
- [PTUI User Guide](docs/ptui-user-guide.md) - Terminal UI reference

**Security:**
- [Security Setup](docs/security-setup.md) - Hardening and authentication

---

### 📊 Reports & Analysis

**Recent Implementation Reports:**
- [Critical Audit Report](docs/reports/CRITICAL-AUDIT-REPORT.md) - Comprehensive audit (2025-11-08)
- [Fixes Applied](docs/reports/FIXES-APPLIED-2025-11-08.md) - Critical fixes summary
- [Priorities Implementation](docs/reports/PRIORITIES-IMPLEMENTATION-2025-11-08.md) - All priority features
- [Phase 2 Completion](docs/reports/PHASE-2-COMPLETION-REPORT.md) - Phase 2 features

**Analysis Documents:**
- [LiteLLM Official Docs Gap Analysis](docs/reports/LITELLM-OFFICIAL-DOCS-GAP-ANALYSIS.md)
- [Consolidation Summary](docs/reports/CONSOLIDATION-SUMMARY.md)

**Historical Reports (Archived):**
- [docs/archive/](docs/archive/) - Previous audit reports and summaries

---

### 🧠 Knowledge Base (Serena Memories)

**Comprehensive Knowledge:**
- [01 - Architecture](.serena/memories/01-architecture.md) - Complete system design
- [02 - Provider Registry](.serena/memories/02-provider-registry.md) - All provider details
- [03 - Routing Config](.serena/memories/03-routing-config.md) - Routing logic
- [04 - Model Mappings](.serena/memories/04-model-mappings.md) - Model selection patterns
- [05 - Integration Guide](.serena/memories/05-integration-guide.md) - Usage examples
- [06 - Troubleshooting Patterns](.serena/memories/06-troubleshooting-patterns.md) - Common issues
- [07 - Operational Runbooks](.serena/memories/07-operational-runbooks.md) - Step-by-step procedures
- [08 - Testing Patterns](.serena/memories/08-testing-patterns.md) - Test strategies
- [Phase 2 Technical Discoveries](.serena/memories/phase2-technical-discoveries.md)

---

## 🎯 Common Tasks

### I Want To...

**Use the System:**
- **Get started quickly** → [Quick Start](docs/quick-start.md)
- **Understand the API** → [API Reference](docs/API-REFERENCE.md) + [Consuming API](docs/consuming-api.md)
- **Choose a model** → [Model Selection Guide](docs/model-selection-guide.md)

**Configure:**
- **Add a provider** → [Adding Providers](docs/adding-providers.md)
- **Change routing** → [Configuration Quick Reference](docs/reference/CONFIGURATION-QUICK-REFERENCE.md)
- **Switch vLLM models** → [vLLM Model Switching](docs/vllm-model-switching.md)
- **Set up Ollama Cloud** → [Ollama Cloud Setup](docs/ollama-cloud-setup.md)

**Operate:**
- **Monitor the system** → [Observability](docs/observability.md) + [Grafana Dashboards](monitoring/grafana/dashboards/)
- **Troubleshoot issues** → [Troubleshooting Guide](docs/troubleshooting.md)
- **Deploy changes** → [Deployment](docs/operations/DEPLOYMENT.md)
- **Recover from failure** → [Recovery Procedures](docs/recovery-procedures.md)

**Develop:**
- **Understand architecture** → [Architecture](docs/architecture.md)
- **Write tests** → [Testing Patterns](.serena/memories/08-testing-patterns.md) + [tests/README.md](tests/README.md)
- **Migrate configs** → [Migration Scripts](scripts/migrate-config.py)
- **Review audit findings** → [Critical Audit Report](docs/reports/CRITICAL-AUDIT-REPORT.md)

---

## 📁 Additional Resources

### Configuration Files
- [config/providers.yaml](config/providers.yaml) - Provider registry
- [config/model-mappings.yaml](config/model-mappings.yaml) - Routing rules
- [config/litellm-unified.yaml](config/litellm-unified.yaml) - Generated LiteLLM config
- [config/ports.yaml](config/ports.yaml) - Port registry

### Scripts & Tools
- [scripts/](scripts/) - All automation scripts
- [scripts/README.md](scripts/README.md) - Scripts documentation
- [tests/](tests/) - Test suite
- [tests/README.md](tests/README.md) - Testing documentation

### Monitoring
- [monitoring/](monitoring/) - Monitoring stack
- [monitoring/grafana/dashboards/](monitoring/grafana/dashboards/) - Pre-configured dashboards

---

## 🔄 Documentation Maintenance

### For Contributors

**When adding documentation:**
1. Place in appropriate category (guides/reference/operations)
2. Update this index
3. Cross-reference related docs
4. Add to relevant knowledge base memory

**When updating features:**
1. Update relevant guides
2. Update API reference if needed
3. Update CLAUDE.md if affecting Claude behavior
4. Create report in docs/reports/ for major changes

---

## 📞 Getting Help

**Documentation Issues:**
- Check [Troubleshooting Guide](docs/troubleshooting.md) first
- Review [Error Troubleshooting Guide](docs/error-troubleshooting-guide.md)
- Consult relevant [Serena Memory](.serena/memories/)

**Feature Requests:**
- Review [Critical Audit Report](docs/reports/CRITICAL-AUDIT-REPORT.md) for planned features
- Check [Development History](docs/DEVELOPMENT-HISTORY.md) for context

---

**Index Version:** 2.0
**Last Updated:** 2025-11-08
**Maintained By:** AI Backend Infrastructure Team
