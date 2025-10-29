# Crush CLI Configuration Audit

**Date**: October 27, 2025, 14:30 CET
**Auditor**: Claude (AI Backend Analysis)
**Config File**: `~/.config/crush/crush.json`
**Status**: ⚠️ **Issues Found - Duplication and Inconsistency**

---

## Executive Summary

The Crush CLI configuration has **3 critical issues**:

1. **Duplicate cloud models** - 6 cloud models listed in TWO providers
2. **Provider confusion** - Two providers route to the same endpoint
3. **Inconsistent naming** - Same models have different display names

**Impact**: Users see duplicate models, unclear provider selection, and potential confusion about which endpoint is actually being used.

**Recommendation**: Remove `ollama-cloud` provider, consolidate all models in `workspace-backend`.

---

## Current Configuration Analysis

### Provider Structure

| Provider | Endpoint | Models | Purpose |
|----------|----------|--------|---------|
| **workspace-backend** | `http://127.0.0.1:4000/v1` | 5 local + 6 cloud (11 total) | Unified gateway |
| **ollama-cloud** | `http://127.0.0.1:4000/v1` | 6 cloud | Duplicate gateway |
| **ollama** | `http://localhost:11434/v1` | 4 local | Direct Ollama |
| openai | `https://api.openai.com/v1` | 2 models | OpenAI API |
| anthropic | `https://api.anthropic.com/v1` | 2 models | Anthropic API |
| groq | `https://api.groq.com/openai/v1` | 3 models | Groq API |
| gemini | `https://generativelanguage.googleapis.com/v1beta` | 3 models | Gemini API |

---

## Issue 1: Duplicate Cloud Models ⚠️

### Problem

The **same 6 cloud models** appear in **two different providers**:

#### Provider: workspace-backend (lines 41-76)
```json
{
  "id": "deepseek-v3.1:671b-cloud",
  "name": "DeepSeek V3.1 671B (Cloud)",  // Note: "(Cloud)" suffix
  "context_window": 64000,
  "default_max_tokens": 4000
}
// ... 5 more cloud models
```

#### Provider: ollama-cloud (lines 139-175)
```json
{
  "id": "deepseek-v3.1:671b-cloud",
  "name": "DeepSeek V3.1 671B",  // Note: NO "(Cloud)" suffix
  "context_window": 64000,
  "default_max_tokens": 4000
}
// ... 5 more cloud models
```

### Impact

- **User Experience**: Sees 12 cloud model entries in the model dropdown (6 duplicates)
- **Confusion**: Same model appears with different names depending on provider selection
- **Maintenance**: Any model metadata change must be made in TWO places
- **Consistency**: Naming inconsistency causes user confusion

### Evidence

**Cloud models duplicated**:
1. `deepseek-v3.1:671b-cloud` - appears 2x
2. `qwen3-coder:480b-cloud` - appears 2x
3. `kimi-k2:1t-cloud` - appears 2x
4. `gpt-oss:120b-cloud` - appears 2x
5. `gpt-oss:20b-cloud` - appears 2x
6. `glm-4.6:cloud` - appears 2x

---

## Issue 2: Redundant Provider Configuration ⚠️

### Problem

**Two providers route to the SAME endpoint**:

```json
"workspace-backend": {
  "base_url": "http://127.0.0.1:4000/v1",
  "api_key": "local-unified"
}

"ollama-cloud": {
  "base_url": "http://127.0.0.1:4000/v1",  // SAME
  "api_key": "local-unified"                // SAME
}
```

### Impact

- **Redundancy**: Both providers do the EXACT same thing for cloud models
- **Confusion**: Users don't know which provider to select
- **No benefit**: Having two providers adds no functionality
- **LiteLLM handles routing**: The unified backend already routes based on model name

### Why This Happened

During the Ollama Cloud integration, we:
1. First added cloud models to `workspace-backend` (correct)
2. Then created separate `ollama-cloud` provider (unnecessary)
3. Didn't remove cloud models from `workspace-backend`

Result: **Duplication instead of separation**

---

## Issue 3: Inconsistent Model Naming ⚠️

### Problem

**Same model has different names** depending on which provider is selected:

#### In workspace-backend
- "DeepSeek V3.1 671B **(Cloud)**"
- "Qwen3 Coder 480B **(Cloud)**"
- "Kimi K2 1T **(Cloud)**"

#### In ollama-cloud
- "DeepSeek V3.1 671B" (no suffix)
- "Qwen3 Coder 480B" (no suffix)
- "Kimi K2 1T" (no suffix)

### Impact

- **User Confusion**: Is "DeepSeek V3.1 671B (Cloud)" the same as "DeepSeek V3.1 671B"?
- **UI Clutter**: Looks like different models when they're identical
- **Professional Polish**: Inconsistent naming appears unpolished

---

## Architecture Review

### Current Flow (Problematic)

```
User selects "workspace-backend" → deepseek-v3.1:671b-cloud (Cloud)
                                        ↓
                          http://127.0.0.1:4000/v1
                                        ↓
                          LiteLLM Gateway routes to ollama_chat/deepseek-v3.1:671b-cloud
                                        ↓
                          https://ollama.com/api/chat (Ollama Cloud)

User selects "ollama-cloud" → deepseek-v3.1:671b-cloud (no suffix)
                                        ↓
                          http://127.0.0.1:4000/v1 (SAME ENDPOINT!)
                                        ↓
                          LiteLLM Gateway routes to ollama_chat/deepseek-v3.1:671b-cloud
                                        ↓
                          https://ollama.com/api/chat (Ollama Cloud)
```

**Result**: Both paths are identical - redundant configuration.

### Recommended Flow (Clean)

```
User selects "workspace-backend" → deepseek-v3.1:671b-cloud (Cloud)
                                        ↓
                          http://127.0.0.1:4000/v1
                                        ↓
                          LiteLLM Gateway routes based on model name:
                          - Local models → ollama/ prefix → http://localhost:11434
                          - Cloud models → ollama_chat/ prefix → https://ollama.com
```

**Result**: Single provider, clean routing, no duplication.

---

## Recommended Fix

### Option 1: Remove ollama-cloud Provider (Recommended) ✅

**Actions**:
1. Delete `ollama-cloud` provider entirely
2. Keep all 11 models (5 local + 6 cloud) in `workspace-backend`
3. Standardize naming with "(Cloud)" suffix for cloud models
4. Update default models to use best available

**Configuration**: See `CRUSH-CONFIG-FIX.json`

**Benefits**:
- ✅ No duplication
- ✅ Single source of truth
- ✅ Clear model naming
- ✅ Simplified provider selection
- ✅ Maintains LiteLLM routing logic

**Trade-offs**:
- ❌ Can't explicitly choose "Ollama Cloud" as a provider
- ✅ But models are clearly labeled "(Cloud)" so user knows

### Option 2: Remove Cloud Models from workspace-backend

**Actions**:
1. Remove 6 cloud models from `workspace-backend`
2. Keep only `ollama-cloud` provider for cloud models
3. workspace-backend becomes "Local Only"

**Benefits**:
- ✅ Clear separation: workspace-backend = local, ollama-cloud = cloud
- ✅ Explicit provider choice

**Trade-offs**:
- ❌ More providers to choose from (increases complexity)
- ❌ Both still route to the same endpoint (redundancy remains)
- ❌ Requires updating default model selections

### Option 3: Auto-Discover Models

**Actions**:
1. Remove static `"models": []` arrays
2. Let Crush fetch models from `/v1/models` endpoint dynamically

**Benefits**:
- ✅ Always in sync with LiteLLM gateway
- ✅ No manual updates needed
- ✅ No duplication possible

**Trade-offs**:
- ❌ Can't customize model names (uses LiteLLM's names)
- ❌ Can't set custom context windows or max tokens
- ❌ Requires `"disable_provider_auto_update": false`

---

## Recommended Implementation (Option 1)

### Before (Current - Problematic)
```json
{
  "providers": {
    "workspace-backend": {
      "models": [
        /* 5 local models */,
        /* 6 cloud models with "(Cloud)" suffix */
      ]
    },
    "ollama-cloud": {
      "models": [
        /* SAME 6 cloud models WITHOUT suffix */
      ]
    }
  }
}
```

### After (Clean)
```json
{
  "providers": {
    "workspace-backend": {
      "models": [
        {"id": "llama3.1:latest", "name": "Llama 3.1 8B (Local)"},
        {"id": "qwen2.5-coder:7b", "name": "Qwen2.5 Coder 7B (Local)"},
        {"id": "mythomax-l2-13b-q5_k_m", "name": "MythoMax 13B (Local)"},
        {"id": "qwen-coder-vllm", "name": "Qwen Coder vLLM (Local)"},
        {"id": "dolphin-uncensored-vllm", "name": "Dolphin Uncensored vLLM (Local)"},
        {"id": "deepseek-v3.1:671b-cloud", "name": "DeepSeek V3.1 671B (Cloud)"},
        {"id": "qwen3-coder:480b-cloud", "name": "Qwen3 Coder 480B (Cloud)"},
        {"id": "kimi-k2:1t-cloud", "name": "Kimi K2 1T (Cloud)"},
        {"id": "gpt-oss:120b-cloud", "name": "GPT-OSS 120B (Cloud)"},
        {"id": "gpt-oss:20b-cloud", "name": "GPT-OSS 20B (Cloud)"},
        {"id": "glm-4.6:cloud", "name": "GLM 4.6 (Cloud)"}
      ]
    }
    // ollama-cloud provider removed
  },
  "models": {
    "large": {
      "model": "kimi-k2:1t-cloud",
      "provider": "workspace-backend"
    },
    "small": {
      "model": "qwen2.5-coder:7b",
      "provider": "workspace-backend"
    }
  }
}
```

**Changes**:
1. ❌ Removed `ollama-cloud` provider
2. ✅ Kept all 11 models in `workspace-backend`
3. ✅ Added "(Local)" suffix to local models for clarity
4. ✅ Consistent "(Cloud)" suffix for cloud models
5. ✅ Updated default "large" model to Kimi K2 1T (most powerful)

---

## Additional Improvements

### 1. Clearer Model Categorization

Add model metadata tags:

```json
{
  "id": "kimi-k2:1t-cloud",
  "name": "Kimi K2 1T (Cloud)",
  "context_window": 128000,
  "default_max_tokens": 4000,
  "tags": ["cloud", "reasoning", "trillion-parameter"],
  "cost_tier": "premium"
}
```

### 2. Default Model Optimization

**Current defaults**:
- `large`: llama3.1:latest (8B, local)
- `small`: qwen2.5-coder:7b (7B, local)

**Recommended defaults**:
- `large`: kimi-k2:1t-cloud (1T, cloud) - Most powerful available
- `small`: qwen2.5-coder:7b (7B, local) - Fast and free

### 3. Provider Descriptions

Add descriptions to providers:

```json
"workspace-backend": {
  "id": "workspace-backend",
  "name": "LAB Unified Backend",
  "description": "Unified gateway with automatic routing (5 local + 6 cloud models)",
  "type": "openai",
  "base_url": "http://127.0.0.1:4000/v1",
  "api_key": "local-unified"
}
```

---

## Testing Checklist

After applying fix:

- [ ] Restart Crush CLI
- [ ] Verify only ONE instance of each cloud model appears
- [ ] Test cloud model (e.g., Kimi K2 1T) - should work
- [ ] Test local model (e.g., Qwen2.5 Coder 7B) - should work
- [ ] Verify model naming is consistent (all cloud models have "(Cloud)" suffix)
- [ ] Check default "large" model is Kimi K2 1T
- [ ] Check default "small" model is Qwen2.5 Coder 7B

---

## Maintenance Notes

### When adding new models:

1. **Add to LiteLLM config first**:
   - Edit `config/providers.yaml`
   - Regenerate: `python3 scripts/generate-litellm-config.py`
   - Restart: `systemctl --user restart litellm.service`

2. **Then add to Crush config**:
   - Edit `~/.config/crush/crush.json`
   - Add to `workspace-backend.models` array
   - Use consistent naming: "Model Name (Cloud)" or "Model Name (Local)"
   - Restart Crush

3. **Verify**:
   - `curl http://localhost:4000/v1/models | jq`
   - Should see new model in Crush provider dropdown

### When removing models:

1. **Remove from both places**:
   - LiteLLM config (`config/providers.yaml`)
   - Crush config (`~/.config/crush/crush.json`)

2. **Regenerate and restart**:
   - Regenerate LiteLLM config
   - Restart LiteLLM service
   - Restart Crush

---

## Summary

### Issues Found
1. ⚠️ **6 cloud models duplicated** in two providers
2. ⚠️ **Two providers route to same endpoint** (redundancy)
3. ⚠️ **Inconsistent model naming** (with/without "(Cloud)" suffix)

### Recommended Fix
- ❌ Remove `ollama-cloud` provider
- ✅ Consolidate all models in `workspace-backend`
- ✅ Standardize naming: "(Local)" and "(Cloud)" suffixes
- ✅ Update defaults: `large` → Kimi K2 1T, `small` → Qwen2.5 Coder 7B

### Files
- **Current config**: `~/.config/crush/crush.json` (problematic)
- **Fixed config**: `CRUSH-CONFIG-FIX.json` (recommended)
- **Audit report**: `CRUSH-CONFIG-AUDIT.md` (this file)

### Next Steps
1. Review `CRUSH-CONFIG-FIX.json`
2. Apply fix: `cp CRUSH-CONFIG-FIX.json ~/.config/crush/crush.json`
3. Restart Crush: `pkill crush && crush`
4. Test cloud model: Select "Kimi K2 1T (Cloud)" and verify it works

---

**Audit Complete**: October 27, 2025, 14:30 CET
