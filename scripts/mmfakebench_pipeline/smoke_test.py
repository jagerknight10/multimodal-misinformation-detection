import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).parent))
    from prompts import BASELINE_INSTRUCTIONS, skill_instructions
    from soclaas import SoCLaaSClient
    from parse import parse_prediction
else:
    from .prompts import BASELINE_INSTRUCTIONS, skill_instructions
    from .soclaas import SoCLaaSClient
    from .parse import parse_prediction


EVIDENCE_INSTRUCTIONS = """Retrieve evidence for the supplied news caption using the
web_search_preview tool. Search the exact claim and distinctive entities. Return a
concise evidence brief with source titles, URLs when available, dates, and whether
each source supports or contradicts the claim. Do not make a final benchmark
classification. If retrieval fails, say so explicitly."""

IMAGE_DESCRIPTION_INSTRUCTIONS = """Describe only what is visibly present in the supplied
image. Extract readable text, names, logos, people, places, events, and other
distinctive clues that could be used for inverse evidence retrieval. Do not judge
the caption."""


def main():
    parser = argparse.ArgumentParser(description="Smoke-test SoCLaaS with one local image.")
    parser.add_argument("--image", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--skill-path")
    parser.add_argument("--insecure-tls", action="store_true")
    args = parser.parse_args()
    tools = [{"type": "web_search_preview"}]
    try:
        client = SoCLaaSClient(insecure_tls=args.insecure_tls)
        image_response = client.chat_completions(
            args.caption, args.image, IMAGE_DESCRIPTION_INSTRUCTIONS,
            max_tokens=500)
        image_description = client.text_from_chat_response(image_response)
        evidence_prompt = (
            f"News caption:\n{args.caption}\n\n"
            f"Image-derived clues:\n{image_description}"
        )
        evidence_response = client.responses_text(
            evidence_prompt, EVIDENCE_INSTRUCTIONS, tools, max_output_tokens=1000)
        evidence = client.text_from_response(evidence_response)
        conditions = (("baseline", BASELINE_INSTRUCTIONS),
                      ("skill", skill_instructions(args.skill_path)))
        for condition, instructions in conditions:
            final_instructions = instructions + f"\n\nRetrieved evidence block:\n{evidence}"
            response = client.chat_completions(
                args.caption, args.image, final_instructions, max_tokens=1200)
            raw = client.text_from_chat_response(response)
            print(json.dumps({
                "condition": condition, "model": client.model,
                "parsed": parse_prediction(raw), "runtime_seconds": response.get("_runtime_seconds"),
                "usage": response.get("usage"), "response": raw,
                "image_description": image_description if condition == "baseline" else None,
                "retrieved_evidence": evidence if condition == "baseline" else None,
            }, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"error": repr(exc)}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
