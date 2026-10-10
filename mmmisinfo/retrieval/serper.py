"""Cached access to Serper text and image search."""

import hashlib
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi


class SerperError(RuntimeError):
    """A Serper request failed without writing a cache entry."""


def cached_search(query: str, endpoint: str, cache_dir: Path, api_key: str | None = None) -> tuple[dict, Path, bool]:
    """Return (saved result, path, cache_hit); only request on a cache miss."""
    if endpoint not in {"search", "images"}:
        raise ValueError(f"Unsupported Serper endpoint: {endpoint}")
    if not query.strip():
        raise ValueError("Search query must not be empty")
    request_spec = {"endpoint": endpoint, "q": query}
    cache_id = hashlib.sha256(json.dumps(request_spec, sort_keys=True).encode()).hexdigest()[:20]
    cache_path = cache_dir / f"{cache_id}.json"
    if cache_path.exists():
        result = json.loads(cache_path.read_text(encoding="utf-8"))
        if result.get("request") != request_spec:
            raise SerperError(f"Cache request mismatch: {cache_path}")
        return result, cache_path, True

    if not api_key:
        raise SerperError("SERPER_API_KEY is required on a cache miss")
    body = json.dumps({"q": query, "num": 5}).encode()
    request = Request(
        f"https://google.serper.dev/{endpoint}",
        data=body,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=25, context=ssl.create_default_context(cafile=certifi.where())) as response:
            payload = json.load(response)
            status = response.status
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise SerperError(f"HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise SerperError(f"Connection failed: {exc.reason}") from exc

    result = {
        "request": request_spec,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": status,
        "response": payload,
    }
    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary = cache_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(cache_path)
    return result, cache_path, False
