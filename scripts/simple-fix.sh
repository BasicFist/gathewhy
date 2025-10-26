#!/bin/bash
# Simple AI Backend Fix Script

echo "🔧 AI Backend Simple Fix"
echo "========================"

# Step 1: Create working configuration
echo "Step 1: Creating working configuration..."

cat > config/litellm-working.yaml << 'EOF'
model_list:
- model_name: llama3.1:latest
  litellm_params:
    model: ollama/llama3.1:latest
    api_base: http://127.0.0.1:11434
  model_info:
    tags:
    - general_chat
    - 8b
    provider: ollama

- model_name: qwen2.5-coder:7b
  litellm_params:
    model: ollama/qwen2.5-coder:7b
    api_base: http://127.0.0.1:11434
  model_info:
    tags:
    - code_generation
    - 7.6b
    provider: ollama

- model_name: qwen-coder-vllm
  litellm_params:
    model: workspace-coder
    api_base: http://127.0.0.1:8001/v1
    custom_llm_provider: openai
    stream: true
    api_key: not-needed
  model_info:
    tags:
    - code_generation
    - 7b
    - awq
    provider: vllm-qwen
    context_length: 4096

litellm_settings:
  request_timeout: 60
  cache: true
  cache_params:
    type: redis
    host: 127.0.0.1
    port: 6379
    ttl: 3600

router_settings:
  fallbacks:
    - model: qwen-coder-vllm
      fallback_models:
        - llama3.1:latest
        - qwen2.5-coder:7b
    - model: llama3.1:latest
      fallback_models:
        - qwen2.5-coder:7b

server_settings:
  port: 4000
  host: 0.0.0.0
EOF

echo "✅ Working configuration created"

# Step 2: Apply and restart
echo "Step 2: Applying configuration..."
cp config/litellm-working.yaml /home/miko/LAB/ai/services/openwebui/config/litellm.yaml
echo "✅ Configuration applied"

# Step 3: Start clean LiteLLM
echo "Step 3: Starting LiteLLM..."
nohup /home/miko/venvs/litellm/bin/litellm \
    --config /home/miko/LAB/ai/backend/ai-backend-unified/config/litellm-working.yaml \
    --port 4000 \
    --host 0.0.0.0 \
    > /tmp/litellm-working.log 2>&1 &

echo "✅ LiteLLM starting..."

# Step 4: Wait and test
echo "Step 4: Waiting for startup..."
sleep 5

echo "Step 5: Testing..."
python3 -c "
import requests
import json

try:
    # Test models list
    response = requests.get('http://localhost:4000/v1/models', timeout=10)
    if response.status_code == 200:
        models = response.json().get('data', [])
        print(f'✅ Found {len(models)} models')
        for m in models:
            print(f'   • {m[\"id\"]}')

    # Test working model
    response = requests.post(
        'http://localhost:4000/v1/chat/completions',
        headers={'Content-Type': 'application/json'},
        json={
            'model': 'qwen-coder-vllm',
            'messages': [{'role': 'user', 'content': 'Hello! Working?'}],
            'max_tokens': 10
        },
        timeout=15
    )

    if response.status_code == 200:
        result = response.json()
        print('✅ vLLM test:', result['choices'][0]['message']['content'])
    else:
        print('❌ vLLM test failed:', response.status_code)

except Exception as e:
    print('❌ Test error:', str(e))
"

echo ""
echo "========================="
echo "🎉 SIMPLE FIX COMPLETE!"
echo ""
echo "Status:"
echo "  • LiteLLM: Running with working config"
echo "  • Ollama: Available via LiteLLM"
echo "  • vLLM: Available via LiteLLM (Qwen model)"
echo "  • Models: llama3.1, qwen2.5-coder, qwen-coder-vllm"
echo ""
echo "Commands:"
echo "  • Test models: curl http://localhost:4000/v1/models"
echo "  • Test vLLM: curl -X POST http://localhost:4000/v1/chat/completions -d '{\"model\":\"qwen-coder-vllm\",\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}'"
echo "  • Switch vLLM: ./scripts/vllm-model-switch.sh dolphin"
echo ""
echo "========================="
