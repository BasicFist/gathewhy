"""HTTP helpers used by the PTUI dashboard."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:  # pragma: no cover - optional dependency
    import aiohttp
except ImportError:  # pragma: no cover - async mode disabled automatically
    aiohttp = None

ASYNC_AVAILABLE = aiohttp is not None


def fetch_json(url: str, timeout: float) -> tuple[dict[str, Any] | None, float | None, str | None]:
    """Fetch JSON payload from a URL synchronously."""

    start_time = time.perf_counter()
    try:
        request = Request(url, headers={"User-Agent": "ptui-dashboard"})
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - controlled URLs
            data = json.loads(response.read().decode("utf-8"))
        latency = time.perf_counter() - start_time
        return data, latency, None
    except (HTTPError, URLError, TimeoutError) as exc:
        latency = time.perf_counter() - start_time
        return None, latency, str(exc)
    except Exception as exc:  # pragma: no cover - safety guard
        return None, None, str(exc)


async def fetch_json_async(
    session: "aiohttp.ClientSession", url: str, timeout: float
) -> tuple[dict[str, Any] | None, float | None, str | None]:
    """Fetch JSON payload asynchronously when aiohttp is available."""

    if aiohttp is None:  # pragma: no cover - sanity guard
        raise RuntimeError("aiohttp is not installed")

    start_time = time.perf_counter()
    try:
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        headers = {"User-Agent": "ptui-dashboard"}
        async with session.get(url, headers=headers, timeout=timeout_obj) as response:
            data = await response.json()
        latency = time.perf_counter() - start_time
        return data, latency, None
    except TimeoutError:
        latency = time.perf_counter() - start_time
        return None, latency, "Request timed out"
    except aiohttp.ClientError as exc:
        latency = time.perf_counter() - start_time
        return None, latency, str(exc)
    except Exception as exc:  # pragma: no cover - safety guard
        return None, None, str(exc)
