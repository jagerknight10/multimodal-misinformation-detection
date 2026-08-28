import argparse
import json


def read_rows(path):
    return {row["index"]: row for row in
            (json.loads(line) for line in open(path, encoding="utf-8") if line.strip())}


def accuracy(rows, prediction, truth):
    pairs = [(row.get(prediction), row.get(truth)) for row in rows if not row.get("error")]
    pairs = [(p, g) for p, g in pairs if p is not None and g is not None]
    return sum(p == g for p, g in pairs) / len(pairs) if pairs else None


def main():
    parser = argparse.ArgumentParser(description="Compare matched baseline and skill JSONL outputs.")
    parser.add_argument("baseline")
    parser.add_argument("skill")
    args = parser.parse_args()
    baseline, skill = read_rows(args.baseline), read_rows(args.skill)
    common = sorted(set(baseline) & set(skill))
    pairs = [{"index": index, "baseline": baseline[index], "skill": skill[index]}
             for index in common]
    binary = {
        "baseline": accuracy([p["baseline"] for p in pairs], "predicted_binary", "ground_truth_binary"),
        "skill": accuracy([p["skill"] for p in pairs], "predicted_binary", "ground_truth_binary"),
    }
    four_way = {
        "baseline": accuracy([p["baseline"] for p in pairs], "predicted_class", "ground_truth_class"),
        "skill": accuracy([p["skill"] for p in pairs], "predicted_class", "ground_truth_class"),
    }
    print(json.dumps({
        "baseline_rows": len(baseline), "skill_rows": len(skill), "paired_rows": len(pairs),
        "binary_accuracy": binary,
        "binary_accuracy_delta": (binary["skill"] - binary["baseline"]
                                   if binary["skill"] is not None and binary["baseline"] is not None else None),
        "four_way_accuracy": four_way,
        "four_way_accuracy_delta": (four_way["skill"] - four_way["baseline"]
                                     if four_way["skill"] is not None and four_way["baseline"] is not None else None),
        "changed_binary_predictions": sum(
            p["baseline"].get("predicted_binary") != p["skill"].get("predicted_binary") for p in pairs
        ),
        "changed_class_predictions": sum(
            p["baseline"].get("predicted_class") != p["skill"].get("predicted_class") for p in pairs
        ),
    }, indent=2))


if __name__ == "__main__":
    main()
