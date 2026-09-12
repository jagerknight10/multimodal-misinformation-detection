"""Gemini adapter implementing the benchmark runner's one-call client interface."""

import base64
import json
import mimetypes
import os
import ssl
import time
import urllib.error
import urllib.request

from .soclaas import load_env_file


class GeminiError(RuntimeError):
    pass


class GeminiClient:
    provider = "gemini"

    def __init__(self, api_key=None, model=None, timeout=180, max_retries=1,
                 insecure_tls=False):
        load_env_file()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise GeminiError("Set GEMINI_API_KEY before calling Gemini.")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")
        self.timeout = timeout
        self.max_retries = max_retries
        if insecure_tls:
            self.ssl_context = ssl._create_unverified_context()
        else:
            try:
                import certifi
                self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            except ImportError:
                self.ssl_context = ssl.create_default_context()

    @staticmethod
    def _image_part(image_path):
        mime = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
        with open(image_path, "rb") as stream:
            data = base64.b64encode(stream.read()).decode("ascii")
        return {"inline_data": {"mime_type": mime, "data": data}}

    def chat_completions_with_evidence(self, caption, image_path, evidence, instructions,
                                       temperature=0.0, max_tokens=1200):
        payload = {
            "system_instruction": {"parts": [{"text": instructions}]},
            "contents": [{"role": "user", "parts": [
                {"text": f"News caption:\n{caption}\n\n{evidence}"},
                self._image_part(image_path),
            ]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent")
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
            method="POST")
        started = time.monotonic()
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, context=self.ssl_context,
                                            timeout=self.timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    result["_runtime_seconds"] = round(time.monotonic() - started, 3)
                    result["usage"] = result.get("usageMetadata")
                    return result
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code not in {408, 429, 500, 502, 503, 504} or attempt >= self.max_retries:
                    print(f"[gemini] HTTP {exc.code}: {detail[:300]}", flush=True)
                    raise GeminiError(f"HTTP {exc.code}: {detail[:1000]}") from exc
                delay = min(60, 2 ** attempt)
                print(f"[gemini] HTTP {exc.code}; retry {attempt + 1}/{self.max_retries} "
                      f"in {delay}s: {detail[:220]}", flush=True)
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt >= self.max_retries:
                    print(f"[gemini] network error: {exc}", flush=True)
                    raise GeminiError(str(exc)) from exc
                delay = min(60, 2 ** attempt)
                print(f"[gemini] network error; retry {attempt + 1}/{self.max_retries} "
                      f"in {delay}s: {exc}", flush=True)
            time.sleep(delay)
        raise GeminiError("request failed")

    @staticmethod
    def text_from_chat_response(response):
        candidate = (response.get("candidates") or [{}])[0]
        parts = candidate.get("content", {}).get("parts", [])
        return "\n".join(part.get("text", "") for part in parts
                         if isinstance(part, dict) and "text" in part).strip()
