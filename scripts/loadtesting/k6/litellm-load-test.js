/**
 * LiteLLM Load Testing with k6
 * High-performance load testing for LiteLLM unified backend
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const completionDuration = new Trend('completion_duration');
const tokenCount = new Counter('total_tokens');
const successfulRequests = new Counter('successful_requests');
const failedRequests = new Counter('failed_requests');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:4000';

// Load test scenarios
export const options = {
  scenarios: {
    // Scenario 1: Gradual ramp-up (realistic production simulation)
    gradual_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 10 },   // Ramp up to 10 users over 1 minute
        { duration: '3m', target: 10 },   // Stay at 10 for 3 minutes
        { duration: '1m', target: 50 },   // Ramp up to 50
        { duration: '3m', target: 50 },   // Stay at 50 for 3 minutes
        { duration: '1m', target: 0 },    // Ramp down to 0
      ],
      gracefulRampDown: '30s',
    },

    // Scenario 2: Spike test (sudden traffic surge)
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },  // Baseline
        { duration: '10s', target: 100 }, // Sudden spike!
        { duration: '1m', target: 100 },  // Hold spike
        { duration: '30s', target: 10 },  // Back to baseline
        { duration: '30s', target: 0 },   // Ramp down
      ],
      startTime: '10m',  // Start after gradual_load
    },

    // Scenario 3: Constant load (stress test)
    constant_load: {
      executor: 'constant-vus',
      vus: 30,
      duration: '5m',
      startTime: '15m',  // Start after spike_test
    },
  },

  thresholds: {
    // Success criteria
    http_req_failed: ['rate<0.05'],      // Less than 5% failures
    http_req_duration: ['p(95)<5000'],   // 95% of requests under 5s
    'errors': ['rate<0.05'],             // Less than 5% error rate
    'completion_duration': ['p(95)<6000'], // 95% of completions under 6s
  },
};

// Test data
const PROMPTS = [
  "What is the capital of France?",
  "Write a Python function to calculate fibonacci numbers",
  "Explain quantum computing in simple terms",
  "Translate 'Hello, how are you?' to Spanish",
  "Summarize the importance of clean code",
  "What are the best practices for REST API design?",
  "Debug this Python code: print(hello world)",
  "Compare Python and JavaScript for web development",
  "Explain the SOLID principles",
  "Write a SQL query to find duplicate records",
];

const MODELS = {
  'llama3.1:8b': 0.60,
  'llama-3.1-8b-instruct': 0.25,
  'qwen-coder-vllm': 0.15,
};

// Helper functions
function selectModel() {
  const rand = Math.random();
  let cumulative = 0;

  for (const [model, weight] of Object.entries(MODELS)) {
    cumulative += weight;
    if (rand < cumulative) {
      return model;
    }
  }

  return 'llama3.1:8b';  // Fallback
}

function randomChoice(array) {
  return array[Math.floor(Math.random() * array.length)];
}

// Main test function
export default function () {
  const model = selectModel();
  const prompt = randomChoice(PROMPTS);
  const maxTokens = randomChoice([50, 100, 150]);

  const payload = JSON.stringify({
    model: model,
    messages: [
      { role: 'user', content: prompt }
    ],
    max_tokens: maxTokens,
    metadata: {
      user_id: `k6_user_${__VU}`,
      environment: 'loadtest',
      iteration: __ITER,
    }
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    tags: {
      model: model,
      type: 'completion',
    },
  };

  // Make request
  const startTime = Date.now();
  const response = http.post(`${BASE_URL}/v1/chat/completions`, payload, params);
  const duration = Date.now() - startTime;

  // Record metrics
  completionDuration.add(duration);

  // Check response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'has completion': (r) => {
      if (r.status === 200) {
        try {
          const body = JSON.parse(r.body);
          return body.choices && body.choices.length > 0;
        } catch (e) {
          return false;
        }
      }
      return false;
    },
    'has usage data': (r) => {
      if (r.status === 200) {
        try {
          const body = JSON.parse(r.body);
          return body.usage && body.usage.total_tokens > 0;
        } catch (e) {
          return false;
        }
      }
      return false;
    },
  });

  if (!success) {
    errorRate.add(1);
    failedRequests.add(1);
    console.log(`❌ Request failed: ${response.status} - ${model}`);
  } else {
    errorRate.add(0);
    successfulRequests.add(1);

    try {
      const body = JSON.parse(response.body);
      const tokens = body.usage.total_tokens;
      tokenCount.add(tokens);
    } catch (e) {
      console.log(`⚠️  Failed to parse response body`);
    }
  }

  // Simulate realistic user think time (1-5 seconds)
  sleep(Math.random() * 4 + 1);
}

// Setup function (runs once per VU before main function)
export function setup() {
  console.log('🚀 Starting LiteLLM load test...');
  console.log(`   Target: ${BASE_URL}`);
  console.log(`   Models: ${Object.keys(MODELS).join(', ')}`);
  console.log('');

  // Test health endpoint
  const healthResponse = http.get(`${BASE_URL}/health`);
  if (healthResponse.status !== 200) {
    console.error('❌ Health check failed! LiteLLM may not be running.');
    throw new Error('LiteLLM health check failed');
  }

  console.log('✅ Health check passed');
  return { startTime: Date.now() };
}

// Teardown function (runs once after all iterations)
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log('');
  console.log('🏁 Load test complete');
  console.log(`   Duration: ${duration.toFixed(0)}s`);
  console.log('');
}

// Handle summary data
export function handleSummary(data) {
  console.log('');
  console.log('=' .repeat(80));
  console.log('📊 LOAD TEST SUMMARY');
  console.log('=' .repeat(80));

  const metrics = data.metrics;

  // Request statistics
  console.log('\nRequests:');
  console.log(`  Total:      ${metrics.http_reqs.values.count}`);
  console.log(`  Successful: ${metrics.successful_requests?.values.count || 0}`);
  console.log(`  Failed:     ${metrics.failed_requests?.values.count || 0}`);
  console.log(`  Rate:       ${metrics.http_reqs.values.rate.toFixed(2)} req/s`);

  // Response time statistics
  console.log('\nResponse Time:');
  console.log(`  Average:    ${metrics.http_req_duration.values.avg.toFixed(0)}ms`);
  console.log(`  Median:     ${metrics.http_req_duration.values.med.toFixed(0)}ms`);
  console.log(`  P90:        ${metrics.http_req_duration.values['p(90)'].toFixed(0)}ms`);
  console.log(`  P95:        ${metrics.http_req_duration.values['p(95)'].toFixed(0)}ms`);
  console.log(`  P99:        ${metrics.http_req_duration.values['p(99)'].toFixed(0)}ms`);
  console.log(`  Max:        ${metrics.http_req_duration.values.max.toFixed(0)}ms`);

  // Completion duration
  if (metrics.completion_duration) {
    console.log('\nCompletion Duration:');
    console.log(`  Average:    ${metrics.completion_duration.values.avg.toFixed(0)}ms`);
    console.log(`  P95:        ${metrics.completion_duration.values['p(95)'].toFixed(0)}ms`);
  }

  // Token statistics
  if (metrics.total_tokens) {
    console.log('\nTokens:');
    console.log(`  Total:      ${metrics.total_tokens.values.count}`);
    console.log(`  Rate:       ${metrics.total_tokens.values.rate.toFixed(2)} tokens/s`);
  }

  // Error rate
  console.log('\nError Rate:');
  const errorPct = (metrics.errors.values.rate * 100).toFixed(2);
  console.log(`  ${errorPct}%`);

  // Thresholds
  console.log('\nThresholds:');
  for (const [name, threshold] of Object.entries(data.thresholds)) {
    const status = threshold.ok ? '✅ PASS' : '❌ FAIL';
    console.log(`  ${name}: ${status}`);
  }

  console.log('');

  return {
    'stdout': JSON.stringify(data, null, 2),
    'summary.json': JSON.stringify(data, null, 2),
  };
}
