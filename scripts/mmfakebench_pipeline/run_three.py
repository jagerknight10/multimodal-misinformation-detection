"""Run the matched baseline, unified-skill, and routed-specialist conditions."""

import argparse
from pathlib import Path

from .data import load_evidence, select_stratified
from .experiment import (build_run_config, validate_completed_smoke,
                         write_run_config)
from .providers import create_client
from .runner import run_condition, write_manifest
from .status import StatusWriter


CONDITIONS = ("baseline", "unified", "routed")


def main():
    parser = argparse.ArgumentParser(
        description="Run three matched MMFakeBench conditions with fixed evidence.")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--smoke-config", required=True,
                        help="run_config.json from the completed 4-sample smoke run")
    parser.add_argument("--provider", choices=["gemini", "soclaas"], default="gemini")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--selection", choices=["first", "stratified"], default="stratified")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--rpm", type=float, default=10)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument("--temperature", type=float, default=0.0)
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

    client = create_client(args.provider, timeout=args.timeout,
                           max_retries=args.max_retries,
                           insecure_tls=args.insecure_tls)
    config = build_run_config(
        "full", args.evidence, args.annotations, args.image_root, len(records),
        client.provider, client.model, args.temperature, args.max_output_tokens,
        args.rpm, args.concurrency)
    validate_completed_smoke(args.smoke_config, config)
    write_run_config(config, output_dir)

    status = StatusWriter(args.status)
    status.start()
    try:
        for condition in CONDITIONS:
            run_condition(
                records, condition, args.image_root,
                output_dir / f"{condition}.jsonl", status,
                rpm=args.rpm, concurrency=args.concurrency,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature, timeout=args.timeout,
                max_retries=args.max_retries, insecure_tls=args.insecure_tls,
                client=client)
            if status.state.get("message", "").startswith("Stopped"):
                break
    except Exception as exc:
        status.close(phase="failed", message=f"Fatal error: {exc!r}")
        raise
    else:
        status.close(phase="finished_three_conditions",
                     message="Baseline, unified, and routed runs finished.")


if __name__ == "__main__":
    main()
