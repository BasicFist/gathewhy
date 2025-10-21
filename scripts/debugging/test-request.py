#!/usr/bin/env python3
"""
LiteLLM Test Request Utility
Make test requests to LiteLLM with detailed debugging output and tracing.
"""

import sys
import json
import time
import argparse
from typing import Optional, Dict, Any
import requests


class RequestTester:
    """Test LiteLLM requests with detailed debugging."""

    def __init__(self, base_url: str = "http://localhost:4000", verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose

    def test_health(self) -> bool:
        """Test if LiteLLM is healthy."""
        print("🔍 Testing LiteLLM health...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ LiteLLM is healthy")
                if self.verbose:
                    print(f"   Response: {response.json()}")
                return True
            else:
                print(f"⚠️  Health check returned: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

    def list_models(self) -> None:
        """List available models."""
        print("\n📋 Available models:")
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                print(f"   Found {len(models)} models:")
                for model in models[:20]:  # Limit to first 20
                    model_id = model.get('id', 'unknown')
                    print(f"   - {model_id}")
                if len(models) > 20:
                    print(f"   ... and {len(models) - 20} more")
            else:
                print(f"   ❌ Failed to list models: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error listing models: {e}")

    def make_completion_request(
        self,
        model: str,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        max_tokens: int = 100
    ) -> None:
        """Make a completion request with detailed logging."""
        print(f"\n🚀 Testing completion request")
        print(f"   Model: {model}")
        print(f"   Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

        request_data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "stream": stream
        }

        if metadata:
            request_data["metadata"] = metadata
            print(f"   Metadata: {json.dumps(metadata)}")

        print(f"\n📤 Request:")
        if self.verbose:
            print(json.dumps(request_data, indent=2))

        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=60,
                stream=stream
            )

            elapsed = (time.time() - start_time) * 1000  # Convert to ms

            print(f"\n📥 Response:")
            print(f"   Status: {response.status_code}")
            print(f"   Time: {elapsed:.0f} ms")

            # Show headers (especially request ID)
            if 'x-request-id' in response.headers:
                print(f"   Request ID: {response.headers['x-request-id']}")

            if response.status_code == 200:
                if stream:
                    print(f"   Response (streaming):")
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith('data: '):
                                data = decoded[6:]  # Remove 'data: ' prefix
                                if data == '[DONE]':
                                    print("\n   Stream complete")
                                    break
                                try:
                                    chunk = json.loads(data)
                                    content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                    if content:
                                        print(content, end='', flush=True)
                                except json.JSONDecodeError:
                                    pass
                else:
                    data = response.json()
                    if self.verbose:
                        print(json.dumps(data, indent=2))
                    else:
                        # Show just the important parts
                        choice = data.get('choices', [{}])[0]
                        content = choice.get('message', {}).get('content', '')
                        usage = data.get('usage', {})

                        print(f"\n   Content: {content[:200]}{'...' if len(content) > 200 else ''}")
                        print(f"\n   Usage:")
                        print(f"     Prompt tokens: {usage.get('prompt_tokens', 0)}")
                        print(f"     Completion tokens: {usage.get('completion_tokens', 0)}")
                        print(f"     Total tokens: {usage.get('total_tokens', 0)}")

                print("\n✅ Request successful")

            else:
                print(f"   Error: {response.text[:500]}")
                print("\n❌ Request failed")

        except requests.exceptions.Timeout:
            print(f"\n❌ Request timed out after 60s")
        except Exception as e:
            print(f"\n❌ Request failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()

    def test_provider_routing(self, providers: list) -> None:
        """Test routing to different providers."""
        print("\n🔀 Testing provider routing")

        # Map providers to test models
        test_cases = {
            'ollama': 'llama3.1:8b',
            'llamacpp': 'llama-3.1-8b-instruct',
            'vllm': 'qwen-coder-vllm'
        }

        for provider in providers:
            model = test_cases.get(provider)
            if not model:
                print(f"   ⚠️  No test model configured for provider: {provider}")
                continue

            print(f"\n   Testing {provider} ({model})...")
            self.make_completion_request(
                model=model,
                prompt="Hello, world!",
                metadata={"provider": provider, "test": "routing"},
                max_tokens=10
            )
            time.sleep(1)  # Brief pause between tests


def main():
    parser = argparse.ArgumentParser(description="Test LiteLLM requests with debugging")
    parser.add_argument('--url', default='http://localhost:4000',
                       help="LiteLLM base URL (default: http://localhost:4000)")
    parser.add_argument('--model', default='llama3.1:8b',
                       help="Model to test (default: llama3.1:8b)")
    parser.add_argument('--prompt', default='What is 2+2? Answer briefly.',
                       help="Test prompt")
    parser.add_argument('--stream', action='store_true',
                       help="Test streaming response")
    parser.add_argument('--max-tokens', type=int, default=100,
                       help="Maximum tokens to generate (default: 100)")
    parser.add_argument('--metadata', type=json.loads,
                       help='Custom metadata as JSON string (e.g., \'{"project":"test"}\')')
    parser.add_argument('--test-routing', action='store_true',
                       help="Test routing to all providers")
    parser.add_argument('--list-models', action='store_true',
                       help="List available models")
    parser.add_argument('-v', '--verbose', action='store_true',
                       help="Verbose output")

    args = parser.parse_args()

    tester = RequestTester(base_url=args.url, verbose=args.verbose)

    # Always test health first
    if not tester.test_health():
        print("\n⚠️  LiteLLM may not be running or accessible")
        print(f"   Check: {args.url}/health")
        sys.exit(1)

    # List models if requested
    if args.list_models:
        tester.list_models()

    # Test routing if requested
    if args.test_routing:
        tester.test_provider_routing(['ollama', 'llamacpp', 'vllm'])

    # Always make at least one test request
    if not args.test_routing:
        tester.make_completion_request(
            model=args.model,
            prompt=args.prompt,
            metadata=args.metadata,
            stream=args.stream,
            max_tokens=args.max_tokens
        )

    print("\n✅ Testing complete")


if __name__ == '__main__':
    main()
