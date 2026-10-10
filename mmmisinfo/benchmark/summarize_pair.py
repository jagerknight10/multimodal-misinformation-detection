"""Create a row-by-row baseline/skill summary from two JSONL result files."""

import argparse
import json
from pathlib import Path

from .compare import compare_rows, read_rows


def summarize(baseline_path, skill_path):
    baseline = read_rows(baseline_path)
    skill = read_rows(skill_path)
    common = sorted(set(baseline) & set(skill), key=lambda key: baseline[key].get("index", key))
    samples = []
    condition_fields = (
        "predicted_binary", "predicted_class", "raw_response", "call_started_sgt",
        "call_duration_seconds", "call_timed_out", "runtime_seconds", "usage", "error",
    )
    for key in common:
        left, right = baseline[key], skill[key]
        samples.append({
            "sample_id": key,
            "index": left.get("index"),
            "validation_index": left.get("validation_index"),
            "text": left.get("text"),
            "image_path": left.get("image_path"),
            "evidence_image_path": left.get("evidence_image_path"),
            "ground_truth_binary": left.get("ground_truth_binary"),
            "ground_truth_class": left.get("ground_truth_class"),
            "evidence_hash": left.get("evidence_hash"),
            "direct_evidence": left.get("direct_evidence", []),
            "inverse_evidence": left.get("inverse_evidence", []),
            "baseline": {field: left.get(field) for field in condition_fields},
            "skill": {field: right.get(field) for field in condition_fields},
        })
    return {
        "schema": "mmfakebench-paired-summary-v1",
        "baseline_source": str(baseline_path),
        "skill_source": str(skill_path),
        "sample_count": len(samples),
        "aggregate_comparison": compare_rows(baseline, skill),
        "samples": samples,
    }


def main():
    parser = argparse.ArgumentParser(description="Create a side-by-side paired JSON summary.")
    parser.add_argument("baseline")
    parser.add_argument("skill")
    parser.add_argument("output")
    args = parser.parse_args()
    result = summarize(args.baseline, args.skill)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "samples": len(result["samples"])}, indent=2))


if __name__ == "__main__":
    main()
