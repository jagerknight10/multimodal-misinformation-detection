import argparse
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
