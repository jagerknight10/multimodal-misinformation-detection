"""Evaluate a diverse set of Qwen routed failures with Gemini.

Selection is deterministic, uses only already-saved Qwen outputs, and the
evaluation reuses the canonical routed prompt/evidence runner. The runner
writes checkpointed JSONL so an interrupted run can be resumed safely.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from .gemini import GeminiClient
from .runner import run_condition, write_manifest
from .status import StatusWriter


ANCHORS = [30, 29, 56, 296, 7, 736]
QUOTAS = {
    "real_false_positive": 6,
    "textual_failure": 6,
    "visual_failure": 6,
    "cross_modal_failure": 7,
}


def read_rows(path):
    rows = []
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def error_group(row):
    if row.get("error") or not row.get("predicted_binary") or not row.get("predicted_class"):
        return None
    gold = row.get("ground_truth_binary")
    predicted = row.get("predicted_binary")
    gold_class = row.get("ground_truth_class")
    predicted_class = row.get("predicted_class")
    if gold == "Real" and (predicted != "Real" or predicted_class != "real"):
        return "real_false_positive"
    if gold == "Fake" and (predicted != "Fake" or predicted_class != gold_class):
        short_class = gold_class.replace("_veracity_distortion", "").replace(
            "_consistency_distortion", "")
        return f"{short_class}_failure"
    return None


def source_key(row):
    parts = str(row.get("image_path", "")).strip("/").split("/")
    return parts[1] if len(parts) > 1 else parts[0] if parts else "unknown"


def diverse_pick(candidates, needed, already):
    """Round-robin over source datasets and prefer unseen source families."""
    pools = defaultdict(list)
    for row in candidates:
        if row["sample_id"] not in already:
            pools[source_key(row)].append(row)
    for values in pools.values():
        values.sort(key=lambda row: (int(row.get("index", 0)), row["sample_id"]))
    selected = []
    keys = sorted(pools)
    while len(selected) < needed and keys:
        progressed = False
        for key in keys:
            if pools[key] and len(selected) < needed:
                selected.append(pools[key].pop(0))
                progressed = True
        if not progressed:
            break
    return selected


def select_rows(rows):
    by_index = {int(row["index"]): row for row in rows}
    selected = []
    selected_ids = set()
    for index in ANCHORS:
        row = by_index.get(index)
        if row and error_group(row) and row["sample_id"] not in selected_ids:
            selected.append(row)
            selected_ids.add(row["sample_id"])

    groups = defaultdict(list)
    for row in rows:
        group = error_group(row)
        if group:
            groups[group].append(row)

    for group, quota in QUOTAS.items():
        current = sum(error_group(row) == group for row in selected)
        if current < quota:
            selected.extend(diverse_pick(groups[group], quota - current, selected_ids))
            selected_ids.update(row["sample_id"] for row in selected)

    if len(selected) != sum(QUOTAS.values()):
        raise RuntimeError(f"Expected {sum(QUOTAS.values())} selected failures, got {len(selected)}")
    return sorted(selected, key=lambda row: int(row.get("index", 0)))


def write_selection(rows, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    write_manifest(rows, output_dir / "input_manifest.jsonl")
    summary = {
        "selection_size": len(rows),
        "selection_rule": "Qwen routed binary errors with fixed anchors and stratified source-family sampling",
        "anchors": ANCHORS,
        "quotas": QUOTAS,
        "groups": Counter(error_group(row) for row in rows),
        "sources": Counter(source_key(row) for row in rows),
        "samples": [
            {
                "index": row["index"],
                "sample_id": row["sample_id"],
                "group": error_group(row),
                "source": source_key(row),
                "caption": row["text"],
                "ground_truth": [row.get("ground_truth_binary"), row.get("ground_truth_class")],
                "qwen_routed": [row.get("predicted_binary"), row.get("predicted_class")],
            }
            for row in rows
        ],
    }
    (output_dir / "selection.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qwen-routed", default="results/full_extracted_skills_soclaas/routed.jsonl")
    parser.add_argument("--output-dir", default="results/gemini_qwen_routed_failures_25")
    parser.add_argument("--image-root", default="data/MMFakeBench_val")
    parser.add_argument("--model", default="gemini-3.7-flash")
    parser.add_argument("--rpm", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--max-output-tokens", type=int, default=1800)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--status", default="results/gemini_qwen_routed_failures_25/status.md")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    rows = select_rows(read_rows(args.qwen_routed))
    summary = write_selection(rows, output_dir)
    print(json.dumps({"selected": len(rows), "groups": summary["groups"], "sources": summary["sources"]}, indent=2))

    status = StatusWriter(args.status)
    status.start()
    try:
        # max_retries=0 is deliberate: the daily Gemini request budget is 25.
        client = GeminiClient(model=args.model, timeout=args.timeout, max_retries=0)
        run_condition(
            rows, "routed", args.image_root, output_dir / "gemini_routed.jsonl",
            status, rpm=args.rpm, concurrency=1,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature, timeout=args.timeout,
            max_retries=0, client=client,
        )
        status.close(phase="finished_gemini_routed_failures",
                     message="Gemini evaluated the selected Qwen routed failures.")
    except Exception as exc:
        status.close(phase="failed", message=f"Fatal error: {exc!r}")
        raise


if __name__ == "__main__":
    main()
