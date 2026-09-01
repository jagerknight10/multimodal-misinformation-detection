import argparse
from pathlib import Path

from .data import load_evidence, select_stratified
from .runner import run_condition, write_manifest
from .status import StatusWriter
from .soclaas import SoCLaaSClient


def main():
    parser = argparse.ArgumentParser(description="Run one fixed-evidence MMFakeBench condition.")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--annotations", help="Validation JSON used to align image paths")
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--condition", choices=["baseline", "skill"], required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--selection", choices=["first", "stratified"], default="first")
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
    status = StatusWriter(args.status)
    status.start()
    try:
        client = SoCLaaSClient(timeout=args.timeout, max_retries=args.max_retries,
                               insecure_tls=args.insecure_tls)
        manifest = Path(args.output).with_name("input_manifest.jsonl")
        write_manifest(records, manifest)
        run_condition(records, args.condition, args.image_root, args.output, status,
                      rpm=args.rpm, concurrency=args.concurrency,
                      max_output_tokens=args.max_output_tokens, temperature=args.temperature,
                      timeout=args.timeout, max_retries=args.max_retries,
                      skill_path=args.skill_path, insecure_tls=args.insecure_tls, client=client)
    except Exception as exc:
        status.close(phase="failed", message=f"Fatal error: {exc!r}")
        raise
    else:
        status.close(phase=f"finished_{args.condition}", message="Run finished.")


if __name__ == "__main__":
    main()
