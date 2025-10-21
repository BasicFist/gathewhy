/**
 * LiteLLM Smoke Test
 * Quick validation test to verify basic functionality
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,           // 5 virtual users
  duration: '30s',  // Run for 30 seconds
  thresholds: {
    http_req_failed: ['rate<0.01'],    // Less than 1% failures
    http_req_duration: ['p(95)<3000'], // 95% under 3s
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:4000';

export default function () {
  // Test 1: List models
  const modelsResponse = http.get(`${BASE_URL}/v1/models`);
  check(modelsResponse, {
    'models endpoint works': (r) => r.status === 200,
  });

  // Test 2: Simple completion
  const completionResponse = http.post(
    `${BASE_URL}/v1/chat/completions`,
    JSON.stringify({
      model: 'llama3.1:8b',
      messages: [{ role: 'user', content: 'Say hello' }],
      max_tokens: 10,
    }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  check(completionResponse, {
    'completion works': (r) => r.status === 200,
    'has response': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.choices && body.choices.length > 0;
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1);
}

export function setup() {
  console.log('🔥 Running smoke test...');

  const healthResponse = http.get(`${BASE_URL}/health`);
  if (healthResponse.status !== 200) {
    throw new Error('❌ Health check failed');
  }

  console.log('✅ Health check passed\n');
}

export function handleSummary(data) {
  console.log('\n📊 Smoke Test Results:');
  console.log(`   Requests: ${data.metrics.http_reqs.values.count}`);
  console.log(`   Failures: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%`);
  console.log(`   Avg duration: ${data.metrics.http_req_duration.values.avg.toFixed(0)}ms`);
  console.log(`   P95 duration: ${data.metrics.http_req_duration.values['p(95)'].toFixed(0)}ms`);

  const allPassed = Object.values(data.thresholds).every(t => t.ok);
  console.log(`\n${allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}\n`);

  return {
    'stdout': '',
  };
}
