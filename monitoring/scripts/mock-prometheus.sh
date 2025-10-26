#!/bin/bash

# LiteLLM Mock Prometheus Server
# Provides mock metrics for Grafana dashboards when Prometheus is not available

PORT=${1:-4222}
INTERVAL=${2:-5}

echo "Starting LiteLLM mock Prometheus server on port $PORT"

# Mock metrics that simulate LiteLLM behavior
cat << EOF | nc -l $PORT -k -e
# HELP litellm_requests_total Total number of requests
# TYPE litellm_requests_total counter
litellm_requests_total{model="llama3.1:8b",provider="ollama"} 42
litellm_requests_total{model="qwen-coder-vllm",provider="vllm"} 18
litellm_requests_total{model="llama2-13b-vllm",provider="vllm"} 7

# HELP litellm_latency_seconds Request latency in seconds
# TYPE litellm_latency_seconds histogram
litellm_latency_seconds_bucket{le="0.1",model="llama3.1:8b"} 12
litellm_latency_seconds_bucket{le="0.5",model="llama3.1:8b"} 28
litellm_latency_seconds_bucket{le="1.0",model="llama3.1:8b"} 35
litellm_latency_seconds_bucket{le="+Inf",model="llama3.1:8b"} 3
litellm_latency_seconds_bucket{le="0.1",model="qwen-coder-vllm"} 8
litellm_latency_seconds_bucket{le="0.5",model="qwen-coder-vllm"} 15
litellm_latency_seconds_bucket{le="1.0",model="qwen-coder-vllm"} 20
litellm_latency_seconds_bucket{le="+Inf",model="qwen-coder-vllm"} 2
litellm_latency_seconds_count{model="llama3.1:8b"} 78
litellm_latency_seconds_sum{model="llama3.1:8b"} 12.5
litellm_latency_seconds_count{model="qwen-coder-vllm"} 45
litellm_latency_seconds_sum{model="qwen-coder-vllm"} 8.7

# HELP litellm_tokens_total Total tokens processed
# TYPE litellm_tokens_total counter
litellm_tokens_total{model="llama3.1:8b",type="prompt"} 840
litellm_tokens_total{model="llama3.1:8b",type="completion"} 1250
litellm_tokens_total{model="qwen-coder-vllm",type="prompt"} 320
litellm_tokens_total{model="qwen-coder-vllm",type="completion"} 480
EOF

echo "Mock Prometheus server stopped"
