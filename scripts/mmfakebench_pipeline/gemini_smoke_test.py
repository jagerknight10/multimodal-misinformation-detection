"""Single-call Gemini multimodal misinformation smoke test with Google Search grounding."""

import base64
import json
import mimetypes
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).parents[2]
IMAGE = ROOT / "tmp/trustvl_examples/rumour-sample.jpeg"
CAPTION = "The church that survived the California wildfire."


def load_env():
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    load_env()
    key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    if not key:
        raise SystemExit("GEMINI_API_KEY is missing from .env")
    if not IMAGE.exists():
        raise SystemExit(f"Image not found: {IMAGE}")

    mime = mimetypes.guess_type(IMAGE.name)[0] or "image/jpeg"
    image_b64 = base64.b64encode(IMAGE.read_bytes()).decode("ascii")
    prompt = f"""You are verifying a multimodal news claim.

Caption: {CAPTION}

Inspect the image independently, use Google Search grounding to verify the claim,
and assess whether the image actually depicts the claimed church and wildfire event.
Return concise sections for Image analysis, Evidence, Cross-modal assessment, and
Final judgment. End with exactly: Judgement: Real or Judgement: Fake."""
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime, "data": image_b64}},
            ],
        }],
        "tools": [{"google_search": {}}],
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        try:
            import certifi
            context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            context = ssl.create_default_context()
        with urllib.request.urlopen(request, context=context, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Gemini HTTP {exc.code}: {body}") from exc

    candidate = (result.get("candidates") or [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = "\n".join(p.get("text", "") for p in parts if "text" in p).strip()
    grounding = candidate.get("groundingMetadata", {})
    chunks = grounding.get("groundingChunks", [])
    supports = bool(grounding)
    print(json.dumps({
        "model": model,
        "image": str(IMAGE),
        "caption": CAPTION,
        "google_search_grounding_returned": supports,
        "grounding_chunks": len(chunks),
        "response": text,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
