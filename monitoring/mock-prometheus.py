#!/usr/bin/env python3

import time
import http.server
import socketserver

# Mock Prometheus metrics for LiteLLM free mode
MOCK_METRICS = """# HELP litellm_requests_total Total number of requests
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
litellm_latency_seconds_count{model="llama3.1:8b"} 78
litellm_latency_seconds_sum{model="llama3.1:8b"} 12.5

# HELP litellm_tokens_total Total tokens processed
# TYPE litellm_tokens_total counter
litellm_tokens_total{model="llama3.1:8b",type="prompt"} 840
litellm_tokens_total{model="llama3.1:8b",type="completion"} 1250
"""

class PrometheusHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(MOCK_METRICS)
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Mock Prometheus Server</h1><p><a href="/metrics">Metrics</a></p></body></html>')

def main():
    port = 4222
    server = http.server.HTTPServer(('0.0.0.0', port), PrometheusHandler)
    print(f"Mock Prometheus server listening on port {port}")
    server.serve_forever()

if __name__ == '__main__':
    main()
