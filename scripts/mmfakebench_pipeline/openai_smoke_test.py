"""Run one OpenAI Responses call per condition on a local image."""

import argparse
import base64
import json
import mimetypes
import os
import ssl
import urllib.request
from pathlib import Path

if __package__ in {None, ""}:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from prompts import BASELINE_INSTRUCTIONS, skill_instructions
    from parse import parse_prediction
else:
    from .prompts import BASELINE_INSTRUCTIONS, skill_instructions
    from .parse import parse_prediction


def load_env():
    env_path = Path(__file__).parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def image_data_url(path):
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def output_text(response):
    chunks = []
    for item in response.get("output", []):
        for content in item.get("content", []) if isinstance(item, dict) else []:
            if content.get("type") == "output_text":
                chunks.append(content.get("text", ""))
    return "\n".join(chunks).strip()


def run_call(api_key, model, image_path, caption, instructions):
    payload = {
        "model": model,
        "instructions": instructions + (
            "\n\nYou have web search available in this same call. You must use it "
            "to verify the caption and image-derived clues before judging."
        ),
        "tools": [{"type": "web_search"}],
        "include": ["web_search_call.action.sources"],
        "input": [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": f"News caption:\n{caption}"},
                {"type": "input_image", "image_url": image_data_url(image_path), "detail": "high"},
            ],
        }],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    with urllib.request.urlopen(request, context=context, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="tmp/trustvl_examples/rumour-sample.jpeg")
    parser.add_argument("--caption", default="The church that survived the California wildfire.")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()
    load_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is missing from the environment or .env")
    model = args.model or os.environ.get("OPENAI_MODEL", "gpt-5.4-nano")

    for condition, instructions in (("baseline", BASELINE_INSTRUCTIONS),
                                    ("skill", skill_instructions())):
        response = run_call(api_key, model, args.image, args.caption, instructions)
        text = output_text(response)
        web_calls = [item for item in response.get("output", [])
                     if item.get("type") == "web_search_call"]
        print(json.dumps({
            "condition": condition,
            "model": model,
            "web_search_calls": len(web_calls),
            "parsed": parse_prediction(text),
            "response": text,
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
