import argparse
from collections import Counter
import json


def read_rows(path):
    rows = {}
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                rows[str(row.get("sample_id", row.get("index")))] = row
    return rows


def _metrics(pairs, prediction, truth):
    pairs = [(row.get(prediction), row.get(truth)) for row in pairs
             if not row.get("error") and row.get(prediction) and row.get(truth)]
    labels = sorted({p for p, _ in pairs} | {g for _, g in pairs})
    matrix = {gold: {pred: 0 for pred in labels} for gold in labels}
    for pred, gold in pairs:
        matrix[gold][pred] += 1
    per_class = {}
    f1s = []
    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[other][label] for other in labels if other != label)
        fn = sum(matrix[label][other] for other in labels if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1s.append(f1)
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1,
                            "support": tp + fn}
    return {"n": len(pairs), "accuracy": sum(p == g for p, g in pairs) / len(pairs)
            if pairs else None, "macro_f1": sum(f1s) / len(f1s) if f1s else None,
            "per_class": per_class, "confusion_matrix_gold_by_prediction": matrix}


def compare_rows(baseline, skill):
    common = sorted(set(baseline) & set(skill))
    pairs = [(baseline[key], skill[key]) for key in common]
    mismatched_hashes = [key for key in common
                         if baseline[key].get("evidence_hash") != skill[key].get("evidence_hash")]
    if mismatched_hashes:
        raise ValueError(f"Evidence differs between conditions for {len(mismatched_hashes)} samples")
    binary_pairs = [(b, s) for b, s in pairs
                    if not b.get("error") and not s.get("error")
                    and b.get("predicted_binary") and s.get("predicted_binary")]
    class_pairs = [(b, s) for b, s in pairs
                   if not b.get("error") and not s.get("error")
                   and b.get("predicted_class") and s.get("predicted_class")]
    result = {
        "baseline_rows": len(baseline), "skill_rows": len(skill), "paired_rows": len(pairs),
        "paired_complete_binary_rows": len(binary_pairs),
        "paired_complete_four_way_rows": len(class_pairs),
        "binary_accuracy": {
            "baseline": _metrics([p[0] for p in binary_pairs], "predicted_binary", "ground_truth_binary"),
            "skill": _metrics([p[1] for p in binary_pairs], "predicted_binary", "ground_truth_binary"),
        },
        "four_way": {
            "baseline": _metrics([p[0] for p in class_pairs], "predicted_class", "ground_truth_class"),
            "skill": _metrics([p[1] for p in class_pairs], "predicted_class", "ground_truth_class"),
        },
        "changed_binary_predictions": sum(p[0].get("predicted_binary") != p[1].get("predicted_binary") for p in pairs),
        "changed_class_predictions": sum(p[0].get("predicted_class") != p[1].get("predicted_class") for p in pairs),
    }
    for metric in ("binary_accuracy", "four_way"):
        result[metric]["delta_accuracy"] = (
            result[metric]["skill"]["accuracy"] - result[metric]["baseline"]["accuracy"]
            if result[metric]["skill"]["accuracy"] is not None and result[metric]["baseline"]["accuracy"] is not None
            else None
        )
    return result


def compare_conditions(conditions):
    """Compare two or more conditions on their common, evidence-matched samples."""
    if "baseline" not in conditions or len(conditions) < 2:
        raise ValueError("A baseline and at least one comparison condition are required")
    names = list(conditions)
    common = set.intersection(*(set(rows) for rows in conditions.values()))
    common = sorted(common)
    mismatched_hashes = [
        key for key in common
        if len({conditions[name][key].get("evidence_hash") for name in names}) != 1
    ]
    if mismatched_hashes:
        raise ValueError(
            f"Evidence differs between conditions for {len(mismatched_hashes)} samples")
    mismatched_bundles = [
        key for key in common
        if len({conditions[name][key].get("skill_bundle_hash") for name in names}) != 1
    ]
    if mismatched_bundles:
        raise ValueError(
            f"Skill bundle differs between conditions for {len(mismatched_bundles)} samples")

    def complete_ids(prediction):
        return [key for key in common if all(
            not conditions[name][key].get("error")
            and conditions[name][key].get(prediction)
            and conditions[name][key].get(
                "ground_truth_binary" if prediction == "predicted_binary"
                else "ground_truth_class")
            for name in names)]

    binary_ids = complete_ids("predicted_binary")
    class_ids = complete_ids("predicted_class")
    binary = {
        name: _metrics([conditions[name][key] for key in binary_ids],
                       "predicted_binary", "ground_truth_binary")
        for name in names
    }
    four_way = {
        name: _metrics([conditions[name][key] for key in class_ids],
                       "predicted_class", "ground_truth_class")
        for name in names
    }
    for metrics in (binary, four_way):
        baseline_accuracy = metrics["baseline"]["accuracy"]
        for name in names:
            accuracy = metrics[name]["accuracy"]
            metrics[name]["delta_accuracy_vs_baseline"] = (
                accuracy - baseline_accuracy
                if accuracy is not None and baseline_accuracy is not None else None)

    paired_changes = {}
    for name in names:
        if name == "baseline":
            continue
        binary_improved = binary_worsened = 0
        for key in binary_ids:
            base = conditions["baseline"][key]
            other = conditions[name][key]
            base_ok = base["predicted_binary"] == base["ground_truth_binary"]
            other_ok = other["predicted_binary"] == other["ground_truth_binary"]
            binary_improved += int(other_ok and not base_ok)
            binary_worsened += int(base_ok and not other_ok)
        class_improved = class_worsened = 0
        for key in class_ids:
            base = conditions["baseline"][key]
            other = conditions[name][key]
            base_ok = base["predicted_class"] == base["ground_truth_class"]
            other_ok = other["predicted_class"] == other["ground_truth_class"]
            class_improved += int(other_ok and not base_ok)
            class_worsened += int(base_ok and not other_ok)
        paired_changes[name] = {
            "changed_binary_predictions": sum(
                conditions["baseline"][key].get("predicted_binary") !=
                conditions[name][key].get("predicted_binary") for key in binary_ids),
            "binary_improved": binary_improved,
            "binary_worsened": binary_worsened,
            "changed_class_predictions": sum(
                conditions["baseline"][key].get("predicted_class") !=
                conditions[name][key].get("predicted_class") for key in class_ids),
            "four_way_improved": class_improved,
            "four_way_worsened": class_worsened,
        }

    class_names = (
        "real", "textual_veracity_distortion", "visual_veracity_distortion",
        "cross_modal_consistency_distortion",
    )
    by_ground_truth_class = {}
    for class_name in class_names:
        ids = [key for key in class_ids
               if conditions["baseline"][key].get("ground_truth_class") == class_name]
        by_ground_truth_class[class_name] = {
            "n": len(ids),
            "binary": {
                name: _metrics([conditions[name][key] for key in ids],
                               "predicted_binary", "ground_truth_binary")
                for name in names
            },
            "four_way": {
                name: _metrics([conditions[name][key] for key in ids],
                               "predicted_class", "ground_truth_class")
                for name in names
            },
        }

    binary_real_vs_distortion = {}
    for class_name in class_names[1:]:
        ids = [key for key in binary_ids if conditions["baseline"][key].get(
            "ground_truth_class") in {"real", class_name}]
        binary_real_vs_distortion[class_name] = {
            name: _metrics([conditions[name][key] for key in ids],
                           "predicted_binary", "ground_truth_binary")
            for name in names
        }

    routing = None
    if "routed" in conditions:
        routed_rows = [conditions["routed"][key] for key in common
                       if not conditions["routed"][key].get("error")]
        combination_counts = Counter(
            ", ".join(row.get("selected_skills") or []) or "(none reported)"
            for row in routed_rows)
        skill_counts = Counter(
            skill for row in routed_rows for skill in (row.get("selected_skills") or []))
        expected = {
            "textual_veracity_distortion": "Check_textual_factuality",
            "visual_veracity_distortion": "Check_visual_manipulation",
            "cross_modal_consistency_distortion": "Check_cross_modal_consistency",
        }
        eligible = [row for row in routed_rows if row.get("ground_truth_class") in expected]
        routing = {
            "rows": len(routed_rows),
            "rows_without_reported_selection": sum(
                not row.get("selected_skills") for row in routed_rows),
            "selection_combinations": dict(combination_counts),
            "individual_skill_selections": dict(skill_counts),
            "gold_distortion_skill_included": sum(
                expected[row["ground_truth_class"]] in (row.get("selected_skills") or [])
                for row in eligible),
            "gold_distortion_rows": len(eligible),
        }

    return {
        "schema": "mmfakebench-three-condition-comparison-v1",
        "condition_rows": {name: len(rows) for name, rows in conditions.items()},
        "paired_rows": len(common),
        "paired_complete_binary_rows": len(binary_ids),
        "paired_complete_four_way_rows": len(class_ids),
        "binary": binary,
        "four_way": four_way,
        "by_ground_truth_class": by_ground_truth_class,
        "binary_real_vs_distortion": binary_real_vs_distortion,
        "paired_changes_vs_baseline": paired_changes,
        "routing": routing,
    }


def main():
    parser = argparse.ArgumentParser(description="Compare matched baseline and skill outputs.")
    parser.add_argument("baseline")
    parser.add_argument("skill")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = compare_rows(read_rows(args.baseline), read_rows(args.skill))
    encoded = json.dumps(result, indent=2)
    print(encoded)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(encoded + "\n")


if __name__ == "__main__":
    main()
