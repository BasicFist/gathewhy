# API Reference - AI Unified Backend

**Complete API reference for the LiteLLM unified gateway**

Endpoint: `http://localhost:4000`

---

## Quick Reference

### Base Configuration

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="not-needed"  # Local development
)
```

### Available Models

Query the `/v1/models` endpoint to get current list:

```bash
curl http://localhost:4000/v1/models | jq '.data[] | .id'
```

---

## OpenAI-Compatible Endpoints

### Chat Completions

**Endpoint**: `POST /v1/chat/completions`

**Purpose**: Generate conversational responses

#### Basic Request

```python
response = client.chat.completions.create(
    model="llama3.1:latest",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is quantum computing?"}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)
```

#### cURL Example

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:latest",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 100
  }'
```

#### Streaming Response

```python
stream = client.chat.completions.create(
    model="qwen2.5-coder:7b",
    messages=[{"role": "user", "content": "Write a Python function"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### cURL Streaming

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:latest",
    "messages": [{"role": "user", "content": "Count to 10"}],
    "stream": true
  }'
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model identifier (e.g., "llama3.1:latest") |
| `messages` | array | Yes | Array of message objects with role and content |
| `temperature` | float | No | 0.0-2.0, controls randomness (default: 1.0) |
| `max_tokens` | integer | No | Maximum tokens to generate |
| `top_p` | float | No | 0.0-1.0, nucleus sampling (default: 1.0) |
| `frequency_penalty` | float | No | -2.0 to 2.0, penalize repetition |
| `presence_penalty` | float | No | -2.0 to 2.0, penalize topics already mentioned |
| `stream` | boolean | No | Enable streaming (default: false) |
| `stop` | string/array | No | Stop sequences |
| `user` | string | No | User identifier for tracking |

#### Response Format

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699000000,
  "model": "llama3.1:latest",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

---

### Completions (Legacy)

**Endpoint**: `POST /v1/completions`

**Purpose**: Text completion without chat format

#### Request

```python
response = client.completions.create(
    model="llama3.1:latest",
    prompt="Once upon a time,",
    max_tokens=100,
    temperature=0.8
)

print(response.choices[0].text)
```

#### cURL Example

```bash
curl -X POST http://localhost:4000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:latest",
    "prompt": "The capital of France is",
    "max_tokens": 10
  }'
```

---

### Models List

**Endpoint**: `GET /v1/models`

**Purpose**: List all available models

#### Request

```python
models = client.models.list()
for model in models.data:
    print(f"{model.id} - {model.object}")
```

#### cURL Example

```bash
curl http://localhost:4000/v1/models
```

#### Response Format

```json
{
  "object": "list",
  "data": [
    {
      "id": "llama3.1:latest",
      "object": "model",
      "created": 1699000000,
      "owned_by": "ollama",
      "provider": "workspace-backend"
    }
  ]
}
```

#### Filter by Provider

```bash
curl http://localhost:4000/v1/models | \
  jq '.data[] | select(.provider == "workspace-backend")'
```

#### Filter Cloud Models

```bash
curl http://localhost:4000/v1/models | \
  jq '.data[] | select(.id | contains("cloud"))'
```

---

### Model Info

**Endpoint**: `GET /v1/models/{model_id}`

**Purpose**: Get detailed information about a specific model

#### Request

```python
model_info = client.models.retrieve("llama3.1:latest")
print(model_info)
```

#### cURL Example

```bash
curl http://localhost:4000/v1/models/llama3.1:latest
```

---

## Model Selection

### Local Models

Available through Ollama and vLLM providers:

```python
# General chat - Ollama
response = client.chat.completions.create(
    model="llama3.1:latest",
    messages=[{"role": "user", "content": "Hello"}]
)

# Code generation - Ollama
response = client.chat.completions.create(
    model="qwen2.5-coder:7b",
    messages=[{"role": "user", "content": "Write a function"}]
)

# High throughput - vLLM
response = client.chat.completions.create(
    model="qwen-coder-vllm",
    messages=[{"role": "user", "content": "Refactor this code"}]
)

# Creative/Uncensored - vLLM
response = client.chat.completions.create(
    model="dolphin-uncensored-vllm",
    messages=[{"role": "user", "content": "Write a story"}]
)
```

### Cloud Models

Ollama Cloud models (require `OLLAMA_API_KEY`):

```python
# Advanced reasoning - 671B
response = client.chat.completions.create(
    model="deepseek-v3.1:671b-cloud",
    messages=[{"role": "user", "content": "Explain quantum mechanics"}]
)

# Code generation - 480B
response = client.chat.completions.create(
    model="qwen3-coder:480b-cloud",
    messages=[{"role": "user", "content": "Design a microservice architecture"}]
)

# Extreme reasoning - 1T parameters
response = client.chat.completions.create(
    model="kimi-k2:1t-cloud",
    messages=[{"role": "user", "content": "Solve this complex problem"}]
)
```

---

## Advanced Features

### Automatic Routing

The unified backend automatically routes to the best provider:

```python
# Automatically routes to Ollama
response = client.chat.completions.create(
    model="llama3.1:latest",
    messages=[{"role": "user", "content": "Hello"}]
)

# Automatically routes to vLLM for better throughput
response = client.chat.completions.create(
    model="qwen-coder-vllm",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Fallback Chains

If primary provider fails, automatically falls back:

```python
# Primary: ollama, Fallback: llama.cpp
response = client.chat.completions.create(
    model="llama3.1:latest",
    messages=[{"role": "user", "content": "Hello"}]
)
# If Ollama fails, automatically tries llama.cpp
```

### Response Caching

Identical requests are cached (Redis, 1 hour TTL):

```python
# First request - hits provider
response1 = client.chat.completions.create(
    model="llama3.1:latest",
    messages=[{"role": "user", "content": "What is AI?"}],
    temperature=0.7
)

# Second identical request - served from cache (~5ms)
response2 = client.chat.completions.create(
    model="llama3.1:latest",
    messages=[{"role": "user", "content": "What is AI?"}],
    temperature=0.7
)
```

---

## Language-Specific Examples

### Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="qwen2.5-coder:7b",
    messages=[{"role": "user", "content": "Write a quicksort"}]
)
print(response.choices[0].message.content)
```

### JavaScript/Node.js

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:4000/v1',
  apiKey: 'not-needed',
});

const response = await client.chat.completions.create({
  model: 'llama3.1:latest',
  messages: [{ role: 'user', content: 'Hello!' }],
});

console.log(response.choices[0].message.content);
```

### Go

```go
package main

import (
    "context"
    "fmt"
    "github.com/sashabaranov/go-openai"
)

func main() {
    config := openai.DefaultConfig("not-needed")
    config.BaseURL = "http://localhost:4000/v1"
    client := openai.NewClientWithConfig(config)

    resp, err := client.CreateChatCompletion(
        context.Background(),
        openai.ChatCompletionRequest{
            Model: "llama3.1:latest",
            Messages: []openai.ChatCompletionMessage{
                {Role: "user", Content: "Hello!"},
            },
        },
    )

    if err != nil {
        panic(err)
    }

    fmt.Println(resp.Choices[0].Message.Content)
}
```

### R

```r
library(httr)
library(jsonlite)

response <- POST(
  "http://localhost:4000/v1/chat/completions",
  add_headers(`Content-Type` = "application/json"),
  body = list(
    model = "llama3.1:latest",
    messages = list(
      list(role = "user", content = "Hello from R!")
    )
  ),
  encode = "json"
)

content <- content(response, as = "text", encoding = "UTF-8")
result <- fromJSON(content)
print(result$choices[[1]]$message$content)
```

### cURL

```bash
#!/bin/bash

MODEL="llama3.1:latest"
PROMPT="What is the meaning of life?"

curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}],
    \"max_tokens\": 200
  }" | jq -r '.choices[0].message.content'
```

---

## Error Handling

### Common Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 400 | Bad Request | Invalid parameters or malformed JSON |
| 404 | Not Found | Model not available |
| 500 | Internal Server Error | Provider failure (check logs) |
| 503 | Service Unavailable | All providers down (check health) |

### Error Response Format

```json
{
  "error": {
    "message": "Model 'invalid-model' not found",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

### Python Error Handling

```python
from openai import OpenAI, APIError, APIConnectionError

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="not-needed"
)

try:
    response = client.chat.completions.create(
        model="llama3.1:latest",
        messages=[{"role": "user", "content": "Hello"}]
    )
except APIConnectionError as e:
    print(f"Connection error: {e}")
except APIError as e:
    print(f"API error: {e}")
```

---

## Performance Optimization

### Use Streaming for Long Responses

```python
stream = client.chat.completions.create(
    model="llama3.1:latest",
    messages=[{"role": "user", "content": "Write a long story"}],
    stream=True,
    max_tokens=2000
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Set Appropriate max_tokens

```python
# Short responses - faster
response = client.chat.completions.create(
    model="llama3.1:latest",
    messages=[{"role": "user", "content": "Say hi"}],
    max_tokens=10  # Limit to short response
)
```

### Use Lower Temperature for Deterministic Output

```python
response = client.chat.completions.create(
    model="qwen2.5-coder:7b",
    messages=[{"role": "user", "content": "Write a function"}],
    temperature=0.1  # More deterministic
)
```

---

## Monitoring & Debugging

### Check Provider Health

```bash
# All providers
curl http://localhost:4000/health

# Specific provider
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8001/v1/models  # vLLM
```

### View Request Logs

```bash
# Real-time monitoring
./scripts/debugging/tail-requests.py

# Search logs
./scripts/debugging/analyze-logs.py --last 1h --model llama3.1
```

### Check Routing Decisions

```bash
# Test which provider a model routes to
./scripts/debugging/test-routing.sh llama3.1:latest
```

---

## Rate Limits & Quotas

### Local Models
- **No rate limits** - Limited only by hardware
- **Concurrency**: Depends on provider (vLLM: ~30+, Ollama: ~4)

### Cloud Models (Ollama Cloud)
- **Rate limits**: Applied by Ollama (check at https://ollama.com/settings/usage)
- **Fallback**: Automatically routes to local models if rate limited
- **Monitoring**: Track usage with `./scripts/profiling/analyze-token-usage.py`

---

## Best Practices

### 1. Choose the Right Model

```python
# Simple chat → local models
response = client.chat.completions.create(
    model="llama3.1:latest",
    messages=[{"role": "user", "content": "Hello"}]
)

# Code generation → specialized models
response = client.chat.completions.create(
    model="qwen2.5-coder:7b",
    messages=[{"role": "user", "content": "Write code"}]
)

# Complex reasoning → cloud models
response = client.chat.completions.create(
    model="deepseek-v3.1:671b-cloud",
    messages=[{"role": "user", "content": "Explain quantum field theory"}]
)
```

### 2. Handle Errors Gracefully

```python
import time
from openai import APIError

def chat_with_retry(client, model, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages
            )
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

### 3. Use Streaming for Better UX

```python
def stream_response(client, model, prompt):
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

---

## Additional Resources

- **Architecture**: [docs/architecture.md](architecture.md)
- **Model Selection**: [docs/model-selection-guide.md](model-selection-guide.md)
- **Troubleshooting**: [docs/troubleshooting.md](troubleshooting.md)
- **Integration Examples**: [.serena/memories/05-integration-guide.md](../.serena/memories/05-integration-guide.md)

---

**API Version**: OpenAI-compatible v1
**Last Updated**: 2025-10-30
**Endpoint**: `http://localhost:4000/v1`
