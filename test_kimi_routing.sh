#!/bin/bash

echo "=== Testing Kimi K2 Routing Configuration ==="
echo

# Test 1: Direct Kimi K2 request
echo "Test 1: Direct request to kimi-k2:1t-cloud"
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kimi-k2:1t-cloud",
    "messages": [{"role": "user", "content": "Hello, can you help me with quantum computing? (Keep it brief)"}],
    "max_tokens": 50,
    "stream": false
  }' \
  2>/dev/null | jq -r '.choices[0].message.content' 2>/dev/null || echo "FAILED - Check OLLAMA_API_KEY"

echo
echo "Test 2: Reasoning capability request (should load balance including Kimi K2)"
echo "Test 2: Reasoning capability request"
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "reasoning",
    "messages": [{"role": "user", "content": "Explain quantum entanglement in one sentence"}],
    "max_tokens": 50,
    "stream": false
  }' \
  2>/dev/null | jq -r '.choices[0].message.content' 2>/dev/null || echo "FAILED"

echo
echo "Test 3: Check available models for Kimi"
echo "Test 3: Available models"
curl -s http://localhost:4000/v1/models 2>/dev/null | jq -r '.data[] | select(.id | contains("kimi")) | .id' || echo "No Kimi models found"

echo
echo "=== Configuration Summary ==="
echo "✅ Priority changed: secondary → primary"
echo "✅ Added to reasoning capability"
echo "✅ Fallback chain: kimi → deepseek → gpt-oss → local"
echo "✅ Load balancing: reasoning requests distribute between deepseek and kimi"
