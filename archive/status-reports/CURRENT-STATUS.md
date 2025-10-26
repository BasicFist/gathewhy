# Current Backend Status

**Date**: 2025-10-24 00:10 CEST
**Assessment**: System Down - Configuration Conflicts Identified

---

## Executive Summary

The unified backend project has **configuration drift** issues:
- Multiple LiteLLM configs exist for different purposes
- Charm-assistant service crashed due to vLLM tool calling incompatibility
- Config changes in this project (Dolphin model) are not deployed
- vLLM attempts (DeepSeek-R1, Dolphin) failed with engine initialization errors

---

## Service Status

### LiteLLM Gateway (:4000) - ❌ DOWN

**Service**: `litellm.service` (Charm Assistant Unified Backend)
**Status**: Inactive (dead) since 21:20:54 CEST (2h 49min ago)
**Config**: `~/LAB/ai/services/charm-assistant/litellm_config.yaml`
**Last Error**: vLLM tool calling incompatibility

```
Error: "auto" tool choice requires --enable-auto-tool-choice
       and --tool-call-parser to be set
Cause: Client requested function calling, vLLM backend not configured
Result: Service crashed after retry exhaustion
```

**Active Config When Running**:
- Model: `qwen-coder-7b` only
- Backend: vLLM :8001 (Qwen2.5-Coder-7B-Instruct-AWQ)
- Settings: Fail-fast (5s timeout, 0 retries)
- Purpose: Minimal config for charm-assistant TUI

### vLLM Server (:8001) - ✅ RUNNING

**Current Model**: `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ`
**Status**: Operational
**Issue**: Missing `--enable-auto-tool-choice` flag for function calling

**Failed Attempts**:
```
❌ DeepSeek-R1-Distill-Qwen-7B-abliterated-v2 (2 attempts)
   Error: Engine core initialization failed
   Cause: Likely vLLM v1 engine incompatibility or GPU memory

❌ solidrust/dolphin-2.8-mistral-7b-v02-AWQ
   Error: Started → Received bad requests → Shutdown
   Cause: Unknown (possibly same tool calling issue)
```

### Ollama (:11434) - ❓ UNKNOWN

Not validated in current session.

### llama.cpp (:8000, :8080) - ❓ UNKNOWN

Not validated in current session.

---

## Configuration Landscape

### 1. Charm-Assistant Config (ACTIVE when running)

**Location**: `~/LAB/ai/services/charm-assistant/litellm_config.yaml`
**Size**: 819 bytes (minimal)
**Purpose**: Fail-fast backend for TUI application
**Models**: 1 (qwen-coder-7b)

```yaml
model_list:
  - model_name: qwen-coder-7b
    litellm_params:
      model: openai/Qwen/Qwen2.5-Coder-7B-Instruct-AWQ
      api_base: http://localhost:8001/v1
      supports_function_calling: true  # ❌ But vLLM not configured
      timeout: 5
      max_retries: 0
```

### 2. AI-Backend-Unified Config (NOT DEPLOYED)

**Location**: `config/litellm-unified.yaml` (this project)
**Size**: 106 lines (comprehensive)
**Purpose**: Unified gateway for all LAB projects
**Models**: 4 (llama3.1, qwen ollama, qwen vllm, dolphin)
**Status**: ⚠️ Modified with Dolphin config, uncommitted, not applied

**Recent Changes** (uncommitted):
```diff
+ dolphin-uncensored-vllm model definition
+ Fallback: dolphin → llama3.1:latest
+ Rate limits: 100 RPM / 50k TPM
+ Capabilities: uncensored, conversational
+ Pattern matching: solidrust/dolphin.*AWQ → vLLM
```

### 3. Architecture Mismatch

```
EXPECTED:
LAB Projects → LiteLLM :4000 (unified config) → {Ollama, llama.cpp, vLLM}

ACTUAL:
Charm-Assistant → LiteLLM :4000 (minimal config) → vLLM :8001 only
                                                  → ❌ Service crashed

ai-backend-unified config → Not deployed, not used
```

---

## Issues Identified

### 1. Tool Calling Incompatibility (CRITICAL)

**Problem**: vLLM backend lacks required flags for function calling
**Impact**: Service crashes when clients request tool use
**Fix Required**: Add to vLLM startup:
```bash
--enable-auto-tool-choice \
--tool-call-parser <parser-type>
```

### 2. Configuration Drift (HIGH)

**Problem**: Multiple LiteLLM configs for different purposes
**Impact**: Changes to unified config don't affect running service
**Decision Needed**:
- A. Merge configs (single unified gateway)
- B. Keep separate (different use cases)
- C. Document and coordinate changes

### 3. vLLM Model Compatibility (MEDIUM)

**Problem**: DeepSeek-R1 fails engine initialization
**Tested**: 2 attempts with different memory settings
**Status**: Blocked, needs investigation or different model

**Problem**: Dolphin model crashes after startup
**Status**: Needs further investigation

### 4. Uncommitted Config Changes (LOW)

**Problem**: Dolphin model config added but not committed
**Impact**: Local changes not version controlled
**Status**: git status shows modified files

---

## Recommendations

### Immediate Actions

1. **Fix vLLM Tool Calling**
   ```bash
   # Stop current vLLM
   pkill -f "vllm serve"

   # Restart with tool support
   vllm serve Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \
     --host 0.0.0.0 \
     --port 8001 \
     --enable-auto-tool-choice \
     --tool-call-parser <appropriate-parser> \
     --gpu-memory-utilization 0.8
   ```

2. **Restart LiteLLM Service**
   ```bash
   systemctl --user start litellm.service
   systemctl --user status litellm.service
   ```

3. **Validate Basic Routing**
   ```bash
   curl http://localhost:4000/v1/models
   curl http://localhost:4000/health
   ```

### Strategic Decisions Needed

**A. Config Architecture**

Options:
1. **Single unified config**: Merge charm-assistant into ai-backend-unified
   - Pro: Single source of truth
   - Con: Charm-assistant loses fail-fast behavior

2. **Separate configs**: Keep both for different use cases
   - Pro: Specialized configs for specific needs
   - Con: Coordination complexity, drift risk

3. **Layered approach**: Unified base + application overlays
   - Pro: Flexibility + consistency
   - Con: Added complexity

**B. Dolphin Config**

Options:
1. **Commit changes**: Keep Dolphin config for future deployment
   - When: After vLLM successfully runs Dolphin

2. **Revert changes**: Remove uncommitted Dolphin config
   - When: If Dolphin model won't be used

3. **Stash changes**: Temporarily save for later
   - When: Need to test other changes first

---

## Validation Checklist

When service is restored:

- [ ] LiteLLM :4000 responds to /health
- [ ] vLLM :8001 lists available models
- [ ] qwen-coder-7b model routes correctly
- [ ] Function calling works (if enabled)
- [ ] Service logs show no errors
- [ ] Uptime >1 hour without crashes

---

## Previous State (v1.2.1)

**Date**: 2025-10-23 18:52 CEST
**Status**: ✅ All systems operational
**Achievement**: Fixed vLLM routing issue (model_group_alias)
**Models Working**: llama3.1:latest, qwen2.5-coder:7b, qwen-coder-vllm

See `POST-SESSION-SUMMARY.md` for details.

---

## Files

**Uncommitted Changes**:
- `config/litellm-unified.yaml` (Dolphin model added)
- `config/model-mappings.yaml` (Dolphin routing added)

**Documentation**:
- `POST-SESSION-SUMMARY.md` (v1.2.1 session)
- `STATUS.md` (v1.2.1 status - now outdated)
- `CURRENT-STATUS.md` (this file - current truth)

---

**Next Update**: After service restoration and validation
