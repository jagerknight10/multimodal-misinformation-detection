import argparse
import json


def norm_binary(value):
    value = str(value).strip().lower()
    return value.title() if value in {"real", "fake"} else None


def main():
    parser = argparse.ArgumentParser(description="Evaluate MMFakeBench JSONL predictions.")
    parser.add_argument("predictions")
    args = parser.parse_args()
    rows = [json.loads(line) for line in open(args.predictions, encoding="utf-8") if line.strip()]
    valid = [row for row in rows if not row.get("error")]
    binary = [(norm_binary(r.get("predicted_binary")), norm_binary(r.get("ground_truth_binary")))
              for r in valid]
    classes = [(r.get("predicted_class"), r.get("ground_truth_class")) for r in valid]

    def report(pairs):
        pairs = [(p, g) for p, g in pairs if p and g]
        labels = sorted({p for p, _ in pairs} | {g for _, g in pairs})
        matrix = {label: {other: 0 for other in labels} for label in labels}
        for prediction, gold in pairs:
            matrix[gold][prediction] += 1
        accuracy = sum(p == g for p, g in pairs) / len(pairs) if pairs else None
        f1s = []
        per_class = {}
        for label in labels:
            tp = matrix[label][label]
            fp = sum(matrix[other][label] for other in labels if other != label)
            fn = sum(matrix[label][other] for other in labels if other != label)
            precision = tp / (tp + fp) if tp + fp else 0
            recall = tp / (tp + fn) if tp + fn else 0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
            f1s.append(f1)
            per_class[label] = {"precision": precision, "recall": recall, "f1": f1,
                                "support": tp + fn}
        return {"n": len(pairs), "accuracy": accuracy,
                "macro_f1": sum(f1s) / len(f1s) if f1s else None,
                "per_class": per_class,
                "confusion_matrix_gold_by_prediction": matrix}

    usage = [r.get("usage") or {} for r in valid]
    print(json.dumps({
        "rows": len(rows), "successful": len(valid), "errors": len(rows) - len(valid),
        "runtime_seconds": sum(r.get("runtime_seconds") or 0 for r in valid),
        "usage": {
            "input_tokens": sum(u.get("input_tokens", 0) for u in usage),
            "output_tokens": sum(u.get("output_tokens", 0) for u in usage),
            "total_tokens": sum(u.get("total_tokens", u.get("input_tokens", 0) + u.get("output_tokens", 0))
                              for u in usage),
        },
        "binary": report(binary), "four_way": report(classes),
    }, indent=2))


if __name__ == "__main__":
    main()
