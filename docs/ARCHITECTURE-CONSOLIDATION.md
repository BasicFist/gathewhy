# AI Backend Unified - Architecture Clarification & Consolidation

## Overview

This document clarifies the AI backend architecture following the consolidation effort and explains the relationship between different components.

## Historical Context

During AI-assisted analysis of the LAB infrastructure, an artifact directory was created at:
`/home/miko/LAB/ai/services/litellm-gateway/` 

This directory contained a simple configuration file that duplicated some functionality from the main unified backend but was not a fully functional implementation. It was created as a result of AI analysis tools examining the backend configuration and creating derivative artifacts.

## Current Architecture (Post-Consolidation)

### Single Backend System
The actual production AI backend infrastructure is located at:
`/home/miko/LAB/ai/backend/ai-backend-unified/`

This is the **single source of truth** for all AI backend routing and management, featuring:
- LiteLLM gateway for unified API endpoint at `:4000`
- Configuration-driven provider registry with Pydantic validation
- Multiple backend support (Ollama, llama.cpp, vLLM)
- Comprehensive monitoring and observability stack
- Configuration hot-reload with backup/rollback capabilities

### Artifact Directory
The directory at `/home/miko/LAB/ai/services/litellm-gateway/` was an AI-generated artifact that should be considered:
- **Not functional** as a standalone backend
- **Redundant** with the main unified backend
- **Historical artifact** from AI analysis processes

## Configuration Files Location

All configuration is managed through the unified backend:

- **Provider Registry**: `config/providers.yaml` (source of truth for all providers)
- **Model Mappings**: `config/model-mappings.yaml` (routing rules and fallback chains) 
- **Generated Config**: `config/litellm-unified.yaml` (auto-generated from above)
- **Health Endpoints**: `config/health-checks.yaml` (provider health monitoring)

## Key Improvements Implemented

### 1. Configuration Validation
- Pydantic schemas for configuration validation
- Automated consistency checks across provider and model mappings
- Pre-commit hooks to prevent invalid configurations

### 2. Enhanced Monitoring
- Real-time provider status monitoring
- GPU utilization tracking
- Service control via systemctl integration
- Comprehensive logging with Rich formatting

### 3. Port Management
- Explicit port registry with conflict detection
- Health checks for all registered services
- Automated port validation in deployment scripts

### 4. Dashboard Enhancement
- The main dashboard at `scripts/ai-dashboard` provides comprehensive monitoring
- Interactive TUI with service controls and real-time metrics
- Clean separation of concerns without redundant implementations

## Consolidation Results

✅ **Main backend preserved**: Full-featured unified infrastructure remains intact
✅ **Artifacts identified**: Derivative gateway directory recognized as AI-generated artifact
✅ **Documentation clarified**: Architecture properly documented to avoid future confusion
✅ **Configuration validated**: Single source of truth established with proper validation

## Usage Patterns

### For LAB Projects
Use the single unified endpoint:
```
Base URL: http://localhost:4000
Provider routing: Transparent via model names (llama3.1:8b, qwen-coder-vllm, etc.)
```

### For Operations
Monitor via the main dashboard:
```bash
python3 /home/miko/LAB/ai/backend/ai-backend-unified/scripts/ai-dashboard
```

### For Development
Update provider configurations in:
- `config/providers.yaml` - Add/modify provider definitions
- `config/model-mappings.yaml` - Update routing rules
- Run `scripts/generate-litellm-config.py` - Regenerate unified config

## Moving Forward

This consolidation ensures:
- **Single system to maintain**: Only one backend with comprehensive features
- **Clear operational procedures**: Established patterns for configuration management
- **Reduced complexity**: No confusion about which backend to use or maintain
- **Proper documentation**: Architecture clearly defined to prevent future duplication

The enhanced features and functionality remain intact in the main unified backend, with proper safeguards against configuration inconsistencies and operational issues.