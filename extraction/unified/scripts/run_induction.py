#!/usr/bin/env python3
"""Run a small fixture or full cached TRUST-Instruct induction pass."""

import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from extraction.unified.src.clients import FixtureClient, SoCLaaSTextClient
from extraction.unified.src.extractor import run_induction
from extraction.unified.src.loaders import load_fixture, load_representatives, load_trust_instruct


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--representatives", type=Path)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed-dir", type=Path,
                        help="Optional prior artifact directory used to seed memory and ledgers")
    parser.add_argument("--batch-size", type=int, default=60000,
                        help="Approximate prompt character limit")
    parser.add_argument("--limit", type=int,
                        help="Optional local limit for a controlled test")
    parser.add_argument("--provider", choices=("fixture", "soclaas"), default="fixture")
    parser.add_argument("--model")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.fixture and args.representatives:
        parser.error("choose only one of --fixture or --representatives")
    if args.fixture:
        items = load_fixture(args.fixture)
    elif args.representatives:
        items = load_representatives(args.representatives)
    else:
        items = load_trust_instruct(args.cache_dir)
    if args.limit is not None:
        items = items[:args.limit]
    if args.seed_dir and not args.output_dir.exists():
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name in ("working_unified_skill.md", "rule_ledger.json",
                     "workflow_catalog.json", "workflow_memory.jsonl",
                     "skill_change_log.jsonl"):
            source = args.seed_dir / name
            if source.exists():
                shutil.copy2(source, args.output_dir / name)
    client = FixtureClient() if args.dry_run or args.provider == "fixture" else SoCLaaSTextClient(args.model)
    progress = run_induction(items, client, args.output_dir, max_chars=args.batch_size)
    print({"eligible_rows": len(items), "model_calls": progress.get("api_calls", 0),
           "output_dir": str(args.output_dir)})


if __name__ == "__main__":
    main()
