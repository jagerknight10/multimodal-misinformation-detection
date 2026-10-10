"""Twelve-call API smoke test: four representative records, three conditions each."""

import argparse
from pathlib import Path

from .data import load_evidence, select_stratified
from .experiment import build_run_config, write_run_config
from .providers import create_client
from .runner import run_condition, write_manifest
from .status import StatusWriter


def main():
    parser = argparse.ArgumentParser(
        description="Run four stratified samples under baseline, unified, and routed conditions.")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output-dir", default="results/smoke")
    parser.add_argument("--provider", choices=["gemini", "soclaas"], default="gemini")
    parser.add_argument("--rpm", type=float, default=10)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--insecure-tls", action="store_true")
    parser.add_argument("--status", default="results/mmfakebench_status.md")
    args = parser.parse_args()
    records = select_stratified(load_evidence(
        args.evidence, annotations_path=args.annotations, drop_unmatched=True), 4)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_manifest(records, output_dir / "input_manifest.jsonl")
    client = create_client(args.provider, timeout=args.timeout,
                           max_retries=args.max_retries,
                           insecure_tls=args.insecure_tls)
    config = build_run_config(
        "smoke", args.evidence, args.annotations, args.image_root, len(records),
        client.provider, client.model, args.temperature, args.max_output_tokens, args.rpm, 1)
    write_run_config(config, output_dir)
    status = StatusWriter(args.status)
    status.start()
    try:
        for condition in ("baseline", "unified", "routed"):
            run_condition(records, condition, args.image_root,
                          output_dir / f"{condition}.jsonl", status,
                          rpm=args.rpm, concurrency=1, timeout=args.timeout,
                          max_retries=args.max_retries,
                          max_output_tokens=args.max_output_tokens,
                          temperature=args.temperature, client=client)
    finally:
        status.close(phase="finished_smoke", message="Three-condition smoke test finished.")


if __name__ == "__main__":
    main()
