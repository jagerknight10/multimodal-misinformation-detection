#!/usr/bin/env python3
"""Run the local TRUST-Instruct audit without model calls."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from extraction.unified.src.audit import audit_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--write-row-ids", action="store_true")
    args = parser.parse_args()
    if args.fixture:
        items = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        from datasets import load_dataset
        dataset = load_dataset("NUSryan/TRUST-Instruct", split="train",
                               cache_dir=str(args.cache_dir), streaming=False)
        items = list(dataset)
    if args.limit:
        items = items[:args.limit]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = audit_rows(items, args.output_dir / "row_manifest.jsonl" if args.write_row_ids else None)
    (args.output_dir / "data_card.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"rows_inspected": len(items), "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
