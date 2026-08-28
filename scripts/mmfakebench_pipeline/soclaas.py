import base64
import json
import mimetypes
import os
import ssl
import time
import urllib.error
import urllib.request


def load_env_file(path=None):
    """Load simple KEY=value entries without overriding existing environment variables."""
    env_path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key.startswith("export "):
                key = key[7:].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            os.environ.setdefault(key, value)


class SoCLaaSError(RuntimeError):
    pass


class SoCLaaSClient:
    def __init__(self, base_url=None, api_key=None, model=None, timeout=180,
                 max_retries=5, insecure_tls=False):
        load_env_file()
        self.base_url = (base_url or os.environ.get("SOCLAAS_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("SOCLAAS_API_KEY", "")
        if not self.base_url or not self.api_key:
            raise SoCLaaSError(
                "Set SOCLAAS_BASE_URL and SOCLAAS_API_KEY before calling SoCLaaS."
            )
        self.model = model or os.environ.get("SOCLAAS_MODEL", "qwen3-vl:32b")
        self.timeout = timeout
        self.max_retries = max_retries
        if insecure_tls:
            self.ssl_context = ssl._create_unverified_context()
        else:
            ca_bundle = os.environ.get("SOCLAAS_CA_BUNDLE")
            if not ca_bundle:
                try:
                    import certifi
                    ca_bundle = certifi.where()
                except ImportError:
                    ca_bundle = None
            self.ssl_context = ssl.create_default_context(
                cafile=ca_bundle
            )

    def _post(self, path, payload):
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/v1/{path.lstrip('/')}",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout,
                                            context=self.ssl_context) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code not in {408, 429, 500, 502, 503, 504} or attempt >= self.max_retries:
                    raise SoCLaaSError(f"HTTP {exc.code}: {detail[:1000]}") from exc
                time.sleep(min(60, 2 ** attempt))
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt >= self.max_retries:
                    raise SoCLaaSError(str(exc)) from exc
                time.sleep(min(60, 2 ** attempt))
        raise SoCLaaSError("request failed")

    def models(self):
        request = urllib.request.Request(
            f"{self.base_url}/v1/models",
            headers={"Authorization": f"Bearer {self.api_key}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout,
                                        context=self.ssl_context) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SoCLaaSError(f"HTTP {exc.code}: {detail[:1000]}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise SoCLaaSError(str(exc)) from exc

    @staticmethod
    def image_data_url(image_path):
        mime = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
        with open(image_path, "rb") as stream:
            encoded = base64.b64encode(stream.read()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def responses(self, caption, image_path, instructions, tools=None,
                  temperature=0.0, max_output_tokens=1200):
        content = [
            {"type": "input_text", "text": f"News caption:\n{caption}"},
            {"type": "input_image", "image_url": self.image_data_url(image_path),
             "detail": "high"},
        ]
        payload = {
            "model": self.model,
            "instructions": instructions,
            "input": [{"role": "user", "content": content}],
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }
        if tools:
            payload["tools"] = tools
        started = time.monotonic()
        response = self._post("responses", payload)
        response["_runtime_seconds"] = round(time.monotonic() - started, 3)
        return response

    def responses_text(self, prompt, instructions, tools=None,
                       temperature=0.0, max_output_tokens=1000):
        """Text-only Responses call, used for gateway-executed web retrieval."""
        payload = {
            "model": self.model,
            "instructions": instructions,
            "input": prompt,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }
        if tools:
            payload["tools"] = tools
        started = time.monotonic()
        response = self._post("responses", payload)
        response["_runtime_seconds"] = round(time.monotonic() - started, 3)
        return response

    def chat_completions(self, caption, image_path, instructions,
                         temperature=0.0, max_tokens=1200):
        """Vision-preserving fallback using the gateway's low-transformation chat endpoint."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": [
                    {"type": "text", "text": f"News caption:\n{caption}"},
                    {"type": "image_url", "image_url": {
                        "url": self.image_data_url(image_path), "detail": "high"
                    }},
                ]},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        started = time.monotonic()
        response = self._post("chat/completions", payload)
        response["_runtime_seconds"] = round(time.monotonic() - started, 3)
        return response

    @staticmethod
    def text_from_response(response):
        if response.get("output_text"):
            return response["output_text"]
        chunks = []
        for item in response.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    chunks.append(content.get("text", ""))
        return "\n".join(chunks)

    @staticmethod
    def text_from_chat_response(response):
        choices = response.get("choices", [])
        if not choices:
            return ""
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, str):
            return content
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
