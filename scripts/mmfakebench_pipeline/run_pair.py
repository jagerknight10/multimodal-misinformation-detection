import argparse
import json
import os
from pathlib import Path

from .data import load_evidence, select_stratified
from .runner import run_condition, write_manifest
from .status import StatusWriter
from .soclaas import SoCLaaSClient


def main():
    parser = argparse.ArgumentParser(
        description="Run matched MMFakeBench baseline then TRUST-VL-skill conditions."
    )
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--annotations", required=True,
                        help="Validation JSON used to align image paths")
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--selection", choices=["first", "stratified"], default="stratified")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--rpm", type=float, default=10)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--skill-path")
    parser.add_argument("--status", default="results/mmfakebench_status.md")
    parser.add_argument("--insecure-tls", action="store_true")
    args = parser.parse_args()
    records = load_evidence(args.evidence, annotations_path=args.annotations,
                            drop_unmatched=True)
    if args.limit is not None:
        records = (select_stratified(records, args.limit) if args.selection == "stratified"
                   else records[:args.limit])
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_manifest(records, output_dir / "input_manifest.jsonl")
    (output_dir / "run_config.json").write_text(json.dumps({
        "evidence": str(args.evidence), "image_root": str(args.image_root),
        "sample_count": len(records), "excluded_unmatched_evidence_records": 8,
        "text_evidence_cap": 10,
        "image_evidence_cap": 10, "conditions": ["baseline", "skill"],
        "model": os.environ.get("SOCLAAS_MODEL", "qwen3-vl:32b"),
        "temperature": args.temperature, "max_output_tokens": args.max_output_tokens,
        "rpm": args.rpm, "concurrency": args.concurrency,
    }, indent=2) + "\n", encoding="utf-8")
    status = StatusWriter(args.status)
    status.start()
    try:
        client = SoCLaaSClient(timeout=args.timeout, max_retries=args.max_retries,
                               insecure_tls=args.insecure_tls)
        for condition in ("baseline", "skill"):
            run_condition(records, condition, args.image_root,
                          output_dir / f"{condition}.jsonl", status,
                          rpm=args.rpm, concurrency=args.concurrency,
                          max_output_tokens=args.max_output_tokens,
                          temperature=args.temperature, timeout=args.timeout,
                          max_retries=args.max_retries, skill_path=args.skill_path,
                          insecure_tls=args.insecure_tls, client=client)
            if status.state.get("message", "").startswith("Stopped"):
                break
    except Exception as exc:
        status.close(phase="failed", message=f"Fatal error: {exc!r}")
        raise
    else:
        status.close(phase="finished_pair", message="Baseline and skill runs finished.")


if __name__ == "__main__":
    main()
