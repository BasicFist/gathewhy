# Quick Start Guide

Get started with the AI Unified Backend in under 5 minutes.

## Prerequisites

- LiteLLM gateway running on `http://localhost:4000`
- At least one provider running (Ollama, llama.cpp, or vLLM)

## Verify Gateway is Running

```bash
# Check gateway health
curl http://localhost:4000/health

# List available models
curl http://localhost:4000/v1/models | jq
```

## Your First Request

### Using curl

```bash
# Basic chat completion
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello! Introduce yourself."}],
    "max_tokens": 100
  }'
```

### Using Python (OpenAI SDK)

```python
from openai import OpenAI

# Point to the unified gateway
client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="not-needed"  # No auth required for local development  # pragma: allowlist secret
)

# Make your first request
response = client.chat.completions.create(
    model="llama3.1:8b",  # Routes to Ollama
    messages=[
        {"role": "user", "content": "Hello! Introduce yourself."}
    ]
)

print(response.choices[0].message.content)
```

### Using JavaScript/TypeScript

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:4000/v1',
  apiKey: 'not-needed'  # pragma: allowlist secret
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'llama3.1:8b',
    messages: [
      { role: 'user', content: 'Hello! Introduce yourself.' }
    ]
  });

  console.log(response.choices[0].message.content);
}

chat();
```

## Try Different Providers

### Ollama (General Purpose)

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Explain quantum computing in simple terms."}],
    "max_tokens": 150
  }'
```

### vLLM (Code Generation)

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-coder-vllm",
    "messages": [{"role": "user", "content": "Write a Python function to check if a number is prime"}],
    "max_tokens": 200
  }'
```

### Streaming Responses

```bash
# Add stream: true for real-time token delivery
curl -N -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Count from 1 to 10"}],
    "max_tokens": 100,
    "stream": true
  }'
```

## Python Streaming Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="not-needed"  # pragma: allowlist secret
)

# Stream tokens as they're generated
stream = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[
        {"role": "user", "content": "Write a short story about a robot."}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()  # Newline at the end
```

## Common Model Names

| Model Name | Provider | Best For |
|------------|----------|----------|
| `llama3.1:8b` | Ollama | General chat, quick prototyping |
| `qwen2.5-coder:7b` | Ollama | Code generation (Ollama) |
| `qwen-coder-vllm` | vLLM | High-concurrency code generation |
| `llama2-13b-vllm` | vLLM | Production workloads |

## Troubleshooting

### "Connection refused"
```bash
# Check if LiteLLM is running
systemctl --user status litellm.service

# Check if it's listening on port 4000
ss -tlnp | grep 4000
```

### "Model not found"
```bash
# List all available models
curl http://localhost:4000/v1/models | jq -r '.data[].id'
```

### "Provider timeout"
```bash
# Check provider health
curl http://localhost:11434/api/tags          # Ollama
curl http://localhost:8001/v1/models          # vLLM
```

## Next Steps

- **Choose the right model**: See [Model Selection Guide](model-selection-guide.md)
- **Understand routing**: Read [Architecture Documentation](architecture.md)
- **Integration examples**: Check [Consuming API Guide](consuming-api.md)
- **Add providers**: Follow [Adding Providers Guide](adding-providers.md)

## Quick Reference

**Gateway Endpoint**: `http://localhost:4000`
**OpenAI Format**: Standard OpenAI API compatible
**Authentication**: None (local development)
**Health Check**: `curl http://localhost:4000/health`
**Model List**: `curl http://localhost:4000/v1/models`

---

**Need help?** See [Troubleshooting Guide](troubleshooting.md)
