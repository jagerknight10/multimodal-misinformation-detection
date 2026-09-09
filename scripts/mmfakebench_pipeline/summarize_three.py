"""Create a row-by-row baseline/unified/routed summary without API calls."""

import argparse
import json
from pathlib import Path

from .compare import compare_conditions, read_rows


CONDITION_FIELDS = (
    "predicted_binary", "predicted_class", "selected_skills", "raw_response",
    "reported_confidence", "instructions_hash", "skill_bundle_hash",
    "call_started_sgt", "call_duration_seconds", "call_timed_out",
    "runtime_seconds", "usage", "error",
)


def summarize(baseline_path, unified_path, routed_path):
    conditions = {
        "baseline": read_rows(baseline_path),
        "unified": read_rows(unified_path),
        "routed": read_rows(routed_path),
    }
    common = set.intersection(*(set(rows) for rows in conditions.values()))
    common = sorted(common, key=lambda key: conditions["baseline"][key].get("index", key))
    samples = []
    case_groups = {
        "routed_binary_improves_over_baseline": [],
        "routed_binary_regresses_vs_baseline": [],
        "unified_binary_improves_over_baseline": [],
        "unified_binary_regresses_vs_baseline": [],
        "routed_four_way_improves_over_baseline": [],
        "routed_four_way_regresses_vs_baseline": [],
        "all_three_binary_correct": [],
        "all_three_binary_wrong": [],
        "routed_without_reported_skill_selection": [],
    }
    for key in common:
        base = conditions["baseline"][key]
        sample = {
            "sample_id": key,
            "index": base.get("index"),
            "validation_index": base.get("validation_index"),
            "text": base.get("text"),
            "image_path": base.get("image_path"),
            "evidence_image_path": base.get("evidence_image_path"),
            "ground_truth_binary": base.get("ground_truth_binary"),
            "ground_truth_class": base.get("ground_truth_class"),
            "evidence_hash": base.get("evidence_hash"),
            "direct_evidence": base.get("direct_evidence", []),
            "inverse_evidence": base.get("inverse_evidence", []),
        }
        for name, rows in conditions.items():
            sample[name] = {field: rows[key].get(field) for field in CONDITION_FIELDS}
        samples.append(sample)
        truth_binary = base.get("ground_truth_binary")
        truth_class = base.get("ground_truth_class")
        binary_ok = {
            name: rows[key].get("predicted_binary") == truth_binary
            for name, rows in conditions.items()
        }
        class_ok = {
            name: rows[key].get("predicted_class") == truth_class
            for name, rows in conditions.items()
        }
        if binary_ok["routed"] and not binary_ok["baseline"]:
            case_groups["routed_binary_improves_over_baseline"].append(key)
        if binary_ok["baseline"] and not binary_ok["routed"]:
            case_groups["routed_binary_regresses_vs_baseline"].append(key)
        if binary_ok["unified"] and not binary_ok["baseline"]:
            case_groups["unified_binary_improves_over_baseline"].append(key)
        if binary_ok["baseline"] and not binary_ok["unified"]:
            case_groups["unified_binary_regresses_vs_baseline"].append(key)
        if class_ok["routed"] and not class_ok["baseline"]:
            case_groups["routed_four_way_improves_over_baseline"].append(key)
        if class_ok["baseline"] and not class_ok["routed"]:
            case_groups["routed_four_way_regresses_vs_baseline"].append(key)
        if all(binary_ok.values()):
            case_groups["all_three_binary_correct"].append(key)
        if not any(binary_ok.values()):
            case_groups["all_three_binary_wrong"].append(key)
        if not conditions["routed"][key].get("selected_skills"):
            case_groups["routed_without_reported_skill_selection"].append(key)
    return {
        "schema": "mmfakebench-three-condition-summary-v1",
        "sources": {
            "baseline": str(baseline_path),
            "unified": str(unified_path),
            "routed": str(routed_path),
        },
        "sample_count": len(samples),
        "aggregate_comparison": compare_conditions(conditions),
        "representative_case_ids": {
            name: {"count": len(ids), "first_10": ids[:10]}
            for name, ids in case_groups.items()
        },
        "samples": samples,
    }


def main():
    parser = argparse.ArgumentParser(description="Create a three-way side-by-side JSON.")
    parser.add_argument("baseline")
    parser.add_argument("unified")
    parser.add_argument("routed")
    parser.add_argument("output")
    args = parser.parse_args()
    result = summarize(args.baseline, args.unified, args.routed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({"output": str(output), "samples": len(result["samples"])},
                     indent=2))


if __name__ == "__main__":
    main()
