# Integration Guide - Consuming the Unified API

## Overview

This guide shows LAB projects (KANNA, ComfyUI, custom apps) how to consume the unified AI backend through the single LiteLLM endpoint. All examples use the OpenAI-compatible API at `http://localhost:4000`.

## Quick Start

### Basic Chat Completion

```python
import requests

response = requests.post(
    "http://localhost:4000/v1/chat/completions",
    json={
        "model": "llama3.1:8b",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }
)

print(response.json()["choices"][0]["message"]["content"])
```

### Using OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="not-needed-for-local"  # Required by SDK but unused locally  # pragma: allowlist secret
)

response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)

print(response.choices[0].message.content)
```

---

## Integration Patterns by Project

### KANNA (Research Assistant)

**Use Case**: AI-powered research with code generation capabilities

**Recommended Models**:
- General research: `llama3.1:8b`
- Code generation: `qwen-coder`
- High throughput: `llama2-13b-vllm`

**Example Integration**:

```python
# kanna/ai_backend.py
from openai import OpenAI
from typing import Generator

class UnifiedAIBackend:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:4000/v1",
            api_key="not-needed"  # pragma: allowlist secret
        )

    def research_query(self, query: str) -> str:
        """General research queries"""
        response = self.client.chat.completions.create(
            model="llama3.1:8b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a research assistant. Provide detailed, accurate information."
                },
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content

    def code_generation(self, task: str, language: str = "python") -> str:
        """Code generation tasks"""
        response = self.client.chat.completions.create(
            model="qwen-coder",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert {language} programmer. Write clean, well-documented code."
                },
                {"role": "user", "content": task}
            ],
            temperature=0.3  # Lower temp for code
        )
        return response.choices[0].message.content

    def streaming_research(self, query: str) -> Generator[str, None, None]:
        """Streaming for long-form research"""
        stream = self.client.chat.completions.create(
            model="llama3.1:8b",
            messages=[{"role": "user", "content": query}],
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

# Usage
backend = UnifiedAIBackend()

# Research query
answer = backend.research_query("Explain transformer architecture")

# Code generation
code = backend.code_generation("Write a binary search function")

# Streaming
for chunk in backend.streaming_research("Write an essay on AI ethics"):
    print(chunk, end="", flush=True)
```

**Benefits for KANNA**:
- ✅ Automatic provider selection (Ollama for chat, qwen-coder for code)
- ✅ Failover if provider unavailable
- ✅ No KANNA code changes if providers are added/removed
- ✅ Streaming support for long-form research

---

### ComfyUI (Workflow Automation)

**Use Case**: Text generation nodes in visual workflows

**Recommended Models**:
- Text generation: `llama3.1:8b`
- Prompt enhancement: `llama3.1:8b`
- Batch processing: `llama2-13b-vllm`

**Example Integration**:

```python
# comfyui/custom_nodes/ai_text_node.py
import requests
from typing import Any

class AITextGenerator:
    """ComfyUI node for AI text generation"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "model": (["llama3.1:8b", "qwen-coder", "llama2-13b-vllm"],),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0}),
                "max_tokens": ("INT", {"default": 500, "min": 1, "max": 4000}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate"
    CATEGORY = "AI"

    def generate(self, prompt: str, model: str, temperature: float, max_tokens: int) -> tuple[str]:
        response = requests.post(
            "http://localhost:4000/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )

        result = response.json()["choices"][0]["message"]["content"]
        return (result,)

class AIPromptEnhancer:
    """Enhance image generation prompts with AI"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_prompt": ("STRING", {"multiline": True}),
                "style": (["realistic", "artistic", "anime", "cinematic"],),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "enhance"
    CATEGORY = "AI"

    def enhance(self, base_prompt: str, style: str) -> tuple[str]:
        system_prompt = f"""You are a prompt engineering expert for image generation.
        Enhance the user's prompt for {style} style.
        Add relevant details, lighting, composition, and quality tags.
        Return only the enhanced prompt, no explanations."""

        response = requests.post(
            "http://localhost:4000/v1/chat/completions",
            json={
                "model": "llama3.1:8b",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": base_prompt}
                ],
                "temperature": 0.8,
                "max_tokens": 200
            }
        )

        enhanced = response.json()["choices"][0]["message"]["content"]
        return (enhanced,)

# Register nodes
NODE_CLASS_MAPPINGS = {
    "AITextGenerator": AITextGenerator,
    "AIPromptEnhancer": AIPromptEnhancer,
}
```

**Benefits for ComfyUI**:
- ✅ Visual node interface for AI generation
- ✅ Model selection in workflow UI
- ✅ Automatic failover for reliability
- ✅ Batched workflows use vLLM for efficiency

---

### Custom Web Applications

**Use Case**: Frontend apps with AI features

**Example: React + TypeScript Frontend**

```typescript
// src/lib/aiBackend.ts
interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

class UnifiedAIClient {
  private baseUrl = 'http://localhost:4000/v1';

  async chatCompletion(request: ChatCompletionRequest): Promise<string> {
    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    const data = await response.json();
    return data.choices[0].message.content;
  }

  async *streamChatCompletion(
    request: ChatCompletionRequest
  ): AsyncGenerator<string> {
    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...request, stream: true }),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader!.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(line => line.trim() !== '');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;

          try {
            const parsed = JSON.parse(data);
            const content = parsed.choices[0].delta.content;
            if (content) yield content;
          } catch (e) {
            // Skip malformed JSON
          }
        }
      }
    }
  }
}

// Usage in React component
import { useState } from 'react';

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const client = new UnifiedAIClient();

  const sendMessage = async () => {
    const userMessage: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setStreaming(true);

    let assistantMessage = '';

    for await (const chunk of client.streamChatCompletion({
      model: 'llama3.1:8b',
      messages: [...messages, userMessage],
      temperature: 0.7,
    })) {
      assistantMessage += chunk;
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: assistantMessage },
      ]);
    }

    setStreaming(false);
  };

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i} className={msg.role}>
          {msg.content}
        </div>
      ))}
      <input
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyPress={e => e.key === 'Enter' && sendMessage()}
        disabled={streaming}
      />
    </div>
  );
}
```

**Benefits for Web Apps**:
- ✅ Real-time streaming for better UX
- ✅ Provider abstraction (frontend doesn't know Ollama vs vLLM)
- ✅ Standard OpenAI SDK compatibility
- ✅ TypeScript type safety

---

### Backend Services (FastAPI, Express)

**Example: FastAPI Backend**

```python
# backend/ai_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from typing import List, Optional

app = FastAPI()

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="not-needed"  # pragma: allowlist secret
)

class ChatRequest(BaseModel):
    message: str
    model: str = "llama3.1:8b"
    context: Optional[List[dict]] = None

class CodeRequest(BaseModel):
    task: str
    language: str = "python"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """General chat endpoint"""
    messages = request.context or []
    messages.append({"role": "user", "content": request.message})

    try:
        response = client.chat.completions.create(
            model=request.model,
            messages=messages
        )
        return {
            "response": response.choices[0].message.content,
            "model_used": response.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/code")
async def code_generation(request: CodeRequest):
    """Code generation endpoint"""
    prompt = f"Write a {request.language} function that: {request.task}"

    response = client.chat.completions.create(
        model="qwen-coder",
        messages=[
            {
                "role": "system",
                "content": f"You are an expert {request.language} programmer. Write clean, documented code."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return {
        "code": response.choices[0].message.content,
        "language": request.language
    }

@app.get("/api/models")
async def list_models():
    """List available models"""
    models = client.models.list()
    return {"models": [model.id for model in models.data]}
```

**Usage**:
```bash
# Chat request
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Explain Docker", "model": "llama3.1:8b"}'

# Code generation
curl -X POST http://localhost:8000/api/code \
  -d '{"task": "sort an array", "language": "python"}'

# List models
curl http://localhost:8000/api/models
```

---

## Advanced Integration Patterns

### Pattern 1: Multi-Model Workflows

```python
class MultiModelWorkflow:
    """Use different models for different stages"""

    def __init__(self):
        self.client = OpenAI(base_url="http://localhost:4000/v1", api_key="not-needed")  # pragma: allowlist secret

    def research_and_code(self, topic: str, language: str) -> dict:
        # Stage 1: Research with general model
        research = self.client.chat.completions.create(
            model="llama3.1:8b",
            messages=[{
                "role": "user",
                "content": f"Explain the key concepts of {topic} for implementation"
            }]
        ).choices[0].message.content

        # Stage 2: Code generation with specialized model
        code = self.client.chat.completions.create(
            model="qwen-coder",
            messages=[
                {"role": "system", "content": f"Research: {research}"},
                {
                    "role": "user",
                    "content": f"Implement {topic} in {language} based on the research"
                }
            ]
        ).choices[0].message.content

        return {"research": research, "code": code}
```

### Pattern 2: Capability-Based Selection

```python
class SmartModelSelector:
    """Automatically select best model for task"""

    CAPABILITY_MAP = {
        "code": "qwen-coder",
        "chat": "llama3.1:8b",
        "high_volume": "llama2-13b-vllm"
    }

    def __init__(self):
        self.client = OpenAI(base_url="http://localhost:4000/v1", api_key="not-needed")  # pragma: allowlist secret

    def infer_capability(self, prompt: str) -> str:
        """Infer task type from prompt"""
        code_keywords = ["function", "class", "implement", "code", "programming"]
        if any(kw in prompt.lower() for kw in code_keywords):
            return "code"
        return "chat"

    def generate(self, prompt: str, capability: Optional[str] = None) -> str:
        if capability is None:
            capability = self.infer_capability(prompt)

        model = self.CAPABILITY_MAP.get(capability, "llama3.1:8b")

        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content
```

### Pattern 3: Fallback Handling

```python
from openai import OpenAI, OpenAIError

class ResilientAIClient:
    """Handle failures gracefully with custom fallback logic"""

    def __init__(self):
        self.client = OpenAI(base_url="http://localhost:4000/v1", api_key="not-needed")  # pragma: allowlist secret
        self.fallback_models = ["llama3.1:8b", "llama-cpp-python"]

    def generate_with_fallback(self, prompt: str, preferred_model: str) -> dict:
        models_to_try = [preferred_model] + self.fallback_models

        for model in models_to_try:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=10
                )
                return {
                    "content": response.choices[0].message.content,
                    "model_used": model,
                    "fallback_used": model != preferred_model
                }
            except OpenAIError as e:
                print(f"Model {model} failed: {e}")
                continue

        raise Exception("All models failed")
```

### Pattern 4: Caching for Efficiency

```python
import hashlib
import redis
from typing import Optional

class CachedAIClient:
    """Client-side caching layer"""

    def __init__(self):
        self.client = OpenAI(base_url="http://localhost:4000/v1", api_key="not-needed")  # pragma: allowlist secret
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.cache_ttl = 3600  # 1 hour

    def _cache_key(self, model: str, messages: list, temperature: float) -> str:
        content = f"{model}:{str(messages)}:{temperature}"
        return f"ai_cache:{hashlib.md5(content.encode()).hexdigest()}"

    def generate(self, model: str, messages: list, temperature: float = 0.7) -> str:
        cache_key = self._cache_key(model, messages, temperature)

        # Check cache
        cached = self.redis.get(cache_key)
        if cached:
            return cached

        # Generate
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )

        result = response.choices[0].message.content

        # Cache result
        self.redis.setex(cache_key, self.cache_ttl, result)

        return result
```

---

## Error Handling Best Practices

### Comprehensive Error Handler

```python
from openai import OpenAI, OpenAIError, APIError, RateLimitError, APIConnectionError

class SafeAIClient:
    def __init__(self):
        self.client = OpenAI(base_url="http://localhost:4000/v1", api_key="not-needed")  # pragma: allowlist secret

    def generate(self, model: str, prompt: str, max_retries: int = 3) -> Optional[str]:
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=30
                )
                return response.choices[0].message.content

            except RateLimitError:
                print(f"Rate limited, waiting {2 ** attempt}s...")
                time.sleep(2 ** attempt)

            except APIConnectionError:
                print("Connection error, retrying...")
                time.sleep(1)

            except APIError as e:
                if e.status_code >= 500:
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

---

## Performance Optimization

### Batch Requests
```python
async def batch_generate(prompts: List[str], model: str = "llama2-13b-vllm"):
    """Use vLLM for batched requests"""
    tasks = [
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        for prompt in prompts
    ]

    responses = await asyncio.gather(*tasks)
    return [r.choices[0].message.content for r in responses]
```

### Streaming for Long Responses
```python
def stream_long_form(prompt: str) -> Generator[str, None, None]:
    """Stream for better perceived performance"""
    stream = client.chat.completions.create(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

---

## Testing Your Integration

### Validation Script

```bash
#!/bin/bash
# test_integration.sh

echo "Testing unified AI backend integration..."

# Test 1: Model availability
echo "1. Checking available models..."
curl -s http://localhost:4000/v1/models | jq '.data[].id'

# Test 2: Basic completion
echo "2. Testing basic completion..."
curl -s -X POST http://localhost:4000/v1/chat/completions \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Say hello"}]
  }' | jq '.choices[0].message.content'

# Test 3: Code generation
echo "3. Testing code generation..."
curl -s -X POST http://localhost:4000/v1/chat/completions \
  -d '{
    "model": "qwen-coder",
    "messages": [{
      "role": "user",
      "content": "Write a Python function to reverse a string"
    }]
  }' | jq '.choices[0].message.content'

# Test 4: Streaming
echo "4. Testing streaming..."
curl -s -X POST http://localhost:4000/v1/chat/completions \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }'

echo "Integration tests complete!"
```

---

## Troubleshooting

### Common Issues

**Issue: Connection refused**
```python
# Solution: Verify LiteLLM is running
import subprocess
result = subprocess.run(["systemctl", "--user", "status", "litellm.service"], capture_output=True)
print(result.stdout.decode())
```

**Issue: Model not found**
```python
# Solution: List available models
models = client.models.list()
available = [m.id for m in models.data]
print(f"Available models: {available}")
```

**Issue: Slow responses**
```python
# Solution: Use smaller model or vLLM for batching
# For single request speed: llama-cpp-native
# For batch throughput: llama2-13b-vllm
```

---

## Migration from Direct Provider Access

### Before (Direct Ollama)
```python
# Old: Coupled to Ollama
import requests
response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.1:8b", "prompt": "Hello"}
)
```

### After (Unified Backend)
```python
# New: Provider-agnostic
from openai import OpenAI
client = OpenAI(base_url="http://localhost:4000/v1", api_key="not-needed")  # pragma: allowlist secret
response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Benefits**:
- ✅ Same code works with any provider
- ✅ Automatic failover
- ✅ Standard OpenAI SDK
- ✅ No code changes when adding providers

---

## Integration Checklist

Before deploying your integration:

- [ ] Test with `scripts/validate-unified-backend.sh`
- [ ] Implement error handling and retries
- [ ] Use appropriate model for task (chat vs code vs high-throughput)
- [ ] Consider streaming for long-form content
- [ ] Add client-side caching if needed
- [ ] Test fallback behavior (stop provider and verify failover)
- [ ] Monitor response times and adjust models
- [ ] Document model choices in your code

**Version**: 1.0
**Last Updated**: 2025-10-19
