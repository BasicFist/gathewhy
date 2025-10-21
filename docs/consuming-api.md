# Consuming the Unified API - Developer Guide

This guide shows how to integrate with the unified AI backend from your LAB projects.

## Quick Start

### Endpoint

All requests go to: `http://localhost:4000`

### API Format

OpenAI-compatible API (supports any OpenAI SDK)

### No Authentication Required

For local development, no API key needed.

## Basic Examples

### Python (requests)

```python
import requests

response = requests.post(
    "http://localhost:4000/v1/chat/completions",
    json={
        "model": "llama3.1:8b",
        "messages": [
            {"role": "user", "content": "Explain Docker in simple terms"}
        ]
    }
)

result = response.json()
print(result["choices"][0]["message"]["content"])
```

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="not-needed"  # pragma: allowlist secret - Required by SDK but unused locally
)

response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[
        {"role": "user", "content": "Write a Python function to reverse a string"}
    ]
)

print(response.choices[0].message.content)
```

### JavaScript/TypeScript

```javascript
// Using fetch
const response = await fetch('http://localhost:4000/v1/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'llama3.1:8b',
    messages: [
      { role: 'user', content: 'Hello!' }
    ]
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

```typescript
// Using OpenAI SDK
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:4000/v1',
  apiKey: 'not-needed'  # pragma: allowlist secret
});

const response = await client.chat.completions.create({
  model: 'llama3.1:8b',
  messages: [
    { role: 'user', content: 'Explain async/await' }
  ]
});

console.log(response.choices[0].message.content);
```

### cURL

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

## Available Models

### List All Models

```bash
curl http://localhost:4000/v1/models | jq
```

**Response**:
```json
{
  "data": [
    {"id": "llama3.1:8b", "object": "model"},
    {"id": "qwen-coder", "object": "model"},
    {"id": "llama2-13b-vllm", "object": "model"},
    {"id": "llama-cpp-python", "object": "model"}
  ]
}
```

### Model Selection Guide

**General Chat**: `llama3.1:8b`
- Best for: Conversations, Q&A, general tasks
- Performance: Fast (~50-150ms)
- Provider: Ollama

**Code Generation (Ollama)**: `qwen-coder`
- Best for: Writing code, explaining code, debugging
- Performance: Fast (~50-150ms)
- Context: 32K tokens (exceptional)
- Provider: Ollama (GGUF quantized)

**Code Generation (vLLM)**: `qwen-coder-vllm` or `llama2-13b-vllm`
- Best for: Code generation with high concurrency
- Performance: ~100-200ms TTFT (first token)
- Context: 4096 tokens
- Provider: vLLM (AWQ 4-bit quantized)
- Model: Qwen/Qwen2.5-Coder-7B-Instruct-AWQ
- Concurrency: Excellent (33.63x for 4096-token requests)

**Low Latency**: `llama-cpp-python` or `llama-cpp-native`
- Best for: Single-request speed priority
- Performance: Very fast (~20-120ms)
- Provider: llama.cpp

## API Reference

### Chat Completions

**Endpoint**: `POST /v1/chat/completions`

**Request Body**:
```json
{
  "model": "llama3.1:8b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is recursion?"}
  ],
  "temperature": 0.7,
  "max_tokens": 500,
  "stream": false
}
```

**Response**:
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699999999,
  "model": "llama3.1:8b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Recursion is a programming technique..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 100,
    "total_tokens": 120
  }
}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | required | Model identifier |
| `messages` | array | required | Chat history |
| `temperature` | float | 0.7 | Randomness (0-2) |
| `max_tokens` | integer | - | Max output length |
| `stream` | boolean | false | Enable streaming |
| `top_p` | float | 1.0 | Nucleus sampling |
| `frequency_penalty` | float | 0.0 | Reduce repetition |
| `presence_penalty` | float | 0.0 | Encourage new topics |

## Advanced Features

### Streaming Responses

**Python**:
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:4000/v1", api_key="not-needed")  # pragma: allowlist secret

stream = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

**JavaScript**:
```javascript
const response = await fetch('http://localhost:4000/v1/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'llama3.1:8b',
    messages: [{ role: 'user', content: 'Tell me a story' }],
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n').filter(line => line.trim());

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      if (data === '[DONE]') break;

      const parsed = JSON.parse(data);
      const content = parsed.choices[0].delta.content;
      if (content) process.stdout.write(content);
    }
  }
}
```

### System Prompts

Set behavior with system messages:

```python
response = client.chat.completions.create(
    model="qwen-coder",
    messages=[
        {
            "role": "system",
            "content": "You are an expert Python programmer. Write clean, well-documented code with type hints."
        },
        {
            "role": "user",
            "content": "Write a binary search function"
        }
    ]
)
```

### Multi-Turn Conversations

Maintain context across messages:

```python
conversation = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
]

response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=conversation
)

# Add assistant response to conversation
conversation.append({
    "role": "assistant",
    "content": response.choices[0].message.content
})

# Continue conversation
conversation.append({
    "role": "user",
    "content": "What are its main features?"
})

response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=conversation
)
```

### Temperature Control

Adjust creativity vs. consistency:

```python
# Creative writing (high temperature)
creative = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Write a poem about coding"}],
    temperature=1.2
)

# Technical accuracy (low temperature)
technical = client.chat.completions.create(
    model="qwen-coder",
    messages=[{"role": "user", "content": "Explain binary search"}],
    temperature=0.3
)
```

## Integration Patterns

### Pattern 1: Simple Chat Bot

```python
class SimpleChatBot:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:4000/v1",
            api_key="not-needed"  # pragma: allowlist secret
        )
        self.conversation = []

    def chat(self, user_message: str) -> str:
        self.conversation.append({
            "role": "user",
            "content": user_message
        })

        response = self.client.chat.completions.create(
            model="llama3.1:8b",
            messages=self.conversation
        )

        assistant_message = response.choices[0].message.content

        self.conversation.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

# Usage
bot = SimpleChatBot()
print(bot.chat("Hello!"))
print(bot.chat("What is Docker?"))
```

### Pattern 2: Code Assistant

```python
class CodeAssistant:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:4000/v1",
            api_key="not-needed"  # pragma: allowlist secret
        )

    def generate_code(self, task: str, language: str = "python") -> str:
        response = self.client.chat.completions.create(
            model="qwen-coder",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert {language} programmer. Write clean, well-documented code."
                },
                {"role": "user", "content": task}
            ],
            temperature=0.3  # Lower for code accuracy
        )
        return response.choices[0].message.content

    def explain_code(self, code: str) -> str:
        response = self.client.chat.completions.create(
            model="llama3.1:8b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a code teacher. Explain code clearly and concisely."
                },
                {"role": "user", "content": f"Explain this code:\n\n{code}"}
            ]
        )
        return response.choices[0].message.content

    def debug(self, code: str, error: str) -> str:
        response = self.client.chat.completions.create(
            model="qwen-coder",
            messages=[
                {"role": "user", "content": f"This code:\n{code}\n\nProduces this error:\n{error}\n\nHow do I fix it?"}
            ]
        )
        return response.choices[0].message.content

# Usage
assistant = CodeAssistant()
code = assistant.generate_code("Write a function to calculate factorial")
explanation = assistant.explain_code(code)
```

### Pattern 3: Batch Processing

```python
import asyncio
from openai import AsyncOpenAI

class BatchProcessor:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="http://localhost:4000/v1",
            api_key="not-needed"  # pragma: allowlist secret
        )

    async def process_batch(self, prompts: list[str]) -> list[str]:
        tasks = [
            self.client.chat.completions.create(
                model="llama2-13b-vllm",  # Best for batching
                messages=[{"role": "user", "content": prompt}]
            )
            for prompt in prompts
        ]

        responses = await asyncio.gather(*tasks)
        return [r.choices[0].message.content for r in responses]

# Usage
processor = BatchProcessor()
prompts = [
    "Summarize: Article 1 text...",
    "Summarize: Article 2 text...",
    "Summarize: Article 3 text...",
]
summaries = asyncio.run(processor.process_batch(prompts))
```

### Pattern 4: vLLM Code Generation

```python
from openai import OpenAI

class VLLMCodeGenerator:
    """Leverage vLLM's high concurrency for code generation tasks"""
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:4000/v1",
            api_key="not-needed"  # pragma: allowlist secret
        )

    def generate_code(
        self,
        task: str,
        language: str = "python",
        streaming: bool = True
    ) -> str:
        """Generate code using vLLM's AWQ-quantized Qwen model"""
        response = self.client.chat.completions.create(
            model="qwen-coder-vllm",  # Routes to vLLM
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert {language} programmer. Write clean, production-ready code."
                },
                {"role": "user", "content": task}
            ],
            temperature=0.3,  # Lower for code accuracy
            max_tokens=1024,
            stream=streaming
        )

        if streaming:
            # Stream tokens for better UX
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            print()  # Newline after streaming
            return full_response
        else:
            return response.choices[0].message.content

    def batch_generate(self, tasks: list[str]) -> list[str]:
        """Leverage vLLM's 33.63x concurrency for batch code generation"""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.generate_code, task, streaming=False)
                for task in tasks
            ]
            return [f.result() for f in concurrent.futures.as_completed(futures)]

# Usage
generator = VLLMCodeGenerator()

# Single code generation with streaming
print("Generating prime number function...")
code = generator.generate_code("Write a Python function to check if a number is prime")

# Batch code generation (leverages vLLM's high concurrency)
tasks = [
    "Write a function to reverse a string",
    "Write a function to find factorial",
    "Write a function for binary search"
]
results = generator.batch_generate(tasks)
```

**Why vLLM for Code Generation?**
- **High Concurrency**: 33.63x parallel requests (vs 2-4x for Ollama)
- **Code Specialist**: Qwen2.5-Coder trained specifically for code
- **Production Quality**: AWQ quantization with minimal quality loss
- **Streaming Support**: Real-time token delivery for better UX

## Error Handling

### Comprehensive Error Handler

```python
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
import time

class ResilientClient:
    def __init__(self, max_retries=3):
        self.client = OpenAI(
            base_url="http://localhost:4000/v1",
            api_key="not-needed"  # pragma: allowlist secret
        )
        self.max_retries = max_retries

    def generate(self, model: str, prompt: str) -> str:
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=30
                )
                return response.choices[0].message.content

            except RateLimitError:
                wait_time = 2 ** attempt
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)

            except APIConnectionError:
                print(f"Connection error, attempt {attempt + 1}/{self.max_retries}")
                time.sleep(1)

            except APIError as e:
                if 500 <= e.status_code < 600:
                    print(f"Server error: {e}, retrying...")
                    time.sleep(2 ** attempt)
                else:
                    print(f"Client error: {e}")
                    return None

            except Exception as e:
                print(f"Unexpected error: {e}")
                return None

        print("Max retries exceeded")
        return None
```

## Performance Tips

### 1. Choose the Right Model

```python
# For speed: Use llama-cpp-native
fast_response = client.chat.completions.create(
    model="llama-cpp-native",
    messages=[{"role": "user", "content": "Quick question"}]
)

# For throughput: Use vLLM
batch_response = client.chat.completions.create(
    model="llama2-13b-vllm",
    messages=[{"role": "user", "content": "Complex analysis"}]
)
```

### 2. Use Streaming for Long Responses

```python
# Better UX for long-form content
stream = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Write a detailed essay"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 3. Adjust max_tokens

```python
# Short responses (faster)
quick = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "What is Docker?"}],
    max_tokens=150  # Limit response length
)

# Long responses
detailed = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Explain Docker in detail"}],
    max_tokens=2000
)
```

### 4. Reduce temperature for Consistency

```python
# Deterministic outputs
response = client.chat.completions.create(
    model="qwen-coder",
    messages=[{"role": "user", "content": "Write a sort function"}],
    temperature=0.1  # More consistent
)
```

## Troubleshooting

### Connection Issues

```python
# Test endpoint availability
import requests

try:
    response = requests.get("http://localhost:4000/v1/models", timeout=5)
    if response.status_code == 200:
        print("✅ API is accessible")
    else:
        print(f"❌ API returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to API. Is LiteLLM running?")
    print("Run: systemctl --user status litellm.service")
```

### Model Not Found

```python
# List available models
models_response = requests.get("http://localhost:4000/v1/models")
available_models = [m["id"] for m in models_response.json()["data"]]
print(f"Available models: {available_models}")
```

### Slow Responses

```python
import time

start = time.time()
response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Hello"}]
)
elapsed = time.time() - start

print(f"Response time: {elapsed:.2f}s")

if elapsed > 5:
    print("⚠️ Slow response. Consider:")
    print("  - Using llama-cpp-native for speed")
    print("  - Reducing max_tokens")
    print("  - Checking provider health")
```

## Best Practices

### 1. Use Appropriate System Prompts

```python
# Good: Clear, specific system prompt
good_system = "You are a Python expert. Provide concise, correct code examples."

# Bad: Vague system prompt
bad_system = "You are helpful."
```

### 2. Handle Streaming Properly

```python
# Good: Check for content before printing
for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)

# Bad: Assume content exists
for chunk in stream:
    print(chunk.choices[0].delta.content)  # May be None
```

### 3. Limit Conversation History

```python
# Good: Keep last N messages
MAX_HISTORY = 10
conversation = conversation[-MAX_HISTORY:]

# Bad: Unlimited history growth
# conversation.append(...)  # Grows forever
```

### 4. Set Reasonable Timeouts

```python
# Good: Set timeout for long-running requests
response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[...],
    timeout=30  # 30 seconds
)

# Bad: No timeout (may hang)
```

## Testing Your Integration

```bash
# Quick integration test script
cat > test_api.py << 'EOF'
from openai import OpenAI

client = OpenAI(base_url="http://localhost:4000/v1", api_key="not-needed")  # pragma: allowlist secret

print("Testing unified API...")

# Test 1: Basic completion
print("\n1. Basic completion:")
response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Say hello"}]
)
print(f"✅ Response: {response.choices[0].message.content[:50]}...")

# Test 2: Code generation
print("\n2. Code generation:")
response = client.chat.completions.create(
    model="qwen-coder",
    messages=[{"role": "user", "content": "Write a Python hello world"}]
)
print(f"✅ Generated code")

# Test 3: Streaming
print("\n3. Streaming:")
stream = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Count to 3"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print("\n✅ Streaming works")

print("\n✅ All tests passed!")
EOF

python test_api.py
```

## Next Steps

- Review [Architecture](architecture.md) to understand the system
- Check [Troubleshooting Guide](troubleshooting.md) for common issues
- See [Adding Providers](adding-providers.md) to extend the system
