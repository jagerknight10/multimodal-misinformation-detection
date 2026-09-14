#!/usr/bin/env python3
"""Rebuild structured ledgers from cached induction responses."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from extraction.unified.src.extractor import (  # noqa: E402
    _merge_catalog, _read_json, _render_skill, parse_json,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    cache_dir = args.output_dir / "cache"
    rules, workflows, accepted_log = [], [], []
    summaries = []
    for cache_path in sorted(cache_dir.glob("batch_*.json")):
        cached = _read_json(cache_path, {})
        try:
            result = parse_json(cached["raw_response"])
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
        batch = int(cached.get("batch", 0))
        summaries.append(str(result.get("working_skill", "")).strip())
        candidates = result.get("candidate_changes", [])
        rules = _merge_catalog(rules, candidates, batch)
        updates = result.get("updates", [])
        for update in updates:
            if not isinstance(update, dict) or update.get("action") == "no_change":
                continue
            accepted_log.append({
                "batch": batch, "row_id": update.get("row_id"),
                "action": update.get("action"), "rule": update.get("rule", ""),
                "supporting_row_ids": update.get("supporting_row_ids", []),
            })
            rule = update.get("rule", "")
            if isinstance(rule, str) and rule.strip():
                rules = _merge_catalog(rules, [{
                    "name": f"rule_from_{update.get('row_id', 'unknown')}",
                    "purpose": "Dataset-supported verification rule",
                    "steps": [rule], "supporting_row_ids": update.get("supporting_row_ids", []),
                    "action": update.get("action"),
                }], batch)
        workflows = _merge_catalog(workflows, result.get("workflows", []), batch)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "rule_ledger.json").write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n")
    (args.output_dir / "workflow_catalog.json").write_text(json.dumps(workflows, ensure_ascii=False, indent=2) + "\n")
    (args.output_dir / "skill_change_log.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in accepted_log))
    summary = next((item for item in reversed(summaries) if item), "")
    (args.output_dir / "working_unified_skill.md").write_text(
        _render_skill(summary, rules, workflows), encoding="utf-8")
    print({"cached_batches": len(list(cache_dir.glob('batch_*.json'))),
           "rules": len(rules), "workflows": len(workflows),
           "accepted_changes": len(accepted_log)})


if __name__ == "__main__":
    main()
