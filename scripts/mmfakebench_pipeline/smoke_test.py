"""Eight-call API smoke test: four representative records, two conditions each."""

import argparse
from pathlib import Path

from .data import load_evidence, select_stratified
from .runner import run_condition, write_manifest
from .status import StatusWriter
from .soclaas import SoCLaaSClient


def main():
    parser = argparse.ArgumentParser(description="Run a four-sample paired SoCLaaS smoke test.")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output-dir", default="results/smoke")
    parser.add_argument("--rpm", type=float, default=10)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--insecure-tls", action="store_true")
    parser.add_argument("--status", default="results/mmfakebench_status.md")
    args = parser.parse_args()
    records = select_stratified(load_evidence(
        args.evidence, annotations_path=args.annotations, drop_unmatched=True), 4)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_manifest(records, output_dir / "input_manifest.jsonl")
    status = StatusWriter(args.status)
    status.start()
    try:
        client = SoCLaaSClient(timeout=args.timeout, max_retries=args.max_retries,
                               insecure_tls=args.insecure_tls)
        for condition in ("baseline", "skill"):
            run_condition(records, condition, args.image_root,
                          output_dir / f"{condition}.jsonl", status,
                          rpm=args.rpm, concurrency=1, timeout=args.timeout,
                          max_retries=args.max_retries, client=client)
    finally:
        status.close(phase="finished_smoke", message="Smoke test finished.")


if __name__ == "__main__":
    main()
