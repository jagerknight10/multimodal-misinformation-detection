#!/usr/bin/env python3
"""Create a deterministic representative trajectory set for induction."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from extraction.unified.src.grouping import group_items, grouping_report, select_representatives
from extraction.unified.src.loaders import load_fixture, load_trust_instruct


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--per-group", type=int, default=3)
    args = parser.parse_args()
    items = load_fixture(args.fixture) if args.fixture else load_trust_instruct(args.cache_dir)
    groups = group_items(items)
    representatives = select_representatives(groups, args.per_group)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "representatives.json").write_text(json.dumps([
        {"row_id": item.row_id, "image": item.image, "instruction": item.instruction,
         "response": item.response, "family": item.family}
        for item in representatives
    ], ensure_ascii=False, indent=2), encoding="utf-8")
    report = grouping_report(items, args.per_group)
    report["group_sizes"] = {str(size): count for size, count in report["group_sizes"].items()}
    (args.output_dir / "grouping_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
