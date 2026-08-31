import argparse
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if __package__ in {None, ""}:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from data import load_annotations, resolve_image
    from prompts import BASELINE_INSTRUCTIONS, skill_instructions
    from soclaas import SoCLaaSClient
    from parse import parse_prediction
    from workflow import retrieve_evidence
else:
    from .data import load_annotations, resolve_image
    from .prompts import BASELINE_INSTRUCTIONS, skill_instructions
    from .soclaas import SoCLaaSClient
    from .parse import parse_prediction
    from .workflow import retrieve_evidence


def main():
    parser = argparse.ArgumentParser(description="Run MMFakeBench through SoCLaaS.")
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output", required=True, help="JSONL output path")
    parser.add_argument("--condition", choices=["baseline", "skill"], required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--skill-path")
    parser.add_argument("--insecure-tls", action="store_true",
                        help="Disable TLS verification only when the gateway uses an untrusted certificate.")
    args = parser.parse_args()
    # Evidence retrieval is a required part of this evaluation, not an optional
    # condition. Both baseline and skill receive identical web-tool access.
    tools = [{"type": "web_search_preview"}]
    records = load_annotations(args.annotations)
    if args.limit:
        records = records[:args.limit]
    instructions = (BASELINE_INSTRUCTIONS if args.condition == "baseline"
                    else skill_instructions(args.skill_path))
    client = SoCLaaSClient(insecure_tls=args.insecure_tls)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = set()
    if output.exists():
        with output.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    prior = json.loads(line)
                    if prior.get("error") is None:
                        completed.add(prior["index"])
                except (json.JSONDecodeError, KeyError):
                    continue
    pending = [(i, record) for i, record in enumerate(records) if i not in completed]
    print(json.dumps({"total": len(records), "already_completed": len(completed),
                      "pending": len(pending), "concurrency": args.concurrency}))
    write_lock = threading.Lock()

    def run_one(index, record):
        image_path = resolve_image(args.image_root, record["image_path"])
        try:
            retrieval = retrieve_evidence(client, record["text"], str(image_path), tools)
            final_instructions = instructions + (
                "\n\nRetrieved evidence block:\n" + retrieval["retrieved_evidence"]
            )
            response = client.chat_completions(
                record["text"], str(image_path), final_instructions,
                args.temperature, args.max_output_tokens)
            raw = client.text_from_chat_response(response)
            result = parse_prediction(raw)
            result.update({
                "index": index,
                "condition": args.condition,
                "model": client.model,
                "image_path": record["image_path"],
                "text": record["text"],
                "ground_truth_binary": record.get("gt_answers"),
                "ground_truth_class": record.get("fake_cls", "real"),
                "raw_response": raw,
                "api_response": response,
                "image_description": retrieval["image_description"],
                "retrieved_evidence": retrieval["retrieved_evidence"],
                "retrieval": {key: value for key, value in retrieval.items()
                               if key not in {"evidence_api_response"}},
                "runtime_seconds": response.get("_runtime_seconds"),
                "usage": response.get("usage"),
                "error": None,
            })
        except Exception as exc:
            result = {
                "index": index, "condition": args.condition,
                "model": client.model, "image_path": record.get("image_path"),
                "text": record.get("text"), "ground_truth_binary": record.get("gt_answers"),
                "ground_truth_class": record.get("fake_cls", "real"),
                "raw_response": "", "error": repr(exc),
            }
        with write_lock, output.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(result, ensure_ascii=False) + "\n")
        return result

    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        futures = [pool.submit(run_one, i, record) for i, record in pending]
        for future in as_completed(futures):
            result = future.result()
            print(json.dumps({"index": result["index"], "error": result.get("error")}))


if __name__ == "__main__":
    main()
