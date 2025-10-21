# Web UI - Model Testing Interface

Interactive Gradio-based interface for testing and comparing models via the LiteLLM unified backend.

## Features

### 💬 Chat Interface
- **Model Selection**: Dropdown with all available models from LiteLLM
- **Parameter Controls**: Adjust temperature, max_tokens, top_p
- **Chat History**: Persistent conversation context
- **Real-time Metrics**: Response time, token usage, finish reason
- **Request Logging**: All interactions saved to SQLite database

### 🔀 Model Comparison
- **Side-by-side Testing**: Compare 2-4 models simultaneously
- **Same Prompt**: Send identical prompt to multiple models
- **Performance Metrics**: Compare response times and token efficiency
- **Quality Assessment**: Evaluate response quality across models

### 📊 Analytics & History
- **Usage Statistics**: Request volume, token consumption, error rates
- **Recent History**: Last 20 requests with timestamps and metrics
- **Export Functionality**: CSV/JSON export for further analysis
- **Retention Management**: Automatic cleanup of old requests (30 days)

## Installation

### 1. Install Dependencies

```bash
cd /home/miko/LAB/ai/backend/ai-backend-unified

# Install Web UI dependencies in LiteLLM venv
/home/miko/venvs/litellm/bin/pip install -r web-ui/requirements.txt
```

### 2. Configure (Optional)

Edit `web-ui/config.yaml` to customize:
- Server host/port (default: 0.0.0.0:5001)
- LiteLLM endpoint (default: localhost:4000)
- UI theme and appearance
- Parameter ranges
- Database settings

### 3. Run Manually

```bash
# From project root
python3 web-ui/app.py
```

Access at: http://localhost:5001

### 4. Install as Systemd Service (Recommended)

```bash
# Copy service file
cp web-ui/litellm-webui.service ~/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload

# Enable and start
systemctl --user enable litellm-webui.service
systemctl --user start litellm-webui.service

# Check status
systemctl --user status litellm-webui.service
```

## Usage

### Chat Interface

1. Select a model from the dropdown
2. Adjust parameters (temperature, max_tokens, top_p)
3. Type your message and click "Send"
4. View response with timing metrics
5. Continue conversation with context preserved

### Model Comparison

1. Go to "Compare Models" tab
2. Select 2-4 models using checkboxes
3. Enter your prompt
4. Adjust parameters (applied to all models)
5. Click "Run Comparison"
6. Review side-by-side results with metrics

### Analytics

1. Go to "Analytics" tab
2. View 7-day statistics:
   - Total requests
   - Average response time
   - Token usage breakdown
   - Top models by usage
   - Error rates
3. Check recent request history
4. Click "Refresh" to update

## Database

### Location
`web-ui/requests.db` (SQLite)

### Schema

**requests** table:
- id (INTEGER PRIMARY KEY)
- timestamp (DATETIME)
- model (TEXT)
- provider (TEXT)
- messages (JSON)
- temperature, max_tokens, top_p (parameters)
- response (TEXT)
- response_time_ms (INTEGER)
- prompt_tokens, completion_tokens, total_tokens (INTEGER)
- finish_reason (TEXT)
- error (TEXT)
- metadata (JSON)

### Indexes
- idx_model
- idx_timestamp
- idx_provider

### Python API

```python
from database import RequestDatabase

db = RequestDatabase("web-ui/requests.db")

# Get recent requests
requests = db.get_recent_requests(limit=50)

# Search with filters
results = db.search_requests(
    model="llama3.1:8b",
    has_error=False,
    limit=100
)

# Get analytics
analytics = db.get_analytics(days=7)
print(f"Total requests: {analytics['total_requests']}")
print(f"Avg latency: {analytics['avg_response_time_ms']}ms")

# Export data
db.export_to_csv("requests.csv", days=30)
db.export_to_json("requests.json", days=7)

# Cleanup old data
deleted = db.cleanup_old_requests(days=30)
print(f"Deleted {deleted} old requests")
```

## Configuration Reference

### config.yaml

```yaml
server:
  host: "0.0.0.0"  # Listen on all interfaces
  port: 5001        # Web UI port
  share: false      # Set true for public Gradio link

litellm:
  base_url: "http://localhost:4000"
  api_key: "not-needed"  # pragma: allowlist secret
  timeout: 120

ui:
  title: "AI Backend - Model Testing Interface"
  description: "Interactive testing and comparison..."
  theme: "soft"  # soft, default, monochrome
  max_chat_history: 50

comparison:
  max_models: 4
  min_models: 2
  show_timing: true
  show_tokens: true

parameters:
  temperature:
    min: 0.0
    max: 2.0
    default: 0.7
    step: 0.1

  max_tokens:
    min: 1
    max: 4096
    default: 512
    step: 1

  top_p:
    min: 0.0
    max: 1.0
    default: 0.9
    step: 0.05

database:
  path: "web-ui/requests.db"
  enable_analytics: true
  retention_days: 30
```

## Troubleshooting

### Web UI won't start

**Check LiteLLM is running**:
```bash
curl http://localhost:4000/health
```

**Check dependencies**:
```bash
/home/miko/venvs/litellm/bin/pip list | grep gradio
```

**Check logs**:
```bash
journalctl --user -u litellm-webui.service -f
```

### Models not appearing in dropdown

**Verify LiteLLM has models configured**:
```bash
curl http://localhost:4000/v1/models | jq '.data[].id'
```

**Check network connectivity**:
```bash
telnet localhost 4000
```

### Database errors

**Check database file exists and is writable**:
```bash
ls -lh web-ui/requests.db
sqlite3 web-ui/requests.db "SELECT COUNT(*) FROM requests;"
```

**Reset database** (⚠️ deletes all data):
```bash
rm web-ui/requests.db
python3 -c "from web_ui.database import RequestDatabase; RequestDatabase()"
```

## Performance

### Expected Latency
- **Page Load**: <1s
- **Model Dropdown**: <500ms (cached)
- **Chat Response**: Depends on model (typically 1-10s)
- **Comparison (4 models)**: 4x single chat latency
- **Analytics Refresh**: <100ms (up to 10K requests)

### Scaling
- **Concurrent Users**: 10-20 (single Gradio instance)
- **Request History**: Handles 100K+ requests efficiently
- **Database Size**: ~1MB per 1000 requests

For higher concurrency, run multiple instances on different ports:
```bash
# Instance 1
PORT=5001 python3 web-ui/app.py &

# Instance 2
PORT=5002 python3 web-ui/app.py &
```

## Integration with LAB Projects

```python
# From any LAB project
from openai import OpenAI

# Use via Web UI or programmatically
client = OpenAI(
    base_url="http://localhost:4000",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.choices[0].message.content)
```

All requests (whether from Web UI or programmatic API) are logged to the same database for centralized analytics.

## Security Considerations

- **No Authentication**: Web UI has no built-in auth (runs locally)
- **Network Exposure**: Default `0.0.0.0` listens on all interfaces
- **API Keys**: LiteLLM gateway has no auth by default
- **Database**: SQLite file is world-readable by default

For production deployment:
1. Add authentication (Gradio supports OAuth)
2. Restrict to localhost (`host: "127.0.0.1"`)
3. Enable LiteLLM API key auth
4. Set proper file permissions on database

## Future Enhancements

- [ ] Streaming support for real-time token display
- [ ] User authentication and multi-user support
- [ ] Request replay functionality
- [ ] Custom prompt templates
- [ ] Export comparison results as reports
- [ ] Grafana dashboard integration
- [ ] Cost tracking per user/project
- [ ] Rate limiting controls
- [ ] Model performance benchmarking

## Related Documentation

- [Main README](../README.md)
- [Observability Guide](../docs/observability.md)
- [Architecture](../docs/architecture.md)
- [Debugging Tools](../scripts/debugging/README.md)
